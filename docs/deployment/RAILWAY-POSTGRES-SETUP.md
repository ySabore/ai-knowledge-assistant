# Railway Postgres Setup (First-Time Guide)

This guide shows how to create a PostgreSQL database in Railway and connect it to this project.

> Status: **Deferred / TODO**. We are prioritizing local Clerk + Ollama workflow first.

## 1) Create a Railway project

1. Sign in to Railway and click **New Project**.
2. Choose either:
   - **Deploy from GitHub repo** (recommended), or
   - **Empty Project** (you can add services manually).

## 2) Add a Postgres service

1. Inside the Railway project, click **+ New**.
2. Select **Database** → **PostgreSQL**.
3. Railway provisions the DB and generates connection variables automatically.

## 3) Find the connection string

You can get DB credentials in either place:

- **Postgres service → Variables** (recommended)
- **Project → Variables** (if you shared variables at project scope)

Look for one of these:

- `DATABASE_URL` (single full URL)
- or split values like `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`

If `DATABASE_URL` exists, copy it and use that as your app connection string.

## 4) Add env vars to the API service

In your **API service** on Railway:

1. Open **Variables**.
2. Add/confirm:
   - `DATABASE_URL=<your railway postgres url>`
   - `AUTH_MODE=clerk`
   - `CLERK_DOMAIN=...` (or issuer/jwks vars)
   - `OPENAI_API_KEY=...` (for production OpenAI)
   - Pinecone vars (`PINECONE_API_KEY`, `PINECONE_INDEX_HOST` or `PINECONE_INDEX_NAME`)

## 5) Verify DB connectivity

After deploy/restart:

1. Open the API service logs.
2. Hit `/health` and `/health/ready`.
3. Confirm there are no DB connection errors.

## 6) Optional: connect locally to Railway Postgres

If you want local scripts/migrations against Railway DB:

1. Copy `DATABASE_URL` from Railway.
2. Export it locally before running migration commands.
3. Keep test runs on local/temporary DB fixtures (as already implemented in `tests/smoke_test.py`).

## Common first-time gotchas

- Using Postgres variables on the wrong service (set them on the API service actually running the code).
- Forgetting to redeploy/restart after changing variables.
- Mixing local SQLite assumptions with remote Postgres runtime settings.
- Not setting Clerk issuer/JWKS values correctly when `AUTH_MODE=clerk`.
