from __future__ import annotations

from src.matching.years_extractor import extract_required_years


def test_extract_required_years_handles_plus_notation() -> None:
    assert extract_required_years("We require 5+ years of experience.") == 5.0


def test_extract_required_years_handles_range_notation() -> None:
    assert extract_required_years("Looking for someone with 3-5 years of experience.") == 3.0


def test_extract_required_years_handles_italian() -> None:
    assert extract_required_years("Richiesti almeno 4 anni di esperienza.") == 4.0


def test_extract_required_years_returns_none_when_not_mentioned() -> None:
    assert extract_required_years("Great opportunity to grow your career.") is None


def test_extract_required_years_returns_none_for_empty_or_none() -> None:
    assert extract_required_years(None) is None
    assert extract_required_years("") is None
