# -*- coding: utf-8 -*-
"""focused tests for workflow-core export landing checklist generation."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_workflow_core_export_materialize import (  # noqa: E402
    commit_all,
    create_sample_tree,
    init_git_repo,
    write_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / ".agent" / "runtime" / "scripts"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入模組：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_runtime_scripts(repo_root: Path) -> None:
    target_dir = repo_root / ".agent" / "runtime" / "scripts"
    target_dir.mkdir(parents=True, exist_ok=True)
    for filename in [
        "workflow_core_manifest.py",
        "workflow_core_contracts.py",
        "workflow_core_export_materialize.py",
        "workflow_core_export_landing_checklist.py",
    ]:
        (target_dir / filename).write_text((SCRIPTS_DIR / filename).read_text(encoding="utf-8"), encoding="utf-8")


class WorkflowCoreExportLandingChecklistTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checklist = load_module(
            "test_workflow_core_export_landing_checklist_module",
            SCRIPTS_DIR / "workflow_core_export_landing_checklist.py",
        )

    def test_checklist_classifies_source_ref_worktree_only_and_missing_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(
                repo_root,
                extra_profile_includes=[".agent/skills/python-expert/**", "doc/logs/Idx-000_log.template.md"],
                extra_managed_patterns=[".agent/skills/python-expert/**", "doc/logs/Idx-000_log.template.md"],
            )
            write_runtime_scripts(repo_root)
            create_sample_tree(repo_root)
            commit_all(repo_root, "seed export tree")

            python_expert_file = repo_root / ".agent" / "skills" / "python-expert" / "SKILL.md"
            python_expert_file.parent.mkdir(parents=True, exist_ok=True)
            python_expert_file.write_text("python expert\n", encoding="utf-8")

            output_dir = repo_root / "out"
            result = self.checklist.run_export_landing_checklist(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                output_path=output_dir,
            )
            markdown = (output_dir / "workflow-core-export-landing-curated-core-v1.md").read_text(encoding="utf-8")
            payload = json.loads((output_dir / "workflow-core-export-landing-curated-core-v1.json").read_text(encoding="utf-8"))

        self.assertEqual(result["status"], "warn")
        self.assertIn(".agent/skills/python-expert/**", result["worktree_only_include_patterns"])
        self.assertIn("doc/logs/Idx-000_log.template.md", result["missing_include_patterns"])
        self.assertIn("Present Only In Working Tree", markdown)
        self.assertIn("Still Missing", markdown)
        self.assertEqual(payload["status"], "warn")

    def test_checklist_fails_on_profile_contract_violation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root, include_unmanaged_pattern=True)
            write_runtime_scripts(repo_root)
            create_sample_tree(repo_root)
            (repo_root / "README.md").write_text("readme\n", encoding="utf-8")
            commit_all(repo_root, "seed export tree")

            result = self.checklist.run_export_landing_checklist(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
            )

        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("README.md" in item for item in result["profile_contract_violations"]))


if __name__ == "__main__":
    unittest.main()
