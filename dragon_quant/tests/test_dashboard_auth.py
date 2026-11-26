from __future__ import annotations

import base64

import pytest

from dragon_quant.intelligence.llm_agent import agent_status
from web_ui.backend.auth import basic_auth_matches
from web_ui.backend.app import create_app


def test_basic_auth_matches_valid_credentials_and_rejects_invalid_headers():
    encoded = base64.b64encode("demo:long-secret".encode()).decode()
    assert basic_auth_matches("Basic " + encoded, "demo", "long-secret")
    assert not basic_auth_matches("Basic " + encoded, "demo", "wrong")
    assert not basic_auth_matches("Bearer " + encoded, "demo", "long-secret")
    assert not basic_auth_matches("Basic !!!", "demo", "long-secret")
    assert not basic_auth_matches(None, "demo", "long-secret")


def test_public_dashboard_refuses_missing_or_short_basic_auth_password(monkeypatch):
    monkeypatch.setenv("DQ_PUBLIC_DEPLOYMENT", "1")
    monkeypatch.setenv("DQ_DASHBOARD_USERNAME", "demo")
    monkeypatch.setenv("DQ_DASHBOARD_PASSWORD", "too-short")
    monkeypatch.setenv("DQ_ALLOWED_HOSTS", "example.test")
    with pytest.raises(RuntimeError, match="at least 32 characters"):
        create_app()


def test_public_dashboard_requires_explicit_allowed_host(monkeypatch):
    monkeypatch.setenv("DQ_PUBLIC_DEPLOYMENT", "1")
    monkeypatch.setenv("DQ_DASHBOARD_USERNAME", "demo")
    monkeypatch.setenv("DQ_DASHBOARD_PASSWORD", "x" * 40)
    monkeypatch.delenv("DQ_ALLOWED_HOSTS", raising=False)
    with pytest.raises(RuntimeError, match="DQ_ALLOWED_HOSTS"):
        create_app()


def test_agent_status_never_returns_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "never-return-this-value")
    monkeypatch.setenv("DQ_INTELLIGENCE_LLM_ENABLED", "1")
    payload = agent_status()
    assert payload["configured"] is True
    assert payload["enabled"] is True
    assert "never-return-this-value" not in repr(payload)
    assert "OPENAI_API_KEY" not in payload
