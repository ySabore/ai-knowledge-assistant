# Clerk implementation notes

Status:
- Current implementation target: direct Clerk sign-in and Clerk JWT verification.
- Deferred TODO: "Enterprise Login Center" remains a product/UX option we may layer on later, but it is not a separate auth track in this phase.

## Target behavior

- Browser obtains Clerk session / JWT after sign-in.
- **API** validates JWT (signature + audience/issuer), resolves `user_id` and org membership against the SQLite registry (or syncs users on first login).

## Code touchpoints

- Replace or extend `auth.py` `current_user_id` to accept `Authorization: Bearer <clerk-jwt>` when not in dev mode.
- Implement `clerk_auth.py`: verify JWT with Clerk JWKS, extract subject, map to `users.auth_subject`.

## Multi-tenant

- Align Clerk org IDs with `organization_id` in SQLite, or maintain a mapping table if IDs differ.
