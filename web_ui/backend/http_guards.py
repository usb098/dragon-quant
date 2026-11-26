"""HTTP write guards: localhost by default, explicit same-origin allowlist in cloud."""
from __future__ import annotations

import os
from urllib.parse import urlsplit

_ALLOWED_ORIGIN_HOSTS = {"localhost", "127.0.0.1", "::1"}


def origin_allowed(origin: str) -> bool:
    try:
        parsed = urlsplit(origin)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        return False
    if parsed.hostname.lower() in _ALLOWED_ORIGIN_HOSTS:
        return True
    allowed = {
        item.strip().rstrip("/").lower()
        for item in os.environ.get("DQ_ALLOWED_ORIGINS", "").split(",")
        if item.strip()
    }
    return (parsed.scheme.lower() + "://" + parsed.netloc.lower()) in allowed


__all__ = ["origin_allowed"]
