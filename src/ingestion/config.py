from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RiskTier(str, Enum):
    """Classificazione del rischio legale/ToS di ogni fonte.

    NONE     -> API pubblica ufficiale, nessuna zona grigia (Greenhouse, SmartRecruiters).
    LOW      -> Dati pubblici per finalità istituzionale (es. inPA, sitemap SuccessFactors).
    MEDIUM   -> Endpoint non documentato ma usato dal frontend stesso (Workday tenant JSON).
    EXCLUDED -> Automazione esclusa per policy esplicita (LinkedIn).
    """

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    EXCLUDED = "excluded"


@dataclass(frozen=True, slots=True)
class IngestionTarget:
    source: str
    company_identifier: str
    risk_tier: RiskTier


# Elenco dichiarativo delle fonti da interrogare.
# Aggiungere una fonte = aggiungere una riga qui (+ eventuale nuovo connector).
TARGETS: list[IngestionTarget] = [
    IngestionTarget("greenhouse", "stripe", RiskTier.NONE),
    IngestionTarget("greenhouse", "airbnb", RiskTier.NONE),
    IngestionTarget("smartrecruiters", "bosch", RiskTier.NONE),
]
