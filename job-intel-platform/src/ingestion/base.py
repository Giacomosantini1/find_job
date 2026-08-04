from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Iterator

import requests

from .models import RawJobPosting

logger = logging.getLogger(__name__)

# Status code che NON vale la pena ritentare: l'errore è nella richiesta,
# non transitorio (board_token sbagliato, company non trovata, ecc.)
_NON_RETRYABLE_STATUS = {400, 401, 403, 404}


class JobBoardConnector(ABC):
    """Contratto comune per ogni fonte di offerte di lavoro.

    Ogni nuova fonte implementa solo `build_request_url` e `parse_response`;
    tutta la logica di retry/backoff è centralizzata qui.
    """

    source_name: str
    max_retries: int = 4
    backoff_base_seconds: float = 1.5
    min_seconds_between_requests: float = 0.5

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self._last_request_at: float = 0.0

    @abstractmethod
    def build_request_url(self, company_identifier: str) -> str:
        ...

    @abstractmethod
    def parse_response(
        self, company_identifier: str, payload: dict
    ) -> Iterator[RawJobPosting]:
        ...

    def fetch(self, company_identifier: str) -> list[RawJobPosting]:
        url = self.build_request_url(company_identifier)
        payload = self._get_with_retry(url)
        return list(self.parse_response(company_identifier, payload))

    def _respect_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait_for = self.min_seconds_between_requests - elapsed
        if wait_for > 0:
            time.sleep(wait_for)
        self._last_request_at = time.monotonic()

    def _get_with_retry(self, url: str) -> dict:
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            self._respect_rate_limit()
            try:
                response = self.session.get(
                    url,
                    timeout=15,
                    headers={"User-Agent": "job-intel-platform/0.1 (portfolio project)"},
                )
                if response.status_code in _NON_RETRYABLE_STATUS:
                    response.raise_for_status()
                response.raise_for_status()
                return response.json()
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status in _NON_RETRYABLE_STATUS:
                    logger.error(
                        "source=%s url=%s non-retryable status=%s, aborting",
                        self.source_name, url, status,
                    )
                    raise RuntimeError(
                        f"[{self.source_name}] non-retryable error {status} for {url}"
                    ) from exc
                last_exc = exc
            except requests.RequestException as exc:
                last_exc = exc

            sleep_for = self.backoff_base_seconds * (2 ** (attempt - 1))
            logger.warning(
                "source=%s url=%s attempt=%d/%d failed (%s), retrying in %.1fs",
                self.source_name, url, attempt, self.max_retries, last_exc, sleep_for,
            )
            time.sleep(sleep_for)

        raise RuntimeError(
            f"[{self.source_name}] exhausted retries for {url}"
        ) from last_exc
