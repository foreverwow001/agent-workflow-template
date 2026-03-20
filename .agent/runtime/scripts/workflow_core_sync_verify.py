#!/usr/bin/env python3
"""檔案用途：在 workflow-core sync 後驗證 live path、portable smoke 與最小 preflight。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workflow_core_contracts import evaluate_manifest_contract, run_shell_command, worktree_path_matches_ref  # noqa: E402
from workflow_core_manifest import manifest_default_path  # noqa: E402
from workflow_core_sync_precheck import run_sync_precheck  # noqa: E402


EXIT_PASS = 0
EXIT_WARN = 10
EXIT_FAIL = 20
EXIT_ERROR = 30


def load_module(file_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module: {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def worktree_path_matches_staging_root(repo_root: Path, staging_root: Path, path: str) -> bool:
    worktree_path = repo_root / path
    source_path = staging_root / path
    if not worktree_path.exists() or not source_path.exists():
        return False
    return worktree_path.read_bytes() == source_path.read_bytes()


def run_sync_verify(
    repo_root: Path,
    manifest_path: Path,
    release_ref: str,
    required_live_paths: list[str] | None = None,
    preflight_command: str | None = None,
    smoke_command: str | None = None,
    staging_root: Path | None = None,
) -> dict:
    contract = evaluate_manifest_contract(repo_root, manifest_path, extra_required_live_paths=required_live_paths)
    failures: list[str] = []
    notes: list[str] = []
    preflight_context_notes: list[str] = []

    if preflight_command:
        preflight_ok, preflight_output = run_shell_command(repo_root, preflight_command)
    else:
        precheck = run_sync_precheck(repo_root=repo_root, release_ref=release_ref, manifest_path=manifest_path)
        if precheck["core_divergence_paths"]:
            if staging_root is not None:
                aligned_paths = [
                    path for path in precheck["core_divergence_paths"] if worktree_path_matches_staging_root(repo_root, staging_root, path)
                ]
                context_label = "staged export tree"
            else:
                aligned_paths = [
                    path for path in precheck["core_divergence_paths"] if worktree_path_matches_ref(repo_root, release_ref, path)
                ]
                context_label = "requested release ref"
            unexpected_paths = [path for path in precheck["core_divergence_paths"] if path not in aligned_paths]
            if unexpected_paths:
                preflight_ok = False
                preflight_output = "; ".join(
                    [
                        *precheck.get("notes", []),
                        f"managed paths still differ from target {context_label}: {', '.join(unexpected_paths)}",
                    ]
                )
            else:
                preflight_ok = True
                preflight_output = f"managed worktree changes already match the target {context_label}"
                preflight_context_notes.append(preflight_output)
        else:
            preflight_ok = precheck["status"] != "fail"
            preflight_output = "; ".join(precheck.get("notes", []))

    if smoke_command:
        portable_smoke_ok, smoke_output = run_shell_command(repo_root, smoke_command)
    else:
        smoke_module = load_module(repo_root / contract["smoke_suite_path"], "workflow_core_smoke_runtime")
        smoke_result = smoke_module.run_portable_smoke(repo_root=repo_root, manifest_path=manifest_path)
        portable_smoke_ok = smoke_result["status"] == "pass"
        smoke_output = "; ".join(smoke_result.get("notes", []))

    live_paths_ok = contract["live_path_contract_ok"]
    agent_entry_contract_ok = contract["agent_entry_present"]
    skills_split_ok = contract["skills_mutable_split_ok"]

    if not live_paths_ok:
        failures.append("required live path anchors are missing")
    if not agent_entry_contract_ok:
        failures.append("AGENT_ENTRY.md is missing")
    if not preflight_ok:
        failures.append(f"preflight failed: {preflight_output}")
    else:
        notes.extend(preflight_context_notes)
    if not portable_smoke_ok:
        failures.append(f"portable smoke failed: {smoke_output}")
    if not skills_split_ok:
        failures.append("skills split contract is violated")

    status = "fail" if failures else "pass"
    if status == "pass":
        notes.append("sync verification passed with manifest-backed preflight and portable smoke")
    else:
        notes = [*failures, *notes]

    return {
        "status": status,
        "repo_root": contract["repo_root"],
        "manifest_path": contract["manifest_path"],
        "release_ref": release_ref,
        "live_paths_ok": live_paths_ok,
        "agent_entry_contract_ok": agent_entry_contract_ok,
        "preflight_ok": preflight_ok,
        "portable_smoke_ok": portable_smoke_ok,
        "skills_split_ok": skills_split_ok,
        "notes": notes,
    }


def format_text_report(result: dict) -> str:
    lines = [
        f"workflow-core sync verify: {result['status']}",
        f"repo_root: {result['repo_root']}",
        f"manifest_path: {result['manifest_path']}",
        f"release_ref: {result['release_ref']}",
        f"live_paths_ok: {result['live_paths_ok']}",
        f"agent_entry_contract_ok: {result['agent_entry_contract_ok']}",
        f"preflight_ok: {result['preflight_ok']}",
        f"portable_smoke_ok: {result['portable_smoke_ok']}",
        f"skills_split_ok: {result['skills_split_ok']}",
    ]
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
    parser.add_argument("--release-ref", required=True, help="剛套用的 release ref")
    parser.add_argument("--manifest", type=Path, default=None, help="workflow-core canonical manifest path")
    parser.add_argument("--require-live-path", action="append", default=[], help="額外要求存在的 live path")
    parser.add_argument("--preflight-command", default=None, help="自訂 preflight command")
    parser.add_argument("--smoke-command", default=None, help="自訂 smoke command")
    parser.add_argument("--staging-root", type=Path, default=None, help="可選的 staged/export tree root，用於獨立 downstream repo verify")
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest.resolve() if args.manifest else manifest_default_path(repo_root)
    try:
        result = run_sync_verify(
            repo_root=repo_root,
            manifest_path=manifest_path,
            release_ref=args.release_ref,
            required_live_paths=list(args.require_live_path or []),
            preflight_command=args.preflight_command,
            smoke_command=args.smoke_command,
            staging_root=args.staging_root.resolve() if args.staging_root else None,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"workflow-core sync verify error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(result))
    return exit_code_for_status(result["status"])


if __name__ == "__main__":
    raise SystemExit(main())
