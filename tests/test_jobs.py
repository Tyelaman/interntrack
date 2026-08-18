from unittest.mock import Mock

import pytest
import requests

import jobs


def test_missing_credentials_raise_job_search_error(monkeypatch):
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)

    with pytest.raises(jobs.JobSearchError, match="not configured"):
        jobs.search_jobs("python", "")


def test_api_failure_becomes_friendly_job_search_error(monkeypatch):
    monkeypatch.setenv("ADZUNA_APP_ID", "fake-id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "fake-key")
    monkeypatch.setattr(
        jobs.requests,
        "get",
        Mock(side_effect=requests.Timeout),
    )

    with pytest.raises(jobs.JobSearchError, match="took too long"):
        jobs.search_jobs("python", "Remote")


def test_results_without_ids_are_skipped_and_missing_urls_become_none(
    monkeypatch,
):
    monkeypatch.setenv("ADZUNA_APP_ID", "fake-id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "fake-key")
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "count": 2,
        "results": [
            {"title": "Missing ID"},
            {
                "id": "valid-id",
                "title": "Valid Job",
                "company": {"display_name": "Example Corp"},
                "location": {"display_name": "Remote"},
            },
        ],
    }
    get_mock = Mock(return_value=response)
    monkeypatch.setattr(jobs.requests, "get", get_mock)

    results, total = jobs.search_jobs("python", "")

    assert total == 2
    assert len(results) == 1
    assert results[0]["external_id"] == "valid-id"
    assert results[0]["apply_url"] is None
    get_mock.assert_called_once()
