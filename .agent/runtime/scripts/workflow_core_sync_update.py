#!/usr/bin/env python3
"""檔案用途：以單一入口串接 workflow-core downstream sync lane。"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workflow_core_manifest import manifest_default_path  # noqa: E402
from workflow_core_sync_apply import run_sync_apply  # noqa: E402
from workflow_core_sync_stage import default_staging_root, run_sync_stage  # noqa: E402
from workflow_core_sync_verify import run_sync_verify  # noqa: E402


EXIT_PASS = 0
EXIT_WARN = 10
EXIT_FAIL = 20
EXIT_ERROR = 30


def prepare_staging_root(repo_root: Path, release_ref: str, staging_root: Path | None, replace_staging_root: bool) -> tuple[Path, bool]:
    resolved = default_staging_root(repo_root, release_ref, staging_root)
    replaced = False

    if not resolved.exists():
        return resolved, replaced

    should_replace = replace_staging_root or staging_root is None
    if resolved.is_dir():
        if not any(resolved.iterdir()):
            return resolved, replaced
        if not should_replace:
            raise RuntimeError(f"staging root is not empty; pass --replace-staging-root or omit --staging-root: {resolved}")
        shutil.rmtree(resolved)
        return resolved, True

    if not should_replace:
        raise RuntimeError(f"staging root path already exists and is not a directory: {resolved}")
    resolved.unlink()
    return resolved, True


def run_sync_update(
    repo_root: Path,
    manifest_path: Path,
    release_ref: str,
    source_ref: str | None = None,
    source_remote: str | None = None,
    profile_name: str | None = None,
    staging_root: Path | None = None,
    replace_staging_root: bool = False,
    sync_mode: str | None = None,
    projection_script: Path | None = None,
    setup_obsidian_restricted_access: bool = False,
    obsidian_mount_output_dir: Path | None = None,
    force_obsidian_mount_sample: bool = False,
) -> dict:
    effective_staging_root, replaced_existing_staging_root = prepare_staging_root(
        repo_root=repo_root,
        release_ref=release_ref,
        staging_root=staging_root,
        replace_staging_root=replace_staging_root,
    )

    stage_result = run_sync_stage(
        repo_root=repo_root,
        release_ref=release_ref,
        source_ref=source_ref,
        source_remote=source_remote,
        profile_name=profile_name,
        staging_root=effective_staging_root,
        manifest_path=manifest_path,
    )

    notes = list(stage_result.get("notes", []))
    if replaced_existing_staging_root:
        notes.append("replaced existing staging root before running one-click sync")

    if stage_result["status"] != "pass":
        return {
            "status": "fail",
            "repo_root": str(repo_root.resolve()),
            "manifest_path": str(manifest_path.resolve()),
            "release_ref": release_ref,
            "source_ref": source_ref or release_ref,
            "source_remote": source_remote,
            "staging_root": str(effective_staging_root),
            "replaced_existing_staging_root": replaced_existing_staging_root,
            "setup_obsidian_restricted_access": setup_obsidian_restricted_access,
            "obsidian_mount_sample_generated": False,
            "failed_stage": "sync-stage",
            "stage_result": stage_result,
            "apply_result": None,
            "verify_result": None,
            "notes": notes,
        }

    apply_result = run_sync_apply(
        repo_root=repo_root,
        manifest_path=manifest_path,
        release_ref=release_ref,
        sync_mode=sync_mode,
        projection_script=projection_script,
        staging_root=effective_staging_root,
        emit_obsidian_restricted_mount_sample=setup_obsidian_restricted_access,
        obsidian_mount_output_dir=obsidian_mount_output_dir,
        force_obsidian_mount_sample=force_obsidian_mount_sample,
    )
    notes.extend(apply_result.get("notes", []))
    if apply_result["status"] != "pass":
        return {
            "status": "fail",
            "repo_root": str(repo_root.resolve()),
            "manifest_path": str(manifest_path.resolve()),
            "release_ref": release_ref,
            "source_ref": source_ref or release_ref,
            "source_remote": source_remote,
            "staging_root": str(effective_staging_root),
            "replaced_existing_staging_root": replaced_existing_staging_root,
            "setup_obsidian_restricted_access": setup_obsidian_restricted_access,
            "obsidian_mount_sample_generated": bool(apply_result.get("obsidian_mount_sample_generated")),
            "failed_stage": "sync-apply",
            "stage_result": stage_result,
            "apply_result": apply_result,
            "verify_result": None,
            "notes": notes,
        }

    verify_result = run_sync_verify(
        repo_root=repo_root,
        manifest_path=manifest_path,
        release_ref=release_ref,
        staging_root=effective_staging_root,
    )
    notes.extend(verify_result.get("notes", []))

    return {
        "status": verify_result["status"],
        "repo_root": str(repo_root.resolve()),
        "manifest_path": str(manifest_path.resolve()),
        "release_ref": release_ref,
        "source_ref": source_ref or release_ref,
        "source_remote": source_remote,
        "staging_root": str(effective_staging_root),
        "replaced_existing_staging_root": replaced_existing_staging_root,
        "setup_obsidian_restricted_access": setup_obsidian_restricted_access,
        "obsidian_mount_sample_generated": bool(apply_result.get("obsidian_mount_sample_generated")),
        "failed_stage": None if verify_result["status"] == "pass" else "sync-verify",
        "stage_result": stage_result,
        "apply_result": apply_result,
        "verify_result": verify_result,
        "notes": notes,
    }


def format_text_report(result: dict) -> str:
    lines = [
        f"workflow-core sync update: {result['status']}",
        f"repo_root: {result['repo_root']}",
        f"manifest_path: {result['manifest_path']}",
        f"release_ref: {result['release_ref']}",
        f"source_ref: {result['source_ref']}",
        f"source_remote: {result['source_remote']}",
        f"staging_root: {result['staging_root']}",
        f"replaced_existing_staging_root: {result['replaced_existing_staging_root']}",
        f"setup_obsidian_restricted_access: {result['setup_obsidian_restricted_access']}",
        f"obsidian_mount_sample_generated: {result['obsidian_mount_sample_generated']}",
        f"failed_stage: {result['failed_stage']}",
    ]
    if result.get("stage_result"):
        lines.append(f"sync_stage_status: {result['stage_result']['status']}")
    if result.get("apply_result"):
        lines.append(f"sync_apply_status: {result['apply_result']['status']}")
    if result.get("verify_result"):
        lines.append(f"sync_verify_status: {result['verify_result']['status']}")
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
    parser.add_argument("--release-ref", required=True, help="下游要追蹤的 workflow-core release ref")
    parser.add_argument("--source-ref", default=None, help="來源 ref；未指定時預設為 --release-ref")
    parser.add_argument("--source-remote", default=None, help="可選的 upstream remote 名稱；指定時會先 fetch 再 stage")
    parser.add_argument("--profile", default=None, help="export profile name；未指定時使用 manifest active profile")
    parser.add_argument("--manifest", type=Path, default=None, help="workflow-core canonical manifest path")
    parser.add_argument("--staging-root", type=Path, default=None, help="可選的 staging root；未指定時自動使用預設位置")
    parser.add_argument("--replace-staging-root", action="store_true", help="允許覆蓋非空的自訂 staging root")
    parser.add_argument(
        "--sync-mode",
        choices=["direct-root", "staging-plus-projection"],
        default=None,
        help="同步模式，未指定時依 manifest 自動判定",
    )
    parser.add_argument("--projection-script", type=Path, default=None, help="可選的 projection script override")
    parser.add_argument(
        "--setup-obsidian-restricted-access",
        action="store_true",
        help="套用後一併建立 downstream restricted Obsidian access sample",
    )
    parser.add_argument(
        "--obsidian-mount-output-dir",
        type=Path,
        default=None,
        help="restricted mount sample 輸出目錄（預設：<repo-root>/.devcontainer）",
    )
    parser.add_argument(
        "--force-obsidian-mount-sample",
        action="store_true",
        help="若 sample 已存在且內容不同，允許覆蓋",
    )
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest.resolve() if args.manifest else manifest_default_path(repo_root)
    try:
        result = run_sync_update(
            repo_root=repo_root,
            manifest_path=manifest_path,
            release_ref=args.release_ref,
            source_ref=args.source_ref,
            source_remote=args.source_remote,
            profile_name=args.profile,
            staging_root=args.staging_root.resolve() if args.staging_root else None,
            replace_staging_root=bool(args.replace_staging_root),
            sync_mode=args.sync_mode,
            projection_script=args.projection_script.resolve() if args.projection_script else None,
            setup_obsidian_restricted_access=bool(args.setup_obsidian_restricted_access),
            obsidian_mount_output_dir=args.obsidian_mount_output_dir.resolve() if args.obsidian_mount_output_dir else None,
            force_obsidian_mount_sample=bool(args.force_obsidian_mount_sample),
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"workflow-core sync update error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(result))
    return exit_code_for_status(result["status"])


if __name__ == "__main__":
    raise SystemExit(main())
