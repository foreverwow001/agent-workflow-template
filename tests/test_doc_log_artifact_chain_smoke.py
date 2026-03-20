# -*- coding: utf-8 -*-
"""
tests/test_doc_log_artifact_chain_smoke.py
==========================================
用途：驗證 doc/logs 產物鏈已成為可實際 smoke 的狀態
職責：
  - 驗證 repo 已提供 doc/logs/Idx-000_log.template.md
  - 驗證 plan template 的 log_file_path 可對上 doc/logs 落點
  - 驗證 skills_evaluator 可對 template-based log 產生統計結果
==========================================
"""

from __future__ import annotations

import importlib.util
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_TEMPLATE_FILE = REPO_ROOT / "doc" / "plans" / "Idx-000_plan.template.md"
LOG_TEMPLATE_FILE = REPO_ROOT / "doc" / "logs" / "Idx-000_log.template.md"
PLAN_VALIDATOR_FILE = REPO_ROOT / ".agent" / "skills" / "plan-validator" / "scripts" / "plan_validator.py"
SKILLS_EVALUATOR_FILE = REPO_ROOT / ".agent" / "skills" / "skills-evaluator" / "scripts" / "skills_evaluator.py"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入模組：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DocLogArtifactChainSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan_template = PLAN_TEMPLATE_FILE.read_text(encoding="utf-8")
        cls.log_template = LOG_TEMPLATE_FILE.read_text(encoding="utf-8")
        cls.plan_validator = load_module("test_plan_validator_for_log_chain", PLAN_VALIDATOR_FILE)
        cls.skills_evaluator = load_module("test_skills_evaluator_for_log_chain", SKILLS_EVALUATOR_FILE)

    def test_repo_exposes_real_doc_logs_template(self) -> None:
        self.assertTrue(LOG_TEMPLATE_FILE.exists())
        self.assertIn("## 🔗 ARTIFACT_CHAIN", self.log_template)
        self.assertIn("plan_file_path: `doc/plans/Idx-XXX_plan.md`", self.log_template)
        self.assertIn("log_file_path: `doc/logs/Idx-XXX_log.md`", self.log_template)
        self.assertIn("## 🛠️ SKILLS_EXECUTION_REPORT", self.log_template)
        self.assertIn("## 📈 SKILLS_EVALUATION", self.log_template)

    def test_plan_to_log_chain_smoke_runs_skills_evaluator(self) -> None:
        plan_log_match = re.search(r"log_file_path:\s*\[(doc/logs/Idx-XXX_log\.md)\]", self.plan_template)
        self.assertIsNotNone(plan_log_match)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            plan_path = temp_root / "Idx-999_plan.md"
            log_path = temp_root / "doc" / "logs" / "Idx-999_log.md"
            log_path.parent.mkdir(parents=True, exist_ok=True)

            plan_content = self.plan_template.replace("Idx-XXX_log.md", "Idx-999_log.md")
            plan_path.write_text(plan_content, encoding="utf-8")

            validation_result = self.plan_validator.validate_plan(plan_path)
            self.assertEqual(validation_result["status"], "pass", validation_result)

            log_content = (
                self.log_template.replace("Idx-XXX", "Idx-999").replace(
                    "<!-- SKILLS_EXECUTION_REPORT_ROWS -->",
                    "| plan-validator | doc/plans/Idx-999_plan.md | pass | Plan contract validated | 2026-03-18T12:00:00Z |\n"
                    "| skills-evaluator | doc/logs/Idx-999_log.md | pass | Log artifact chain smoke | 2026-03-18T12:05:00Z |",
                )
            )
            log_path.write_text(log_content, encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = self.skills_evaluator.main(["skills_evaluator.py", str(log_path)])

            evaluator_result = json.loads(stdout.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(evaluator_result["status"], "pass")
        self.assertEqual(evaluator_result["statistics"]["total_executions"], 2)
        self.assertEqual(evaluator_result["statistics"]["skill_counts"].get("plan-validator"), 1)
        self.assertEqual(evaluator_result["statistics"]["skill_counts"].get("skills-evaluator"), 1)


if __name__ == "__main__":
    unittest.main()
