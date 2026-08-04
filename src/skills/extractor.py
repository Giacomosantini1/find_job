from __future__ import annotations

import re

from .catalog import TECHNOLOGY_CATALOG


def _build_pattern_index() -> list[tuple[str, re.Pattern[str]]]:
    """Precompila un pattern regex per ogni tecnologia del catalogo.

    Ogni variante viene racchiusa in `\\b...\\b` (word-boundary) per evitare
    falsi positivi banali (es. "sql" non deve far match dentro "graphql").
    Le varianti multi-parola (es. "power bi") funzionano comunque, perché
    `\\b` si applica correttamente anche a bordi di frase con spazi interni.
    """
    index: list[tuple[str, re.Pattern[str]]] = []
    for canonical_name, variants in TECHNOLOGY_CATALOG.items():
        escaped_variants = [re.escape(v) for v in variants]
        pattern = re.compile(
            r"\b(?:" + "|".join(escaped_variants) + r")\b", re.IGNORECASE
        )
        index.append((canonical_name, pattern))
    return index


_PATTERN_INDEX = _build_pattern_index()


def extract_technologies(text: str | None) -> list[str]:
    """Estrae le tecnologie note menzionate nel testo, in modo deterministico.

    Ritorna una lista ordinata alfabeticamente (per rendere l'output stabile
    e facilmente testabile/confrontabile), senza duplicati.
    """
    if not text:
        return []

    found = {
        canonical_name
        for canonical_name, pattern in _PATTERN_INDEX
        if pattern.search(text)
    }
    return sorted(found)
