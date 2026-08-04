from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.ingestion.connectors.greenhouse import GreenhouseConnector
from src.ingestion.connectors.smartrecruiters import SmartRecruitersConnector


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    if status_code >= 400:
        error = requests.HTTPError(response=mock_resp)
        mock_resp.raise_for_status.side_effect = error
    else:
        mock_resp.raise_for_status.side_effect = None
    return mock_resp


def test_greenhouse_connector_parses_jobs() -> None:
    payload = {
        "jobs": [
            {
                "id": 12345,
                "title": "Senior Data Engineer",
                "absolute_url": "https://boards.greenhouse.io/acme/jobs/12345",
            }
        ]
    }
    connector = GreenhouseConnector()
    with patch.object(
        connector.session, "get", return_value=_mock_response(payload)
    ) as mocked_get:
        results = connector.fetch("acme")

    mocked_get.assert_called_once()
    assert len(results) == 1
    assert results[0].source == "greenhouse"
    assert results[0].source_job_id == "12345"
    assert results[0].company_identifier == "acme"
    assert results[0].url == "https://boards.greenhouse.io/acme/jobs/12345"
    assert results[0].raw_payload["title"] == "Senior Data Engineer"


def test_smartrecruiters_connector_parses_postings() -> None:
    payload = {
        "content": [
            {
                "id": "98765",
                "name": "Data Platform Lead",
                "applyUrl": "https://jobs.smartrecruiters.com/acme/98765",
            }
        ]
    }
    connector = SmartRecruitersConnector()
    with patch.object(connector.session, "get", return_value=_mock_response(payload)):
        results = connector.fetch("acme")

    assert len(results) == 1
    assert results[0].source == "smartrecruiters"
    assert results[0].source_job_id == "98765"
    assert results[0].url == "https://jobs.smartrecruiters.com/acme/98765"


def test_greenhouse_connector_raises_on_non_retryable_error() -> None:
    connector = GreenhouseConnector()
    error_response = _mock_response({"error": "not found"}, status_code=404)

    with patch.object(connector.session, "get", return_value=error_response):
        with pytest.raises(RuntimeError, match="non-retryable"):
            connector.fetch("unknown-co")


def test_greenhouse_connector_retries_on_server_error_then_succeeds() -> None:
    payload = {
        "jobs": [
            {"id": 1, "title": "X", "absolute_url": "https://example.com/1"}
        ]
    }
    connector = GreenhouseConnector()
    connector.backoff_base_seconds = 0.01  # velocizza il test
    connector.min_seconds_between_requests = 0.0

    error_response = _mock_response({}, status_code=503)
    success_response = _mock_response(payload, status_code=200)

    with patch.object(
        connector.session, "get", side_effect=[error_response, success_response]
    ) as mocked_get:
        results = connector.fetch("acme")

    assert mocked_get.call_count == 2
    assert len(results) == 1
