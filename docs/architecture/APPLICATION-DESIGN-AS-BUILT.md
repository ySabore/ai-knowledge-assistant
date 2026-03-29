# Application design (as built)

## Layers

1. **FastAPI** (`main.py`) — CORS, request ID middleware, routers.
2. **Auth** (`auth.py`) — Dev user id or bearer token; `clerk_auth.py` reserved for JWT.
3. **Registry** (`registry.py`) — SQLite: orgs, workspaces, memberships, documents.
4. **RAG** — `embeddings.py`, `vectorstore.py` (Pinecone), `retrieval.py`, `rag_service.py`, `chat.py` (`POST /workspaces/{workspace_id}/chat`).
5. **Ingest** — `ingest.py` queues jobs; `ingestion_worker.py` processes file/URL sources into Pinecone + registry.

## Key routes


| Prefix                       | Purpose                                      |
| ---------------------------- | -------------------------------------------- |
| `/me`                        | Current user orgs (and workspaces via query) |
| `/workspaces/{id}/documents` | List documents                               |
| `/workspaces/{id}/chat`      | RAG chat                                     |
| `/workspaces/{id}/ingest`    | Queue ingestion job                          |
| `/health`, `/health/ready`   | Liveness / readiness                         |


## Configuration

- Env loading: `startup.load_env_files()` reads project root `.env` and `backend/.env`.
- See `backend/ai_knowledge_assistant/config.py` for variables and legacy aliases (`TOP_K`, `PINECONE_DIMENSION`, …).

