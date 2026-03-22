# -*- coding: utf-8 -*-
"""focused tests for workflow-core export profile materialization."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
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


def commit_all(repo_root: Path, message: str) -> None:
    subprocess.run(["git", "-C", str(repo_root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-q", "-m", message], check=True)


def write_runtime_scripts(repo_root: Path) -> None:
    target_dir = repo_root / ".agent" / "runtime" / "scripts"
    target_dir.mkdir(parents=True, exist_ok=True)
    for filename in [
        "workflow_core_manifest.py",
        "workflow_core_contracts.py",
        "workflow_core_export_materialize.py",
        "workflow_core_obsidian_restricted_mount.py",
        "workflow_core_sync_update.py",
    ]:
        (target_dir / filename).write_text((SCRIPTS_DIR / filename).read_text(encoding="utf-8"), encoding="utf-8")


def write_manifest(
    repo_root: Path,
    include_unmanaged_pattern: bool = False,
    extra_profile_includes: list[str] | None = None,
    extra_managed_patterns: list[str] | None = None,
    split_required: list[dict[str, str]] | None = None,
) -> None:
    profile_includes = [
        "core_ownership_manifest.yml",
        ".agent/workflows/**",
        ".agent/runtime/**",
        ".agent/roles/coordinator.md",
        ".agent/skills/code-reviewer/**",
        ".agent/skills/refactor/**",
    ]
    profile_includes.extend(extra_profile_includes or [])
    if include_unmanaged_pattern:
        profile_includes.append("README.md")

    managed_patterns = [
        "core_ownership_manifest.yml",
        ".agent/workflows/**",
        ".agent/runtime/**",
        ".agent/roles/coordinator.md",
        ".agent/skills/code-reviewer/**",
        ".agent/skills/refactor/**",
    ]
    managed_patterns.extend(extra_managed_patterns or [])

    lines = [
        'manifest_version: "1.0"',
        'root_path_contract:',
        '  required_live_paths: []',
        'skill_ownership:',
        '  review_required_package_dirs: []',
        '  local_install_target: ".agent/skills_local/**"',
        'projection_bootstrap:',
        '  artifact_path: ".agent/runtime/scripts/workflow_core_projection.py"',
        'verification_strategy:',
        '  portable_smoke_suite_path: ".agent/runtime/scripts/portable_smoke/workflow_core_smoke.py"',
        'automation_contract:',
        '  canonical_manifest_path: "./core_ownership_manifest.yml"',
        'managed_paths:',
    ]
    lines.extend(f'  - path: "{pattern}"' for pattern in managed_patterns)
    lines.extend(
        [
            'excluded_paths: []',
            'split_required: []',
            'export_profiles:',
            '  - name: "curated-core-v1"',
            '    status: "active"',
            '    purpose: "test profile"',
            '    includes:',
        ]
    )
    lines.extend(f'      - "{pattern}"' for pattern in profile_includes)
    lines.extend(
        [
            '    excludes:',
            '      - ".agent/skills/_shared/**"',
            '      - ".agent/skills/github-explorer/**"',
            '    deferred_paths:',
            '      - path: ".agent/skills/github-explorer/**"',
            '        reason: "writes mutable state"',
            '    notes:',
            '      - "test export profile"',
        ]
    )

    if split_required:
        lines.append('split_required:')
        for item in split_required:
            lines.append(f'  - path: "{item["path"]}"')
            lines.append(f'    recommended_target: "{item["recommended_target"]}"')
    else:
        lines.append('split_required: []')

    manifest = "\n".join(lines) + "\n"
    (repo_root / "core_ownership_manifest.yml").write_text(manifest, encoding="utf-8")


def create_sample_tree(repo_root: Path) -> None:
    (repo_root / ".agent" / "workflows").mkdir(parents=True, exist_ok=True)
    (repo_root / ".agent" / "roles").mkdir(parents=True, exist_ok=True)
    (repo_root / ".agent" / "skills" / "code-reviewer").mkdir(parents=True, exist_ok=True)
    (repo_root / ".agent" / "skills" / "refactor").mkdir(parents=True, exist_ok=True)
    (repo_root / ".agent" / "skills" / "github-explorer").mkdir(parents=True, exist_ok=True)
    (repo_root / ".agent" / "skills" / "_shared").mkdir(parents=True, exist_ok=True)
    (repo_root / ".agent" / "workflows" / "dev-team.md").write_text("workflow\n", encoding="utf-8")
    (repo_root / ".agent" / "roles" / "coordinator.md").write_text("role\n", encoding="utf-8")
    (repo_root / ".agent" / "skills" / "code-reviewer" / "SKILL.md").write_text("code review\n", encoding="utf-8")
    (repo_root / ".agent" / "skills" / "refactor" / "SKILL.md").write_text("refactor\n", encoding="utf-8")
    (repo_root / ".agent" / "skills" / "github-explorer" / "SKILL.md").write_text("explorer\n", encoding="utf-8")
    (repo_root / ".agent" / "skills" / "_shared" / "__init__.py").write_text("shared\n", encoding="utf-8")


class WorkflowCoreExportMaterializeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.export_materialize = load_module(
            "test_workflow_core_export_materialize_module",
            SCRIPTS_DIR / "workflow_core_export_materialize.py",
        )

    def test_materialize_exports_curated_profile_and_excludes_deferred_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            write_runtime_scripts(repo_root)
            create_sample_tree(repo_root)
            commit_all(repo_root, "seed export tree")

            output_dir = repo_root / "exported"
            result = self.export_materialize.run_export_materialize(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                output_dir=output_dir,
            )
            metadata = json.loads((output_dir / "workflow-core-export-curated-core-v1.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "pass")
            self.assertTrue((output_dir / ".agent" / "workflows" / "dev-team.md").exists())
            self.assertTrue((output_dir / ".agent" / "runtime" / "scripts" / "workflow_core_obsidian_restricted_mount.py").exists())
            self.assertTrue((output_dir / ".agent" / "runtime" / "scripts" / "workflow_core_sync_update.py").exists())
            self.assertTrue((output_dir / ".agent" / "skills" / "code-reviewer" / "SKILL.md").exists())
            self.assertTrue((output_dir / ".agent" / "skills" / "refactor" / "SKILL.md").exists())
            self.assertFalse((output_dir / ".agent" / "skills" / "github-explorer" / "SKILL.md").exists())
            self.assertFalse((output_dir / ".agent" / "skills" / "_shared" / "__init__.py").exists())
            self.assertEqual(metadata["selected_path_count"], result["selected_path_count"])
            self.assertTrue(any(item["path"] == ".agent/skills/github-explorer/**" for item in metadata["deferred_paths"]))

    def test_materialize_warns_when_include_pattern_has_no_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(
                repo_root,
                extra_profile_includes=[".agent/skills/python-expert/**"],
                extra_managed_patterns=[".agent/skills/python-expert/**"],
            )
            write_runtime_scripts(repo_root)
            create_sample_tree(repo_root)
            commit_all(repo_root, "seed export tree")

            output_dir = repo_root / "exported"
            result = self.export_materialize.run_export_materialize(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                output_dir=output_dir,
            )

        self.assertEqual(result["status"], "warn")
        self.assertIn(".agent/skills/python-expert/**", result["missing_include_patterns"])

    def test_materialize_fails_when_profile_includes_unmanaged_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root, include_unmanaged_pattern=True)
            write_runtime_scripts(repo_root)
            create_sample_tree(repo_root)
            (repo_root / "README.md").write_text("readme\n", encoding="utf-8")
            commit_all(repo_root, "seed export tree")

            output_dir = repo_root / "exported"
            result = self.export_materialize.run_export_materialize(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                output_dir=output_dir,
            )
            self.assertEqual(result["status"], "fail")
            self.assertTrue(any("README.md" in item for item in result["profile_contract_violations"]))

    def test_materialize_keeps_managed_index_even_when_split_required_targets_include_local_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(
                repo_root,
                extra_profile_includes=[".agent/skills/INDEX.md"],
                extra_managed_patterns=[".agent/skills/INDEX.md"],
                split_required=[
                    {
                        "path": ".agent/skills/INDEX.md",
                        "recommended_target": ".agent/skills/INDEX.md + .agent/state/skills/INDEX.local.md",
                    }
                ],
            )
            write_runtime_scripts(repo_root)
            create_sample_tree(repo_root)
            (repo_root / ".agent" / "skills" / "INDEX.md").write_text("builtin index\n", encoding="utf-8")
            commit_all(repo_root, "seed export tree")

            output_dir = repo_root / "exported"
            result = self.export_materialize.run_export_materialize(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                output_dir=output_dir,
            )

        self.assertEqual(result["status"], "pass")
        self.assertIn(".agent/skills/INDEX.md", result["selected_paths"])


if __name__ == "__main__":
    unittest.main()
