#!/usr/bin/env bash
# Full project build: backend tests + compile, then Vite production build.
# Requires: Python 3.11+, Node 18+ (npm).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate
pip install -q -r ../requirements-backend.txt
pip install -q pytest httpx
pytest "$ROOT/tests/smoke_test.py" -q
python -m compileall -q ai_knowledge_assistant
cd "$ROOT/apps/web"
npm install
npm run build
echo "Build OK: backend tests passed, apps/web/dist ready."
