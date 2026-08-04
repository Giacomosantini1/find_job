from __future__ import annotations

from collections.abc import Iterator

from ..base import JobBoardConnector
from ..models import RawJobPosting


class SmartRecruitersConnector(JobBoardConnector):
    """Posting API pubblica di SmartRecruiters, nessuna autenticazione richiesta.

    Docs: https://developers.smartrecruiters.com/
    """

    source_name = "smartrecruiters"

    def build_request_url(self, company_identifier: str) -> str:
        return (
            f"https://api.smartrecruiters.com/v1/companies/"
            f"{company_identifier}/postings?limit=100"
        )

    def parse_response(
        self, company_identifier: str, payload: dict
    ) -> Iterator[RawJobPosting]:
        jobs = payload.get("content", payload.get("postings", []))
        for job in jobs:
            yield RawJobPosting(
                source=self.source_name,
                source_job_id=str(job["id"]),
                company_identifier=company_identifier,
                fetched_at=RawJobPosting.now(),
                url=job.get("applyUrl", job.get("jobAdUrl", "")),
                raw_payload=job,
            )
