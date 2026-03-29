# Aurora Facilities — organization

Organization-scenario docs for **Aurora Facilities Group** (`aurora-facilities-group`):

- **[RUNBOOK-AURORA.md](./RUNBOOK-AURORA.md)** — end-to-end runbook (startup, seed, validation prompts).

Workspace-level demo files and per-workspace test scripts live in the parent folder: [`../README.md`](../README.md).

Recommended workspace sequence:
- create the Aurora organization
- add the three workspace assistants
- ingest the bundled sample docs from each workspace folder
- validate isolation with the workspace-specific `test-questions.md` prompts
