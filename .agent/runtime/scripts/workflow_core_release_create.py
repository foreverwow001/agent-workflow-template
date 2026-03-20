#!/usr/bin/env python3
"""檔案用途：建立 workflow-core 可供 downstream 引用的 release ref 與 metadata。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workflow_core_contracts import default_release_artifacts_dir, git_run, ref_exists, resolve_ref, write_json_file  # noqa: E402
from workflow_core_manifest import manifest_default_path  # noqa: E402
from workflow_core_release_precheck import run_release_precheck  # noqa: E402


EXIT_PASS = 0
EXIT_WARN = 10
EXIT_FAIL = 20
EXIT_ERROR = 30


def default_output_path(repo_root: Path, release_ref: str, output: Path | None) -> Path | None:
    if output is None:
        output = default_release_artifacts_dir(repo_root)
    if output.suffix.lower() == ".json":
        return output
    safe_ref = re.sub(r"[^A-Za-z0-9._-]+", "-", release_ref)
    return output / f"workflow-core-release-{safe_ref}.metadata.json"


def run_release_create(
    repo_root: Path,
    manifest_path: Path,
    release_ref: str,
    source_ref: str | None = None,
    output_path: Path | None = None,
) -> dict:
    precheck = run_release_precheck(repo_root=repo_root, manifest_path=manifest_path, release_candidate_ref=release_ref)
    if precheck["status"] != "pass":
        return {
            "status": "fail",
            "repo_root": precheck["repo_root"],
            "manifest_path": precheck["manifest_path"],
            "release_ref": release_ref,
            "source_ref": source_ref,
            "created_artifacts": [],
            "notes": ["release precheck failed; release ref was not created", *precheck["notes"]],
        }

    resolved_source_ref = resolve_ref(repo_root, source_ref)
    if resolved_source_ref is None:
        raise RuntimeError(f"source ref does not resolve: {source_ref or 'HEAD'}")
    if ref_exists(repo_root, f"refs/tags/{release_ref}"):
        return {
            "status": "fail",
            "repo_root": str(repo_root.resolve()),
            "manifest_path": str(manifest_path.resolve()),
            "release_ref": release_ref,
            "source_ref": resolved_source_ref,
            "created_artifacts": [],
            "notes": ["release tag already exists"],
        }

    git_run(repo_root, ["tag", release_ref, resolved_source_ref])
    created_artifacts = [f"git:refs/tags/{release_ref}"]

    metadata = {
        "release_ref": release_ref,
        "source_ref": resolved_source_ref,
        "manifest_path": str(manifest_path.resolve()),
        "requires_projection": True,
        "requires_manual_followup": False,
        "breaking_contracts": [],
        "migration_notes": [],
    }

    resolved_output_path = default_output_path(repo_root, release_ref, output_path)
    if resolved_output_path is not None:
        created_artifacts.append(write_json_file(resolved_output_path, metadata))

    return {
        "status": "pass",
        "repo_root": str(repo_root.resolve()),
        "manifest_path": str(manifest_path.resolve()),
        "release_ref": release_ref,
        "source_ref": resolved_source_ref,
        "created_artifacts": created_artifacts,
        "notes": ["created workflow-core release tag and metadata"],
    }


def format_text_report(result: dict) -> str:
    lines = [
        f"workflow-core release create: {result['status']}",
        f"repo_root: {result['repo_root']}",
        f"manifest_path: {result['manifest_path']}",
        f"release_ref: {result['release_ref']}",
        f"source_ref: {result['source_ref']}",
    ]
    if result["created_artifacts"]:
        lines.append("created_artifacts:")
        for item in result["created_artifacts"]:
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
    parser.add_argument("--release-ref", required=True, help="要建立的 release ref/tag")
    parser.add_argument("--manifest", type=Path, default=None, help="workflow-core canonical manifest path")
    parser.add_argument("--source-ref", default=None, help="來源 ref，預設為 HEAD")
    parser.add_argument("--output", type=Path, default=None, help="metadata JSON 輸出路徑或目錄")
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest.resolve() if args.manifest else manifest_default_path(repo_root)
    try:
        result = run_release_create(
            repo_root=repo_root,
            manifest_path=manifest_path,
            release_ref=args.release_ref,
            source_ref=args.source_ref,
            output_path=args.output.resolve() if args.output else None,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"workflow-core release create error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(result))
    return exit_code_for_status(result["status"])


if __name__ == "__main__":
    raise SystemExit(main())
