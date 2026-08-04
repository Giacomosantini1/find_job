from __future__ import annotations

import shutil
import tempfile
from datetime import date, datetime, timezone

import pytest

from src.bronze.spark_session import get_spark_session
from src.bronze.writer import BronzeWriter
from src.gold.new_removed_postings import compute_new_postings, compute_removed_postings
from src.ingestion.models import RawJobPosting


@pytest.fixture(scope="module")
def spark():
    session = get_spark_session(app_name="test-gold-new-removed")
    yield session
    session.stop()


@pytest.fixture()
def bronze_path():
    path = tempfile.mkdtemp(prefix="bronze_gold_test_")
    yield path
    shutil.rmtree(path, ignore_errors=True)


def _posting(job_id: str) -> RawJobPosting:
    return RawJobPosting(
        source="greenhouse",
        source_job_id=job_id,
        company_identifier="acme",
        fetched_at=datetime.now(timezone.utc),
        url=f"https://boards.greenhouse.io/acme/jobs/{job_id}",
        raw_payload={"id": job_id, "title": "Data Engineer"},
    )


def test_compute_new_postings_detects_job_added_in_latest_batch(spark, bronze_path) -> None:
    writer = BronzeWriter(spark, bronze_path)
    writer.write([_posting("1"), _posting("2")], ingestion_date=date(2026, 8, 3))
    writer.write([_posting("1"), _posting("2"), _posting("3")], ingestion_date=date(2026, 8, 4))

    new_df = compute_new_postings(
        spark, bronze_path, previous_date=date(2026, 8, 3), current_date=date(2026, 8, 4)
    )
    new_job_ids = {row["job_id"] for row in new_df.collect()}

    assert new_job_ids == {"greenhouse:3"}


def test_compute_removed_postings_detects_job_missing_in_latest_batch(spark, bronze_path) -> None:
    writer = BronzeWriter(spark, bronze_path)
    writer.write([_posting("1"), _posting("2")], ingestion_date=date(2026, 8, 3))
    writer.write([_posting("1")], ingestion_date=date(2026, 8, 4))

    removed_df = compute_removed_postings(
        spark, bronze_path, previous_date=date(2026, 8, 3), current_date=date(2026, 8, 4)
    )
    removed_job_ids = {row["job_id"] for row in removed_df.collect()}

    assert removed_job_ids == {"greenhouse:2"}


def test_compute_new_postings_is_empty_when_batches_are_identical(spark, bronze_path) -> None:
    writer = BronzeWriter(spark, bronze_path)
    writer.write([_posting("1")], ingestion_date=date(2026, 8, 3))
    writer.write([_posting("1")], ingestion_date=date(2026, 8, 4))

    new_df = compute_new_postings(
        spark, bronze_path, previous_date=date(2026, 8, 3), current_date=date(2026, 8, 4)
    )

    assert new_df.count() == 0
