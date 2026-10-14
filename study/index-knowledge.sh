#!/usr/bin/env bash
# Indexes the guidelines into the four docs MCP servers (scenarios "d-mcp-server", "e-mcp-and-specs",
# "g-target-mcp-conflict-specs" and "h-conflict-mcp-target-specs").
# Needs the stack from docker-compose.yml and the scenarios from study/build-scenarios.py.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 study/build-scenarios.py >/dev/null

# A server is stopped while its index is written, so that two processes never write the same database.
for service in docs-mcp docs-mcp-static docs-mcp-target docs-mcp-conflict; do
  docker compose stop "$service"
  docker compose run --rm --no-deps "$service" scrape guidelines file:///docs
  docker compose up -d "$service"
done
echo "Indexed: all guidelines on port ${DOCS_MCP_PORT:-6281}, DB only on ${DOCS_MCP_STATIC_PORT:-6282}, DB and STD on ${DOCS_MCP_TARGET_PORT:-6283}, DES only on ${DOCS_MCP_CONFLICT_PORT:-6284} (library 'guidelines')"
