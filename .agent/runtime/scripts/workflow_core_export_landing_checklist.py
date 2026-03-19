#!/usr/bin/env python3
"""檔案用途：輸出 workflow-core export profile 的 landing checklist，區分 source ref、working tree 與 deferred 範圍。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workflow_core_contracts import write_json_file  # noqa: E402
from workflow_core_export_materialize import analyze_export_profile, exit_code_for_status  # noqa: E402
from workflow_core_manifest import manifest_default_path  # noqa: E402


EXIT_PASS = 0
EXIT_WARN = 10
EXIT_FAIL = 20
EXIT_ERROR = 30


def resolve_output_paths(profile_name: str, output_path: Path | None) -> tuple[Path | None, Path | None]:
    if output_path is None:
        return None, None
    if output_path.suffix.lower() == ".md":
        markdown_path = output_path
    else:
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", profile_name)
        markdown_path = output_path / f"workflow-core-export-landing-{safe_name}.md"
    json_path = markdown_path.with_suffix(".json")
    return markdown_path, json_path


def render_pattern_section(title: str, marker: str, items: list[dict[str, object]], action: str) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.extend(["- None", ""])
        return lines

    for item in items:
        pattern = str(item["pattern"])
        matches = list(item.get("worktree_matches") or item.get("source_ref_matches") or [])
        lines.append(f"- [{marker}] {pattern}")
        lines.append(f"  Action: {action}")
        if matches:
            lines.append(f"  Matched paths: {', '.join(matches)}")
        else:
            lines.append("  Matched paths: none")
    lines.append("")
    return lines


def render_deferred_section(items: list[dict[str, object]]) -> list[str]:
    lines = ["## Deferred By Design", ""]
    if not items:
        lines.extend(["- None", ""])
        return lines
    for item in items:
        lines.append(f"- [ ] {item.get('path', '')}")
        lines.append(f"  Reason: {item.get('reason', '')}")
    lines.append("")
    return lines


def render_violation_section(items: list[str]) -> list[str]:
    lines = ["## Contract Violations", ""]
    if not items:
        lines.extend(["- None", ""])
        return lines
    for item in items:
        lines.append(f"- [ ] {item}")
    lines.append("")
    return lines


def render_landing_checklist(result: dict) -> str:
    ready_items = [item for item in result["include_pattern_statuses"] if item["status"] == "ready"]
    worktree_only_items = [item for item in result["include_pattern_statuses"] if item["status"] == "worktree-only"]
    missing_items = [item for item in result["include_pattern_statuses"] if item["status"] == "missing"]

    lines = [
        f"# Workflow Core Export Landing Checklist: {result['profile_name']}",
        "",
        "## Summary",
        f"- status: {result['status']}",
        f"- source_ref: {result['source_ref']}",
        f"- profile_status: {result['profile_status']}",
        f"- selected_path_count_at_source_ref: {result['selected_path_count']}",
        f"- ready_include_patterns: {len(result['ready_include_patterns'])}",
        f"- worktree_only_include_patterns: {len(result['worktree_only_include_patterns'])}",
        f"- missing_include_patterns: {len(result['missing_include_patterns'])}",
        "",
        "## Purpose",
        result["profile_purpose"],
        "",
    ]
    lines.extend(render_pattern_section("Ready In Source Ref", "x", ready_items, "No action required for this release candidate."))
    lines.extend(render_pattern_section("Present Only In Working Tree", " ", worktree_only_items, "Land these paths into the next release candidate before export."))
    lines.extend(render_pattern_section("Still Missing", " ", missing_items, "Create or re-scope these paths before treating the profile as release-ready."))
    lines.extend(render_deferred_section(result["deferred_paths"]))
    lines.extend(render_violation_section(result["profile_contract_violations"]))
    lines.extend(["## Notes", ""])
    for note in result["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def run_export_landing_checklist(
    repo_root: Path,
    manifest_path: Path,
    profile_name: str | None = None,
    source_ref: str | None = None,
    output_path: Path | None = None,
) -> dict:
    result = analyze_export_profile(
        repo_root=repo_root,
        manifest_path=manifest_path,
        profile_name=profile_name,
        source_ref=source_ref,
    )

    markdown_path, json_path = resolve_output_paths(str(result["profile_name"]), output_path)
    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_landing_checklist(result), encoding="utf-8")
    if json_path is not None:
        write_json_file(json_path, result)

    return {
        **result,
        "output_path": str(markdown_path.resolve()) if markdown_path is not None else None,
        "json_output_path": str(json_path.resolve()) if json_path is not None else None,
    }


def format_text_report(result: dict) -> str:
    lines = [
        f"workflow-core export landing-checklist: {result['status']}",
        f"repo_root: {result['repo_root']}",
        f"manifest_path: {result['manifest_path']}",
        f"profile_name: {result['profile_name']}",
        f"source_ref: {result['source_ref']}",
        f"ready_include_patterns: {len(result['ready_include_patterns'])}",
        f"worktree_only_include_patterns: {len(result['worktree_only_include_patterns'])}",
        f"missing_include_patterns: {len(result['missing_include_patterns'])}",
        f"output_path: {result['output_path']}",
    ]
    if result["worktree_only_include_patterns"]:
        lines.append("worktree_only_include_patterns:")
        for item in result["worktree_only_include_patterns"]:
            lines.append(f"  - {item}")
    if result["missing_include_patterns"]:
        lines.append("missing_include_patterns:")
        for item in result["missing_include_patterns"]:
            lines.append(f"  - {item}")
    if result["profile_contract_violations"]:
        lines.append("profile_contract_violations:")
        for item in result["profile_contract_violations"]:
            lines.append(f"  - {item}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repo 根目錄（預設：目前目錄）")
    parser.add_argument("--manifest", type=Path, default=None, help="workflow-core canonical manifest path")
    parser.add_argument("--profile", default=None, help="manifest export profile name（預設：manifest 中 status=active 的 profile）")
    parser.add_argument("--source-ref", default=None, help="分析的來源 ref，預設為 HEAD")
    parser.add_argument("--output", type=Path, default=None, help="輸出 markdown 路徑或目錄")
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest.resolve() if args.manifest else manifest_default_path(repo_root)
    try:
        result = run_export_landing_checklist(
            repo_root=repo_root,
            manifest_path=manifest_path,
            profile_name=args.profile,
            source_ref=args.source_ref,
            output_path=args.output.resolve() if args.output else None,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"workflow-core export landing-checklist error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(result))
    return exit_code_for_status(str(result["status"]))


if __name__ == "__main__":
    raise SystemExit(main())
