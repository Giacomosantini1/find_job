from __future__ import annotations

import re

# Pattern per riconoscere richieste di esperienza espresse in anni, sia in
# inglese che in italiano, con o senza il simbolo "+" (es. "5+ years",
# "3-5 years", "5 anni di esperienza"). Il gruppo catturato è sempre il
# primo numero incontrato: per un intervallo (es. "3-5 anni") lo
# interpretiamo come requisito minimo, quindi prendiamo il valore più
# basso dell'intervallo (coerente con "almeno 3 anni").
_YEARS_PATTERN = re.compile(
    r"(\d+)\s*(?:\+)?\s*(?:-\s*\d+\s*)?\s*(?:years?|anni)\b",
    re.IGNORECASE,
)


def extract_required_years(text: str | None) -> float | None:
    """Estrae il numero minimo di anni di esperienza richiesti dal testo.

    Ritorna `None` se il testo non menziona esplicitamente un requisito di
    anni di esperienza: in quel caso il chiamante (scorer.py) tratta
    l'assenza del requisito come neutrale, non come penalità.
    """
    if not text:
        return None

    match = _YEARS_PATTERN.search(text)
    if not match:
        return None

    return float(match.group(1))
