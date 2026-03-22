# -*- coding: utf-8 -*-
"""focused tests for downstream restricted Obsidian mount generator."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_FILE = REPO_ROOT / ".agent" / "runtime" / "scripts" / "workflow_core_obsidian_restricted_mount.py"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入模組：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkflowCoreObsidianRestrictedMountTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_module("test_workflow_core_obsidian_restricted_mount_module", SCRIPT_FILE)

    def test_generator_writes_restricted_mount_artifacts_and_gitignore_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")

            result = self.generator.run_generate_downstream_obsidian_mount(repo_root=repo_root)

            snippet = (repo_root / ".devcontainer" / "devcontainer.obsidian-restricted.jsonc").read_text(encoding="utf-8")
            guide = (repo_root / ".devcontainer" / "OBSIDIAN_RESTRICTED_MOUNT.md").read_text(encoding="utf-8")
            gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")

        self.assertEqual(result["status"], "pass")
        self.assertIn("OBSIDIAN_HOST_VAULT_ROOT", snippet)
        self.assertIn("obsidian-knowledge/00-indexes", snippet)
        self.assertIn("obsidian-knowledge/20-reviewed", snippet)
        self.assertNotIn("10-inbox/pending-review-notes", snippet)
        self.assertNotIn("30-archives", snippet)
        self.assertIn("single-root workspace", guide)
        self.assertIn("這不是 multi-root workspace", guide)
        self.assertIn("obsidian-knowledge/", gitignore)

    def test_generator_is_idempotent_for_gitignore_updates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            self.generator.run_generate_downstream_obsidian_mount(repo_root=repo_root)
            self.generator.run_generate_downstream_obsidian_mount(repo_root=repo_root)
            gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")

        self.assertEqual(gitignore.count("obsidian-knowledge/"), 1)

    def test_generator_refuses_to_overwrite_modified_snippet_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            output_dir = repo_root / ".devcontainer"
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "devcontainer.obsidian-restricted.jsonc").write_text("custom\n", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                self.generator.run_generate_downstream_obsidian_mount(repo_root=repo_root)
