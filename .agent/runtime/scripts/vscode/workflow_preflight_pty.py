#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def load_jsonl_events(debug_file: Path) -> list[dict[str, Any]]:
    if not debug_file.exists():
        return []

    events: list[dict[str, Any]] = []
    for line in debug_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            events.append(obj)
    return events


def extract_latest_event(events: list[dict[str, Any]], event_type: str) -> dict[str, Any] | None:
    for event in reversed(events):
        if event.get("type") == event_type:
            return event
    return None


def extract_latest_recovery_state(events: list[dict[str, Any]]) -> str | None:
    event = extract_latest_event(events, "pty.state.changed")
    if not event:
        return None
    return event.get("to") or None


def load_workspace_settings(repo_root: Path) -> dict[str, Any]:
    settings_file = repo_root / ".vscode" / "settings.json"
    if not settings_file.exists():
        return {}

    cleaned_lines: list[str] = []
    for line in settings_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.lstrip().startswith("//"):
            continue
        cleaned_lines.append(line)

    try:
        payload = json.loads("\n".join(cleaned_lines))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def resolve_backend_command(repo_root: Path, backend: str) -> str:
    settings = load_workspace_settings(repo_root)
    key = f"ivyhouseTerminalPty.{backend}Command"
    value = settings.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return backend


def summarize_backend_pty(repo_root: Path, backend: str) -> dict[str, Any]:
    debug_file = repo_root / ".service" / "terminal_capture" / f"{backend}_pty_debug.jsonl"
    artifact_exists = debug_file.exists()
    events = load_jsonl_events(debug_file)
    command = resolve_backend_command(repo_root, backend)
    command_path = shutil.which(command)
    command_available = command_path is not None

    latest_startup_ready = extract_latest_event(events, "pty.startup.ready")
    latest_command_succeeded = extract_latest_event(events, "pty.command.succeeded")
    latest_command_failed = extract_latest_event(events, "pty.command.failed")
    latest_recovery_state = extract_latest_recovery_state(events)

    if not command_available:
        status = "failed"
    elif not artifact_exists:
        status = "cold"
    elif not events:
        status = "degraded"
    elif latest_command_failed and (
        not latest_command_succeeded or str(latest_command_failed.get("ts", "")) >= str(latest_command_succeeded.get("ts", ""))
    ) and latest_recovery_state in {"rebuildable", "prompting-fallback", "fallback-active", "fallback-declined"}:
        status = "failed"
    elif latest_startup_ready or latest_command_succeeded:
        status = "ready"
    else:
        status = "degraded"

    return {
        "artifact_exists": artifact_exists,
        "path": str(debug_file),
        "command": command,
        "command_available": command_available,
        "command_path": command_path,
        "latest_startup_ready_ts": latest_startup_ready.get("ts") if latest_startup_ready else None,
        "latest_command_succeeded_ts": latest_command_succeeded.get("ts") if latest_command_succeeded else None,
        "latest_command_failed_ts": latest_command_failed.get("ts") if latest_command_failed else None,
        "latest_recovery_state": latest_recovery_state,
        "status": status,
    }


def run_pty_preflight(repo_root: Path, backends: list[str], allow_cold_start: bool) -> dict[str, Any]:
    normalized_backends = [backend.strip().lower() for backend in backends if backend.strip()]
    if not normalized_backends:
        normalized_backends = ["codex", "copilot"]

    backend_summaries = {backend: summarize_backend_pty(repo_root, backend) for backend in normalized_backends}
    statuses = {summary["status"] for summary in backend_summaries.values()}

    failures: list[str] = []
    warnings: list[str] = []

    for backend, summary in backend_summaries.items():
        if not summary.get("command_available", True):
            failures.append(f"{backend}_command_missing")

    if "failed" in statuses:
        status = "failed"
        if "pty_backend_failed" not in failures:
            failures.append("pty_backend_failed")
    elif "degraded" in statuses:
        status = "degraded"
        warnings.append("pty_backend_degraded")
    elif statuses == {"cold"} or "cold" in statuses:
        status = "cold"
        if not allow_cold_start:
            failures.append("pty_cold_start")
        else:
            warnings.append("pty_cold_start")
    else:
        status = "ready"

    return {
        "status": status,
        "backends": backend_summaries,
        "checks": {},
        "failures": failures,
        "warnings": warnings,
    }
