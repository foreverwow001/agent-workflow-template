#!/usr/bin/env python3
"""檔案用途：輸出 workflow-core release note 與 metadata sidecar。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workflow_core_contracts import default_release_artifacts_dir, evaluate_manifest_contract, write_json_file  # noqa: E402
from workflow_core_manifest import manifest_default_path  # noqa: E402


EXIT_PASS = 0
EXIT_WARN = 10
EXIT_FAIL = 20
EXIT_ERROR = 30


def load_metadata(metadata_path: Path | None) -> dict:
    if metadata_path is None:
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def resolve_output_paths(repo_root: Path, release_ref: str, output_path: Path | None) -> tuple[Path | None, Path | None]:
    if output_path is None:
        output_path = default_release_artifacts_dir(repo_root)
    if output_path.suffix.lower() == ".md":
        markdown_path = output_path
    else:
        safe_ref = re.sub(r"[^A-Za-z0-9._-]+", "-", release_ref)
        markdown_path = output_path / f"workflow-core-release-{safe_ref}.md"
    json_path = markdown_path.with_suffix(".json")
    return markdown_path, json_path


def render_release_note(release_ref: str, manifest_path: str, projection_artifact_path: str, smoke_suite_path: str, requires_projection: bool, requires_manual_followup: bool, migration_notes: list[str]) -> str:
    lines = [
        f"# Workflow Core Release {release_ref}",
        "",
        "## Contract Metadata",
        f"- manifest_path: {manifest_path}",
        f"- projection_artifact_path: {projection_artifact_path}",
        f"- portable_smoke_suite_path: {smoke_suite_path}",
        f"- requires_projection: {str(requires_projection).lower()}",
        f"- requires_manual_followup: {str(requires_manual_followup).lower()}",
        "",
        "## Migration Notes",
    ]
    if migration_notes:
        for item in migration_notes:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def run_release_publish_notes(
    repo_root: Path,
    manifest_path: Path,
    release_ref: str,
    metadata_path: Path | None = None,
    output_path: Path | None = None,
) -> dict:
    contract = evaluate_manifest_contract(repo_root, manifest_path)
    metadata = load_metadata(metadata_path)

    if not contract["live_path_contract_ok"] or not contract["projection_artifact_exists"] or not contract["smoke_suite_exists"]:
        return {
            "status": "fail",
            "repo_root": contract["repo_root"],
            "manifest_path": contract["manifest_path"],
            "release_ref": release_ref,
            "output_path": None,
            "requires_projection": bool(contract["projection_artifact_path"]),
            "requires_manual_followup": True,
            "notes": ["manifest contract is incomplete; publish-notes aborted"],
        }

    requires_projection = bool(metadata.get("requires_projection", bool(contract["projection_artifact_path"])))
    requires_manual_followup = bool(metadata.get("requires_manual_followup", False))
    migration_notes = list(metadata.get("migration_notes", []))
    notes = ["generated workflow-core release notes from canonical manifest"]
    status = "warn" if requires_manual_followup else "pass"

    markdown_path, json_path = resolve_output_paths(repo_root, release_ref, output_path)
    if markdown_path is not None:
        content = render_release_note(
            release_ref=release_ref,
            manifest_path=contract["manifest_path"],
            projection_artifact_path=contract["projection_artifact_path"],
            smoke_suite_path=contract["smoke_suite_path"],
            requires_projection=requires_projection,
            requires_manual_followup=requires_manual_followup,
            migration_notes=migration_notes,
        )
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(content, encoding="utf-8")
        if json_path is not None:
            sidecar_payload = {
                "release_ref": release_ref,
                "manifest_path": contract["manifest_path"],
                "requires_projection": requires_projection,
                "requires_manual_followup": requires_manual_followup,
                "migration_notes": migration_notes,
            }
            write_json_file(json_path, sidecar_payload)

    return {
        "status": status,
        "repo_root": contract["repo_root"],
        "manifest_path": contract["manifest_path"],
        "release_ref": release_ref,
        "output_path": str(markdown_path.resolve()) if markdown_path is not None else None,
        "requires_projection": requires_projection,
        "requires_manual_followup": requires_manual_followup,
        "notes": notes,
    }


def format_text_report(result: dict) -> str:
    lines = [
        f"workflow-core release publish-notes: {result['status']}",
        f"repo_root: {result['repo_root']}",
        f"manifest_path: {result['manifest_path']}",
        f"release_ref: {result['release_ref']}",
        f"output_path: {result['output_path']}",
        f"requires_projection: {result['requires_projection']}",
        f"requires_manual_followup: {result['requires_manual_followup']}",
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
    parser.add_argument("--release-ref", required=True, help="release ref")
    parser.add_argument("--manifest", type=Path, default=None, help="workflow-core canonical manifest path")
    parser.add_argument("--metadata", type=Path, default=None, help="可選的 release metadata JSON")
    parser.add_argument("--output", type=Path, default=None, help="輸出 markdown 路徑或目錄")
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest.resolve() if args.manifest else manifest_default_path(repo_root)
    try:
        result = run_release_publish_notes(
            repo_root=repo_root,
            manifest_path=manifest_path,
            release_ref=args.release_ref,
            metadata_path=args.metadata.resolve() if args.metadata else None,
            output_path=args.output.resolve() if args.output else None,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"workflow-core release publish-notes error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(result))
    return exit_code_for_status(result["status"])


if __name__ == "__main__":
    raise SystemExit(main())
