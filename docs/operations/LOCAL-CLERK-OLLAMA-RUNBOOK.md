# Local Runbook: React Frontend + Clerk Auth + Ollama Backend

This runbook prioritizes local development and keeps Railway/Postgres as a later TODO.

## Goal

Run locally with:

- React frontend (`apps/web`)
- FastAPI backend (`backend`)
- `AUTH_MODE=clerk` on backend
- Ollama for LLM + embeddings

## 1) Start Ollama

Make sure Ollama is running locally and models are pulled:

```bash
ollama serve
ollama pull llama3.2
ollama pull nomic-embed-text
```

## 2) Configure backend env

In `backend/.env` (or project root `.env`), set at minimum:

```bash
AUTH_MODE=clerk
CLERK_DOMAIN=<your-clerk-domain>
# optional explicit values:
# CLERK_ISSUER=https://<your-clerk-domain>
# CLERK_JWKS_URL=https://<your-clerk-domain>/.well-known/jwks.json
# CLERK_AUDIENCE=<if your token includes aud>

LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_CHAT_MODEL=llama3.2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
PINECONE_EMBEDDING_DIMENSION=768
```

If using Pinecone for retrieval, also set:

```bash
PINECONE_API_KEY=...
PINECONE_INDEX_HOST=...    # or PINECONE_INDEX_NAME=ai-knowledge-assistant
```

## 3) Start backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r ../requirements-backend.txt
uvicorn ai_knowledge_assistant.main:app --reload --host 127.0.0.1 --port 8000
```

## 4) Start frontend

```bash
cd apps/web
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## 5) Authenticate from frontend

The recovery UI now supports setting the bearer token in-page.

- Keep `dev-local-token` for `AUTH_MODE=dev`.
- For `AUTH_MODE=clerk`, paste a valid Clerk JWT into the token field and click **Apply**.

This lets you validate React + Clerk-backed API auth without adding Clerk SDK coupling into the recovered UI yet.

## Current TODOs

- Railway + Postgres deployment path (deferred for now).
- Full native Clerk frontend SDK integration (session management, sign-in UI, token refresh).
