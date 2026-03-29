# Operations runbook (local / demo)

## API

```bash
cd backend
source .venv/bin/activate   # if using venv
pip install -r ../requirements-backend.txt
export REGISTRY_DATABASE_PATH="$(cd .. && pwd)/app.db"
export DEV_USER_ID=user-alpha   # or use bearer token
uvicorn ai_knowledge_assistant.main:app --reload --host 127.0.0.1 --port 8000
```

## Web

```bash
cd apps/web
npm install
npm run dev
# VITE_DEV_BEARER_TOKEN must match DEV_BEARER_TOKEN on the API
```

## RAG

1. Fill `.env` using `backend/.env.example` (Pinecone + OpenAI or Ollama, matching index dimension).
2. `GET /health/ready` should show `rag_env.ok` when keys are set.
3. Run ingestion worker: `python -m ai_knowledge_assistant.ingestion_worker` from `backend`.

## When things fail

- **503 on chat** — RAG env incomplete; read `detail.messages` in the JSON error.
- **502** — Upstream LLM or Pinecone error; check logs (no secrets in log lines).
- **`.env` not loading** — File must be UTF-8; see `scripts/normalize-text-encoding.py`.
