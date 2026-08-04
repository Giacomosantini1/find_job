from __future__ import annotations

from collections.abc import Iterator

from ..base import JobBoardConnector
from ..models import RawJobPosting


class GreenhouseConnector(JobBoardConnector):
    """Job Board API pubblica di Greenhouse, nessuna autenticazione richiesta.

    Docs: https://developers.greenhouse.io/job-board.html
    """

    source_name = "greenhouse"

    def build_request_url(self, company_identifier: str) -> str:
        return (
            f"https://boards-api.greenhouse.io/v1/boards/"
            f"{company_identifier}/jobs?content=true"
        )

    def parse_response(
        self, company_identifier: str, payload: dict
    ) -> Iterator[RawJobPosting]:
        for job in payload.get("jobs", []):
            yield RawJobPosting(
                source=self.source_name,
                source_job_id=str(job["id"]),
                company_identifier=company_identifier,
                fetched_at=RawJobPosting.now(),
                url=job.get("absolute_url", ""),
                raw_payload=job,
            )
