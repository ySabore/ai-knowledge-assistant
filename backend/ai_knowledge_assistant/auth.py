"""Development bearer auth. Wire Clerk/JWT verification for production."""

from __future__ import annotations

import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import config

_scheme = HTTPBearer(auto_error=False)


async def current_user_id(
    creds: HTTPAuthorizationCredentials | None = Depends(_scheme),
) -> str:
    fixed = config.dev_user_id()
    if fixed:
        return fixed
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")
    if creds.credentials != config.dev_bearer_token():
        raise HTTPException(status_code=401, detail="Invalid bearer token")
    return os.environ.get("DEV_BEARER_USER_ID", "user-alpha")
