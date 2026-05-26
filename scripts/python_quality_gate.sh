#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[1/3] Ruff auto-fix"
uv run ruff check --fix app.py pages utils

echo "[2/3] Ruff verify"
uv run ruff check app.py pages utils

echo "[3/3] Pylance confirm"
echo "Open VS Code Problems and confirm no Pylance errors for app.py/pages/*.py."
echo "Done"
