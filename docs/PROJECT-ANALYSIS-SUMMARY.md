# Project Analysis Summary (2026-03-29)

## What this repository is

`ai-knowledge-assistant` is a recovery-state multi-tenant RAG assistant project with:

- A FastAPI backend (`backend/ai_knowledge_assistant`) exposing health, identity, workspace document listing, chat, and ingest queue routes.
- A Vite + React web UI (`apps/web`) that currently functions as a lightweight operational/status view.
- A SQLite registry (`app.db`) expected to hold tenants, memberships, workspaces, documents, and ingestion metadata.
- Documentation and roadmaps that indicate the current build is a reconstructed baseline after file corruption.

## Architecture snapshot

### Backend

The application entry point wires CORS, request-context middleware, and route groups:

- `/me/*` for user/org context
- `/admin/*` for operational utilities
- `/workspaces/*` for documents, chat, and ingestion
- `/health` and `/health/ready`

Configuration is fully environment-driven for auth, CORS, DB path, model provider selection, embedding model selection, Pinecone connection, and ingestion policy.

### RAG flow (current capability)

The backend expects:

- Pinecone configured (`PINECONE_API_KEY` and index host/name)
- Embedding provider (`openai` or `ollama`)
- Chat provider (`openai`, `anthropic`, or `ollama`)

Chat endpoint behavior is defensive: if RAG config is incomplete, requests return `503` with detailed configuration errors.

### Frontend

The React app is intentionally minimal:

- Performs `GET /health`
- Performs `GET /me/organizations`
- Uses a bearer token from `VITE_DEV_BEARER_TOKEN` (defaults to `dev-local-token`)
- Labels itself as a “recovery UI” and explicitly notes this is not the full original UI

## Current maturity assessment

### Strengths

- Clear separation of backend/API, frontend, docs, and scripts.
- Good env-driven configuration surface for multi-provider RAG.
- Basic but useful smoke tests and health/readiness endpoints.
- Extensive planning/roadmap docs to guide phased execution.

### Gaps / Risks

- Recovery-state codebase: several docs explicitly describe rebuilt or placeholder behavior.
- Clerk auth integration is still a placeholder for production JWT validation.
- RAG path depends on external services and complete env wiring; not turnkey by default.
- Without explicit fixtures, local runtime workflows can still be sensitive to SQLite schema/data state (especially outside tests).

## Recommended next priorities

1. **Stabilize local development DB bootstrap**
   - Add deterministic schema migration/init + seed fixtures for tests.
2. **Close auth hardening**
   - Replace dev bearer fallback with proper Clerk/JWT verification path.
3. **Improve ingest/chat end-to-end confidence**
   - Add integration tests with mocked vectorstore/provider adapters.
4. **Expand UI beyond status page**
   - Rebuild workspace/document/chat workflows from roadmap priorities.
5. **Codify deployment contracts**
   - Validate env vars at startup and publish strict deployment profile(s).

## Validation notes

- A hermetic smoke-test registry DB fixture now exists in `tests/smoke_test.py`, so smoke tests no longer depend on the local `app.db` schema state.
- Current smoke status: `4 passed` with `pytest tests/smoke_test.py -q`.
