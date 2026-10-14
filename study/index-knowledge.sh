#!/usr/bin/env bash
# Indexes the guidelines into the two docs MCP servers (scenarios "d-mcp" and "e-hybrid").
# Needs the stack from docker-compose.yml and the scenarios from study/build-scenarios.py.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 study/build-scenarios.py >/dev/null

# A server is stopped while its index is written, so that two processes never write the same database.
for service in docs-mcp docs-mcp-static; do
  docker compose stop "$service"
  docker compose run --rm --no-deps "$service" scrape guidelines file:///docs
  docker compose up -d "$service"
done
echo "Indexed: all guidelines on http://localhost:${DOCS_MCP_PORT:-6281}, static rules on http://localhost:${DOCS_MCP_STATIC_PORT:-6282} (library 'guidelines')"
