from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from .base import SilverRecord, SourceMapper

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str | None) -> str | None:
    if not text:
        return None
    without_tags = _HTML_TAG_RE.sub(" ", text)
    collapsed = re.sub(r"\s+", " ", without_tags).strip()
    return collapsed or None


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class GreenhouseMapper(SourceMapper):
    """Normalizza il payload della Job Board API di Greenhouse.

    Forma tipica del payload (vedi Fase 1, connectors/greenhouse.py):
    {
        "id": 12345,
        "title": "...",
        "updated_at": "2026-01-14T10:55:28-05:00",
        "location": {"name": "Rome, Italy"},
        "absolute_url": "https://...",
        "content": "<p>HTML description...</p>",
    }
    """

    source_name = "greenhouse"

    def map(
        self,
        raw_payload: dict[str, Any],
        company_identifier: str,
        source_job_id: str,
        url: str | None,
    ) -> SilverRecord:
        location_name = (raw_payload.get("location") or {}).get("name")
        description = _strip_html(raw_payload.get("content"))
        title = raw_payload.get("title", "")

        return SilverRecord(
            job_id=self.build_job_id(source_job_id),
            company=company_identifier,
            title=title,
            location=location_name,
            remote=self.looks_remote(location_name, title, description),
            salary=None,  # Greenhouse Job Board API non espone la retribuzione
            description=description,
            technologies=None,  # popolato in Fase 5 (Skill Extraction)
            source=self.source_name,
            publication_date=_parse_iso_datetime(raw_payload.get("updated_at")),
            link=url or raw_payload.get("absolute_url"),
        )
