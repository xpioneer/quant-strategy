#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ -f .venv/bin/python ]; then
  ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8120 --reload
else
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8120 --reload
fi
