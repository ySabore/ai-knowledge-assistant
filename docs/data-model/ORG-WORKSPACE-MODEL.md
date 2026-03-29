# Organization and workspace model

## Concepts

- **Organization** — Security and billing boundary. Users belong to orgs via **organization_memberships** with a **role**.
- **Workspace** — A knowledge scope inside one organization (documents, RAG chat, ingestion). Identified by **`workspace_id`** (stable string, often `org-slug::workspace-slug` style).
- **Pinecone** — Vectors are stored in a namespace per **`workspace_id`**, not a single global “demo” namespace.

## Access control

- API routes take **`workspace_id`** and call `registry.user_can_access_workspace(user_id, workspace_id)` which requires an active membership on the workspace’s organization.

## Namespaces (app vs vectors)

- SQLite **`namespace`** on documents/jobs is an ingestion label inside the workspace.
- Pinecone **namespace** for queries/upserts is the **`workspace_id`** (see `vectorstore.py`).
