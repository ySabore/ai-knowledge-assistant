# Registry schema (SQLite)

Source of truth: `app.db` (path override: `REGISTRY_DATABASE_PATH`). Below matches a typical migration; verify with `sqlite3 app.db ".schema"` if you change versions.

## Entity overview

- **users** — identities (`user_id`, `email`, `auth_subject`, …)
- **organizations** — tenant boundary (`organization_id`, …)
- **organization_memberships** — user ↔ org role (`role`, `status`)
- **workspaces** — knowledge scope within an org (`workspace_id`, `workspace_slug`, unique per org)
- **documents** / **chunks** — ingestion metadata; vector ids align with Pinecone
- **ingestion_jobs** — async queue for the worker
- **companies** — legacy/demo table (may coexist with organizations)
- **demo_requests** / **funnel_events** — marketing funnel (optional)

## DDL (reference)

```sql
CREATE TABLE documents (
  document_id TEXT PRIMARY KEY,
  namespace TEXT NOT NULL,
  source TEXT NOT NULL,
  source_type TEXT NOT NULL,
  chunk_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  workspace_id TEXT,
  organization_id TEXT,
  record_status TEXT NOT NULL DEFAULT 'active',
  ingestion_status TEXT NOT NULL DEFAULT 'pending',
  health_status TEXT NOT NULL DEFAULT 'pending',
  refresh_status TEXT NOT NULL DEFAULT 'idle',
  last_error TEXT,
  refresh_requested_at TEXT,
  last_ingested_at TEXT,
  archived_at TEXT,
  updated_at TEXT
);

CREATE TABLE chunks (
  chunk_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL,
  namespace TEXT NOT NULL,
  source TEXT NOT NULL,
  chunk_number INTEGER NOT NULL,
  vector_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  workspace_id TEXT,
  organization_id TEXT,
  FOREIGN KEY(document_id) REFERENCES documents(document_id)
);

CREATE TABLE organizations (
  organization_id TEXT PRIMARY KEY,
  organization_name TEXT NOT NULL,
  industry TEXT NOT NULL DEFAULT 'other',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  owner_user_id TEXT
);

CREATE TABLE workspaces (
  workspace_id TEXT PRIMARY KEY,
  organization_id TEXT NOT NULL,
  workspace_name TEXT NOT NULL,
  workspace_slug TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  purpose TEXT NOT NULL DEFAULT '',
  workspace_type TEXT NOT NULL DEFAULT 'general',
  UNIQUE(organization_id, workspace_slug),
  FOREIGN KEY(organization_id) REFERENCES organizations(organization_id)
);

CREATE TABLE users (
  user_id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  auth_provider TEXT NOT NULL DEFAULT 'dev-bearer',
  auth_subject TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_at TEXT
);

CREATE TABLE organization_memberships (
  membership_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  organization_id TEXT NOT NULL,
  role TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  invited_by_user_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, organization_id),
  FOREIGN KEY(user_id) REFERENCES users(user_id),
  FOREIGN KEY(organization_id) REFERENCES organizations(organization_id)
);

CREATE TABLE ingestion_jobs (
  job_id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  organization_id TEXT NOT NULL,
  namespace TEXT NOT NULL,
  source TEXT NOT NULL,
  source_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  error_message TEXT,
  document_id TEXT,
  chunks_indexed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  started_at TEXT,
  finished_at TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 3,
  cancel_requested INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT,
  payload_json TEXT,
  FOREIGN KEY(workspace_id) REFERENCES workspaces(workspace_id)
);
```

Indexes exist on memberships, workspaces, documents, chunks, ingestion job status — see live DB for the full list.
