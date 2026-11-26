from __future__ import annotations

import base64

from web_ui.backend.auth import basic_auth_matches
from web_ui.backend.http_guards import origin_allowed


def _basic(username: str, password: str) -> str:
    token = base64.b64encode((username + ":" + password).encode()).decode()
    return "Basic " + token


def test_basic_auth_rejects_missing_malformed_and_wrong_credentials():
    password = "a-secure-password-that-is-long-enough"
    assert not basic_auth_matches(None, "viewer", password)
    assert not basic_auth_matches("Bearer abc", "viewer", password)
    assert not basic_auth_matches("Basic !!!", "viewer", password)
    assert not basic_auth_matches(_basic("viewer", "wrong"), "viewer", password)


def test_basic_auth_accepts_matching_credentials():
    password = "a-secure-password-that-is-long-enough"
    assert basic_auth_matches(_basic("viewer", password), "viewer", password)


def test_origin_allowlist_is_exact_and_rejects_cross_site(monkeypatch):
    monkeypatch.setenv("DQ_ALLOWED_ORIGINS", "https://dashboard.example.com")
    assert origin_allowed("https://dashboard.example.com")
    assert not origin_allowed("https://evil.example.com")
    assert not origin_allowed("https://dashboard.example.com.attacker.test")
    assert not origin_allowed("null")
