"""Clerk JWT verification helpers."""

from __future__ import annotations

from dataclasses import dataclass

import jwt
from jwt import InvalidTokenError, PyJWKClient

from . import config


@dataclass(frozen=True)
class ClerkIdentity:
    auth_subject: str
    email: str | None
    display_name: str | None


def verify_clerk_jwt(token: str) -> ClerkIdentity:
    issuer = config.clerk_issuer()
    jwks_url = config.clerk_jwks_url()
    if not issuer or not jwks_url:
        raise ValueError("Clerk is not configured: set CLERK_DOMAIN or CLERK_ISSUER/CLERK_JWKS_URL")

    jwks_client = PyJWKClient(jwks_url)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    audience = config.clerk_audience()

    decode_kwargs = {
        "key": signing_key.key,
        "algorithms": ["RS256"],
        "issuer": issuer,
    }
    if audience:
        decode_kwargs["audience"] = audience
    else:
        decode_kwargs["options"] = {"verify_aud": False}

    try:
        claims = jwt.decode(token, **decode_kwargs)
    except InvalidTokenError as exc:
        raise ValueError("Invalid Clerk JWT") from exc

    subject = str(claims.get("sub", "")).strip()
    if not subject:
        raise ValueError("Clerk JWT missing subject")

    email = claims.get("email")
    if isinstance(email, str):
        email = email.strip() or None
    else:
        email = None

    display_name = claims.get("name") or claims.get("preferred_username")
    if isinstance(display_name, str):
        display_name = display_name.strip() or None
    else:
        display_name = None

    return ClerkIdentity(
        auth_subject=subject,
        email=email,
        display_name=display_name,
    )
