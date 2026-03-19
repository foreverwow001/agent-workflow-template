#!/usr/bin/env python3
"""檔案用途：提供 workflow-core shared portable smoke suite 的最小可執行骨架。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PARENT_DIR = SCRIPT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from workflow_core_manifest import (  # noqa: E402
    get_projection_artifact_path,
    get_required_live_paths,
    get_smoke_suite_path,
    load_manifest,
    manifest_default_path,
    pattern_anchor,
)


EXIT_PASS = 0
EXIT_WARN = 10
EXIT_FAIL = 20
EXIT_ERROR = 30


def run_portable_smoke(repo_root: Path, manifest_path: Path) -> dict:
    manifest = load_manifest(manifest_path)
    projection_artifact_path = get_projection_artifact_path(manifest)
    smoke_suite_path = get_smoke_suite_path(manifest)

    missing_live_paths: list[str] = []
    present_live_paths: list[str] = []
    for pattern in get_required_live_paths(manifest):
        anchor = pattern_anchor(pattern)
        if anchor and (repo_root / anchor).exists():
            present_live_paths.append(pattern)
        else:
            missing_live_paths.append(pattern)

    checks = {
        "projection_artifact_declared": bool(projection_artifact_path),
        "smoke_suite_declared": bool(smoke_suite_path),
        "agent_entry_present": (repo_root / ".agent" / "workflows" / "AGENT_ENTRY.md").exists(),
        "required_live_paths_present": not missing_live_paths,
    }
    failures = [key for key, ok in checks.items() if not ok]
    notes: list[str] = []
    if failures:
        notes.append("portable smoke detected contract failures")
        status = "fail"
    else:
        notes.append("portable smoke verified manifest and required live path anchors")
        status = "pass"

    return {
        "status": status,
        "repo_root": str(repo_root.resolve()),
        "manifest_path": str(manifest_path.resolve()),
        "projection_artifact_path": projection_artifact_path,
        "smoke_suite_path": smoke_suite_path,
        "checks": checks,
        "missing_required_live_paths": missing_live_paths,
        "present_required_live_paths": present_live_paths,
        "failures": failures,
        "notes": notes,
    }


def format_text_report(result: dict) -> str:
    lines = [
        f"workflow-core portable smoke: {result['status']}",
        f"repo_root: {result['repo_root']}",
        f"manifest_path: {result['manifest_path']}",
        f"projection_artifact_path: {result['projection_artifact_path']}",
        f"smoke_suite_path: {result['smoke_suite_path']}",
    ]
    lines.append("checks:")
    for key, ok in result["checks"].items():
        lines.append(f"  - {key}: {'OK' if ok else 'FAIL'}")
    if result["missing_required_live_paths"]:
        lines.append("missing_required_live_paths:")
        for item in result["missing_required_live_paths"]:
            lines.append(f"  - {item}")
    if result["notes"]:
        lines.append("notes:")
        for item in result["notes"]:
            lines.append(f"  - {item}")
    return "\n".join(lines)


def exit_code_for_status(status: str) -> int:
    if status == "pass":
        return EXIT_PASS
    if status == "warn":
        return EXIT_WARN
    if status == "fail":
        return EXIT_FAIL
    return EXIT_ERROR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repo 根目錄（預設：目前目錄）")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="workflow-core canonical manifest path（預設：<repo-root>/core_ownership_manifest.yml）",
    )
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest.resolve() if args.manifest else manifest_default_path(repo_root)
    try:
        result = run_portable_smoke(repo_root=repo_root, manifest_path=manifest_path)
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"workflow-core portable smoke error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(result))
    return exit_code_for_status(result["status"])


if __name__ == "__main__":
    raise SystemExit(main())
