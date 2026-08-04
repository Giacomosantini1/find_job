from __future__ import annotations

from dataclasses import dataclass

from src.skills.extractor import extract_matches, extract_technologies

from .keywords import KEYWORD_CATALOG


@dataclass(frozen=True, slots=True)
class CVProfile:
    """Rappresentazione strutturata del CV per il Matching Engine.

    `technologies` e `keywords` sono estratte con lo stesso identico
    vocabolario (TECHNOLOGY_CATALOG/KEYWORD_CATALOG) usato per le offerte
    in Silver (Fase 5): questo garantisce che il confronto CV-vs-offerta
    avvenga sempre sullo stesso "linguaggio", senza mismatch di sinonimi
    non previsti dal catalogo.
    """

    technologies: frozenset[str]
    keywords: frozenset[str]
    years_experience: float


def build_cv_profile(cv_text: str, years_experience: float) -> CVProfile:
    technologies = frozenset(extract_technologies(cv_text))
    keywords = frozenset(extract_matches(cv_text, KEYWORD_CATALOG))
    return CVProfile(
        technologies=technologies,
        keywords=keywords,
        years_experience=years_experience,
    )
