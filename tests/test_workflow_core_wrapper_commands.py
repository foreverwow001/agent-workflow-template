# -*- coding: utf-8 -*-
"""workflow-core 其餘 wrapper commands 的 focused tests。"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_FILE = REPO_ROOT / "core_ownership_manifest.yml"
SCRIPTS_DIR = REPO_ROOT / ".agent" / "runtime" / "scripts"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入模組：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def init_git_repo(repo_root: Path) -> None:
    subprocess.run(["git", "init", "-q", str(repo_root)], check=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.name", "Test User"], check=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.email", "test@example.com"], check=True)


def commit_all(repo_root: Path, message: str) -> str:
    subprocess.run(["git", "-C", str(repo_root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-q", "-m", message], check=True)
    proc = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
    return proc.stdout.strip()


def write_manifest(repo_root: Path) -> None:
    (repo_root / "core_ownership_manifest.yml").write_text(MANIFEST_FILE.read_text(encoding="utf-8"), encoding="utf-8")


def write_runtime_scripts(repo_root: Path) -> None:
    target_dir = repo_root / ".agent" / "runtime" / "scripts"
    target_dir.mkdir(parents=True, exist_ok=True)
    files_to_copy = [
        "workflow_core_manifest.py",
        "workflow_core_contracts.py",
        "workflow_core_obsidian_restricted_mount.py",
        "workflow_core_release_precheck.py",
        "workflow_core_release_create.py",
        "workflow_core_release_publish_notes.py",
        "workflow_core_sync_stage.py",
        "workflow_core_sync_update.py",
        "workflow_core_sync_precheck.py",
        "workflow_core_sync_apply.py",
        "workflow_core_sync_verify.py",
        "workflow_core_projection.py",
    ]
    for filename in files_to_copy:
        (target_dir / filename).write_text((SCRIPTS_DIR / filename).read_text(encoding="utf-8"), encoding="utf-8")
    smoke_dir = target_dir / "portable_smoke"
    smoke_dir.mkdir(parents=True, exist_ok=True)
    (smoke_dir / "workflow_core_smoke.py").write_text(
        (SCRIPTS_DIR / "portable_smoke" / "workflow_core_smoke.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def create_required_live_paths(repo_root: Path, include_index: bool = True) -> None:
    for rel_path in [
        ".agent/workflows",
        ".agent/runtime/scripts/portable_smoke",
        ".agent/roles",
        ".agent/skills/code-reviewer",
        ".agent/skills/doc-generator",
        ".agent/skills/test-runner",
        ".agent/skills/plan-validator",
        ".agent/skills/git-stats-reporter",
        ".agent/skills/skills-evaluator",
        ".agent/skills/github-explorer",
        ".agent/skills/skill-converter",
        ".agent/skills/manifest-updater",
        ".agent/skills/_shared",
        ".agent/templates",
        "project_maintainers/chat/handoff",
        "project_maintainers/chat/archive",
        "project_maintainers/improvement_candidates",
        "doc/plans",
        "doc/logs",
    ]:
        (repo_root / rel_path).mkdir(parents=True, exist_ok=True)
    (repo_root / ".agent" / "workflows" / "AGENT_ENTRY.md").write_text("entry\n", encoding="utf-8")
    (repo_root / ".agent" / "templates" / "handoff_template.md").write_text("template\n", encoding="utf-8")
    (repo_root / ".agent" / "skills" / "_shared" / "__init__.py").write_text("PACKAGED_SKILL_ENTRIES = {}\n", encoding="utf-8")
    (repo_root / "project_maintainers" / "README.md").write_text("# Project Maintainers\n", encoding="utf-8")
    (repo_root / "project_maintainers" / "chat" / "README.md").write_text("# Project Chat\n", encoding="utf-8")
    (repo_root / "project_maintainers" / "chat" / "handoff" / "SESSION-HANDOFF.template.md").write_text("# SESSION-HANDOFF\n", encoding="utf-8")
    (repo_root / "project_maintainers" / "chat" / "archive" / "README.md").write_text("# Archive\n", encoding="utf-8")
    (repo_root / "project_maintainers" / "improvement_candidates" / "README.md").write_text("# Improvement Candidates\n", encoding="utf-8")
    (repo_root / "project_maintainers" / "improvement_candidates" / "IMPROVEMENT-CANDIDATE.template.md").write_text("# IMPROVEMENT-CANDIDATE\n", encoding="utf-8")
    (repo_root / "project_maintainers" / "improvement_candidates" / "PROMOTION-GUIDE.md").write_text("# Promotion Guide\n", encoding="utf-8")
    (repo_root / "doc" / "plans" / "Idx-000_plan.template.md").write_text("# Plan\n", encoding="utf-8")
    (repo_root / "doc" / "logs" / "Idx-000_log.template.md").write_text("# Log\n", encoding="utf-8")
    if include_index:
        (repo_root / "doc" / "implementation_plan_index.md").write_text("# Index\n", encoding="utf-8")


class WorkflowCoreWrapperCommandsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.release_precheck = load_module("test_workflow_core_release_precheck", SCRIPTS_DIR / "workflow_core_release_precheck.py")
        cls.release_create = load_module("test_workflow_core_release_create", SCRIPTS_DIR / "workflow_core_release_create.py")
        cls.release_publish = load_module("test_workflow_core_release_publish_notes", SCRIPTS_DIR / "workflow_core_release_publish_notes.py")
        cls.sync_stage = load_module("test_workflow_core_sync_stage", SCRIPTS_DIR / "workflow_core_sync_stage.py")
        cls.sync_update = load_module("test_workflow_core_sync_update", SCRIPTS_DIR / "workflow_core_sync_update.py")
        cls.sync_apply = load_module("test_workflow_core_sync_apply", SCRIPTS_DIR / "workflow_core_sync_apply.py")
        cls.sync_verify = load_module("test_workflow_core_sync_verify", SCRIPTS_DIR / "workflow_core_sync_verify.py")

    def test_release_precheck_passes_on_complete_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=True)

            result = self.release_precheck.run_release_precheck(repo_root, repo_root / "core_ownership_manifest.yml", "candidate")

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["live_path_contract_ok"])
        self.assertTrue(result["portable_smoke_ok"])
        self.assertTrue(result["skills_mutable_split_ok"])

    def test_release_precheck_fails_when_portable_smoke_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=False)

            result = self.release_precheck.run_release_precheck(repo_root, repo_root / "core_ownership_manifest.yml", "candidate")

        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["portable_smoke_ok"])
        self.assertIn("portable smoke suite failed during release precheck", result["notes"])

    def test_release_create_creates_tag_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=True)
            commit_all(repo_root, "seed")

            output_dir = repo_root / "out"
            result = self.release_create.run_release_create(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                release_ref="core-v20260319-1",
                output_path=output_dir,
            )

            tag_proc = subprocess.run(
                ["git", "-C", str(repo_root), "rev-parse", "--verify", "refs/tags/core-v20260319-1"],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result["status"], "pass")
        self.assertTrue(any(item.startswith("git:refs/tags/core-v20260319-1") for item in result["created_artifacts"]))
        self.assertTrue(any(item.endswith(".metadata.json") for item in result["created_artifacts"]))
        self.assertTrue(tag_proc.stdout.strip())

    def test_release_create_defaults_metadata_to_maintainer_release_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=True)
            commit_all(repo_root, "seed")

            result = self.release_create.run_release_create(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                release_ref="core-v20260319-defaults",
            )

            metadata_path = next(Path(item) for item in result["created_artifacts"] if item.endswith(".metadata.json"))
            self.assertEqual(metadata_path.parent, repo_root / "maintainers" / "release_artifacts")
            self.assertTrue(metadata_path.exists())

    def test_release_create_metadata_does_not_collide_with_publish_notes_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=True)
            commit_all(repo_root, "seed")

            output_dir = repo_root / "out"
            create_result = self.release_create.run_release_create(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                release_ref="core-v20260319-2",
                output_path=output_dir,
            )
            metadata_path = next(Path(item) for item in create_result["created_artifacts"] if item.endswith(".metadata.json"))

            publish_result = self.release_publish.run_release_publish_notes(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                release_ref="core-v20260319-2",
                metadata_path=metadata_path,
                output_path=output_dir,
            )

            notes_json_path = Path(publish_result["output_path"]).with_suffix(".json")
            self.assertTrue(metadata_path.exists())
            self.assertTrue(notes_json_path.exists())
            self.assertNotEqual(metadata_path.name, notes_json_path.name)

    def test_release_publish_notes_writes_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=True)
            metadata_path = repo_root / "metadata.json"
            metadata_path.write_text(
                json.dumps({"requires_projection": True, "requires_manual_followup": True, "migration_notes": ["update overlay index"]}),
                encoding="utf-8",
            )

            result = self.release_publish.run_release_publish_notes(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                release_ref="core-v20260319-1",
                metadata_path=metadata_path,
                output_path=repo_root / "notes",
            )
            output_exists = Path(result["output_path"]).exists()

        self.assertEqual(result["status"], "warn")
        self.assertTrue(result["requires_manual_followup"])
        self.assertTrue(output_exists)

    def test_release_publish_notes_defaults_to_maintainer_release_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=True)

            result = self.release_publish.run_release_publish_notes(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                release_ref="core-v20260319-defaults",
            )

            markdown_path = Path(result["output_path"])
            self.assertEqual(markdown_path.parent, repo_root / "maintainers" / "release_artifacts")
            self.assertTrue(markdown_path.exists())
            self.assertTrue(markdown_path.with_suffix(".json").exists())

    def test_sync_apply_restores_managed_file_from_release_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=True)
            managed_file = repo_root / ".agent" / "workflows" / "example.md"
            managed_file.write_text("v1\n", encoding="utf-8")
            baseline_commit = commit_all(repo_root, "baseline")
            subprocess.run(["git", "-C", str(repo_root), "tag", "core-v20260319-1", baseline_commit], check=True)
            managed_file.write_text("v2\n", encoding="utf-8")
            commit_all(repo_root, "change managed file")

            result = self.sync_apply.run_sync_apply(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                release_ref="core-v20260319-1",
            )

            restored = managed_file.read_text(encoding="utf-8")

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["projection_ran"])
        self.assertIn(".agent/workflows/example.md", result["changed_managed_paths"])
        self.assertEqual(restored, "v1\n")

    def test_sync_apply_materializes_managed_paths_from_staging_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=False)
            commit_all(repo_root, "seed downstream baseline")

            staging_root = repo_root / ".workflow-core" / "staging"
            staged_file = staging_root / ".agent" / "workflows" / "example.md"
            staged_file.parent.mkdir(parents=True, exist_ok=True)
            staged_file.write_text("from staged export\n", encoding="utf-8")

            result = self.sync_apply.run_sync_apply(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                release_ref="core-v20260320-staging",
                staging_root=staging_root,
            )
            verify_result = self.sync_verify.run_sync_verify(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                release_ref="core-v20260320-staging",
                staging_root=staging_root,
            )

            restored = (repo_root / ".agent" / "workflows" / "example.md").read_text(encoding="utf-8")

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["projection_ran"])
        self.assertIn(".agent/workflows/example.md", result["changed_managed_paths"])
        self.assertEqual(verify_result["status"], "pass")
        self.assertEqual(restored, "from staged export\n")

    def test_sync_apply_cli_alias_can_emit_obsidian_restricted_mount_sample(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=True)
            managed_file = repo_root / ".agent" / "workflows" / "example.md"
            managed_file.write_text("v1\n", encoding="utf-8")
            baseline_commit = commit_all(repo_root, "baseline")
            subprocess.run(["git", "-C", str(repo_root), "tag", "core-v20260322-obsidian", baseline_commit], check=True)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "workflow_core_sync_apply.py"),
                    "--repo-root",
                    str(repo_root),
                    "--manifest",
                    str(repo_root / "core_ownership_manifest.yml"),
                    "--release-ref",
                    "core-v20260322-obsidian",
                    "--setup-obsidian-restricted-access",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)

            snippet_path = repo_root / ".devcontainer" / "devcontainer.obsidian-restricted.jsonc"
            guide_path = repo_root / ".devcontainer" / "OBSIDIAN_RESTRICTED_MOUNT.md"
            snippet_exists = snippet_path.exists()
            guide_exists = guide_path.exists()

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["obsidian_mount_sample_generated"])
        self.assertTrue(snippet_exists)
        self.assertTrue(guide_exists)

    def test_sync_apply_allows_staging_tree_only_overlay_warning(self) -> None:
        precheck = {
            "status": "warn",
            "core_divergence_paths": [],
            "overlay_only_paths": [
                ".workflow-core/staging/core-v20260320-2/.agent/workflows/dev-team.md",
                ".workflow-core/staging/core-v20260320-2/workflow-core-stage-metadata.json",
            ],
            "state_only_paths": [],
            "unclassified_paths": [],
        }

        allowed = self.sync_apply.precheck_allows_staging_tree_only_warning(
            precheck,
            ".workflow-core/staging/core-v20260320-2",
        )

        self.assertTrue(allowed)

    def test_sync_stage_fetches_remote_release_into_staging_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            upstream_root = root / "upstream"
            downstream_root = root / "downstream"

            init_git_repo(upstream_root)
            write_manifest(upstream_root)
            write_runtime_scripts(upstream_root)
            create_required_live_paths(upstream_root, include_index=True)
            (upstream_root / ".agent" / "workflows" / "example.md").write_text("remote staged workflow\n", encoding="utf-8")
            baseline_commit = commit_all(upstream_root, "seed upstream release")
            subprocess.run(["git", "-C", str(upstream_root), "tag", "core-v20260320-remote", baseline_commit], check=True)

            init_git_repo(downstream_root)
            write_manifest(downstream_root)
            write_runtime_scripts(downstream_root)
            create_required_live_paths(downstream_root, include_index=False)
            commit_all(downstream_root, "seed downstream baseline")
            subprocess.run(["git", "-C", str(downstream_root), "remote", "add", "workflow-core-upstream", str(upstream_root)], check=True)

            stage_result = self.sync_stage.run_sync_stage(
                repo_root=downstream_root,
                release_ref="core-v20260320-remote",
                source_remote="workflow-core-upstream",
            )
            staging_root = Path(stage_result["staging_root"])
            apply_result = self.sync_apply.run_sync_apply(
                repo_root=downstream_root,
                manifest_path=downstream_root / "core_ownership_manifest.yml",
                release_ref="core-v20260320-remote",
                staging_root=staging_root,
            )
            verify_result = self.sync_verify.run_sync_verify(
                repo_root=downstream_root,
                manifest_path=downstream_root / "core_ownership_manifest.yml",
                release_ref="core-v20260320-remote",
                staging_root=staging_root,
            )

            staged_metadata = json.loads((staging_root / "workflow-core-stage-metadata.json").read_text(encoding="utf-8"))
            restored = (downstream_root / ".agent" / "workflows" / "example.md").read_text(encoding="utf-8")

        self.assertEqual(stage_result["status"], "pass")
        self.assertEqual(stage_result["source_remote"], "workflow-core-upstream")
        self.assertTrue(stage_result["selected_path_count"] > 0)
        self.assertEqual(staged_metadata["release_ref"], "core-v20260320-remote")
        self.assertEqual(apply_result["status"], "pass")
        self.assertEqual(verify_result["status"], "pass")
        self.assertEqual(restored, "remote staged workflow\n")

    def test_sync_update_runs_stage_apply_verify_with_single_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            upstream_root = root / "upstream"
            downstream_root = root / "downstream"

            init_git_repo(upstream_root)
            write_manifest(upstream_root)
            write_runtime_scripts(upstream_root)
            create_required_live_paths(upstream_root, include_index=True)
            (upstream_root / ".agent" / "workflows" / "example.md").write_text("remote one-click workflow\n", encoding="utf-8")
            baseline_commit = commit_all(upstream_root, "seed upstream one-click release")
            subprocess.run(["git", "-C", str(upstream_root), "tag", "core-v20260322-one-click", baseline_commit], check=True)

            init_git_repo(downstream_root)
            write_manifest(downstream_root)
            write_runtime_scripts(downstream_root)
            create_required_live_paths(downstream_root, include_index=False)
            commit_all(downstream_root, "seed downstream one-click baseline")
            subprocess.run(["git", "-C", str(downstream_root), "remote", "add", "workflow-core-upstream", str(upstream_root)], check=True)

            first_completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "workflow_core_sync_update.py"),
                    "--repo-root",
                    str(downstream_root),
                    "--manifest",
                    str(downstream_root / "core_ownership_manifest.yml"),
                    "--release-ref",
                    "core-v20260322-one-click",
                    "--source-remote",
                    "workflow-core-upstream",
                    "--setup-obsidian-restricted-access",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            first_result = json.loads(first_completed.stdout)
            first_stage_root = Path(first_result["staging_root"])
            (first_stage_root / "stale.txt").write_text("stale\n", encoding="utf-8")
            commit_all(downstream_root, "record one-click sync result")

            second_completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "workflow_core_sync_update.py"),
                    "--repo-root",
                    str(downstream_root),
                    "--manifest",
                    str(downstream_root / "core_ownership_manifest.yml"),
                    "--release-ref",
                    "core-v20260322-one-click",
                    "--source-remote",
                    "workflow-core-upstream",
                    "--setup-obsidian-restricted-access",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            second_result = json.loads(second_completed.stdout)

            restored = (downstream_root / ".agent" / "workflows" / "example.md").read_text(encoding="utf-8")
            snippet_exists = (downstream_root / ".devcontainer" / "devcontainer.obsidian-restricted.jsonc").exists()
            snippet_text = (downstream_root / ".devcontainer" / "devcontainer.obsidian-restricted.jsonc").read_text(encoding="utf-8")
            stale_exists = (Path(second_result["staging_root"]) / "stale.txt").exists()

        self.assertEqual(first_result["status"], "pass")
        self.assertEqual(second_result["status"], "pass")
        self.assertEqual(second_result["stage_result"]["status"], "pass")
        self.assertEqual(second_result["apply_result"]["status"], "pass")
        self.assertEqual(second_result["verify_result"]["status"], "pass")
        self.assertTrue(second_result["replaced_existing_staging_root"])
        self.assertTrue(second_result["obsidian_mount_sample_generated"])
        self.assertEqual(restored, "remote one-click workflow\n")
        self.assertTrue(snippet_exists)
        self.assertIn("obsidian-knowledge/10-inbox/pending-review-notes", snippet_text)
        self.assertFalse(stale_exists)

    def test_sync_update_cli_errors_when_custom_staging_root_is_not_empty_without_replace_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=True)
            managed_file = repo_root / ".agent" / "workflows" / "example.md"
            managed_file.write_text("v1\n", encoding="utf-8")
            baseline_commit = commit_all(repo_root, "baseline")
            subprocess.run(["git", "-C", str(repo_root), "tag", "core-v20260322-error", baseline_commit], check=True)

            staging_root = repo_root / "custom-staging"
            staging_root.mkdir(parents=True, exist_ok=True)
            (staging_root / "keep.txt").write_text("keep\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "workflow_core_sync_update.py"),
                    "--repo-root",
                    str(repo_root),
                    "--manifest",
                    str(repo_root / "core_ownership_manifest.yml"),
                    "--release-ref",
                    "core-v20260322-error",
                    "--staging-root",
                    str(staging_root),
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            error_payload = json.loads(completed.stderr)

        self.assertEqual(completed.returncode, self.sync_update.EXIT_ERROR)
        self.assertIn("staging root is not empty", error_payload["error"])

    def test_sync_update_reports_sync_apply_failure_when_managed_path_diverges(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=True)
            managed_file = repo_root / ".agent" / "workflows" / "example.md"
            managed_file.write_text("v1\n", encoding="utf-8")
            baseline_commit = commit_all(repo_root, "baseline")
            subprocess.run(["git", "-C", str(repo_root), "tag", "core-v20260322-diverge", baseline_commit], check=True)
            managed_file.write_text("local divergent change\n", encoding="utf-8")

            result = self.sync_update.run_sync_update(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                release_ref="core-v20260322-diverge",
            )

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["failed_stage"], "sync-apply")
        self.assertEqual(result["stage_result"]["status"], "pass")
        self.assertEqual(result["apply_result"]["status"], "fail")
        self.assertIsNone(result["verify_result"])

    def test_sync_verify_passes_with_manifest_backed_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=True)
            commit_all(repo_root, "seed")

            result = self.sync_verify.run_sync_verify(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                release_ref="core-v20260319-verify",
            )

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["live_paths_ok"])
        self.assertTrue(result["portable_smoke_ok"])

    def test_sync_verify_accepts_post_apply_managed_paths_matching_release_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_required_live_paths(repo_root, include_index=True)
            managed_file = repo_root / ".agent" / "workflows" / "example.md"
            managed_file.write_text("v1\n", encoding="utf-8")
            baseline_commit = commit_all(repo_root, "baseline")
            subprocess.run(["git", "-C", str(repo_root), "tag", "core-v20260319-verify", baseline_commit], check=True)
            managed_file.write_text("v2\n", encoding="utf-8")
            commit_all(repo_root, "change managed file")

            apply_result = self.sync_apply.run_sync_apply(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                release_ref="core-v20260319-verify",
            )
            verify_result = self.sync_verify.run_sync_verify(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                release_ref="core-v20260319-verify",
            )

        self.assertEqual(apply_result["status"], "pass")
        self.assertEqual(verify_result["status"], "pass")
        self.assertTrue(verify_result["preflight_ok"])
        self.assertTrue(any("match the target requested release ref" in note for note in verify_result["notes"]))
