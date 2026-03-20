# -*- coding: utf-8 -*-
"""
tests/test_workflow_core_delivery_contract.py
============================================
用途：驗證 workflow-core projection/bootstrap 與 portable smoke stub 的最小可執行骨架
職責：
  - 驗證 projection stub 可 bootstrap downstream overlay index placeholder
  - 驗證 portable smoke 會檢查 required live paths 與 manifest contract
============================================
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_FILE = REPO_ROOT / "core_ownership_manifest.yml"
PROJECTION_FILE = REPO_ROOT / ".agent" / "runtime" / "scripts" / "workflow_core_projection.py"
SMOKE_FILE = REPO_ROOT / ".agent" / "runtime" / "scripts" / "portable_smoke" / "workflow_core_smoke.py"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入模組：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_manifest(repo_root: Path) -> None:
    (repo_root / "core_ownership_manifest.yml").write_text(MANIFEST_FILE.read_text(encoding="utf-8"), encoding="utf-8")


def create_required_live_path_anchors(repo_root: Path, include_index: bool) -> None:
    for rel_path in [
        ".agent/workflows",
        ".agent/runtime",
        ".agent/roles",
        ".agent/skills",
        ".agent/templates",
        "doc/plans",
        "doc/logs",
    ]:
        (repo_root / rel_path).mkdir(parents=True, exist_ok=True)
    (repo_root / ".agent" / "workflows" / "AGENT_ENTRY.md").write_text("entry\n", encoding="utf-8")
    if include_index:
        index_path = repo_root / "doc" / "implementation_plan_index.md"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text("# Index\n", encoding="utf-8")


class WorkflowCoreDeliveryContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.projection = load_module("test_workflow_core_projection_module", PROJECTION_FILE)
        cls.smoke = load_module("test_workflow_core_smoke_module", SMOKE_FILE)

    def test_projection_stub_bootstraps_overlay_index_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            write_manifest(repo_root)
            create_required_live_path_anchors(repo_root, include_index=False)

            result = self.projection.run_projection_stub(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
                bootstrap_overlay_index_file=True,
            )

        self.assertEqual(result["status"], "warn")
        self.assertIn("doc/implementation_plan_index.md", result["created_paths"])
        self.assertEqual(result["missing_required_live_paths"], [])

    def test_portable_smoke_passes_when_required_anchors_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            write_manifest(repo_root)
            create_required_live_path_anchors(repo_root, include_index=True)

            result = self.smoke.run_portable_smoke(
                repo_root=repo_root,
                manifest_path=repo_root / "core_ownership_manifest.yml",
            )

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["checks"]["required_live_paths_present"])
        self.assertEqual(result["missing_required_live_paths"], [])
