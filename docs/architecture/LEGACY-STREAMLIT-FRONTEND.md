# Legacy Streamlit frontend

The upstream [ySabore/ai-knowledge-assistant](https://github.com/ySabore/ai-knowledge-assistant) repo used a **Streamlit** UI (`frontend/app.py`) against a flat FastAPI API.

This codebase uses **React** (`apps/web/`) and **workspace-scoped** routes. To reuse Streamlit ideas, point `API_BASE_URL` at this API and **remap** endpoints (`/workspaces/{id}/chat` with `messages` JSON, bearer auth).
