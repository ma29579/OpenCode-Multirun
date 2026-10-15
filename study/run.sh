#!/usr/bin/env bash
# Runs one scenario of the pilot study with one prompt.
#
#   study/run.sh <scenario> <prompt> [runs]
#
# Scenarios (what knowledge the agent gets, see study/build-scenarios.py):
#   baseline          no knowledge
#   a-agents-md       all guidelines inside AGENTS.md
#   b-guideline-files guideline files in guidelines/
#   c-spec-files      rules grouped by requirement as specs in specs/
#   d-mcp-server      all guidelines through the docs MCP server
#   e-mcp-and-specs   general guidelines through the MCP server, project-specific rules as specs in specs/
#   f-split-spec-files        all rules as specs, separated into specs/general and specs/project
#   g-target-mcp-conflict-specs   DB and STD through the MCP server, the contradicting DES rules as specs
#   h-conflict-mcp-target-specs   the contradicting DES rules through the MCP server, DB and STD as specs
#
# Prompts: the file names in study/prompts/ without ".md".
# Environment: MODEL (default github-copilot/claude-sonnet-5), HARNESS (opencode, default, or copilot);
# OUT is set by study/run-all.sh (default results).
# The MCP scenarios need the servers: docker compose up -d && study/index-knowledge.sh
set -euo pipefail
cd "$(dirname "$0")/.."

scenario=${1:?usage: study/run.sh <scenario> <prompt> [runs]}
prompt=${2:?usage: study/run.sh <scenario> <prompt> [runs]}
runs=${3:-3}
model=${MODEL:-github-copilot/claude-sonnet-5}
out=${OUT:-results}
harness=${HARNESS:-opencode}

[ -d study/scenarios ] || python3 study/build-scenarios.py >/dev/null
overlay=study/scenarios/$scenario
if [ ! -d "$overlay" ] || [[ "$scenario" == mcp-* ]]; then
  echo "unknown scenario: $scenario (baseline, a-agents-md, b-guideline-files, c-spec-files, d-mcp-server, e-mcp-and-specs, f-split-spec-files, g-target-mcp-conflict-specs, h-conflict-mcp-target-specs)" >&2
  exit 2
fi

# every top-level file and directory of the scenario goes to the same place in the workspace
adds=()
for entry in "$overlay"/*; do
  adds+=(--add "$entry:$(basename "$entry")")
done

exec python3 tools/opencode_multirun.py -f "study/prompts/$prompt.md" -n "$runs" -m "$model" \
  -w sample_project --label "$scenario" --harness "$harness" -o "$out" "${adds[@]}"
