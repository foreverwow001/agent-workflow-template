#!/usr/bin/env python3
"""檔案用途：從 local 或 remote release ref materialize curated workflow-core export tree 到 downstream staging root。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workflow_core_contracts import (  # noqa: E402
    fetch_ref,
    read_bytes_at_ref,
    read_text_at_ref,
    resolve_ref,
    safe_ref_label,
    write_json_file,
)
from workflow_core_manifest import (  # noqa: E402
    get_default_export_profile_name,
    get_export_profile,
    get_state_patterns,
    load_manifest_text,
    manifest_default_path,
    normalize_path,
    path_matches_pattern,
)


EXIT_PASS = 0
EXIT_WARN = 10
EXIT_FAIL = 20
EXIT_ERROR = 30


def ensure_empty_output_dir(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"output directory must be empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def default_staging_root(repo_root: Path, release_ref: str, staging_root: Path | None) -> Path:
    if staging_root is not None:
        return staging_root.resolve()
    return (repo_root / ".workflow-core" / "staging" / safe_ref_label(release_ref)).resolve()


def list_files_at_ref(repo_root: Path, ref: str) -> list[str]:
    from workflow_core_contracts import list_files_at_ref as contracts_list_files_at_ref

    return contracts_list_files_at_ref(repo_root, ref)


def select_export_paths(files_at_ref: list[str], includes: list[str], excludes: list[str]) -> list[str]:
    selected: list[str] = []
    for path in files_at_ref:
        if not any(path_matches_pattern(path, pattern) for pattern in includes):
            continue
        if any(path_matches_pattern(path, pattern) for pattern in excludes):
            continue
        selected.append(path)
    return selected


def metadata_path_for_staging_root(staging_root: Path) -> Path:
    return staging_root / "workflow-core-stage-metadata.json"


def run_sync_stage(
    repo_root: Path,
    release_ref: str,
    source_ref: str | None = None,
    source_remote: str | None = None,
    profile_name: str | None = None,
    staging_root: Path | None = None,
    manifest_path: Path | None = None,
) -> dict:
    if not str(release_ref or "").strip():
        raise ValueError("release_ref is required")

    manifest_rel_path = normalize_path(
        str((manifest_path or manifest_default_path(repo_root)).resolve().relative_to(repo_root.resolve()))
    )
    requested_source_ref = source_ref or release_ref
    fetched_ref: str | None = None

    if source_remote:
        fetched_ref = f"refs/workflow-core/fetched/{safe_ref_label(source_remote)}-{safe_ref_label(requested_source_ref)}"
        resolved_source_ref = fetch_ref(repo_root, source_remote, requested_source_ref, fetched_ref)
    else:
        resolved_source_ref = resolve_ref(repo_root, requested_source_ref)
        if resolved_source_ref is None:
            raise RuntimeError(f"source ref does not resolve: {requested_source_ref}")

    manifest_text = read_text_at_ref(repo_root, resolved_source_ref, manifest_rel_path)
    manifest = load_manifest_text(manifest_text, source_label=f"{resolved_source_ref}:{manifest_rel_path}")
    resolved_profile_name = profile_name or get_default_export_profile_name(manifest)
    profile = get_export_profile(manifest, resolved_profile_name)

    effective_excludes = [*profile["excludes"], *get_state_patterns(manifest)]
    files_at_ref = list_files_at_ref(repo_root, resolved_source_ref)
    selected_paths = select_export_paths(files_at_ref, profile["includes"], effective_excludes)
    if not selected_paths:
        return {
            "status": "fail",
            "repo_root": str(repo_root.resolve()),
            "release_ref": release_ref,
            "source_ref": requested_source_ref,
            "resolved_source_ref": resolved_source_ref,
            "source_remote": source_remote,
            "profile_name": resolved_profile_name,
            "staging_root": None,
            "metadata_path": None,
            "selected_path_count": 0,
            "selected_paths": [],
            "notes": ["export profile matched no files at the requested source ref"],
        }

    resolved_staging_root = default_staging_root(repo_root, release_ref, staging_root)
    ensure_empty_output_dir(resolved_staging_root)

    written_paths: list[str] = []
    for rel_path in selected_paths:
        target_path = resolved_staging_root / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(read_bytes_at_ref(repo_root, resolved_source_ref, rel_path))
        written_paths.append(rel_path)

    metadata_payload = {
        "release_ref": release_ref,
        "source_ref": requested_source_ref,
        "resolved_source_ref": resolved_source_ref,
        "source_remote": source_remote,
        "fetched_ref": fetched_ref,
        "manifest_path": manifest_rel_path,
        "profile_name": profile["name"],
        "profile_status": profile["status"],
        "profile_purpose": profile["purpose"],
        "selected_paths": written_paths,
        "selected_path_count": len(written_paths),
        "deferred_paths": profile["deferred_paths"],
        "notes": profile["notes"],
    }
    metadata_path = write_json_file(metadata_path_for_staging_root(resolved_staging_root), metadata_payload)

    notes = ["materialized workflow-core export tree into staging root"]
    if source_remote:
        notes.append("fetched source ref from remote before staging export tree")

    return {
        "status": "pass",
        "repo_root": str(repo_root.resolve()),
        "release_ref": release_ref,
        "source_ref": requested_source_ref,
        "resolved_source_ref": resolved_source_ref,
        "source_remote": source_remote,
        "profile_name": profile["name"],
        "staging_root": str(resolved_staging_root),
        "metadata_path": metadata_path,
        "selected_path_count": len(written_paths),
        "selected_paths": written_paths,
        "notes": notes,
    }


def format_text_report(result: dict) -> str:
    lines = [
        f"workflow-core sync stage: {result['status']}",
        f"repo_root: {result['repo_root']}",
        f"release_ref: {result['release_ref']}",
        f"source_ref: {result['source_ref']}",
        f"resolved_source_ref: {result['resolved_source_ref']}",
        f"source_remote: {result['source_remote']}",
        f"profile_name: {result['profile_name']}",
        f"staging_root: {result['staging_root']}",
        f"metadata_path: {result['metadata_path']}",
        f"selected_path_count: {result['selected_path_count']}",
    ]
    if result["selected_paths"]:
        lines.append("selected_paths:")
        for item in result["selected_paths"]:
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
    parser.add_argument("--release-ref", required=True, help="下游要追蹤的 workflow-core release ref")
    parser.add_argument("--source-ref", default=None, help="來源 ref；未指定時預設為 --release-ref")
    parser.add_argument("--source-remote", default=None, help="可選的 upstream remote 名稱；指定時會先 fetch 再 stage")
    parser.add_argument("--profile", default=None, help="export profile name；未指定時使用 manifest active profile")
    parser.add_argument("--staging-root", type=Path, default=None, help="staging root；未指定時預設為 .workflow-core/staging/<release-ref>")
    parser.add_argument("--manifest", type=Path, default=None, help="manifest 路徑；預設為 repo-root/core_ownership_manifest.yml")
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest.resolve() if args.manifest else None
    try:
        result = run_sync_stage(
            repo_root=repo_root,
            release_ref=args.release_ref,
            source_ref=args.source_ref,
            source_remote=args.source_remote,
            profile_name=args.profile,
            staging_root=args.staging_root.resolve() if args.staging_root else None,
            manifest_path=manifest_path,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"workflow-core sync stage error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(result))
    return exit_code_for_status(result["status"])


if __name__ == "__main__":
    raise SystemExit(main())
