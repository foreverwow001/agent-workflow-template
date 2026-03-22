#!/usr/bin/env python3
"""檔案用途：套用指定 release ref 的 workflow-core managed paths，並在需要時串接 projection。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workflow_core_contracts import checkout_paths_from_ref, evaluate_manifest_contract, list_files_at_ref, ref_exists  # noqa: E402
from workflow_core_manifest import manifest_default_path, normalize_path, path_matches_pattern  # noqa: E402
from workflow_core_obsidian_restricted_mount import run_generate_downstream_obsidian_mount  # noqa: E402
from workflow_core_sync_precheck import run_sync_precheck  # noqa: E402


EXIT_PASS = 0
EXIT_WARN = 10
EXIT_FAIL = 20
EXIT_ERROR = 30


def load_projection_module(projection_script: Path):
    spec = importlib.util.spec_from_file_location("workflow_core_projection_runtime", projection_script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load projection script: {projection_script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize_staging_root(repo_root: Path, staging_root: Path | None) -> tuple[Path | None, str | None]:
    if staging_root is None:
        return None, None
    resolved = staging_root.resolve()
    try:
        relative = normalize_path(str(resolved.relative_to(repo_root)))
    except ValueError:
        relative = None
    return resolved, relative


def precheck_allows_staging_tree_only_warning(precheck: dict, staging_root_rel: str | None) -> bool:
    if not staging_root_rel or precheck.get("status") != "warn":
        return False
    if precheck.get("core_divergence_paths") or precheck.get("state_only_paths"):
        return False
    review_paths = [
        *precheck.get("overlay_only_paths", []),
        *precheck.get("unclassified_paths", []),
    ]
    if not review_paths:
        return False
    return all(path == staging_root_rel or path.startswith(staging_root_rel + "/") for path in review_paths)


def select_sync_mode(explicit_mode: str | None, projection_artifact_path: str) -> str:
    if explicit_mode:
        return explicit_mode
    return "staging-plus-projection" if projection_artifact_path else "direct-root"


def run_sync_apply(
    repo_root: Path,
    manifest_path: Path,
    release_ref: str,
    sync_mode: str | None = None,
    projection_script: Path | None = None,
    staging_root: Path | None = None,
    emit_obsidian_restricted_mount_sample: bool = False,
    obsidian_mount_output_dir: Path | None = None,
    force_obsidian_mount_sample: bool = False,
) -> dict:
    resolved_staging_root, staging_root_rel = normalize_staging_root(repo_root, staging_root)
    contract = evaluate_manifest_contract(repo_root, manifest_path)
    precheck = run_sync_precheck(repo_root=repo_root, release_ref=release_ref, manifest_path=manifest_path)
    allow_staging_warning = precheck_allows_staging_tree_only_warning(precheck, staging_root_rel)
    if precheck["status"] != "pass" and not allow_staging_warning:
        return {
            "status": "fail",
            "repo_root": contract["repo_root"],
            "manifest_path": contract["manifest_path"],
            "release_ref": release_ref,
            "sync_mode": select_sync_mode(sync_mode, contract["projection_artifact_path"]),
            "projection_ran": False,
            "obsidian_mount_sample_generated": False,
            "obsidian_mount_output_dir": None,
            "changed_managed_paths": [],
            "failed_stage": "precheck",
            "notes": ["sync precheck did not pass; apply aborted", *precheck["notes"]],
        }

    if resolved_staging_root is None and not ref_exists(repo_root, release_ref):
        return {
            "status": "fail",
            "repo_root": contract["repo_root"],
            "manifest_path": contract["manifest_path"],
            "release_ref": release_ref,
            "sync_mode": select_sync_mode(sync_mode, contract["projection_artifact_path"]),
            "projection_ran": False,
            "obsidian_mount_sample_generated": False,
            "obsidian_mount_output_dir": None,
            "changed_managed_paths": [],
            "failed_stage": "resolve-release-ref",
            "notes": ["release ref does not exist in this repository"],
        }

    resolved_mode = select_sync_mode(sync_mode, contract["projection_artifact_path"])
    if resolved_staging_root is not None:
        files_at_ref = sorted(
            normalize_path(str(path.relative_to(resolved_staging_root)))
            for path in resolved_staging_root.rglob("*")
            if path.is_file()
        )
    else:
        files_at_ref = list_files_at_ref(repo_root, release_ref)

    changed_managed_paths = sorted(
        path
        for path in files_at_ref
        if any(path_matches_pattern(path, pattern) for pattern in contract["managed_patterns"])
    )
    if not changed_managed_paths:
        return {
            "status": "fail",
            "repo_root": contract["repo_root"],
            "manifest_path": contract["manifest_path"],
            "release_ref": release_ref,
            "sync_mode": resolved_mode,
            "projection_ran": False,
            "obsidian_mount_sample_generated": False,
            "obsidian_mount_output_dir": None,
            "changed_managed_paths": [],
            "failed_stage": "select-managed-paths",
            "notes": ["staged export tree contains no managed paths to apply"] if resolved_staging_root is not None else ["release ref contains no managed paths to apply"],
        }

    if resolved_staging_root is None:
        checkout_paths_from_ref(repo_root, release_ref, changed_managed_paths)
    projection_ran = False
    mount_result = None
    notes = ["restored managed paths from release ref"] if resolved_staging_root is None else ["loaded managed paths from staged export tree"]
    if allow_staging_warning:
        notes.append("sync precheck warning was limited to the staged export tree and was ignored for apply")

    if resolved_mode == "staging-plus-projection":
        projection_target = projection_script or (repo_root / contract["projection_artifact_path"])
        if not projection_target.exists():
            return {
                "status": "fail",
                "repo_root": contract["repo_root"],
                "manifest_path": contract["manifest_path"],
                "release_ref": release_ref,
                "sync_mode": resolved_mode,
                "projection_ran": False,
                "obsidian_mount_sample_generated": False,
                "obsidian_mount_output_dir": None,
                "changed_managed_paths": changed_managed_paths,
                "failed_stage": "projection-bootstrap",
                "notes": ["projection script path does not exist"],
            }
        projection_module = load_projection_module(projection_target)
        projection_result = projection_module.run_projection_stub(
            repo_root=repo_root,
            manifest_path=manifest_path,
            source_root=resolved_staging_root,
            bootstrap_overlay_index_file=True,
            emit_obsidian_restricted_mount_sample=emit_obsidian_restricted_mount_sample,
            obsidian_mount_output_dir=obsidian_mount_output_dir,
            force_obsidian_mount_sample=force_obsidian_mount_sample,
        )
        projection_ran = True
        if projection_result.get("obsidian_mount_sample_generated"):
            mount_result = {
                "output_dir": projection_result.get("obsidian_mount_output_dir"),
            }
        notes.extend(projection_result.get("notes", []))
        if projection_result["status"] == "fail":
            return {
                "status": "fail",
                "repo_root": contract["repo_root"],
                "manifest_path": contract["manifest_path"],
                "release_ref": release_ref,
                "sync_mode": resolved_mode,
                "projection_ran": True,
                "obsidian_mount_sample_generated": bool(mount_result),
                "obsidian_mount_output_dir": mount_result.get("output_dir") if mount_result else None,
                "changed_managed_paths": changed_managed_paths,
                "failed_stage": "projection-bootstrap",
                "notes": notes,
            }

    if emit_obsidian_restricted_mount_sample and mount_result is None:
        mount_result = run_generate_downstream_obsidian_mount(
            repo_root=repo_root,
            output_dir=obsidian_mount_output_dir,
            force=force_obsidian_mount_sample,
        )
        notes.extend(mount_result.get("notes", []))

    return {
        "status": "pass",
        "repo_root": contract["repo_root"],
        "manifest_path": contract["manifest_path"],
        "release_ref": release_ref,
        "sync_mode": resolved_mode,
        "projection_ran": projection_ran,
        "obsidian_mount_sample_generated": bool(mount_result),
        "obsidian_mount_output_dir": mount_result.get("output_dir") if mount_result else None,
        "changed_managed_paths": changed_managed_paths,
        "failed_stage": None,
        "notes": notes,
    }


def format_text_report(result: dict) -> str:
    lines = [
        f"workflow-core sync apply: {result['status']}",
        f"repo_root: {result['repo_root']}",
        f"manifest_path: {result['manifest_path']}",
        f"release_ref: {result['release_ref']}",
        f"sync_mode: {result['sync_mode']}",
        f"projection_ran: {result['projection_ran']}",
        f"obsidian_mount_sample_generated: {result['obsidian_mount_sample_generated']}",
        f"obsidian_mount_output_dir: {result['obsidian_mount_output_dir']}",
        f"failed_stage: {result['failed_stage']}",
    ]
    if result["changed_managed_paths"]:
        lines.append("changed_managed_paths:")
        for item in result["changed_managed_paths"]:
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
    parser.add_argument("--release-ref", required=True, help="要套用的 release ref")
    parser.add_argument("--manifest", type=Path, default=None, help="workflow-core canonical manifest path")
    parser.add_argument(
        "--sync-mode",
        choices=["direct-root", "staging-plus-projection"],
        default=None,
        help="同步模式，未指定時依 manifest 自動判定",
    )
    parser.add_argument("--projection-script", type=Path, default=None, help="可選的 projection script override")
    parser.add_argument("--staging-root", type=Path, default=None, help="可選的 staged/export tree root，適用於獨立 downstream repo sync")
    parser.add_argument(
        "--emit-obsidian-restricted-mount-sample",
        dest="emit_obsidian_restricted_mount_sample",
        action="store_true",
        help="套用後額外產出 downstream restricted Obsidian mount sample（opt-in）",
    )
    parser.add_argument(
        "--setup-obsidian-restricted-access",
        dest="emit_obsidian_restricted_mount_sample",
        action="store_true",
        help="高層 alias：套用後一併建立 downstream restricted Obsidian access sample",
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
        result = run_sync_apply(
            repo_root=repo_root,
            manifest_path=manifest_path,
            release_ref=args.release_ref,
            sync_mode=args.sync_mode,
            projection_script=args.projection_script.resolve() if args.projection_script else None,
            staging_root=args.staging_root.resolve() if args.staging_root else None,
            emit_obsidian_restricted_mount_sample=bool(args.emit_obsidian_restricted_mount_sample),
            obsidian_mount_output_dir=args.obsidian_mount_output_dir.resolve() if args.obsidian_mount_output_dir else None,
            force_obsidian_mount_sample=bool(args.force_obsidian_mount_sample),
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"workflow-core sync apply error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(result))
    return exit_code_for_status(result["status"])


if __name__ == "__main__":
    raise SystemExit(main())
