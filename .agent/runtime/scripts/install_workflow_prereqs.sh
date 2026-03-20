#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

CHECK_ONLY=0

usage() {
  cat <<'EOF'
Usage: bash .agent/runtime/scripts/install_workflow_prereqs.sh [--check-only]

Checks the minimum runtime dependencies for a workflow-core downstream repo.
When --check-only is omitted, missing dependencies are installed when possible.
EOF
}

if [[ $# -gt 1 ]]; then
  usage >&2
  exit 2
fi

if [[ $# -eq 1 ]]; then
  case "$1" in
    --check-only)
      CHECK_ONLY=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
fi

CAN_SUDO=0
if command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then
  CAN_SUDO=1
fi

APT_AVAILABLE=0
if command -v apt-get >/dev/null 2>&1; then
  APT_AVAILABLE=1
fi

FAILED_ITEMS=()
WARNINGS=()

log() {
  echo "[workflow-prereqs] $*"
}

warn() {
  echo "[workflow-prereqs][WARN] $*" >&2
  WARNINGS+=("$*")
}

record_failure() {
  local item="$1"
  FAILED_ITEMS+=("$item")
}

apt_install_packages() {
  local packages=("$@")

  if (( CHECK_ONLY )); then
    return 1
  fi

  if (( ! APT_AVAILABLE )); then
    return 1
  fi

  if (( CAN_SUDO )); then
    sudo -n apt-get update
    sudo -n apt-get install -y --no-install-recommends "${packages[@]}"
    sudo -n rm -rf /var/lib/apt/lists/*
    return 0
  fi

  if [[ "$(id -u)" -eq 0 ]]; then
    apt-get update
    apt-get install -y --no-install-recommends "${packages[@]}"
    rm -rf /var/lib/apt/lists/*
    return 0
  fi

  return 1
}

ensure_command_with_apt_fallback() {
  local label="$1"
  local command_name="$2"
  shift 2
  local packages=("$@")

  if command -v "$command_name" >/dev/null 2>&1; then
    log "${label} available: $(command -v "$command_name")"
    return 0
  fi

  if (( CHECK_ONLY )); then
    warn "${label} missing: ${command_name}"
    record_failure "$label"
    return 1
  fi

  if apt_install_packages "${packages[@]}"; then
    if command -v "$command_name" >/dev/null 2>&1; then
      log "Installed ${label}: $(command -v "$command_name")"
      return 0
    fi
  fi

  warn "Unable to install ${label}; missing command '${command_name}'."
  record_failure "$label"
  return 1
}

python_supports_venv() {
  if command -v python >/dev/null 2>&1; then
    python -m venv --help >/dev/null 2>&1
    return $?
  fi

  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv --help >/dev/null 2>&1
    return $?
  fi

  return 1
}

ensure_python_with_venv() {
  if command -v python >/dev/null 2>&1 && python_supports_venv; then
    log "Python with venv available: $(command -v python)"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1 && python_supports_venv; then
    log "Python3 with venv available: $(command -v python3)"
    return 0
  fi

  if (( CHECK_ONLY )); then
    warn "Python with venv support missing."
    record_failure "python+venv"
    return 1
  fi

  if apt_install_packages python3 python3-venv python-is-python3; then
    if python_supports_venv; then
      log "Installed Python with venv support."
      return 0
    fi
  fi

  warn "Unable to install Python with venv support."
  record_failure "python+venv"
  return 1
}

global_npm_prefix_is_writable() {
  local prefix
  prefix="$(npm prefix -g 2>/dev/null || true)"
  [[ -n "$prefix" && -w "$prefix" ]]
}

install_npm_package_global() {
  local package_name="$1"

  if (( CHECK_ONLY )); then
    return 1
  fi

  if [[ "$(id -u)" -eq 0 ]] || global_npm_prefix_is_writable; then
    npm install -g "$package_name"
    return 0
  fi

  if (( CAN_SUDO )); then
    sudo -n npm install -g "$package_name"
    return 0
  fi

  return 1
}

ensure_npm_cli() {
  local label="$1"
  local command_name="$2"
  local package_name="$3"

  if command -v "$command_name" >/dev/null 2>&1; then
    log "${label} CLI available: $(command -v "$command_name")"
    return 0
  fi

  if (( CHECK_ONLY )); then
    warn "${label} CLI missing: ${command_name}"
    record_failure "$label CLI"
    return 1
  fi

  if ! command -v npm >/dev/null 2>&1; then
    warn "npm missing; cannot install ${label} CLI (${package_name})."
    record_failure "$label CLI"
    return 1
  fi

  if install_npm_package_global "$package_name" && command -v "$command_name" >/dev/null 2>&1; then
    log "Installed ${label} CLI: $(command -v "$command_name")"
    return 0
  fi

  warn "Unable to install ${label} CLI (${package_name})."
  record_failure "$label CLI"
  return 1
}

ensure_git() {
  ensure_command_with_apt_fallback "Git" "git" git || true
}

ensure_python_with_venv || true
ensure_git
ensure_command_with_apt_fallback "Node.js" "node" nodejs npm || true
ensure_command_with_apt_fallback "npm" "npm" npm nodejs || true

if [[ "$(uname -s)" == "Linux" ]]; then
  ensure_command_with_apt_fallback "bubblewrap" "bwrap" bubblewrap || true
else
  log "Skipping bubblewrap check on non-Linux platform."
fi

ensure_npm_cli "Codex" "codex" "@openai/codex" || true
ensure_npm_cli "Copilot" "copilot" "@github/copilot" || true

if [[ ${#FAILED_ITEMS[@]} -gt 0 ]]; then
  warn "Missing dependencies remain: ${FAILED_ITEMS[*]}"
  exit 1
fi

log "Minimum workflow dependencies are ready."
