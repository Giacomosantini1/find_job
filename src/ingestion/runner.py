from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import TARGETS, IngestionTarget, RiskTier
from .connectors.greenhouse import GreenhouseConnector
from .connectors.smartrecruiters import SmartRecruitersConnector
from .models import RawJobPosting

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_CONNECTOR_REGISTRY = {
    "greenhouse": GreenhouseConnector(),
    "smartrecruiters": SmartRecruitersConnector(),
}


def _fetch_target(target: IngestionTarget) -> list[RawJobPosting]:
    connector = _CONNECTOR_REGISTRY[target.source]
    postings = connector.fetch(target.company_identifier)
    logger.info(
        "source=%s company=%s fetched=%d",
        target.source, target.company_identifier, len(postings),
    )
    return postings


def run_ingestion(max_workers: int = 4) -> list[RawJobPosting]:
    """Esegue l'ingestion per tutti i target attivi in parallelo (I/O-bound)."""
    active_targets = [t for t in TARGETS if t.risk_tier != RiskTier.EXCLUDED]
    results: list[RawJobPosting] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_target = {
            executor.submit(_fetch_target, target): target for target in active_targets
        }
        for future in as_completed(future_to_target):
            target = future_to_target[future]
            try:
                results.extend(future.result())
            except RuntimeError as exc:
                logger.error("failed target=%s: %s", target, exc)

    return results


if __name__ == "__main__":
    postings = run_ingestion()
    logger.info("Totale offerte raccolte: %d", len(postings))
