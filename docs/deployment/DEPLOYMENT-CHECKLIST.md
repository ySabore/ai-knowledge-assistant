# Deployment checklist

## Phase 0 — Accounts

- [ ] Pinecone index created (dimension matches embedding model)
- [ ] OpenAI (and/or Anthropic / Ollama) access configured
- [ ] Railway/host account and repo connected

## Phase 1 — Backend

- [ ] Env vars set on host (see `DEPLOY.md`)
- [ ] `GET /health` succeeds from public URL
- [ ] Registry DB path writable or managed volume attached

## Phase 2 — Frontend

- [ ] Production build passes (`npm run build`)
- [ ] CORS origins include the web origin

## Phase 3 — Post-deploy

- [ ] Smoke test chat + ingest on staging workspace
- [ ] Logging/monitoring does not print API keys
