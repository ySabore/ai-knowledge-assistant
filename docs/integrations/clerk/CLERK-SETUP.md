# Clerk setup

1. Create an application in the [Clerk dashboard](https://dashboard.clerk.com).
2. Add sign-in methods and (if using orgs) organization features.
3. Copy **publishable** and **secret** keys into the host environment (never commit).
4. Configure **authorized redirect URLs** for local (`http://localhost:5173`) and production web origins.
5. Plan JWT claims needed for `organization_id` / role — map in `clerk_auth` when implemented.

Environment variables (names vary by SDK version — follow Clerk’s FastAPI/React docs):

- `CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`
- Optional: JWKS URL for token verification in the API
