#!/usr/bin/env bash
# Runs one experimental condition of the pilot study.
#
#   study/run.sh <condition> <prompt> [runs] [extra options for opencode_multirun.py]
#
# Conditions (what knowledge the agent gets):
#   none       no guidelines
#   base       database-guidelines.md as files in the workspace
#   standards  base + database-standards.md as files
#   all        all three guidelines as files
#   mcp        all three guidelines through the docs MCP server (run study/index-knowledge.sh once before)
#
# Prompts: the file names in study/prompts/ without ".md".
# The model can be set with the environment variable MODEL.
set -euo pipefail
cd "$(dirname "$0")/.."

condition=${1:?usage: study/run.sh <condition> <prompt> [runs]}
prompt=${2:?usage: study/run.sh <condition> <prompt> [runs]}
runs=${3:-5}
model=${MODEL:-github-copilot/claude-sonnet-5}

config=study/config
guidelines=sample_guidelines
files_config=(--add "$config/opencode.json:opencode.json" --add "$config/AGENTS.files.md:AGENTS.md")

case "$condition" in
  none)      adds=(--add "$config/opencode.json:opencode.json") ;;
  base)      adds=("${files_config[@]}" --add "$guidelines/database-guidelines.md:guidelines/") ;;
  standards) adds=("${files_config[@]}" --add "$guidelines/database-guidelines.md:guidelines/"
                                        --add "$guidelines/database-standards.md:guidelines/") ;;
  all)       adds=("${files_config[@]}" --add "$guidelines/database-guidelines.md:guidelines/"
                                        --add "$guidelines/database-standards.md:guidelines/"
                                        --add "$guidelines/database-design-conventions.md:guidelines/") ;;
  mcp)       adds=(--add "$config/opencode-mcp.json:opencode.json" --add "$config/AGENTS.mcp.md:AGENTS.md") ;;
  *) echo "unknown condition: $condition (none, base, standards, all, mcp)" >&2; exit 2 ;;
esac

exec python3 tools/opencode_multirun.py -f "study/prompts/$prompt.md" -n "$runs" -m "$model" \
  -w sample_project --label "$condition" "${adds[@]}" "${@:4}"
