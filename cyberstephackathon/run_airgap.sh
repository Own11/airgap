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
fi

# The virtual environment may already exist without the optional STT package.
# Check the import instead of relying only on the directory presence.
if ! stt-venv/bin/python -c "import faster_whisper" >/dev/null 2>&1; then
  stt-venv/bin/python -m pip install -r requirements.txt -r requirements-stt.txt
fi

exec stt-venv/bin/python -m uvicorn app.main:app --reload
