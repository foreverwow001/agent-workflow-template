#!/usr/bin/env python3
"""Shared workflow-core contract and git helpers for wrapper commands."""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from workflow_core_manifest import (
    get_canonical_manifest_path,
    get_managed_patterns,
    get_overlay_patterns,
    get_projection_artifact_path,
    get_required_live_paths,
    get_smoke_suite_path,
    get_state_patterns,
    load_manifest,
    normalize_path,
    path_matches_pattern,
    pattern_anchor,
)


def git_run(repo_root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    if shutil.which("git") is None:
        raise RuntimeError("git command not found on PATH")
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or f"git {' '.join(args)} failed"
        raise RuntimeError(message)
    return proc


def ref_exists(repo_root: Path, ref: str) -> bool:
    proc = git_run(repo_root, ["rev-parse", "--verify", "--quiet", ref], check=False)
    return proc.returncode == 0


def resolve_ref(repo_root: Path, ref: str | None) -> str | None:
    if ref is None:
        target = "HEAD"
    else:
        target = ref
    proc = git_run(repo_root, ["rev-parse", "--verify", "--quiet", target], check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def list_files_at_ref(repo_root: Path, ref: str) -> list[str]:
    proc = git_run(repo_root, ["ls-tree", "-r", "--name-only", ref])
    return [normalize_path(line) for line in proc.stdout.splitlines() if line.strip()]


def checkout_paths_from_ref(repo_root: Path, ref: str, paths: list[str]) -> None:
    if not paths:
        return
    git_run(repo_root, ["checkout", ref, "--", *paths])


def worktree_path_matches_ref(repo_root: Path, ref: str, path: str) -> bool:
    proc = git_run(repo_root, ["diff", "--quiet", ref, "--", path], check=False)
    return proc.returncode == 0


def run_shell_command(repo_root: Path, command: str) -> tuple[bool, str]:
    proc = subprocess.run(
        shlex.split(command),
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    output = (proc.stdout or proc.stderr or "").strip()
    return proc.returncode == 0, output


def compute_required_live_path_status(repo_root: Path, manifest: dict[str, Any], extra_paths: list[str] | None = None) -> dict[str, list[str]]:
    required = list(get_required_live_paths(manifest))
    for path in extra_paths or []:
        normalized = normalize_path(path)
        if normalized and normalized not in required:
            required.append(normalized)

    existing: list[str] = []
    missing: list[str] = []
    for pattern in required:
        anchor = pattern_anchor(pattern)
        if anchor and (repo_root / anchor).exists():
            existing.append(pattern)
        else:
            missing.append(pattern)
    return {"existing": existing, "missing": missing}


def patterns_overlap(left: str, right: str) -> bool:
    left_anchor = pattern_anchor(left)
    right_anchor = pattern_anchor(right)
    if not left_anchor or not right_anchor:
        return False
    return (
        path_matches_pattern(left_anchor, right)
        or path_matches_pattern(right_anchor, left)
        or left_anchor.startswith(right_anchor + "/")
        or right_anchor.startswith(left_anchor + "/")
        or left_anchor == right_anchor
    )


def collect_split_targets(manifest: dict[str, Any]) -> list[str]:
    targets: list[str] = []
    for item in manifest.get("split_required", []):
        if not isinstance(item, dict):
            continue
        for part in str(item.get("recommended_target", "")).split("+"):
            normalized = normalize_path(part)
            if normalized and normalized not in targets:
                targets.append(normalized)
    return targets


def collect_review_required_skill_dirs(manifest: dict[str, Any]) -> list[str]:
    skill_ownership = manifest.get("skill_ownership", {})
    values = skill_ownership.get("review_required_package_dirs", [])
    return [normalize_path(str(item)) for item in values if normalize_path(str(item))]


def collect_local_install_targets(manifest: dict[str, Any]) -> list[str]:
    skill_ownership = manifest.get("skill_ownership", {})
    local_target = normalize_path(str(skill_ownership.get("local_install_target", "")))
    return [local_target] if local_target else []


def collect_managed_path_violations(manifest: dict[str, Any]) -> list[str]:
    managed_patterns = get_managed_patterns(manifest)
    forbidden_patterns = [
        *get_overlay_patterns(manifest),
        *collect_split_targets(manifest),
        *collect_review_required_skill_dirs(manifest),
        *collect_local_install_targets(manifest),
    ]

    violations: list[str] = []
    for managed_pattern in managed_patterns:
        for forbidden_pattern in forbidden_patterns:
            if patterns_overlap(managed_pattern, forbidden_pattern):
                violations.append(f"{managed_pattern} overlaps {forbidden_pattern}")
    return sorted(set(violations))


def evaluate_manifest_contract(repo_root: Path, manifest_path: Path, extra_required_live_paths: list[str] | None = None) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    live_paths = compute_required_live_path_status(repo_root, manifest, extra_paths=extra_required_live_paths)
    projection_artifact_path = get_projection_artifact_path(manifest)
    smoke_suite_path = get_smoke_suite_path(manifest)
    canonical_manifest_path = get_canonical_manifest_path(manifest)
    managed_path_violations = collect_managed_path_violations(manifest)

    projection_artifact_exists = bool(projection_artifact_path) and (repo_root / projection_artifact_path).exists()
    smoke_suite_exists = bool(smoke_suite_path) and (repo_root / smoke_suite_path).exists()
    agent_entry_present = (repo_root / ".agent" / "workflows" / "AGENT_ENTRY.md").exists()
    skills_mutable_split_ok = not managed_path_violations
    manifest_path_ok = normalize_path(str(manifest_path.relative_to(repo_root))) == normalize_path(canonical_manifest_path)

    return {
        "manifest": manifest,
        "repo_root": str(repo_root.resolve()),
        "manifest_path": str(manifest_path.resolve()),
        "canonical_manifest_path": canonical_manifest_path,
        "manifest_path_ok": manifest_path_ok,
        "required_live_paths": live_paths,
        "live_path_contract_ok": not live_paths["missing"],
        "projection_artifact_path": projection_artifact_path,
        "projection_artifact_exists": projection_artifact_exists,
        "smoke_suite_path": smoke_suite_path,
        "smoke_suite_exists": smoke_suite_exists,
        "agent_entry_present": agent_entry_present,
        "managed_patterns": get_managed_patterns(manifest),
        "overlay_patterns": get_overlay_patterns(manifest),
        "state_patterns": get_state_patterns(manifest),
        "managed_path_violations": managed_path_violations,
        "skills_mutable_split_ok": skills_mutable_split_ok,
    }


def write_json_file(target_path: Path, payload: dict[str, Any]) -> str:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(target_path.resolve())


def default_release_artifacts_dir(repo_root: Path) -> Path:
    return repo_root / "maintainers" / "release_artifacts"
