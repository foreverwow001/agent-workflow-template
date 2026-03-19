#!/usr/bin/env python3
"""檔案用途：做分層 preflight，先判 PTY 主路徑，再判 fallback 是否可接手。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from workflow_preflight_fallback import run_fallback_preflight
from workflow_preflight_pty import run_pty_preflight


def aggregate_preflight_status(
    pty_result: dict[str, Any],
    fallback_result: dict[str, Any],
    require_pty: bool,
    require_fallback: bool,
    allow_pty_cold_start: bool,
    require_bridge_alias_used: bool = False,
) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []

    pty_status = str(pty_result.get("status", "failed"))
    fallback_status = str(fallback_result.get("status", "unavailable"))

    pty_ready = pty_status == "ready"
    pty_soft = pty_status == "cold"
    pty_hard = pty_status in {"degraded", "failed"}
    fallback_ready = fallback_status == "ready"
    fallback_usable = fallback_status in {"ready", "degraded"}

    for warning in pty_result.get("warnings", []):
        warnings.append(f"pty:{warning}")
    for warning in fallback_result.get("warnings", []):
        warnings.append(f"fallback:{warning}")

    if require_bridge_alias_used:
        warnings.append("cli:require_bridge_alias_used")

    if require_pty:
        if pty_hard:
            failures.append("pty")
        elif pty_soft and not allow_pty_cold_start:
            failures.append("pty")
    elif pty_hard or pty_soft:
        warnings.append("pty")

    if require_fallback:
        if not fallback_ready:
            failures.append("fallback")
    elif fallback_status != "ready":
        if pty_hard and not fallback_usable:
            failures.append("fallback")
        else:
            warnings.append("fallback")

    status = "fail" if failures else "warn" if warnings else "pass"
    if require_fallback:
        mode = "fallback-required"
    elif require_pty:
        mode = "pty-primary"
    else:
        mode = "compat-only"

    next_steps = [
        "若 PTY layer 失敗：先檢查 *_pty_debug.jsonl 是否存在，並確認最近是否有 pty.startup.ready 或 pty.command.succeeded。",
        "若 fallback layer 失敗：優先檢查 bridge healthz、.service/sendtext_bridge/token，必要時再看 monitor_debug.jsonl。",
        "若 PTY 只是 cold：代表主路徑尚未留下 runtime evidence，不一定等同故障。",
    ]

    return {
        "status": status,
        "mode": mode,
        "pty": pty_result,
        "fallback": fallback_result,
        "failures": failures,
        "warnings": warnings,
        "next_steps": next_steps,
    }


def run_preflight(
    repo_root: Path,
    require_pty: bool,
    allow_pty_cold_start: bool,
    require_fallback: bool,
    pty_backends: list[str],
    healthz_url: str,
    timeout_sec: float,
    require_bridge_alias_used: bool = False,
) -> dict[str, Any]:
    pty_result = run_pty_preflight(repo_root, pty_backends, allow_pty_cold_start)
    fallback_result = run_fallback_preflight(repo_root, require_fallback, healthz_url, timeout_sec)
    aggregate = aggregate_preflight_status(
        pty_result=pty_result,
        fallback_result=fallback_result,
        require_pty=require_pty,
        require_fallback=require_fallback,
        allow_pty_cold_start=allow_pty_cold_start,
        require_bridge_alias_used=require_bridge_alias_used,
    )
    aggregate["repo_root"] = str(repo_root)
    return aggregate


def format_text_report(result: dict[str, Any]) -> str:
    lines = [
        f"Preflight status: {result['status']}",
        f"mode: {result['mode']}",
        f"pty.status: {result['pty']['status']}",
        f"fallback.status: {result['fallback']['status']}",
    ]
    for backend, summary in result["pty"].get("backends", {}).items():
        lines.append(f"- pty.{backend}: {summary.get('status')} ({summary.get('path')})")
        if not summary.get("command_available", True):
            command = summary.get("command")
            lines.append(
                f"  command missing: {command} (install the CLI or update ivyhouseTerminalPty.{backend}Command)"
            )
    for key, item in result["fallback"].get("checks", {}).items():
        lines.append(f"- fallback.{key}: {'OK' if item.get('ok') else 'FAIL'} ({item.get('reason')})")
    if result.get("next_steps"):
        lines.append("Next steps:")
        for step in result["next_steps"]:
            lines.append(f"  - {step}")
    if result.get("warnings"):
        lines.append("Warnings:")
        for warning in result["warnings"]:
            lines.append(f"  - {warning}")
    if result.get("failures"):
        lines.append("Failures:")
        for failure in result["failures"]:
            lines.append(f"  - {failure}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repo 根目錄（預設：目前目錄）",
    )
    parser.add_argument(
        "--require-bridge",
        action="store_true",
        help="舊參數別名；等同 --require-fallback。",
    )
    parser.add_argument(
        "--require-fallback",
        action="store_true",
        help="要求 fallback layer 至少必須 usable（ready 或 degraded）。",
    )
    parser.add_argument(
        "--require-pty",
        action="store_true",
        help="要求 PTY layer 必須可工作；搭配 --allow-pty-cold-start 可接受尚未留下 artifact 的 fresh workspace。",
    )
    parser.add_argument(
        "--allow-pty-cold-start",
        action="store_true",
        help="允許 PTY layer 為 cold 時只回 warning，不視為 fail。",
    )
    parser.add_argument(
        "--pty-backends",
        default="codex,copilot",
        help="要檢查的 PTY backends，逗號分隔（預設：codex,copilot）。",
    )
    parser.add_argument(
        "--healthz-url",
        default="http://127.0.0.1:8765/healthz",
        help="SendText Bridge 健康檢查 URL。",
    )
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=2.0,
        help="Bridge 健康檢查 timeout（秒）。",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="輸出 JSON。",
    )
    args = parser.parse_args()

    require_fallback = bool(args.require_fallback or args.require_bridge)
    pty_backends = [item.strip() for item in str(args.pty_backends or "").split(",") if item.strip()]

    result = run_preflight(
        repo_root=args.repo_root.resolve(),
        require_pty=bool(args.require_pty),
        allow_pty_cold_start=bool(args.allow_pty_cold_start),
        require_fallback=require_fallback,
        pty_backends=pty_backends,
        healthz_url=args.healthz_url,
        timeout_sec=args.timeout_sec,
        require_bridge_alias_used=bool(args.require_bridge),
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(result))

    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
