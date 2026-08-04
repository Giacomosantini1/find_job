from __future__ import annotations

from datetime import datetime
from typing import Any

from .base import SilverRecord, SourceMapper


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # SmartRecruiters usa spesso il suffisso "Z" per UTC, non sempre
        # compatibile con fromisoformat prima di Python 3.11+.
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_location(location: dict[str, Any] | None) -> str | None:
    if not location:
        return None
    parts = [
        location.get("city"),
        location.get("region"),
        location.get("country"),
    ]
    joined = ", ".join(p for p in parts if p)
    return joined or None


class SmartRecruitersMapper(SourceMapper):
    """Normalizza il payload della Posting API pubblica di SmartRecruiters.

    Forma tipica del payload (vedi Fase 1, connectors/smartrecruiters.py):
    {
        "id": "98765",
        "name": "...",
        "location": {"city": "Rome", "region": "Lazio", "country": "it",
                      "remote": true},
        "releasedDate": "2026-01-14T10:55:28.000Z",
        "applyUrl": "https://...",
        "jobAd": {"sections": {"jobDescription": {"text": "..."}}},
    }
    """

    source_name = "smartrecruiters"

    def map(
        self,
        raw_payload: dict[str, Any],
        company_identifier: str,
        source_job_id: str,
        url: str | None,
    ) -> SilverRecord:
        location = raw_payload.get("location") or {}
        location_str = _format_location(location)
        title = raw_payload.get("name", "")
        description = (
            (raw_payload.get("jobAd") or {})
            .get("sections", {})
            .get("jobDescription", {})
            .get("text")
        )
        is_remote_flag = bool(location.get("remote", False))

        return SilverRecord(
            job_id=self.build_job_id(source_job_id),
            company=company_identifier,
            title=title,
            location=location_str,
            remote=is_remote_flag or self.looks_remote(location_str, title, description),
            salary=None,  # non esposta dalla Posting API pubblica
            description=description,
            technologies=None,  # popolato in Fase 5 (Skill Extraction)
            source=self.source_name,
            publication_date=_parse_iso_datetime(raw_payload.get("releasedDate")),
            link=url or raw_payload.get("applyUrl"),
        )
