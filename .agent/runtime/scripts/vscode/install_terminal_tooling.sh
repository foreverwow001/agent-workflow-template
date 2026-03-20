#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"

can_use_passwordless_sudo() {
  command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1
}

global_npm_prefix_is_writable() {
  local prefix
  prefix="$(npm prefix -g 2>/dev/null || true)"
  [[ -n "$prefix" && -w "$prefix" ]]
}

install_missing_cli() {
  local label="$1"
  local command_name="$2"
  local package_name="$3"

  if command -v "$command_name" >/dev/null 2>&1; then
    echo "[terminal-tooling] ${label} CLI already available: $(command -v "$command_name")"
    return 0
  fi

  if ! command -v npm >/dev/null 2>&1; then
    echo "[WARN] npm not found; cannot install ${label} CLI package ${package_name}." >&2
    return 0
  fi

  echo "[terminal-tooling] ${label} CLI not found; installing ${package_name}..."

  if [[ "$(id -u)" -eq 0 ]] || global_npm_prefix_is_writable; then
    if npm install -g "$package_name"; then
      return 0
    fi
    echo "[WARN] direct npm install failed for ${package_name}." >&2
  fi

  if can_use_passwordless_sudo; then
    if sudo -n npm install -g "$package_name"; then
      return 0
    fi
    echo "[WARN] sudo npm install failed for ${package_name}." >&2
    return 0
  fi

  echo "[WARN] unable to auto-install ${label} CLI; no writable global npm prefix and passwordless sudo unavailable." >&2
  return 0
}

resolve_extensions_dir() {
  if [[ -d "$HOME/.vscode-server-insiders/extensions" ]]; then
    printf '%s\n' "$HOME/.vscode-server-insiders/extensions"
    return 0
  fi

  printf '%s\n' "$HOME/.vscode-server/extensions"
}

VSCODE_SERVER_EXT_DIR="$(resolve_extensions_dir)"

get_extension_version() {
  local ext_dir="$1"

  python3 - "$ext_dir" <<'PY'
import json
import pathlib
import sys

ext_dir = pathlib.Path(sys.argv[1])
pkg = ext_dir / "package.json"
if not pkg.exists():
    print("")
    raise SystemExit(0)

try:
    data = json.loads(pkg.read_text(encoding="utf-8"))
    print(str(data.get("version", "")).strip())
except Exception:
    print("")
PY
}

install_local_extension_symlink() {
  local ext_id="$1"
  local ext_src="$2"

  if [[ ! -d "$ext_src" ]]; then
    echo "[WARN] extension source not found, skip: $ext_src" >&2
    return 0
  fi

  local version
  version="$(get_extension_version "$ext_src")"
  if [[ -z "$version" ]]; then
    echo "[WARN] failed to read version from: $ext_src/package.json" >&2
    return 0
  fi

  local dest_name="${ext_id}-${version}"
  local dest="$VSCODE_SERVER_EXT_DIR/$dest_name"

  find "$VSCODE_SERVER_EXT_DIR" -maxdepth 1 -mindepth 1 \( -type l -o -type d \) -name "${ext_id}-*" -exec rm -rf {} +
  ln -s "$ext_src" "$dest"

  echo "Installed local extension symlink:"
  echo "  $dest -> $ext_src"
}

warn_missing_cli() {
  local label="$1"
  local command_name="$2"
  local setting_key="$3"

  if command -v "$command_name" >/dev/null 2>&1; then
    return 0
  fi

  echo "[WARN] ${label} CLI not found on PATH: $command_name" >&2
  echo "       Install the CLI or set VS Code setting '${setting_key}' to an available executable." >&2
}

mkdir -p "$VSCODE_SERVER_EXT_DIR"

install_missing_cli "Codex" "codex" "@openai/codex"
install_missing_cli "Copilot" "copilot" "@github/copilot"

echo "[terminal-tooling] Installing PTY primary tooling..."
install_local_extension_symlink \
  "ivyhouse-local.ivyhouse-terminal-pty" \
  "$REPO_ROOT/.agent/runtime/tools/vscode_terminal_pty"

echo "[terminal-tooling] Installing fallback adapter..."
install_local_extension_symlink \
  "ivyhouse-local.ivyhouse-terminal-fallback" \
  "$REPO_ROOT/.agent/runtime/tools/vscode_terminal_fallback"

warn_missing_cli "Codex" "codex" "ivyhouseTerminalPty.codexCommand"
warn_missing_cli "Copilot" "copilot" "ivyhouseTerminalPty.copilotCommand"

echo
echo "Installed PTY primary + fallback tooling. Missing Codex/Copilot CLIs are auto-installed when npm plus writable global prefix or passwordless sudo are available."
echo "Next step: in VS Code run 'Developer: Reload Window' to activate extensions."
