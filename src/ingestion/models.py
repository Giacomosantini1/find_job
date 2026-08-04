from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class RawJobPosting:
    """Rappresenta un'offerta di lavoro grezza, così come ricevuta dalla fonte.

    Nessuna normalizzazione qui: quella avviene nel Silver layer (Fase 3).
    """

    source: str
    source_job_id: str
    company_identifier: str
    fetched_at: datetime
    url: str
    raw_payload: dict[str, Any]

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)
