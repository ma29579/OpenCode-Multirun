#!/usr/bin/env bash
# Indexes the guidelines into the docs MCP server (condition "mcp").
# Needs the stack from docker-compose.yml: docker compose up -d
set -euo pipefail
cd "$(dirname "$0")/.."

# The server is stopped while the index is written, so that two processes never write the same database.
docker compose stop docs-mcp
docker compose run --rm --no-deps docs-mcp scrape guidelines file:///docs
docker compose up -d docs-mcp
echo "Indexed ./sample_guidelines as library 'guidelines'. Check it at http://localhost:6280"
