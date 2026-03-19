#!/usr/bin/env python3
"""檔案用途：依 manifest export profile materialize 第一波 curated workflow-core 匯出樹。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workflow_core_contracts import patterns_overlap, resolve_ref, write_json_file  # noqa: E402
from workflow_core_manifest import (  # noqa: E402
    get_default_export_profile_name,
    get_export_profile,
    get_managed_patterns,
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


def list_worktree_files(repo_root: Path) -> list[str]:
    files: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel_path = normalize_path(str(path.relative_to(repo_root)))
        if rel_path == ".git" or rel_path.startswith(".git/"):
            continue
        if "/__pycache__/" in f"/{rel_path}" or rel_path.endswith(".pyc"):
            continue
        files.append(rel_path)
    return sorted(set(files))


def read_blob_at_ref(repo_root: Path, ref: str, path: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{ref}:{path}"],
        check=False,
        capture_output=True,
    )
    if proc.returncode != 0:
        message = proc.stderr.decode("utf-8", errors="replace").strip() or proc.stdout.decode(
            "utf-8", errors="replace"
        ).strip()
        raise RuntimeError(message or f"unable to read {path} at {ref}")
    return proc.stdout


def list_files_at_ref(repo_root: Path, ref: str) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "ls-tree", "-r", "--name-only", ref],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or f"unable to list files at {ref}"
        raise RuntimeError(message)
    return [normalize_path(line) for line in proc.stdout.splitlines() if line.strip()]


def ensure_empty_output_dir(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"output directory must be empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def validate_profile_contract(profile: dict, managed_patterns: list[str]) -> list[str]:
    violations: list[str] = []
    for include_pattern in profile["includes"]:
        if not any(patterns_overlap(include_pattern, managed_pattern) for managed_pattern in managed_patterns):
            violations.append(f"{include_pattern} is not backed by a managed_path contract")
    return violations


def select_export_paths(files_at_ref: list[str], includes: list[str], excludes: list[str]) -> list[str]:
    selected: list[str] = []
    for path in files_at_ref:
        if not any(path_matches_pattern(path, pattern) for pattern in includes):
            continue
        if any(path_matches_pattern(path, pattern) for pattern in excludes):
            continue
        selected.append(path)
    return selected


def find_unmatched_patterns(files_at_ref: list[str], patterns: list[str]) -> list[str]:
    unmatched: list[str] = []
    for pattern in patterns:
        if not any(path_matches_pattern(path, pattern) for path in files_at_ref):
            unmatched.append(pattern)
    return unmatched


def matched_paths_for_pattern(paths: list[str], pattern: str, excludes: list[str] | None = None) -> list[str]:
    excluded = excludes or []
    return [
        path
        for path in paths
        if path_matches_pattern(path, pattern) and not any(path_matches_pattern(path, exclude) for exclude in excluded)
    ]


def analyze_export_profile(
    repo_root: Path,
    manifest_path: Path,
    profile_name: str | None = None,
    source_ref: str | None = None,
) -> dict:
    manifest = load_manifest(manifest_path)
    resolved_profile_name = profile_name or get_default_export_profile_name(manifest)
    profile = get_export_profile(manifest, resolved_profile_name)
    resolved_source_ref = resolve_ref(repo_root, source_ref)
    if resolved_source_ref is None:
        raise RuntimeError(f"source ref does not resolve: {source_ref or 'HEAD'}")

    files_at_ref = list_files_at_ref(repo_root, resolved_source_ref)
    worktree_files = list_worktree_files(repo_root)
    managed_patterns = get_managed_patterns(manifest)
    state_patterns = get_state_patterns(manifest)
    contract_violations = validate_profile_contract(profile, managed_patterns)
    selected_paths = select_export_paths(files_at_ref, profile["includes"], profile["excludes"])
    effective_excludes = [*profile["excludes"], *state_patterns]

    include_pattern_statuses: list[dict[str, object]] = []
    ready_patterns: list[str] = []
    worktree_only_patterns: list[str] = []
    missing_patterns: list[str] = []

    for pattern in profile["includes"]:
        source_ref_matches = matched_paths_for_pattern(files_at_ref, pattern, effective_excludes)
        worktree_matches = matched_paths_for_pattern(worktree_files, pattern, effective_excludes)
        if source_ref_matches:
            status = "ready"
            ready_patterns.append(pattern)
        elif worktree_matches:
            status = "worktree-only"
            worktree_only_patterns.append(pattern)
        else:
            status = "missing"
            missing_patterns.append(pattern)
        include_pattern_statuses.append(
            {
                "pattern": pattern,
                "status": status,
                "source_ref_matches": source_ref_matches,
                "worktree_matches": worktree_matches,
            }
        )

    if contract_violations:
        status = "fail"
        notes = ["export profile contains include patterns outside managed_paths"]
    elif worktree_only_patterns or missing_patterns:
        status = "warn"
        notes = ["export profile still has landing gaps before the next clean release ref can be exported"]
    else:
        status = "pass"
        notes = ["export profile is fully represented at the requested source ref"]

    return {
        "status": status,
        "repo_root": str(repo_root.resolve()),
        "manifest_path": str(manifest_path.resolve()),
        "profile_name": profile["name"],
        "profile_status": profile["status"],
        "profile_purpose": profile["purpose"],
        "source_ref": resolved_source_ref,
        "selected_paths": selected_paths,
        "selected_path_count": len(selected_paths),
        "ready_include_patterns": ready_patterns,
        "worktree_only_include_patterns": worktree_only_patterns,
        "missing_include_patterns": missing_patterns,
        "include_pattern_statuses": include_pattern_statuses,
        "profile_contract_violations": contract_violations,
        "deferred_paths": profile["deferred_paths"],
        "notes": [*notes, *profile["notes"]],
    }


def materialize_paths(repo_root: Path, ref: str, selected_paths: list[str], output_dir: Path) -> list[str]:
    written_paths: list[str] = []
    for rel_path in selected_paths:
        target_path = output_dir / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(read_blob_at_ref(repo_root, ref, rel_path))
        written_paths.append(normalize_path(str(target_path.relative_to(output_dir))))
    return written_paths


def metadata_output_path(output_dir: Path, profile_name: str) -> Path:
    safe_name = "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in profile_name)
    return output_dir / f"workflow-core-export-{safe_name}.json"


def run_export_materialize(
    repo_root: Path,
    manifest_path: Path,
    output_dir: Path,
    profile_name: str | None = None,
    source_ref: str | None = None,
) -> dict:
    analysis = analyze_export_profile(
        repo_root=repo_root,
        manifest_path=manifest_path,
        profile_name=profile_name,
        source_ref=source_ref,
    )
    manifest = load_manifest(manifest_path)
    profile = get_export_profile(manifest, analysis["profile_name"])
    resolved_source_ref = str(analysis["source_ref"])
    contract_violations = list(analysis["profile_contract_violations"])
    missing_include_patterns = list(analysis["missing_include_patterns"])
    selected_paths = list(analysis["selected_paths"])

    if contract_violations:
        status = "fail"
        notes = ["export profile contains include patterns outside managed_paths"]
        written_paths: list[str] = []
        metadata_path = None
    elif not selected_paths:
        status = "fail"
        notes = ["export profile matched no files at source ref"]
        written_paths = []
        metadata_path = None
    else:
        ensure_empty_output_dir(output_dir)
        written_paths = materialize_paths(repo_root, resolved_source_ref, selected_paths, output_dir)
        payload = {
            "profile_name": profile["name"],
            "profile_status": profile["status"],
            "profile_purpose": profile["purpose"],
            "source_ref": resolved_source_ref,
            "selected_paths": written_paths,
            "selected_path_count": len(written_paths),
            "missing_include_patterns": missing_include_patterns,
            "deferred_paths": profile["deferred_paths"],
            "notes": profile["notes"],
        }
        metadata_path = write_json_file(metadata_output_path(output_dir, profile["name"]), payload)
        notes = ["materialized export profile into output directory"]
        if missing_include_patterns:
            status = "warn"
            notes.append("some export-profile include patterns did not match any file at the source ref")
        else:
            status = "pass"

    return {
        "status": status,
        "repo_root": analysis["repo_root"],
        "manifest_path": analysis["manifest_path"],
        "profile_name": analysis["profile_name"],
        "profile_status": analysis["profile_status"],
        "profile_purpose": analysis["profile_purpose"],
        "source_ref": resolved_source_ref,
        "output_path": str(output_dir.resolve()),
        "selected_paths": written_paths,
        "selected_path_count": len(written_paths),
        "missing_include_patterns": missing_include_patterns,
        "profile_contract_violations": contract_violations,
        "deferred_paths": analysis["deferred_paths"],
        "metadata_path": metadata_path,
        "notes": [*notes, *profile["notes"]],
    }


def format_text_report(result: dict) -> str:
    lines = [
        f"workflow-core export materialize: {result['status']}",
        f"repo_root: {result['repo_root']}",
        f"manifest_path: {result['manifest_path']}",
        f"profile_name: {result['profile_name']}",
        f"source_ref: {result['source_ref']}",
        f"output_path: {result['output_path']}",
        f"selected_path_count: {result['selected_path_count']}",
    ]
    if result["selected_paths"]:
        lines.append("selected_paths:")
        for item in result["selected_paths"]:
            lines.append(f"  - {item}")
    if result["missing_include_patterns"]:
        lines.append("missing_include_patterns:")
        for item in result["missing_include_patterns"]:
            lines.append(f"  - {item}")
    if result["profile_contract_violations"]:
        lines.append("profile_contract_violations:")
        for item in result["profile_contract_violations"]:
            lines.append(f"  - {item}")
    if result["deferred_paths"]:
        lines.append("deferred_paths:")
        for item in result["deferred_paths"]:
            lines.append(f"  - {item.get('path', '')}: {item.get('reason', '')}")
    if result["metadata_path"]:
        lines.append(f"metadata_path: {result['metadata_path']}")
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
    parser.add_argument("--manifest", type=Path, default=None, help="workflow-core canonical manifest path")
    parser.add_argument(
        "--profile",
        default=None,
        help="manifest export profile name（預設：manifest 中 status=active 的 profile）",
    )
    parser.add_argument("--source-ref", default=None, help="要 materialize 的來源 ref，預設為 HEAD")
    parser.add_argument("--output", type=Path, required=True, help="匯出目錄（必須不存在或為空）")
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest.resolve() if args.manifest else manifest_default_path(repo_root)
    try:
        result = run_export_materialize(
            repo_root=repo_root,
            manifest_path=manifest_path,
            output_dir=args.output.resolve(),
            profile_name=args.profile,
            source_ref=args.source_ref,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"workflow-core export materialize error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(result))
    return exit_code_for_status(result["status"])


if __name__ == "__main__":
    raise SystemExit(main())
