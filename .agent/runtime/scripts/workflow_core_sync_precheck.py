#!/usr/bin/env python3
"""檔案用途：在 downstream subtree sync 前做 workflow-core working tree 與 ownership 風險預檢。"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workflow_core_manifest import (  # noqa: E402
    get_managed_patterns,
    get_overlay_patterns,
    get_state_patterns,
    load_manifest,
    manifest_default_path,
    normalize_path,
    path_matches_pattern,
)


EXIT_PASS = 0
EXIT_WARN = 10
EXIT_FAIL = 20
EXIT_ERROR = 30

def merge_patterns(defaults: list[str], extras: list[str] | None) -> list[str]:
    merged: list[str] = []
    for item in [*defaults, *(extras or [])]:
        normalized = normalize_path(str(item))
        if normalized and normalized not in merged:
            merged.append(normalized)
    return merged


def parse_porcelain_line(line: str) -> dict[str, Any]:
    raw_status = line[:2]
    payload = line[3:].strip() if len(line) > 3 else ""
    if " -> " in payload:
        source_path, path = payload.split(" -> ", 1)
        source_path = source_path.strip()
        path = path.strip()
    else:
        source_path = None
        path = payload
    return {
        "raw_status": raw_status,
        "staged_status": raw_status[0],
        "unstaged_status": raw_status[1] if len(raw_status) > 1 else " ",
        "path": normalize_path(path),
        "source_path": normalize_path(source_path) if source_path else None,
        "raw_line": line,
    }


def list_git_status(repo_root: Path) -> list[dict[str, Any]]:
    if shutil.which("git") is None:
        raise RuntimeError("git command not found on PATH")
    if not repo_root.exists():
        raise RuntimeError(f"repo root does not exist: {repo_root}")

    proc = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain=v1", "--untracked-files=all"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or "git status failed"
        raise RuntimeError(message)

    entries: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        if line.strip():
            entries.append(parse_porcelain_line(line))
    return entries


def classify_path(
    path: str,
    managed_patterns: list[str],
    overlay_patterns: list[str],
    state_patterns: list[str],
) -> str:
    if any(path_matches_pattern(path, pattern) for pattern in state_patterns):
        return "state"
    if any(path_matches_pattern(path, pattern) for pattern in overlay_patterns):
        return "overlay"
    if any(path_matches_pattern(path, pattern) for pattern in managed_patterns):
        return "managed"
    return "unclassified"


def classify_entry(
    entry: dict[str, Any],
    managed_patterns: list[str],
    overlay_patterns: list[str],
    state_patterns: list[str],
) -> dict[str, Any]:
    candidate_paths = [entry["path"]]
    if entry.get("source_path"):
        candidate_paths.append(entry["source_path"])

    categories = {
        classify_path(path, managed_patterns, overlay_patterns, state_patterns)
        for path in candidate_paths
        if path
    }

    if "managed" in categories:
        category = "managed"
    elif "state" in categories:
        category = "state"
    elif "overlay" in categories:
        category = "overlay"
    else:
        category = "unclassified"

    return {
        **entry,
        "category": category,
    }


def summarize_dirty_entries(
    entries: list[dict[str, Any]],
    managed_patterns: list[str],
    overlay_patterns: list[str],
    state_patterns: list[str],
) -> dict[str, Any]:
    annotated_entries = [
        classify_entry(entry, managed_patterns, overlay_patterns, state_patterns)
        for entry in entries
    ]

    summary = {
        "dirty_entries": annotated_entries,
        "core_divergence_paths": sorted({entry["path"] for entry in annotated_entries if entry["category"] == "managed"}),
        "overlay_only_paths": sorted({entry["path"] for entry in annotated_entries if entry["category"] == "overlay"}),
        "state_only_paths": sorted({entry["path"] for entry in annotated_entries if entry["category"] == "state"}),
        "unclassified_paths": sorted({entry["path"] for entry in annotated_entries if entry["category"] == "unclassified"}),
    }
    return summary


def run_sync_precheck(
    repo_root: Path,
    release_ref: str,
    manifest_path: Path | None = None,
    strict_clean: bool = False,
    managed_prefixes: list[str] | None = None,
    overlay_prefixes: list[str] | None = None,
    state_prefixes: list[str] | None = None,
) -> dict[str, Any]:
    if not str(release_ref or "").strip():
        raise ValueError("release_ref is required")

    resolved_manifest_path = manifest_path.resolve() if manifest_path else manifest_default_path(repo_root.resolve())
    manifest = load_manifest(resolved_manifest_path)

    merged_managed = merge_patterns(get_managed_patterns(manifest), managed_prefixes)
    merged_overlay = merge_patterns(get_overlay_patterns(manifest), overlay_prefixes)
    merged_state = merge_patterns(get_state_patterns(manifest), state_prefixes)

    entries = list_git_status(repo_root)
    dirty_summary = summarize_dirty_entries(entries, merged_managed, merged_overlay, merged_state)

    notes: list[str] = []
    manual_review_reasons: list[str] = []

    if dirty_summary["overlay_only_paths"]:
        manual_review_reasons.append("overlay-dirty")
    if dirty_summary["state_only_paths"]:
        manual_review_reasons.append("state-dirty")
    if dirty_summary["unclassified_paths"]:
        manual_review_reasons.append("unclassified-dirty")

    if dirty_summary["core_divergence_paths"]:
        status = "fail"
        notes.append("core managed paths contain local divergence; upstream/downstream ownership must be reconciled before sync")
    elif strict_clean and entries:
        status = "fail"
        notes.append("strict-clean is enabled and the working tree is not clean")
    elif manual_review_reasons:
        status = "warn"
        notes.append("working tree contains non-core dirty paths that require manual review before sync")
    else:
        status = "pass"
        notes.append("working tree is clean for workflow-core sync")

    return {
        "status": status,
        "repo_root": str(repo_root.resolve()),
        "manifest_path": str(resolved_manifest_path),
        "release_ref": release_ref,
        "clean_worktree": not entries,
        "strict_clean": strict_clean,
        "core_divergence_paths": dirty_summary["core_divergence_paths"],
        "overlay_only_paths": dirty_summary["overlay_only_paths"],
        "state_only_paths": dirty_summary["state_only_paths"],
        "unclassified_paths": dirty_summary["unclassified_paths"],
        "manual_review_required": bool(manual_review_reasons),
        "manual_review_reasons": manual_review_reasons,
        "dirty_entries": dirty_summary["dirty_entries"],
        "managed_patterns": merged_managed,
        "overlay_patterns": merged_overlay,
        "state_patterns": merged_state,
        "notes": notes,
    }


def format_text_report(result: dict[str, Any]) -> str:
    lines = [
        f"workflow-core sync precheck: {result['status']}",
        f"repo_root: {result['repo_root']}",
        f"manifest_path: {result['manifest_path']}",
        f"release_ref: {result['release_ref']}",
        f"clean_worktree: {result['clean_worktree']}",
        f"manual_review_required: {result['manual_review_required']}",
    ]

    sections = [
        ("core_divergence_paths", result.get("core_divergence_paths", [])),
        ("overlay_only_paths", result.get("overlay_only_paths", [])),
        ("state_only_paths", result.get("state_only_paths", [])),
        ("unclassified_paths", result.get("unclassified_paths", [])),
    ]
    for label, paths in sections:
        lines.append(f"{label}: {len(paths)}")
        for path in paths:
            lines.append(f"  - {path}")

    if result.get("manual_review_reasons"):
        lines.append("manual_review_reasons:")
        for reason in result["manual_review_reasons"]:
            lines.append(f"  - {reason}")

    if result.get("notes"):
        lines.append("notes:")
        for note in result["notes"]:
            lines.append(f"  - {note}")

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
    parser.add_argument("--release-ref", required=True, help="準備同步的 upstream release ref")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="workflow-core canonical manifest path（預設：<repo-root>/core_ownership_manifest.yml）",
    )
    parser.add_argument(
        "--managed-prefix",
        action="append",
        default=[],
        help="額外視為 core managed 的 pattern/prefix，可重複指定（phase-1 override）",
    )
    parser.add_argument(
        "--overlay-prefix",
        action="append",
        default=[],
        help="額外視為 project overlay 的 pattern/prefix，可重複指定（phase-1 override）",
    )
    parser.add_argument(
        "--state-prefix",
        action="append",
        default=[],
        help="額外視為 runtime/config state 的 pattern/prefix，可重複指定（phase-1 override）",
    )
    parser.add_argument(
        "--strict-clean",
        action="store_true",
        help="若 working tree 有任何 dirty path，直接視為 fail",
    )
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = run_sync_precheck(
            repo_root=args.repo_root.resolve(),
            release_ref=args.release_ref,
            manifest_path=args.manifest,
            strict_clean=bool(args.strict_clean),
            managed_prefixes=list(args.managed_prefix or []),
            overlay_prefixes=list(args.overlay_prefix or []),
            state_prefixes=list(args.state_prefix or []),
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"workflow-core sync precheck error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(result))
    return exit_code_for_status(result["status"])


if __name__ == "__main__":
    raise SystemExit(main())
