#!/usr/bin/env python3
"""檔案用途：在 workflow-core 發版前檢查 manifest、live path 與 ownership boundary。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workflow_core_contracts import evaluate_manifest_contract  # noqa: E402
from workflow_core_manifest import manifest_default_path  # noqa: E402


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


def run_release_precheck(repo_root: Path, manifest_path: Path, release_candidate_ref: str | None = None) -> dict:
    contract = evaluate_manifest_contract(repo_root, manifest_path)
    notes: list[str] = []
    failures: list[str] = []
    portable_smoke_ok = False
    portable_smoke_notes: list[str] = []

    if not contract["manifest_path_ok"]:
        failures.append("manifest-path-mismatch")
        notes.append("manifest path does not match automation_contract.canonical_manifest_path")
    if not contract["live_path_contract_ok"]:
        failures.append("missing-live-paths")
        notes.append("required live path anchors are missing")
    if not contract["projection_artifact_exists"]:
        failures.append("missing-projection-artifact")
        notes.append("projection/bootstrap artifact path is missing")
    if not contract["smoke_suite_exists"]:
        failures.append("missing-portable-smoke")
        notes.append("portable smoke suite path is missing")
    else:
        smoke_module = load_module(repo_root / contract["smoke_suite_path"], "workflow_core_release_smoke_runtime")
        smoke_result = smoke_module.run_portable_smoke(repo_root=repo_root, manifest_path=manifest_path)
        portable_smoke_ok = smoke_result["status"] == "pass"
        portable_smoke_notes = list(smoke_result.get("notes", []))
        if not portable_smoke_ok:
            failures.append("portable-smoke-failed")
            notes.append("portable smoke suite failed during release precheck")
    if not contract["skills_mutable_split_ok"]:
        failures.append("skills-split-violation")
        notes.append("managed path contract overlaps with mutable skill split targets")

    status = "fail" if failures else "pass"
    if not notes:
        notes.append("release candidate satisfies manifest ownership and live path contract")
    notes.extend(item for item in portable_smoke_notes if item not in notes)

    return {
        "status": status,
        "repo_root": contract["repo_root"],
        "manifest_path": contract["manifest_path"],
        "release_candidate_ref": release_candidate_ref,
        "managed_path_violations": contract["managed_path_violations"],
        "live_path_contract_ok": contract["live_path_contract_ok"],
        "portable_smoke_ok": portable_smoke_ok,
        "skills_mutable_split_ok": contract["skills_mutable_split_ok"],
        "missing_required_live_paths": contract["required_live_paths"]["missing"],
        "projection_artifact_exists": contract["projection_artifact_exists"],
        "smoke_suite_exists": contract["smoke_suite_exists"],
        "notes": notes,
    }


def format_text_report(result: dict) -> str:
    lines = [
        f"workflow-core release precheck: {result['status']}",
        f"repo_root: {result['repo_root']}",
        f"manifest_path: {result['manifest_path']}",
        f"release_candidate_ref: {result['release_candidate_ref']}",
        f"live_path_contract_ok: {result['live_path_contract_ok']}",
        f"portable_smoke_ok: {result['portable_smoke_ok']}",
        f"skills_mutable_split_ok: {result['skills_mutable_split_ok']}",
    ]
    if result["managed_path_violations"]:
        lines.append("managed_path_violations:")
        for item in result["managed_path_violations"]:
            lines.append(f"  - {item}")
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
    parser.add_argument("--release-candidate-ref", default=None, help="可選的 release candidate ref")
    parser.add_argument("--manifest", type=Path, default=None, help="workflow-core canonical manifest path")
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest.resolve() if args.manifest else manifest_default_path(repo_root)
    try:
        result = run_release_precheck(repo_root=repo_root, manifest_path=manifest_path, release_candidate_ref=args.release_candidate_ref)
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"workflow-core release precheck error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(result))
    return exit_code_for_status(result["status"])


if __name__ == "__main__":
    raise SystemExit(main())
