#!/usr/bin/env bash
# Install meta-ads-mcp + dependencies in a venv.
set -e

cd "$(dirname "$0")/.."
PROJECT_DIR="$(pwd)"

echo "[install] Project: $PROJECT_DIR"

if [ ! -d ".venv" ]; then
    echo "[install] Creating venv..."
    python3 -m venv .venv
fi

. .venv/bin/activate

echo "[install] Upgrading pip..."
python -m pip install --upgrade pip wheel setuptools

echo "[install] Installing meta-ads-mcp + SSE extras..."
pip install -e .
pip install starlette uvicorn

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[install] Created .env (edit it with your META_ACCESS_TOKEN)"
fi

echo
echo "[install] Done. Next steps:"
echo "  1. Edit .env with your META_ACCESS_TOKEN"
echo "  2. Run stdio mode:    .venv/bin/meta-ads-mcp"
echo "  3. Run SSE mode:      .venv/bin/meta-ads-mcp --sse"
echo "  4. Smoke test:        python -m meta_ads_mcp.server --help"
