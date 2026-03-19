#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[compat] install_terminal_orchestrator.sh 已降級為 shim；請改用 .agent/runtime/scripts/vscode/install_terminal_tooling.sh" >&2
exec bash "$SCRIPT_DIR/install_terminal_tooling.sh" "$@"
