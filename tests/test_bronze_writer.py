from __future__ import annotations

import shutil
import tempfile
from datetime import date, datetime, timezone

import pytest

from src.bronze.spark_session import get_spark_session
from src.bronze.writer import BronzeWriter
from src.ingestion.models import RawJobPosting


@pytest.fixture(scope="module")
def spark():
    session = get_spark_session(app_name="test-bronze")
    yield session
    session.stop()


@pytest.fixture()
def bronze_path():
    path = tempfile.mkdtemp(prefix="bronze_test_")
    yield path
    shutil.rmtree(path, ignore_errors=True)


def _sample_posting(job_id: str) -> RawJobPosting:
    return RawJobPosting(
        source="greenhouse",
        source_job_id=job_id,
        company_identifier="acme",
        fetched_at=datetime.now(timezone.utc),
        url=f"https://boards.greenhouse.io/acme/jobs/{job_id}",
        raw_payload={"id": job_id, "title": "Data Engineer"},
    )


def test_write_creates_delta_table_with_correct_row_count(spark, bronze_path) -> None:
    writer = BronzeWriter(spark, bronze_path)
    postings = [_sample_posting("1"), _sample_posting("2")]

    written = writer.write(postings, ingestion_date=date(2026, 8, 4))

    assert written == 2
    df = spark.read.format("delta").load(bronze_path)
    assert df.count() == 2


def test_write_is_append_only_across_two_batches(spark, bronze_path) -> None:
    writer = BronzeWriter(spark, bronze_path)

    writer.write([_sample_posting("1")], ingestion_date=date(2026, 8, 3))
    writer.write([_sample_posting("1")], ingestion_date=date(2026, 8, 4))

    df = spark.read.format("delta").load(bronze_path)
    # Stessa offerta vista in due batch diversi: entrambe le righe restano,
    # perché Bronze è append-only per costruzione.
    assert df.count() == 2
    distinct_dates = df.select("ingestion_date").distinct().count()
    assert distinct_dates == 2


def test_write_with_empty_list_does_not_create_table(spark, bronze_path) -> None:
    writer = BronzeWriter(spark, bronze_path)
    written = writer.write([])

    assert written == 0
    with pytest.raises(Exception):  # noqa: B017
        spark.read.format("delta").load(bronze_path)


def test_partitioning_by_source_and_ingestion_date(spark, bronze_path) -> None:
    import os

    writer = BronzeWriter(spark, bronze_path)
    writer.write([_sample_posting("1")], ingestion_date=date(2026, 8, 4))

    partition_dirs = [
        d for d in os.listdir(bronze_path) if d.startswith("source=")
    ]
    assert any("source=greenhouse" in d for d in partition_dirs)
