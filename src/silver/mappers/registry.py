from __future__ import annotations

from .base import SourceMapper
from .greenhouse import GreenhouseMapper
from .smartrecruiters import SmartRecruitersMapper

# Aggiungere una fonte = aggiungere una riga qui (+ il nuovo mapper).
# Nessun'altra parte del Silver layer richiede modifiche.
MAPPER_REGISTRY: dict[str, SourceMapper] = {
    "greenhouse": GreenhouseMapper(),
    "smartrecruiters": SmartRecruitersMapper(),
}


def get_mapper(source: str) -> SourceMapper:
    try:
        return MAPPER_REGISTRY[source]
    except KeyError as exc:
        raise ValueError(
            f"Nessun mapper registrato per la fonte '{source}'. "
            f"Fonti disponibili: {list(MAPPER_REGISTRY)}"
        ) from exc
