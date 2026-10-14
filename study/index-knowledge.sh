#!/usr/bin/env bash
# Indexes the guidelines into the three docs MCP servers (scenarios "d-mcp-server", "e-mcp-and-specs" and "f-swapped-mcp-and-specs").
# Needs the stack from docker-compose.yml and the scenarios from study/build-scenarios.py.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 study/build-scenarios.py >/dev/null

# A server is stopped while its index is written, so that two processes never write the same database.
for service in docs-mcp docs-mcp-static docs-mcp-swapped; do
  docker compose stop "$service"
  docker compose run --rm --no-deps "$service" scrape guidelines file:///docs
  docker compose up -d "$service"
done
echo "Indexed: all guidelines on http://localhost:${DOCS_MCP_PORT:-6281}, general guidelines only on http://localhost:${DOCS_MCP_STATIC_PORT:-6282}, project-specific rules only on http://localhost:${DOCS_MCP_SWAPPED_PORT:-6283} (library 'guidelines')"
