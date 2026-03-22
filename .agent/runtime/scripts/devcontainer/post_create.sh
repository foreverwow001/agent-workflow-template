#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_UV="$VENV_DIR/bin/uv"
OBSIDIAN_VAULT_ROOT="${OBSIDIAN_VAULT_ROOT:-/obsidian/vault}"
OBSIDIAN_WORKSPACE_LINK="$REPO_ROOT/obsidian-vault"

cd "$REPO_ROOT"

if [[ -f .agent/runtime/scripts/install_workflow_prereqs.sh ]]; then
  bash .agent/runtime/scripts/install_workflow_prereqs.sh || true
fi

ensure_obsidian_workspace_link() {
  if [[ ! -d "$OBSIDIAN_VAULT_ROOT" ]]; then
    return 0
  fi

  if [[ -L "$OBSIDIAN_WORKSPACE_LINK" ]]; then
    local current_target
    current_target="$(readlink "$OBSIDIAN_WORKSPACE_LINK")"
    if [[ "$current_target" == "$OBSIDIAN_VAULT_ROOT" ]]; then
      return 0
    fi

    rm -f "$OBSIDIAN_WORKSPACE_LINK"
  elif [[ -e "$OBSIDIAN_WORKSPACE_LINK" ]]; then
    echo "[post-create] Skipping obsidian-vault symlink; $OBSIDIAN_WORKSPACE_LINK already exists and is not a symlink."
    return 0
  fi

  ln -s "$OBSIDIAN_VAULT_ROOT" "$OBSIDIAN_WORKSPACE_LINK"
  echo "[post-create] Linked obsidian-vault -> $OBSIDIAN_VAULT_ROOT for single-root Explorer access."
}

ensure_obsidian_workspace_link

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
