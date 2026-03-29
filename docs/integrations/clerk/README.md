# Clerk integration

Clerk provides hosted sign-in and JWTs for organizations. This repo ships a **placeholder** in `backend/ai_knowledge_assistant/clerk_auth.py`; production must verify JWTs and map `sub` → `user_id` / org claims.

| Doc | Purpose |
|-----|---------|
| [CLERK-SETUP.md](./CLERK-SETUP.md) | Env vars and dashboard steps |
| [CLERK-IMPLEMENTATION.md](./CLERK-IMPLEMENTATION.md) | Wiring into FastAPI |
| [CLERK-TESTING.md](./CLERK-TESTING.md) | Local and staging tests |
