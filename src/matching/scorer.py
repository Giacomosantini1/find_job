from __future__ import annotations

from dataclasses import dataclass

from src.skills.extractor import extract_matches

from .cv_profile import CVProfile
from .keywords import KEYWORD_CATALOG
from .years_extractor import extract_required_years

# Pesi della formula di scoring, dichiarati esplicitamente come costanti
# (non "magic number" sparsi) per essere facilmente discutibili/regolabili:
# - 70% del punteggio dipende dalla copertura delle tecnologie richieste
#   esplicitamente nell'offerta (il segnale più oggettivo e verificabile).
# - 30% dipende dal fit sugli anni di esperienza richiesti.
# - Un piccolo bonus (max +10 punti) premia le keyword metodologiche in
#   comune (Agile, ETL, Data Warehouse, ecc.), senza però poter mai
#   sostituire la componente tecnica.
_SKILL_WEIGHT = 0.7
_YEARS_WEIGHT = 0.3
_MAX_KEYWORD_BONUS_POINTS = 10
_KEYWORD_BONUS_PER_MATCH = 2


@dataclass(frozen=True, slots=True)
class MatchResult:
    job_id: str
    score: int
    matched_skills: list[str]
    missing_skills: list[str]
    matched_keywords: list[str]
    required_years: float | None
    years_gap: float | None
    rationale: str


def _compute_skill_ratio(
    required_skills: set[str], cv_technologies: frozenset[str]
) -> tuple[float, list[str], list[str]]:
    if not required_skills:
        # L'offerta non menziona esplicitamente tecnologie: trattiamo come
        # neutrale (né penalizzante né premiante), non come "match perfetto".
        return 0.5, [], []

    matched = sorted(required_skills & cv_technologies)
    missing = sorted(required_skills - cv_technologies)
    ratio = len(matched) / len(required_skills)
    return ratio, matched, missing


def _compute_years_score(
    required_years: float | None, candidate_years: float
) -> tuple[float, float | None]:
    if required_years is None:
        # Nessun requisito esplicito di anni: componente neutrale (1.0),
        # non penalizza né premia.
        return 1.0, None

    gap = candidate_years - required_years
    if gap >= 0:
        return 1.0, gap

    # Penalità proporzionale al gap relativo al requisito; mai sotto zero.
    penalty_score = max(0.0, 1.0 + gap / max(required_years, 1.0))
    return penalty_score, gap


def _build_rationale(
    skill_ratio: float,
    matched_skills: list[str],
    missing_skills: list[str],
    years_score: float,
    required_years: float | None,
    years_gap: float | None,
    matched_keywords: list[str],
) -> str:
    parts = []

    if matched_skills or missing_skills:
        parts.append(
            f"Copertura tecnologica: {len(matched_skills)}/"
            f"{len(matched_skills) + len(missing_skills)} skill richieste presenti "
            f"nel CV ({skill_ratio:.0%})."
        )
    else:
        parts.append("Nessuna tecnologia esplicita richiesta dall'offerta.")

    if required_years is not None and years_gap is not None:
        if years_gap >= 0:
            parts.append(
                f"Esperienza richiesta: {required_years:.0f} anni, "
                f"soddisfatta (margine di +{years_gap:.0f})."
            )
        else:
            parts.append(
                f"Esperienza richiesta: {required_years:.0f} anni, "
                f"gap di {abs(years_gap):.0f} anni rispetto al profilo."
            )
    else:
        parts.append("Nessun requisito esplicito di anni di esperienza rilevato.")

    if matched_keywords:
        parts.append(f"Parole chiave in comune: {', '.join(matched_keywords)}.")

    return " ".join(parts)


def compute_match(
    cv: CVProfile,
    job_id: str,
    posting_technologies: list[str] | None,
    description: str | None,
) -> MatchResult:
    """Calcola lo score 0-100 di affinità tra il CV e una singola offerta.

    Formula deterministica e interamente spiegabile (si veda `rationale`):
    nessun componente stocastico o non riproducibile, requisito importante
    dato che questo score guida decisioni concrete dell'utente (a quali
    offerte candidarsi).
    """
    required_skills = set(posting_technologies or [])
    skill_ratio, matched_skills, missing_skills = _compute_skill_ratio(
        required_skills, cv.technologies
    )

    required_years = extract_required_years(description)
    years_score, years_gap = _compute_years_score(required_years, cv.years_experience)

    posting_keywords = set(extract_matches(description, KEYWORD_CATALOG))
    matched_keywords = sorted(cv.keywords & posting_keywords)
    keyword_bonus = min(
        len(matched_keywords) * _KEYWORD_BONUS_PER_MATCH, _MAX_KEYWORD_BONUS_POINTS
    )

    base_score = (skill_ratio * _SKILL_WEIGHT + years_score * _YEARS_WEIGHT) * 100
    final_score = max(0, min(100, round(base_score + keyword_bonus)))

    rationale = _build_rationale(
        skill_ratio, matched_skills, missing_skills,
        years_score, required_years, years_gap, matched_keywords,
    )

    return MatchResult(
        job_id=job_id,
        score=final_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        matched_keywords=matched_keywords,
        required_years=required_years,
        years_gap=years_gap,
        rationale=rationale,
    )
