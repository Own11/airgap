#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

PYTHON_BIN="${PYTHON_BIN:-/usr/local/bin/python3.11}"
if [ ! -x "$PYTHON_BIN" ]; then
  echo "Python 3.11 not found at $PYTHON_BIN" >&2
  exit 1
fi

if [ ! -x "stt-venv/bin/python" ]; then
  "$PYTHON_BIN" -m venv stt-venv
  stt-venv/bin/python -m pip install -r requirements.txt -r requirements-stt.txt
fi

exec stt-venv/bin/python -m uvicorn app.main:app --reload
