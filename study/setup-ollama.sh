#!/usr/bin/env bash
# Checks the local Ollama and pulls the embedding model of the docs MCP servers (scenarios
# "d-mcp-server" and "e-mcp-and-specs"). Ollama must be running on the host.
#
#   study/setup-ollama.sh
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a

host=${OLLAMA_PORT:+localhost:$OLLAMA_PORT}
export OLLAMA_HOST=${host:-localhost:11434}
embedding=${EMBEDDING_MODEL:-nomic-embed-text:latest}

if ! ollama list >/dev/null 2>&1; then
  echo "Ollama does not answer on $OLLAMA_HOST. Start Ollama first." >&2
  exit 1
fi

if ollama list | awk 'NR>1 {print $1}' | grep -qx "$embedding"; then
  echo "present: $embedding"
else
  echo "pulling: $embedding"
  ollama pull "$embedding"
fi
