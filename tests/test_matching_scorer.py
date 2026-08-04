from __future__ import annotations

from src.matching.cv_profile import CVProfile
from src.matching.scorer import compute_match


def _cv(technologies: frozenset[str], years: float = 5.0, keywords: frozenset[str] = frozenset()) -> CVProfile:
    return CVProfile(technologies=technologies, keywords=keywords, years_experience=years)


def test_full_skill_match_and_sufficient_years_gives_high_score() -> None:
    cv = _cv(frozenset({"Databricks", "Spark", "Azure"}), years=5.0)
    result = compute_match(
        cv, job_id="greenhouse:1",
        posting_technologies=["Databricks", "Spark", "Azure"],
        description="Requires 3+ years of experience.",
    )

    assert result.score == 100
    assert result.matched_skills == ["Azure", "Databricks", "Spark"]
    assert result.missing_skills == []


def test_partial_skill_match_reduces_score_proportionally() -> None:
    cv = _cv(frozenset({"Databricks"}), years=5.0)
    result = compute_match(
        cv, job_id="greenhouse:2",
        posting_technologies=["Databricks", "Spark", "Kafka"],
        description=None,
    )

    # skill_ratio = 1/3, years neutro (nessun requisito) -> years_score=1.0
    # base = (1/3 * 0.7 + 1.0 * 0.3) * 100 = 53.33 -> round 53
    assert result.score == 53
    assert result.matched_skills == ["Databricks"]
    assert result.missing_skills == ["Kafka", "Spark"]


def test_insufficient_years_penalizes_score() -> None:
    cv = _cv(frozenset({"Databricks"}), years=2.0)
    result = compute_match(
        cv, job_id="greenhouse:3",
        posting_technologies=["Databricks"],
        description="Requires 5+ years of experience.",
    )

    assert result.required_years == 5.0
    assert result.years_gap == -3.0
    # skill_ratio = 1.0 (full match), years_score = max(0, 1 + (-3/5)) = 0.4
    # base = (1.0*0.7 + 0.4*0.3)*100 = 82
    assert result.score == 82


def test_no_technologies_required_treats_skill_component_as_neutral() -> None:
    cv = _cv(frozenset({"Databricks"}), years=5.0)
    result = compute_match(
        cv, job_id="greenhouse:4", posting_technologies=None, description=None
    )

    # skill_ratio neutro = 0.5, years neutro = 1.0
    # base = (0.5*0.7 + 1.0*0.3)*100 = 65
    assert result.score == 65
    assert result.matched_skills == []
    assert result.missing_skills == []


def test_matched_keywords_add_bonus_without_exceeding_cap() -> None:
    cv = _cv(
        frozenset({"Databricks"}),
        years=5.0,
        keywords=frozenset({"Agile", "Scrum", "ETL/ELT", "DevOps", "Mentoring", "CI/CD"}),
    )
    result = compute_match(
        cv, job_id="greenhouse:5",
        posting_technologies=["Databricks"],
        description="We work in Agile with Scrum, strong ETL background, DevOps culture, CI/CD pipelines and mentoring.",
    )

    # skill_ratio=1.0, years neutro=1.0 -> base = 100, bonus cappato a +10 ma già a 100 -> resta 100
    assert result.score == 100
    assert len(result.matched_keywords) >= 5


def test_score_never_goes_below_zero() -> None:
    cv = _cv(frozenset(), years=1.0)
    result = compute_match(
        cv, job_id="greenhouse:6",
        posting_technologies=["Databricks", "Spark", "Kafka"],
        description="Requires 10+ years of experience.",
    )

    assert 0 <= result.score <= 100
    assert result.missing_skills == ["Databricks", "Kafka", "Spark"]
