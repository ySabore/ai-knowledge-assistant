# Review walkthrough checklist

Use before a demo or release candidate.

## Environment

- [ ] `.env` is UTF-8 and contains required keys for RAG (see `backend/.env.example`)
- [ ] `GET /health` returns `ok`
- [ ] `GET /health/ready` shows registry DB present and RAG env satisfied (`deep=1` optional for Pinecone ping)

## Auth

- [ ] `DEV_USER_ID` or bearer token matches a user in `app.db` with org membership
- [ ] Web `VITE_DEV_BEARER_TOKEN` matches `DEV_BEARER_TOKEN` if using bearer from browser

## Data

- [ ] Target `workspace_id` exists and user has access
- [ ] Ingestion paths under `INGEST_ALLOWED_PATHS` if using file sources

## Product

- [ ] Chat returns `reply` and `sources` for grounded questions after vectors exist
- [ ] No API keys in browser network payloads except expected bearer
