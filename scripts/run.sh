#!/usr/bin/env bash
# Run meta-ads-mcp with .env loaded.
set -e
cd "$(dirname "$0")/.."
. .venv/bin/activate
exec meta-ads-mcp "$@"
