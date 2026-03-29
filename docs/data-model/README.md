# Data model

Docs for **what the product means** (org vs workspace) and **how it is stored** in the SQLite registry.

| Doc | Purpose |
|-----|---------|
| **[ORG-WORKSPACE-MODEL.md](./ORG-WORKSPACE-MODEL.md)** | Product rules: organization as security boundary, hierarchy, namespaces, UI/backend implications |
| **[REGISTRY-SCHEMA.md](./REGISTRY-SCHEMA.md)** | SQLite tables, columns, and relationships (as implemented in `registry.py`) |

Implementation detail for auth and `/me/*` routes: **`../architecture/APPLICATION-DESIGN-AS-BUILT.md`**.
