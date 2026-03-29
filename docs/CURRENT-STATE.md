# Current state (as-built)

## Stack

- **API:** FastAPI under `backend/ai_knowledge_assistant/` — `uvicorn ai_knowledge_assistant.main:app`
- **Registry:** SQLite (`app.db` by default), multi-tenant orgs, workspaces, users, documents, ingestion jobs
- **RAG:** OpenAI / Anthropic / Ollama chat; OpenAI or Ollama embeddings; Pinecone vectors (namespace = `workspace_id`)
- **Web:** Vite + React in `apps/web/` (minimal recovery UI: status + orgs; extend as needed)

## Auth (development)

- `DEV_USER_ID` or `Authorization: Bearer <DEV_BEARER_TOKEN>` — see `backend/ai_knowledge_assistant/auth.py`
- **Clerk:** placeholder in `clerk_auth.py`; production should verify JWTs per `docs/integrations/clerk/`

## Health

- `GET /health` — liveness
- `GET /health/ready` — registry DB + RAG env; `?deep=1` pings Pinecone

## Docs repaired

This file and sibling docs were rewritten in UTF-8 after a bad bulk encoding pass. If something still looks wrong, restore from git/backup and compare paths in `DELETED-FILES-REFERENCE.txt`.
