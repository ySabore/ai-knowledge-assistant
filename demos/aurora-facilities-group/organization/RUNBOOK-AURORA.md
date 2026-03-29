# Aurora Facilities Demo Runbook

This runbook is the canonical walkthrough for the Aurora Facilities Group demo in the current local app.

## Status

- App flow available: Clerk sign-in, organization creation, workspace creation, member invites, document ingestion, and workspace chat.
- Demo content refreshed: each Aurora workspace now includes clean sample documents and validation prompts.
- Best current path: ingest the bundled Aurora files directly, or upload additional replacement files through the web UI when you want to expand the scenario.

## Aurora Demo Shape

Recommended organization:
- `Aurora Facilities Group`

Recommended workspaces:
- `Field Ops Assistant`
- `Corporate HR Assistant`
- `Vendor Procurement Assistant`

Current folder layout:
- `demos/aurora-facilities-group/field-ops-assistant/`
- `demos/aurora-facilities-group/corporate-hr-assistant/`
- `demos/aurora-facilities-group/vendor-procurement-assistant/`

## Demo Content Health

This Aurora pack now includes clean sample text content for all three workspaces:

- `field-ops-assistant/company-profile.txt`
- `field-ops-assistant/operations-playbook.txt`
- `field-ops-assistant/security-and-access-policy.txt`
- `corporate-hr-assistant/employee-hr-handbook.txt`
- `corporate-hr-assistant/workplace-safety-basics.txt`
- `vendor-procurement-assistant/purchase-order-rules.txt`
- `vendor-procurement-assistant/supplier-standards.txt`

Each workspace also includes a `test-questions.md` file for validation prompts.

## Start The App

Backend:
```bash
cd /Users/YeshiwSabore/Documents/ai-knowledge-assistant
source backend/.venv/bin/activate
cd backend
uvicorn ai_knowledge_assistant.main:app --host 127.0.0.1 --port 8000
```

Frontend:
```bash
cd /Users/YeshiwSabore/Documents/ai-knowledge-assistant/apps/web
source ~/.nvm/nvm.sh
nvm use 20.20.1
npm run dev -- --host 127.0.0.1 --port 5173
```

If `5173` is busy, Vite may move to `5174`.

## Environment Requirements

Clerk:
- Root `.env` must have `AUTH_MODE=clerk`
- Root `.env` must have the Clerk publishable key and Clerk domain/JWKS settings

RAG:
- To ingest and chat successfully, configure either:
  - OpenAI + Pinecone, or
  - a local-compatible profile you intentionally support

If RAG is not configured, the UI can still create orgs/workspaces and queue uploads, but chat/indexing will not complete meaningfully.

## Aurora Walkthrough

1. Open the signed-in app.
   - Use `http://127.0.0.1:5173/app`
   - Or use the fallback Vite port shown in the terminal

2. Create the Aurora organization.
   - Organization name: `Aurora Facilities Group`
   - Industry: `facilities`

3. Create the three workspaces.
   - `Field Ops Assistant`
   - `Corporate HR Assistant`
   - `Vendor Procurement Assistant`

4. Invite members.
   - Invite at least one `member` scoped to a single workspace
   - Invite at least one `admin` to validate org-wide visibility

5. Ingest documents.
   - Preferred: use `URL or file path`
   - Use the bundled demo files under `demos/aurora-facilities-group/...`
   - Namespace suggestion: `aurora`
   - Example source path:
     `field-ops-assistant/operations-playbook.txt`

6. Validate workspace isolation.
   - A member invited only to `Field Ops Assistant` should not see the HR or procurement workspace
   - An org admin should see all Aurora workspaces

7. Validate chat.
   - Open one workspace
   - Ask questions from that workspace’s `test-questions.md`
   - Confirm sources/snippets come from the active workspace only

## Suggested Upload Set

Field Ops:
- `company-profile.txt`
- `operations-playbook.txt`
- `security-and-access-policy.txt`

Corporate HR:
- `employee-hr-handbook.txt`
- `workplace-safety-basics.txt`

Vendor Procurement:
- `purchase-order-rules.txt`
- `supplier-standards.txt`

## Suggested Validation Prompts

Field Ops:
- What qualifies as a Priority 1 incident?
- What should a technician do before beginning after-hours entry?
- What must be documented when closing a partially resolved ticket?

Corporate HR:
- How far in advance should PTO requests be submitted?
- Which incidents must be reported the same day?
- When is hearing protection required?

Vendor Procurement:
- What approvals are required for a $3,500 purchase order?
- What details must every purchase order include?
- What vendor behaviors count as disqualifiers?

## Validation Checklist

- Clerk sign-in succeeds
- `Aurora Facilities Group` appears in the org selector
- All three Aurora workspaces can be created
- Member invite succeeds
- Workspace member list updates
- File upload returns queued successfully
- Document list updates after worker ingestion
- Chat returns an answer with sources
- Cross-workspace access is blocked for workspace-scoped members
- Cross-org access is blocked

## Known Limitations

- Workspace invites are implemented as app-level membership grants, not a polished accept-invite email flow.
- Browser upload stages files into `.ingestion_spool/` before worker processing.
- The sample files are synthetic demo content and should not be treated as legal, HR, or procurement advice.

## Screenshot Order

Save screenshots to `demos/aurora-facilities-group/screenshots/` with these names:

1. `01-landing.png`
2. `02-dashboard-signed-in.png`
3. `03-organization-switcher.png`
4. `04-new-workspace-form.png`
5. `05-workspace-open.png`
6. `06-upload-ui.png`
7. `07-ingestion-jobs.png`
8. `08-chat-input.png`
9. `09-chat-answer-with-sources.png`
10. `10-final-overview.png`

## Recovery Note

If you want to deepen the Aurora scenario further, the next step is to add more role-specific documents such as janitorial SOPs, onboarding checklists, and vendor scorecards.
