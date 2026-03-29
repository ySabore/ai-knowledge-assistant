# Demo knowledge bases

Industry-specific sample text under each folder (e.g. `northwind-retail-demo/`, `aurora-facilities-group/`) for ingestion and RAG testing.

**Ingestion:** use paths under `INGEST_ALLOWED_PATHS` (default includes this `demos/` directory). Queue jobs via `POST /workspaces/{workspace_id}/ingest` and run the ingestion worker from `backend`.
