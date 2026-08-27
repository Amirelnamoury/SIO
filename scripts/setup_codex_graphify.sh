#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v graphify >/dev/null 2>&1; then
  if command -v uv >/dev/null 2>&1; then
    uv tool install --upgrade graphifyy
  else
    python3 -m pip install --user --upgrade graphifyy
    export PATH="${HOME}/.local/bin:${PATH}"
  fi
fi

if ! command -v graphify >/dev/null 2>&1; then
  echo "Graphify installation failed: executable not found on PATH." >&2
  exit 1
fi

graphify extract . --code-only
graphify cluster-only . --no-label --no-viz

echo
graphify benchmark graphify-out/graph.json
echo
echo "Graphify is ready. Use: graphify query \"your question\" --budget 1500"
