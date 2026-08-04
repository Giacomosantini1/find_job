from __future__ import annotations

import shutil
import tempfile
from datetime import date, datetime, timezone

import pytest

from src.bronze.spark_session import get_spark_session
from src.bronze.writer import BronzeWriter
from src.gold.active_companies import compute_active_companies
from src.gold.duplicate_postings import compute_duplicate_postings
from src.gold.tech_trends import compute_tech_trends
from src.ingestion.models import RawJobPosting
from src.silver.transformer import SilverTransformer


@pytest.fixture(scope="module")
def spark():
    session = get_spark_session(app_name="test-gold-silver-views")
    yield session
    session.stop()


@pytest.fixture()
def paths():
    bronze_path = tempfile.mkdtemp(prefix="bronze_gold_silver_")
    silver_path = tempfile.mkdtemp(prefix="silver_gold_silver_")
    yield bronze_path, silver_path
    shutil.rmtree(bronze_path, ignore_errors=True)
    shutil.rmtree(silver_path, ignore_errors=True)


def _greenhouse_posting(job_id: str, title: str, company: str) -> RawJobPosting:
    return RawJobPosting(
        source="greenhouse",
        source_job_id=job_id,
        company_identifier=company,
        fetched_at=datetime.now(timezone.utc),
        url=f"https://boards.greenhouse.io/{company}/jobs/{job_id}",
        raw_payload={"id": job_id, "title": title},
    )


def _smartrecruiters_posting(job_id: str, title: str, company: str) -> RawJobPosting:
    return RawJobPosting(
        source="smartrecruiters",
        source_job_id=job_id,
        company_identifier=company,
        fetched_at=datetime.now(timezone.utc),
        url=f"https://jobs.smartrecruiters.com/{company}/{job_id}",
        raw_payload={"id": job_id, "name": title},
    )


def _seed_silver(spark, bronze_path: str, silver_path: str, postings: list[RawJobPosting]) -> None:
    BronzeWriter(spark, bronze_path).write(postings, ingestion_date=date(2026, 8, 4))
    SilverTransformer(spark, bronze_path, silver_path).transform()


def test_compute_duplicate_postings_matches_same_title_and_company_across_sources(
    spark, paths
) -> None:
    bronze_path, silver_path = paths
    _seed_silver(
        spark, bronze_path, silver_path,
        [
            _greenhouse_posting("1", "Senior Data Engineer", "acme"),
            _smartrecruiters_posting("2", "Senior Data Engineer", "acme"),
            _greenhouse_posting("3", "QA Engineer", "acme"),
        ],
    )

    duplicates_df = compute_duplicate_postings(spark, silver_path)
    duplicate_job_ids = {row["job_id"] for row in duplicates_df.collect()}

    assert duplicate_job_ids == {"greenhouse:1", "smartrecruiters:2"}


def test_compute_duplicate_postings_ignores_case_and_spacing(spark, paths) -> None:
    bronze_path, silver_path = paths
    _seed_silver(
        spark, bronze_path, silver_path,
        [
            _greenhouse_posting("1", "Data   Engineer", "acme"),
            _smartrecruiters_posting("2", "data engineer", "acme"),
        ],
    )

    duplicates_df = compute_duplicate_postings(spark, silver_path)
    assert duplicates_df.count() == 2


def test_compute_active_companies_ranks_by_open_postings_count(spark, paths) -> None:
    bronze_path, silver_path = paths
    _seed_silver(
        spark, bronze_path, silver_path,
        [
            _greenhouse_posting("1", "Data Engineer", "acme"),
            _greenhouse_posting("2", "QA Engineer", "acme"),
            _smartrecruiters_posting("3", "Sales Manager", "bosch"),
        ],
    )

    ranking_df = compute_active_companies(spark, silver_path)
    rows = ranking_df.collect()

    assert rows[0]["company"] == "acme"
    assert rows[0]["open_postings_count"] == 2
    assert rows[1]["company"] == "bosch"
    assert rows[1]["open_postings_count"] == 1


def test_compute_tech_trends_returns_empty_when_technologies_not_yet_populated(
    spark, paths
) -> None:
    bronze_path, silver_path = paths
    _seed_silver(
        spark, bronze_path, silver_path,
        [_greenhouse_posting("1", "Data Engineer", "acme")],
    )

    trends_df = compute_tech_trends(spark, silver_path)

    # Fase 5 (Skill Extraction) non è ancora implementata: `technologies`
    # è sempre None in questa fase, quindi la vista è vuota per costruzione.
    assert trends_df.count() == 0
