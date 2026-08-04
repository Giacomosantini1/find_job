from __future__ import annotations

import re

from .catalog import TECHNOLOGY_CATALOG


def _build_pattern_index(
    catalog: dict[str, list[str]],
) -> list[tuple[str, re.Pattern[str]]]:
    """Precompila un pattern regex per ogni voce del catalogo fornito.

    Funzione generica: usata sia per il catalogo tecnologie (Fase 5) sia
    per il catalogo keyword metodologiche/soft (Fase 6, Matching Engine),
    evitando di duplicare la logica di compilazione dei pattern.
    """
    index: list[tuple[str, re.Pattern[str]]] = []
    for canonical_name, variants in catalog.items():
        escaped_variants = [re.escape(v) for v in variants]
        pattern = re.compile(
            r"\b(?:" + "|".join(escaped_variants) + r")\b", re.IGNORECASE
        )
        index.append((canonical_name, pattern))
    return index


def extract_matches(text: str | None, catalog: dict[str, list[str]]) -> list[str]:
    """Estrae le voci del catalogo menzionate nel testo, in modo deterministico.

    Ritorna una lista ordinata alfabeticamente, senza duplicati.
    """
    if not text:
        return []

    pattern_index = _build_pattern_index(catalog)
    found = {
        canonical_name
        for canonical_name, pattern in pattern_index
        if pattern.search(text)
    }
    return sorted(found)


_TECHNOLOGY_PATTERN_INDEX = _build_pattern_index(TECHNOLOGY_CATALOG)


def extract_technologies(text: str | None) -> list[str]:
    """Estrae le tecnologie note menzionate nel testo (catalogo Fase 5).

    Mantiene una firma dedicata (invece di richiedere sempre il catalogo
    esplicito) perché è il caso d'uso più frequente nella pipeline
    (Silver enrichment, Fase 5) ed è quello coperto dai test storici.
    """
    if not text:
        return []

    found = {
        canonical_name
        for canonical_name, pattern in _TECHNOLOGY_PATTERN_INDEX
        if pattern.search(text)
    }
    return sorted(found)
