#!/usr/bin/env bash
# Clone the original flat-layout repo for side-by-side comparison with this codebase.
# Usage: ./scripts/clone-legacy.sh [destination]
# Default destination: ~/Documents/ai-knowledge-assistant-legacy
set -euo pipefail
DEST="${1:-$HOME/Documents/ai-knowledge-assistant-legacy}"
git clone https://github.com/ySabore/ai-knowledge-assistant.git "$DEST"
echo "Cloned to: $DEST"
