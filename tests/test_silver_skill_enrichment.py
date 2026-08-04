from __future__ import annotations

import shutil
import tempfile
from datetime import date, datetime, timezone

import pytest

from src.bronze.spark_session import get_spark_session
from src.bronze.writer import BronzeWriter
from src.gold.tech_trends import compute_tech_trends
from src.ingestion.models import RawJobPosting
from src.silver.transformer import SilverTransformer


@pytest.fixture(scope="module")
def spark():
    session = get_spark_session(app_name="test-silver-skill-enrichment")
    yield session
    session.stop()


@pytest.fixture()
def paths():
    bronze_path = tempfile.mkdtemp(prefix="bronze_skill_test_")
    silver_path = tempfile.mkdtemp(prefix="silver_skill_test_")
    yield bronze_path, silver_path
    shutil.rmtree(bronze_path, ignore_errors=True)
    shutil.rmtree(silver_path, ignore_errors=True)


def _greenhouse_posting_with_description(job_id: str, description_html: str) -> RawJobPosting:
    return RawJobPosting(
        source="greenhouse",
        source_job_id=job_id,
        company_identifier="acme",
        fetched_at=datetime.now(timezone.utc),
        url=f"https://boards.greenhouse.io/acme/jobs/{job_id}",
        raw_payload={
            "id": job_id,
            "title": "Senior Data Engineer",
            "updated_at": "2026-01-14T10:55:28-05:00",
            "content": description_html,
        },
    )


def test_silver_transform_populates_technologies_from_description(spark, paths) -> None:
    bronze_path, silver_path = paths
    writer = BronzeWriter(spark, bronze_path)
    writer.write(
        [
            _greenhouse_posting_with_description(
                "1", "<p>We need Databricks, PySpark and Azure experience.</p>"
            )
        ],
        ingestion_date=date(2026, 8, 4),
    )

    transformer = SilverTransformer(spark, bronze_path, silver_path)
    transformer.transform()

    silver_df = spark.read.format("delta").load(silver_path)
    row = silver_df.filter(silver_df.job_id == "greenhouse:1").collect()[0]

    technologies = set(row["technologies"])
    assert "Databricks" in technologies
    assert "Spark" in technologies
    assert "Azure" in technologies


def test_gold_tech_trends_reflects_extracted_skills_end_to_end(spark, paths) -> None:
    bronze_path, silver_path = paths
    writer = BronzeWriter(spark, bronze_path)
    writer.write(
        [
            _greenhouse_posting_with_description(
                "1", "<p>Databricks and Spark required.</p>"
            ),
            _greenhouse_posting_with_description(
                "2", "<p>Databricks and Kubernetes required.</p>"
            ),
        ],
        ingestion_date=date(2026, 8, 4),
    )

    transformer = SilverTransformer(spark, bronze_path, silver_path)
    transformer.transform()

    trends_df = compute_tech_trends(spark, silver_path)
    trends = {row["technology"]: row["mentions_count"] for row in trends_df.collect()}

    # Databricks compare in entrambe le offerte, Spark e Kubernetes una sola volta
    assert trends["Databricks"] == 2
    assert trends["Spark"] == 1
    assert trends["Kubernetes"] == 1
