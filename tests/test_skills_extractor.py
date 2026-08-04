from __future__ import annotations

from src.skills.extractor import extract_technologies


def test_extract_technologies_finds_multiple_known_technologies() -> None:
    text = "We use Databricks, PySpark and Azure Data Factory for our pipelines."
    result = extract_technologies(text)

    assert "Databricks" in result
    assert "Spark" in result
    assert "Azure" in result
    assert "Azure Data Factory" in result


def test_extract_technologies_is_case_insensitive() -> None:
    text = "Experience with DOCKER, kubernetes and Terraform required."
    result = extract_technologies(text)

    assert "Docker" in result
    assert "Kubernetes" in result
    assert "Terraform" in result


def test_extract_technologies_avoids_false_positive_substring_match() -> None:
    # "sql" non deve fare match dentro "graphql" o "nosql"
    text = "We are looking for a GraphQL and NoSQL expert."
    result = extract_technologies(text)

    assert "SQL" not in result


def test_extract_technologies_handles_multi_word_variants() -> None:
    text = "Strong knowledge of Power BI and PowerBI dashboards."
    result = extract_technologies(text)

    assert "Power BI" in result


def test_extract_technologies_returns_empty_list_for_none_or_empty() -> None:
    assert extract_technologies(None) == []
    assert extract_technologies("") == []


def test_extract_technologies_returns_sorted_deduplicated_list() -> None:
    text = "Python, python, PYTHON and also Scala."
    result = extract_technologies(text)

    assert result == sorted(set(result))
    assert result.count("Python") == 1


def test_extract_technologies_returns_empty_when_no_known_tech_mentioned() -> None:
    text = "We are looking for a great communicator with leadership skills."
    result = extract_technologies(text)

    assert result == []
