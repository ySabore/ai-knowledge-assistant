# Deployment

Guides for shipping the **FastAPI backend** and the **React (`apps/web/`)** app. Runtime behavior is summarized in **`../architecture/APPLICATION-DESIGN-AS-BUILT.md`**.

## Contents

| Doc | Purpose |
|-----|---------|
| **[DEPLOY.md](./DEPLOY.md)** | **Recommended sequence:** prerequisites → third-party services → backend → frontend → integration → post-deploy |
| **[DEPLOYMENT-CHECKLIST.md](./DEPLOYMENT-CHECKLIST.md)** | **Phased checklist** (Phase 0–6) aligned with the same order |

**Repo wiring (root):** `Procfile`, `railway.toml`, `railway.json` — backend start command and health check on **`GET /health`**.
