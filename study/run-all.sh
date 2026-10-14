#!/usr/bin/env bash
# Runs the whole study: every scenario with every prompt, then the schema linter.
#
#   study/run-all.sh [runs per combination]
#
# Environment:
#   MODEL     model of the agent (default github-copilot/claude-sonnet-5)
#   SCENARIOS scenarios to run (default: all six)
#   PROMPTS   prompts to run (default: add-tables fix-feed-table review-schema)
#
# 6 scenarios x 3 prompts x 3 runs = 54 agent runs. Check the quota of your model provider first.
set -euo pipefail
cd "$(dirname "$0")/.."

runs=${1:-3}
export OUT=results/study-$(date +%Y%m%d-%H%M%S)   # a new directory for every study
scenarios=${SCENARIOS:-baseline a-agents-md b-guideline-files c-spec-files d-mcp-server e-mcp-and-specs}
prompts=${PROMPTS:-add-tables fix-feed-table review-schema}

python3 study/build-scenarios.py >/dev/null

# the MCP scenarios are useless without their servers
for scenario in $scenarios; do
  case "$scenario" in
    d-mcp-server)    port=${DOCS_MCP_PORT:-6281} ;;
    e-mcp-and-specs) port=${DOCS_MCP_STATIC_PORT:-6282} ;;
    *) continue ;;
  esac
  if ! curl -s -o /dev/null -m 5 "http://localhost:$port/"; then
    echo "error: the docs MCP server for $scenario does not answer on port $port." >&2
    echo "Run: docker compose up -d && study/index-knowledge.sh" >&2
    exit 1
  fi
done

echo "Output: $OUT"
for prompt in $prompts; do
  for scenario in $scenarios; do
    echo "=== $scenario / $prompt ==="
    study/run.sh "$scenario" "$prompt" "$runs"
  done
done

echo "=== schema lint ==="
python3 tools/schema_lint.py "$OUT"
