from __future__ import annotations

import shutil
import tempfile
from datetime import date, datetime, timezone

import pytest

from src.bronze.spark_session import get_spark_session
from src.bronze.writer import BronzeWriter
from src.gold.matching import compute_match_scores
from src.ingestion.models import RawJobPosting
from src.matching.cv_profile import build_cv_profile
from src.silver.transformer import SilverTransformer

_SAMPLE_CV_TEXT = """
Senior Data Engineer with 5+ years of experience delivering scalable data
platforms and ETL/ELT solutions on Azure. Skilled in Azure Databricks,
Apache Spark, PySpark, Azure Data Factory, SQL Server, Power BI, Git,
Azure DevOps and Agile delivery.
"""


@pytest.fixture(scope="module")
def spark():
    session = get_spark_session(app_name="test-gold-matching")
    yield session
    session.stop()


@pytest.fixture()
def paths():
    bronze_path = tempfile.mkdtemp(prefix="bronze_matching_test_")
    silver_path = tempfile.mkdtemp(prefix="silver_matching_test_")
    yield bronze_path, silver_path
    shutil.rmtree(bronze_path, ignore_errors=True)
    shutil.rmtree(silver_path, ignore_errors=True)


def _posting(job_id: str, description_html: str) -> RawJobPosting:
    return RawJobPosting(
        source="greenhouse",
        source_job_id=job_id,
        company_identifier="acme",
        fetched_at=datetime.now(timezone.utc),
        url=f"https://boards.greenhouse.io/acme/jobs/{job_id}",
        raw_payload={
            "id": job_id,
            "title": "Data Engineer",
            "updated_at": "2026-01-14T10:55:28-05:00",
            "content": description_html,
        },
    )


def test_compute_match_scores_ranks_best_fit_posting_first(spark, paths) -> None:
    bronze_path, silver_path = paths
    writer = BronzeWriter(spark, bronze_path)
    writer.write(
        [
            # Ottimo fit: stesso stack del CV, requisito anni soddisfatto
            _posting(
                "1",
                "<p>Azure Databricks, Apache Spark, Azure Data Factory. "
                "3+ years of experience required.</p>",
            ),
            # Fit scarso: stack completamente diverso, requisito anni alto
            _posting(
                "2",
                "<p>Looking for a Kafka and Kubernetes expert. "
                "10+ years of experience required.</p>",
            ),
        ],
        ingestion_date=date(2026, 8, 4),
    )

    SilverTransformer(spark, bronze_path, silver_path).transform()

    cv_profile = build_cv_profile(_SAMPLE_CV_TEXT, years_experience=5.0)
    matches_df = compute_match_scores(spark, silver_path, cv_profile)
    rows = matches_df.collect()

    scores_by_job_id = {row["job_id"]: row["match_score"] for row in rows}

    assert scores_by_job_id["greenhouse:1"] > scores_by_job_id["greenhouse:2"]
    # Il primo risultato (ordinato per score desc) deve essere il best fit
    assert rows[0]["job_id"] == "greenhouse:1"


def test_compute_match_scores_reports_missing_skills(spark, paths) -> None:
    bronze_path, silver_path = paths
    writer = BronzeWriter(spark, bronze_path)
    writer.write(
        [_posting("1", "<p>Requires Snowflake, Kafka and Terraform.</p>")],
        ingestion_date=date(2026, 8, 4),
    )

    SilverTransformer(spark, bronze_path, silver_path).transform()

    cv_profile = build_cv_profile(_SAMPLE_CV_TEXT, years_experience=5.0)
    matches_df = compute_match_scores(spark, silver_path, cv_profile)
    row = matches_df.collect()[0]

    missing = set(row["missing_skills"])
    assert "Snowflake" in missing
    assert "Kafka" in missing
    assert "Terraform" in missing
    assert row["rationale"] is not None
