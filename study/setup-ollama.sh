#!/usr/bin/env bash
# Checks the local Ollama and pulls the models that are missing. Only needed for the condition
# "mcp" (embeddings of the docs MCP server) and when a local model is used as the agent.
#
#   study/setup-ollama.sh [local coding model ...]
#
# The embedding model (nomic-embed-text) is always pulled. Ollama must be running on the host.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a

host=${OLLAMA_PORT:+localhost:$OLLAMA_PORT}
export OLLAMA_HOST=${host:-localhost:11434}
embedding=${EMBEDDING_MODEL:-nomic-embed-text:latest}
coding=("$@")

if ! ollama list >/dev/null 2>&1; then
  echo "Ollama does not answer on $OLLAMA_HOST. Start Ollama first." >&2
  exit 1
fi

# Context window: agents send long prompts, Ollama's small default cuts them off.
ctx=$(ps eww -p "$(pgrep -x ollama | head -1)" 2>/dev/null | tr ' ' '\n' | sed -n 's/^OLLAMA_CONTEXT_LENGTH=//p' | head -1 || true)
if [ ${#coding[@]} -gt 0 ] && { [ -z "${ctx:-}" ] || [ "$ctx" -lt 16384 ]; }; then
  echo "WARNING: OLLAMA_CONTEXT_LENGTH is ${ctx:-not set}. Start Ollama with OLLAMA_CONTEXT_LENGTH=32768, otherwise tool calls are unreliable." >&2
fi

for model in ${coding[@]+"${coding[@]}"} "$embedding"; do
  if ollama list | awk 'NR>1 {print $1}' | grep -qx "$model"; then
    echo "present: $model"
  else
    echo "pulling: $model"
    ollama pull "$model"
  fi
done
