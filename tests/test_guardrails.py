"""
Unit tests for guardrails – no real API or DB calls needed.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient


# ─── Rate limiter ────────────────────────────────────────────────────────────

def test_rate_limit_passes_under_threshold():
    from app.guardrails import check_rate_limit, _rate_buckets

    _rate_buckets.clear()
    mock_request = MagicMock()
    mock_request.client.host = "1.2.3.4"

    for _ in range(5):
        check_rate_limit(mock_request)


def test_rate_limit_blocks_over_threshold():
    from app.guardrails import check_rate_limit, _rate_buckets
    from app.config import settings

    _rate_buckets.clear()
    mock_request = MagicMock()
    mock_request.client.host = "9.9.9.9"

    for _ in range(settings.max_requests_per_minute):
        check_rate_limit(mock_request)

    with pytest.raises(HTTPException) as exc:
        check_rate_limit(mock_request)

    assert exc.value.status_code == 429


# ─── Max turns ───────────────────────────────────────────────────────────────

def test_max_turns_passes_within_limit():
    from app.guardrails import check_max_turns
    check_max_turns(5)


def test_max_turns_blocks_over_limit():
    from app.guardrails import check_max_turns
    from app.config import settings

    with pytest.raises(HTTPException) as exc:
        check_max_turns(settings.max_turns_per_conversation + 1)

    assert exc.value.status_code == 400


# ─── Input validation ────────────────────────────────────────────────────────

def test_validate_input_strips_whitespace():
    from app.guardrails import validate_input
    result = validate_input("  hello world  ")
    assert result == "hello world"


def test_validate_input_rejects_empty():
    from app.guardrails import validate_input
    with pytest.raises(HTTPException) as exc:
        validate_input("   ")
    assert exc.value.status_code == 422


# ─── Health endpoint ─────────────────────────────────────────────────────────

def test_health_endpoint():
    with patch("app.database.get_supabase"), patch("app.agent.anthropic"):
        from app.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
