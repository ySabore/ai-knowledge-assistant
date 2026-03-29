"""Development bearer auth. Wire Clerk/JWT verification for production."""

from __future__ import annotations

import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import config
from . import registry
from .clerk_auth import verify_clerk_jwt

_scheme = HTTPBearer(auto_error=False)


async def current_user_id(
    creds: HTTPAuthorizationCredentials | None = Depends(_scheme),
) -> str:
    mode = config.auth_mode()
    fixed = config.dev_user_id()
    if mode == "dev" and fixed:
        return fixed

    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")
    if mode == "clerk":
        try:
            identity = verify_clerk_jwt(creds.credentials)
            return registry.ensure_user_for_auth_subject(
                identity.auth_subject,
                email=identity.email,
                display_name=identity.display_name,
            )
        except Exception as exc:
            raise HTTPException(status_code=401, detail=f"Invalid Clerk token: {exc}") from exc

    if mode != "dev":
        raise HTTPException(status_code=500, detail="Invalid AUTH_MODE; use dev or clerk")

    if creds.credentials != config.dev_bearer_token():
        raise HTTPException(status_code=401, detail="Invalid bearer token")
    return os.environ.get("DEV_BEARER_USER_ID", "user-alpha")
