#!/usr/bin/env bash
# Runs the whole study: every scenario with every prompt, then the schema linter.
#
#   study/run-all.sh [runs per combination]
#
# Environment:
#   MODELS    models of the agent (default: github-copilot/claude-sonnet-5 github-copilot/gpt-5.5);
#             "claude:<model>" runs the model with Claude Code instead of OpenCode, e.g. claude:claude-sonnet-5
#   SCENARIOS scenarios to run (default: all nine)
#   PROMPTS   prompts to run (default: add-tables add-animals fix-feed-table urgent-fix review-schema)
#
# 2 models x 9 scenarios x 5 prompts x 3 runs = 270 agent runs. Check the quota of your model provider first.
set -euo pipefail
cd "$(dirname "$0")/.."

runs=${1:-3}
export OUT=results/study-$(date +%Y%m%d-%H%M%S)   # a new directory for every study
models=${MODELS:-github-copilot/claude-sonnet-5 github-copilot/gpt-5.5}
scenarios=${SCENARIOS:-baseline a-agents-md b-guideline-files c-spec-files d-mcp-server e-mcp-and-specs f-split-spec-files g-target-mcp-conflict-specs h-conflict-mcp-target-specs}
prompts=${PROMPTS:-add-tables add-animals fix-feed-table urgent-fix review-schema}

python3 study/build-scenarios.py >/dev/null

# the MCP scenarios are useless without their servers
for scenario in $scenarios; do
  case "$scenario" in
    d-mcp-server)    port=${DOCS_MCP_PORT:-6281} ;;
    e-mcp-and-specs) port=${DOCS_MCP_STATIC_PORT:-6282} ;;
    g-target-mcp-conflict-specs) port=${DOCS_MCP_TARGET_PORT:-6283} ;;
    h-conflict-mcp-target-specs) port=${DOCS_MCP_CONFLICT_PORT:-6284} ;;
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
    for entry in $models; do
      case "$entry" in
        claude:*)   harness=claude;   model=${entry#claude:} ;;
        opencode:*) harness=opencode; model=${entry#opencode:} ;;
        *)          harness=opencode; model=$entry ;;
      esac
      echo "=== $harness / $model / $scenario / $prompt ==="
      HARNESS=$harness MODEL=$model study/run.sh "$scenario" "$prompt" "$runs"
    done
  done
done

echo "=== schema lint ==="
python3 tools/schema_lint.py "$OUT"
