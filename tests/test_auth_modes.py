from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_BACKEND))

from ai_knowledge_assistant import auth


def _bearer(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_dev_mode_accepts_dev_token(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "dev")
    monkeypatch.setenv("DEV_BEARER_TOKEN", "dev-local-token")
    monkeypatch.delenv("DEV_USER_ID", raising=False)
    monkeypatch.setenv("DEV_BEARER_USER_ID", "user-alpha")

    user_id = asyncio.run(auth.current_user_id(creds=_bearer("dev-local-token")))

    assert user_id == "user-alpha"


def test_clerk_mode_resolves_user(monkeypatch):
    class _Identity:
        auth_subject = "user_clerk_123"
        email = "user@example.com"
        display_name = "User Example"

    monkeypatch.setenv("AUTH_MODE", "clerk")
    monkeypatch.delenv("DEV_USER_ID", raising=False)
    monkeypatch.setattr(auth, "verify_clerk_jwt", lambda token: _Identity())
    monkeypatch.setattr(
        auth.registry,
        "ensure_user_for_auth_subject",
        lambda auth_subject, email=None, display_name=None: "clerk:resolved-user",
    )

    user_id = asyncio.run(auth.current_user_id(creds=_bearer("fake-clerk-jwt")))

    assert user_id == "clerk:resolved-user"


def test_clerk_mode_rejects_invalid_token(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "clerk")
    monkeypatch.delenv("DEV_USER_ID", raising=False)
    monkeypatch.setattr(auth, "verify_clerk_jwt", lambda token: (_ for _ in ()).throw(ValueError("bad jwt")))

    try:
        asyncio.run(auth.current_user_id(creds=_bearer("bad")))
    except HTTPException as exc:
        assert exc.status_code == 401
        assert "Invalid Clerk token" in str(exc.detail)
    else:
        raise AssertionError("Expected HTTPException")
