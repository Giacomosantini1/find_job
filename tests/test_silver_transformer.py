from __future__ import annotations

import shutil
import tempfile
from datetime import date, datetime, timezone

import pytest

from src.bronze.spark_session import get_spark_session
from src.bronze.writer import BronzeWriter
from src.ingestion.models import RawJobPosting
from src.silver.transformer import SilverTransformer


@pytest.fixture(scope="module")
def spark():
    session = get_spark_session(app_name="test-silver")
    yield session
    session.stop()


@pytest.fixture()
def paths():
    bronze_path = tempfile.mkdtemp(prefix="bronze_test_")
    silver_path = tempfile.mkdtemp(prefix="silver_test_")
    yield bronze_path, silver_path
    shutil.rmtree(bronze_path, ignore_errors=True)
    shutil.rmtree(silver_path, ignore_errors=True)


def _greenhouse_posting(job_id: str, title: str = "Data Engineer") -> RawJobPosting:
    return RawJobPosting(
        source="greenhouse",
        source_job_id=job_id,
        company_identifier="acme",
        fetched_at=datetime.now(timezone.utc),
        url=f"https://boards.greenhouse.io/acme/jobs/{job_id}",
        raw_payload={
            "id": job_id,
            "title": title,
            "updated_at": "2026-01-14T10:55:28-05:00",
            "location": {"name": "Rome, Italy"},
            "content": "<p>Great opportunity</p>",
        },
    )


def _smartrecruiters_posting(job_id: str) -> RawJobPosting:
    return RawJobPosting(
        source="smartrecruiters",
        source_job_id=job_id,
        company_identifier="bosch",
        fetched_at=datetime.now(timezone.utc),
        url=f"https://jobs.smartrecruiters.com/bosch/{job_id}",
        raw_payload={
            "id": job_id,
            "name": "Data Platform Lead",
            "location": {"city": "Milan", "country": "it", "remote": True},
            "releasedDate": "2026-01-14T10:55:28.000Z",
            "jobAd": {"sections": {"jobDescription": {"text": "Build platforms"}}},
        },
    )


def test_transform_produces_unified_schema_from_mixed_sources(spark, paths) -> None:
    bronze_path, silver_path = paths
    writer = BronzeWriter(spark, bronze_path)
    writer.write(
        [_greenhouse_posting("1"), _smartrecruiters_posting("2")],
        ingestion_date=date(2026, 8, 4),
    )

    transformer = SilverTransformer(spark, bronze_path, silver_path)
    written = transformer.transform()

    assert written == 2
    silver_df = spark.read.format("delta").load(silver_path)
    rows = {row["job_id"]: row for row in silver_df.collect()}

    assert "greenhouse:1" in rows
    assert "smartrecruiters:2" in rows
    assert rows["greenhouse:1"]["company"] == "acme"
    assert rows["smartrecruiters:2"]["remote"] is True


def test_transform_upserts_on_second_run_without_duplicating(spark, paths) -> None:
    bronze_path, silver_path = paths
    writer = BronzeWriter(spark, bronze_path)
    transformer = SilverTransformer(spark, bronze_path, silver_path)

    writer.write([_greenhouse_posting("1", title="Data Engineer")], ingestion_date=date(2026, 8, 3))
    transformer.transform()

    # Stessa offerta ri-scaricata in un batch successivo (titolo aggiornato):
    # Silver deve aggiornare la riga esistente, non duplicarla.
    writer.write([_greenhouse_posting("1", title="Senior Data Engineer")], ingestion_date=date(2026, 8, 4))
    transformer.transform()

    silver_df = spark.read.format("delta").load(silver_path)
    assert silver_df.count() == 1
    assert silver_df.collect()[0]["title"] == "Senior Data Engineer"


def test_transform_with_empty_bronze_returns_zero(spark, paths) -> None:
    bronze_path, _silver_path = paths
    writer = BronzeWriter(spark, bronze_path)
    writer.write([_greenhouse_posting("1")], ingestion_date=date(2026, 8, 4))

    # Filtra bronze a un path vuoto separato per simulare "nessun dato nuovo"
    empty_bronze_path = tempfile.mkdtemp(prefix="bronze_empty_")
    try:
        writer_empty = BronzeWriter(spark, empty_bronze_path)
        written = writer_empty.write([])
        assert written == 0
    finally:
        shutil.rmtree(empty_bronze_path, ignore_errors=True)
