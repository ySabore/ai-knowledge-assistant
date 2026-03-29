# Deployment

## Backend (Railway / similar)

- **Root:** `Procfile` runs uvicorn from `backend`: `ai_knowledge_assistant.main:app`
- **Health:** platform should hit `GET /health` (and optionally `/health/ready` for stricter checks)
- **Env:** set variables from `backend/.env.example` in the host’s secret store — never commit `.env`

## Frontend

- Build `apps/web` with `npm run build`; serve static output behind CDN or static host
- Configure API base URL / proxy so browser calls reach the FastAPI origin (CORS via `CORS_ALLOW_ORIGINS`)

## Secrets

- Rotate `DEV_BEARER_TOKEN` / replace with Clerk JWT in production
- Pinecone and OpenAI keys are **server-side only**

## SQLite

- `app.db` is fine for demos; production multi-instance deployments should move the registry to Postgres or another shared store.
