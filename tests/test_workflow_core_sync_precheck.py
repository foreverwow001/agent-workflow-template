# -*- coding: utf-8 -*-
"""
tests/test_workflow_core_sync_precheck.py
=========================================
用途：驗證 workflow-core sync precheck 的 working tree 分類與 exit code 契約
職責：
  - 驗證 clean workspace 會 pass
  - 驗證 overlay/state dirty 會回 warn 與 manual review
  - 驗證 core managed path dirty 會直接 fail
  - 驗證 strict-clean 會把非 core dirty 升級成 fail
=========================================
"""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_FILE = REPO_ROOT / ".agent" / "runtime" / "scripts" / "workflow_core_sync_precheck.py"
MANIFEST_FILE = REPO_ROOT / "core_ownership_manifest.yml"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入模組：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def init_git_repo(repo_root: Path) -> None:
    subprocess.run(["git", "init", "-q", str(repo_root)], check=True)


def write_manifest(repo_root: Path) -> None:
    (repo_root / "core_ownership_manifest.yml").write_text(MANIFEST_FILE.read_text(encoding="utf-8"), encoding="utf-8")


def commit_all(repo_root: Path, message: str) -> None:
    subprocess.run(["git", "-C", str(repo_root), "config", "user.name", "Test User"], check=True)
    subprocess.run(["git", "-C", str(repo_root), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo_root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo_root), "commit", "-q", "-m", message], check=True)


class WorkflowCoreSyncPrecheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.precheck = load_module("test_workflow_core_sync_precheck_module", SCRIPT_FILE)

    def test_clean_repo_returns_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            commit_all(repo_root, "seed manifest")

            result = self.precheck.run_sync_precheck(repo_root, release_ref="core-v20260319-1")

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["clean_worktree"])
        self.assertFalse(result["manual_review_required"])
        self.assertEqual(result["core_divergence_paths"], [])
        self.assertEqual(Path(result["manifest_path"]), repo_root / "core_ownership_manifest.yml")

    def test_overlay_or_state_dirty_returns_warn(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            commit_all(repo_root, "seed manifest")
            dirty_path = repo_root / ".agent" / "state" / "skills" / "audit.log"
            dirty_path.parent.mkdir(parents=True, exist_ok=True)
            dirty_path.write_text("entry\n", encoding="utf-8")

            result = self.precheck.run_sync_precheck(repo_root, release_ref="core-v20260319-1")

        self.assertEqual(result["status"], "warn")
        self.assertFalse(result["clean_worktree"])
        self.assertTrue(result["manual_review_required"])
        self.assertIn(".agent/state/skills/audit.log", result["state_only_paths"])
        self.assertIn("state-dirty", result["manual_review_reasons"])

    def test_core_managed_dirty_returns_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            commit_all(repo_root, "seed manifest")
            dirty_path = repo_root / ".agent" / "workflows" / "dev-team.md"
            dirty_path.parent.mkdir(parents=True, exist_ok=True)
            dirty_path.write_text("draft\n", encoding="utf-8")

            result = self.precheck.run_sync_precheck(repo_root, release_ref="core-v20260319-1")

        self.assertEqual(result["status"], "fail")
        self.assertIn(".agent/workflows/dev-team.md", result["core_divergence_paths"])
        self.assertFalse(result["manual_review_required"])

    def test_cli_strict_clean_promotes_warn_to_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            commit_all(repo_root, "seed manifest")
            dirty_path = repo_root / "doc" / "plans" / "Idx-999_plan.md"
            dirty_path.parent.mkdir(parents=True, exist_ok=True)
            dirty_path.write_text("plan\n", encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                exit_code = self.precheck.main(
                    [
                        "--repo-root",
                        str(repo_root),
                        "--release-ref",
                        "core-v20260319-1",
                        "--strict-clean",
                        "--json",
                    ]
                )

        self.assertEqual(exit_code, self.precheck.EXIT_FAIL)
        self.assertEqual(stderr.getvalue(), "")
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "fail")
        self.assertIn("doc/plans/Idx-999_plan.md", payload["overlay_only_paths"])

    def test_missing_manifest_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                exit_code = self.precheck.main(
                    [
                        "--repo-root",
                        str(repo_root),
                        "--release-ref",
                        "core-v20260319-1",
                        "--json",
                    ]
                )

        self.assertEqual(exit_code, self.precheck.EXIT_ERROR)
        self.assertEqual(stdout.getvalue(), "")
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["status"], "error")
        self.assertIn("manifest not found", payload["error"])

    def test_review_required_skill_package_is_unclassified_warn(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            init_git_repo(repo_root)
            write_manifest(repo_root)
            commit_all(repo_root, "seed manifest")
            dirty_path = repo_root / ".agent" / "skills" / "explore-cli-tool" / "SKILL.md"
            dirty_path.parent.mkdir(parents=True, exist_ok=True)
            dirty_path.write_text("draft\n", encoding="utf-8")

            result = self.precheck.run_sync_precheck(repo_root, release_ref="core-v20260319-1")

        self.assertEqual(result["status"], "warn")
        self.assertIn(".agent/skills/explore-cli-tool/SKILL.md", result["unclassified_paths"])


if __name__ == "__main__":
    unittest.main()
