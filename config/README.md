# Configuration templates

| File | Purpose |
|------|---------|
| **`environment.example`** | Template for the **backend** `.env` at the repository root (`backend/ai_knowledge_assistant/config.py` loads the repo root `.env`). |

**Local setup:** copy to the repo root and rename:

```powershell
Copy-Item config\environment.example .env
```

Edit `.env` with your API keys. Do not commit `.env`.

The **web frontend** has its own `apps/web/.env.example` for `VITE_*` variables.
