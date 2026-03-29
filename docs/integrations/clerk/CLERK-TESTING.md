# Clerk testing

- **Local:** Use Clerk test keys and `localhost` redirect URLs; exercise sign-in flow in `apps/web` once wired.
- **API:** Unit-test JWT verification with a mocked JWKS or Clerk test tokens (short-lived, never commit tokens).
- **Staging:** Full flow against staging Clerk instance and staging API URL; confirm CORS and cookie/JWT behavior.

Do not paste production secrets into docs or tickets.
