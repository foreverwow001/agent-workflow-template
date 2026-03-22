# -*- coding: utf-8 -*-
"""
tests/test_dev_entry_workflow_contract.py
========================================
用途：驗證 /dev 入口契約的 smoke 與 Plan gate 不會退化
職責：
  - 驗證 READ_BACK_REPORT 仍是硬停頓，且 Mode Selection Gate 位於 Plan 之前
  - 驗證 plan template 已包含新的 Security Review 欄位
  - 驗證 plan_validator 會把新欄位當成必要欄位
========================================
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRY_FILE = REPO_ROOT / ".agent" / "workflows" / "AGENT_ENTRY.md"
PLAN_TEMPLATE_FILE = REPO_ROOT / "doc" / "plans" / "Idx-000_plan.template.md"
PLAN_VALIDATOR_FILE = REPO_ROOT / ".agent" / "skills" / "plan-validator" / "scripts" / "plan_validator.py"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入模組：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DevEntryWorkflowContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entry = ENTRY_FILE.read_text(encoding="utf-8")
        cls.template = PLAN_TEMPLATE_FILE.read_text(encoding="utf-8")
        cls.plan_validator = load_module("test_plan_validator_module", PLAN_VALIDATOR_FILE)

    def test_read_back_report_still_blocks_before_plan(self) -> None:
        self.assertIn("### ===READ_BACK_REPORT===", self.entry)
        self.assertIn("### ===END_READ_BACK_REPORT===", self.entry)
        self.assertIn("輸出後必須停下", self.entry)

        mode_selection_index = self.entry.index("2) **Mode Selection Gate**")
        plan_index = self.entry.index("3) **Plan**")
        self.assertLess(mode_selection_index, plan_index)
        self.assertIn("lightweight-direct-edit", self.entry)

    def test_entry_requires_downstream_obsidian_index_first_gate(self) -> None:
        self.assertIn("Obsidian Knowledge Intake Gate", self.entry)
        self.assertIn("`obsidian-knowledge/00-indexes/`", self.entry)
        self.assertIn("`obsidian-knowledge/20-reviewed/`", self.entry)
        self.assertIn("先檢閱 `00-indexes/`", self.entry)
        self.assertIn("再依索引只讀取最小必要的 `20-reviewed/` 文件", self.entry)
        self.assertIn("`10-inbox/pending-review-notes/` 不屬於啟動前置閱讀", self.entry)

    def test_plan_template_contains_security_review_fields(self) -> None:
        for field in [
            "security_reviewer_tool:",
            "security_review_trigger_source:",
            "security_review_trigger_matches:",
            "security_review_start:",
            "security_review_end:",
            "security_review_result:",
            "security_review_conclusion:",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, self.template)

    def test_plan_validator_requires_new_security_review_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = Path(temp_dir) / "Idx-999_plan.md"
            plan_path.write_text(
                self.template.replace("security_review_result:", "security_review_result_removed:"),
                encoding="utf-8",
            )
            result = self.plan_validator.validate_plan(plan_path)

        self.assertEqual(result["status"], "fail")
        self.assertTrue(
            any("security_review_result:" in error for error in result["format_errors"]),
            result["format_errors"],
        )


if __name__ == "__main__":
    unittest.main()
