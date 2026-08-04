from __future__ import annotations

from src.silver.mappers.greenhouse import GreenhouseMapper
from src.silver.mappers.smartrecruiters import SmartRecruitersMapper


def test_greenhouse_mapper_produces_canonical_record() -> None:
    mapper = GreenhouseMapper()
    payload = {
        "id": 12345,
        "title": "Senior Data Engineer",
        "updated_at": "2026-01-14T10:55:28-05:00",
        "location": {"name": "Rome, Italy"},
        "absolute_url": "https://boards.greenhouse.io/acme/jobs/12345",
        "content": "<p>Great <b>remote</b> opportunity</p>",
    }

    record = mapper.map(
        raw_payload=payload,
        company_identifier="acme",
        source_job_id="12345",
        url=payload["absolute_url"],
    )

    assert record["job_id"] == "greenhouse:12345"
    assert record["company"] == "acme"
    assert record["title"] == "Senior Data Engineer"
    assert record["location"] == "Rome, Italy"
    assert record["remote"] is True
    assert record["description"] == "Great remote opportunity"
    assert record["salary"] is None
    assert record["technologies"] is None
    assert record["source"] == "greenhouse"
    assert record["link"] == "https://boards.greenhouse.io/acme/jobs/12345"
    assert record["publication_date"] is not None


def test_greenhouse_mapper_handles_missing_optional_fields() -> None:
    mapper = GreenhouseMapper()
    payload = {"id": 1, "title": "Data Analyst"}

    record = mapper.map(
        raw_payload=payload, company_identifier="acme", source_job_id="1", url=None
    )

    assert record["location"] is None
    assert record["description"] is None
    assert record["publication_date"] is None
    assert record["link"] is None


def test_smartrecruiters_mapper_produces_canonical_record() -> None:
    mapper = SmartRecruitersMapper()
    payload = {
        "id": "98765",
        "name": "Data Platform Lead",
        "location": {"city": "Milan", "region": "Lombardy", "country": "it", "remote": True},
        "releasedDate": "2026-01-14T10:55:28.000Z",
        "applyUrl": "https://jobs.smartrecruiters.com/acme/98765",
        "jobAd": {"sections": {"jobDescription": {"text": "Build data platforms"}}},
    }

    record = mapper.map(
        raw_payload=payload,
        company_identifier="acme",
        source_job_id="98765",
        url=payload["applyUrl"],
    )

    assert record["job_id"] == "smartrecruiters:98765"
    assert record["location"] == "Milan, Lombardy, it"
    assert record["remote"] is True
    assert record["description"] == "Build data platforms"
    assert record["source"] == "smartrecruiters"
    assert record["publication_date"] is not None


def test_smartrecruiters_mapper_handles_missing_location() -> None:
    mapper = SmartRecruitersMapper()
    payload = {"id": "1", "name": "QA Engineer"}

    record = mapper.map(
        raw_payload=payload, company_identifier="acme", source_job_id="1", url=None
    )

    assert record["location"] is None
    assert record["remote"] is False
    assert record["description"] is None
