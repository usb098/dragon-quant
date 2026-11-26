"""Optional HTTP Basic Auth for a remotely hosted dashboard."""
from __future__ import annotations

import base64
import binascii
import hmac
from typing import Any


def basic_auth_matches(header: str | None, username: str, password: str) -> bool:
    if not header or not username or not password:
        return False
    scheme, separator, token = header.partition(" ")
    if not separator or scheme.lower() != "basic" or not token:
        return False
    try:
        decoded = base64.b64decode(token, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return False
    supplied_user, separator, supplied_password = decoded.partition(":")
    if not separator:
        return False
    return (
        hmac.compare_digest(supplied_user.encode("utf-8"), username.encode("utf-8"))
        and hmac.compare_digest(supplied_password.encode("utf-8"), password.encode("utf-8"))
    )


class BasicAuthMiddleware:
    """Protect every HTTP route except explicit health probes."""

    def __init__(
        self, app: Any, *, username: str, password: str,
        required: bool = False, exempt_paths: set[str] | None = None,
        realm: str = "dragon-quant dashboard",
    ) -> None:
        self.app = app
        self.username = username
        self.password = password
        self.required = required
        self.exempt_paths = exempt_paths or {"/health"}
        self.challenge = b'Basic realm="' + realm.encode("ascii", "ignore") + b'", charset="UTF-8"'

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        if not self.required or scope.get("path", "") in self.exempt_paths:
            await self.app(scope, receive, send)
            return
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        raw = headers.get(b"authorization")
        header = raw.decode("latin-1") if raw else None
        if basic_auth_matches(header, self.username, self.password):
            await self.app(scope, receive, send)
            return
        body = b"Authentication required"
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"text/plain; charset=utf-8"),
                (b"content-length", str(len(body)).encode("ascii")),
                (b"www-authenticate", self.challenge),
                (b"cache-control", b"no-store"),
            ],
        })
        await send({"type": "http.response.body", "body": body})


__all__ = ["BasicAuthMiddleware", "basic_auth_matches"]
