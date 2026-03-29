# AI Knowledge Assistant

Multi-tenant knowledge assistant: FastAPI backend, SQLite registry (`app.db`), React web app.

If your tree was damaged, read **`RECOVERY.txt`** for how this copy was rebuilt and how to run it.

## Quick start

Backend:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r ../requirements-backend.txt
uvicorn ai_knowledge_assistant.main:app --reload --host 127.0.0.1 --port 8000
```

Use `DEV_USER_ID=user-alpha` or `Authorization: Bearer dev-local-token` (override with `DEV_BEARER_TOKEN`).

Web:

```bash
cd apps/web && npm install && npm run dev
```

## Build (CI / release)

From the repo root (needs **Node 18+** for the web bundle):

```bash
./scripts/build-all.sh
```

Or manually: `pytest tests/smoke_test.py -q` with `backend` on `PYTHONPATH`, then `cd apps/web && npm install && npm run build` (output in `apps/web/dist/`).

## Deploy

See `Procfile` (Railway): uvicorn `ai_knowledge_assistant.main:app` from `backend`.
