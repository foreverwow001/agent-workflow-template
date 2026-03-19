#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def load_latest_monitor_proposed_api(debug_file: Path) -> dict[str, Any]:
    if not debug_file.exists():
        return {
            "ok": False,
            "reason": "monitor_debug.jsonl_not_found",
            "path": str(debug_file),
            "value": None,
            "ts": None,
        }

    for line in reversed(debug_file.read_text(encoding="utf-8", errors="ignore").splitlines()):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "proposed_api":
            continue
        value = bool(obj.get("onDidWriteTerminalData", False))
        return {
            "ok": value,
            "reason": "ok" if value else "proposed_api_false",
            "path": str(debug_file),
            "value": value,
            "ts": obj.get("ts"),
        }

    return {
        "ok": False,
        "reason": "no_proposed_api_event_found",
        "path": str(debug_file),
        "value": None,
        "ts": None,
    }


def inspect_shell_integration_attachment(debug_file: Path) -> dict[str, Any]:
    if not debug_file.exists():
        return {
            "ok": False,
            "reason": "monitor_debug.jsonl_not_found",
            "path": str(debug_file),
            "terminal_names": [],
            "ts": None,
        }

    attached_terminals: dict[str, str | None] = {}
    latest_ts: str | None = None

    for line in debug_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = obj.get("type")
        if event_type != "shell_execution_start":
            continue
        if not bool(obj.get("hasRead", False)):
            continue

        terminal_name = str(obj.get("terminalName") or "").strip()
        if not terminal_name:
            continue

        attached_terminals[terminal_name] = obj.get("ts")
        latest_ts = obj.get("ts") or latest_ts

    terminal_names = sorted(attached_terminals)
    ok = bool(terminal_names)
    return {
        "ok": ok,
        "reason": "ok" if ok else "no_shell_integration_attachment_found",
        "path": str(debug_file),
        "terminal_names": terminal_names,
        "ts": latest_ts,
    }


def check_bridge_healthz(healthz_url: str, timeout_sec: float) -> dict[str, Any]:
    try:
        req = urllib.request.Request(healthz_url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            try:
                payload: dict[str, Any] = json.loads(body)
            except json.JSONDecodeError:
                payload = {"raw": body}
            ok = str(payload.get("status", "")).lower() == "ok"
            return {
                "ok": ok,
                "reason": "ok" if ok else "unexpected_healthz_payload",
                "url": healthz_url,
                "http_status": resp.status,
                "payload": payload,
            }
    except urllib.error.URLError as exc:
        return {
            "ok": False,
            "reason": "bridge_unreachable",
            "url": healthz_url,
            "error": str(exc),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": "bridge_healthz_error",
            "url": healthz_url,
            "error": str(exc),
        }


def check_bridge_token(token_file: Path) -> dict[str, Any]:
    if not token_file.exists():
        return {
            "ok": False,
            "reason": "token_file_not_found",
            "path": str(token_file),
        }

    token = token_file.read_text(encoding="utf-8", errors="ignore").strip()
    if not token:
        return {
            "ok": False,
            "reason": "token_file_empty",
            "path": str(token_file),
        }

    return {
        "ok": True,
        "reason": "ok",
        "path": str(token_file),
    }


def inspect_fallback_artifacts(repo_root: Path) -> dict[str, Any]:
    capture_dir = repo_root / ".service" / "terminal_capture"
    files = {
        "monitor_debug": capture_dir / "monitor_debug.jsonl",
        "codex_live": capture_dir / "codex_live.txt",
        "copilot_live": capture_dir / "copilot_live.txt",
        "codex_last": capture_dir / "codex_last.txt",
    }
    existing = {key: str(path) for key, path in files.items() if path.exists()}
    ok = (capture_dir.exists() and capture_dir.is_dir()) or bool(existing)
    return {
        "ok": ok,
        "reason": "ok" if ok else "fallback_artifacts_missing",
        "capture_dir": str(capture_dir),
        "files": existing,
    }


def run_fallback_preflight(repo_root: Path, require_fallback: bool, healthz_url: str, timeout_sec: float) -> dict[str, Any]:
    monitor_debug = repo_root / ".service" / "terminal_capture" / "monitor_debug.jsonl"
    token_file = repo_root / ".service" / "sendtext_bridge" / "token"

    monitor_proposed_api = load_latest_monitor_proposed_api(monitor_debug)
    shell_integration_attached = inspect_shell_integration_attachment(monitor_debug)

    checks = {
        "proposed_api_true": monitor_proposed_api,
        "shell_integration_attached": shell_integration_attached,
        "sendtext_bridge_healthz": check_bridge_healthz(healthz_url, timeout_sec),
        "sendtext_bridge_token": check_bridge_token(token_file),
        "artifact_compatibility": inspect_fallback_artifacts(repo_root),
    }

    failures: list[str] = []
    warnings: list[str] = []

    _ = require_fallback

    critical_keys = ["sendtext_bridge_healthz", "sendtext_bridge_token"]
    warning_keys = ["artifact_compatibility"]

    for key in critical_keys:
        if not checks[key]["ok"]:
            failures.append(key)

    for key in warning_keys:
        if not checks[key]["ok"]:
            warnings.append(key)

    if not monitor_proposed_api["ok"] and not shell_integration_attached["ok"]:
        warnings.append("monitor_capture_backend")

    if failures:
        status = "unavailable"
    elif warnings:
        status = "degraded"
    else:
        status = "ready"

    return {
        "status": status,
        "checks": checks,
        "failures": failures,
        "warnings": warnings,
    }
