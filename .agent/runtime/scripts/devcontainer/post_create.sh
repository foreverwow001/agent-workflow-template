#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_UV="$VENV_DIR/bin/uv"

cd "$REPO_ROOT"

venv_is_usable() {
  [[ -x "$VENV_PYTHON" ]] || return 1

  "$VENV_PYTHON" -c 'import pathlib, sys; expected = (pathlib.Path.cwd() / ".venv").resolve(); actual = pathlib.Path(sys.prefix).resolve(); raise SystemExit(0 if actual == expected else 1)' \
    >/dev/null 2>&1
}

if command -v python >/dev/null 2>&1; then
  if ! venv_is_usable; then
    rm -rf "$VENV_DIR"
    python -m venv "$VENV_DIR"
  fi

  "$VENV_PYTHON" -m pip install --upgrade pip

  UVV="${UV_VERSION:-0.5.24}"
  "$VENV_PYTHON" -m pip install --no-cache-dir "uv==${UVV}"

  if [[ -f pyproject.toml && -f uv.lock ]]; then
    "$VENV_UV" sync --frozen --extra dev
  elif [[ -f requirements.txt ]]; then
    if [[ -f requirements-dev.txt ]]; then
      "$VENV_UV" pip install -r requirements.txt -r requirements-dev.txt
    else
      "$VENV_UV" pip install -r requirements.txt
    fi
  else
    echo "[post-create] No Python dependency manifest found; skipping dependency install."
  fi
else
  echo "[post-create] python not found; skipping Python bootstrap."
fi

if [[ -f .agent/runtime/scripts/vscode/install_terminal_tooling.sh ]]; then
  bash .agent/runtime/scripts/vscode/install_terminal_tooling.sh || true
elif [[ -f .agent/runtime/scripts/vscode/install_terminal_orchestrator.sh ]]; then
  bash .agent/runtime/scripts/vscode/install_terminal_orchestrator.sh || true
fi
