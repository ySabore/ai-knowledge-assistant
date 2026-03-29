# Repository structure

```
ai-knowledge-assistant/
├── backend/ai_knowledge_assistant/   # FastAPI application
├── apps/web/                         # Vite + React client
├── demos/                            # Sample knowledge files for ingest
├── docs/                             # This documentation
├── tests/                            # pytest (smoke_test.py)
├── scripts/                          # Helper scripts (encoding, legacy clone)
├── app.db                            # SQLite registry (local default)
├── Procfile, railway.*               # Deploy wiring
└── README.md, RECOVERY.txt
```
