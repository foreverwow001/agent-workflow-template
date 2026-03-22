# -*- coding: utf-8 -*-
"""
tests/test_pending_review_recorder_skill.py
=========================================
用途：驗證 pending-review-recorder skill 的 note writer / dedupe 行為
職責：
  - 驗證新事件會建立結構化 note
  - 驗證相同 dedupe key 會 update 既有 note
  - 驗證安全 gate 命中時會 skip
=========================================
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_FILE = REPO_ROOT / ".agent" / "skills" / "pending-review-recorder" / "scripts" / "pending_review_recorder.py"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入模組：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def base_payload() -> dict:
    return {
        "title": "auth test keeps failing in seeded env",
        "source_repo": "demo-project",
        "project_scope": "demo-project",
        "recorded_by_role": "qa",
        "detection_mode": "auto",
        "event_class": "qa-defect",
        "workflow_phase": "testing",
        "impact_level": "medium",
        "reproducibility": "reproducible",
        "module_area": "auth/login",
        "symptom_signature": "pytest-login-seeded-admin-failure",
        "occurred_on": "2026-03-21",
        "last_seen_on": "2026-03-21",
        "evidence_refs": ["pytest tests/test_login.py::test_seeded_admin_login"],
        "workaround_applied": False,
        "next_owner": "engineer",
        "tags": ["pending-review", "qa", "triage"],
        "symptom_summary": "seeded admin login 在 QA 環境持續失敗",
        "what_happened": ["在 seeded env 執行登入測試時失敗", "相同條件下可穩定重現"],
        "impact_summary": ["阻斷 QA 驗收 auth/login 流程"],
        "evidence_summary": ["pytest tests/test_login.py::test_seeded_admin_login"],
        "workaround_summary": ["目前無 workaround"],
        "next_action_summary": ["請 engineer 先確認 seeded data 與 auth 流程"],
    }


class PendingReviewRecorderSkillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.recorder = load_module("test_pending_review_recorder_module", SCRIPT_FILE)

    def test_record_event_creates_structured_note_with_filename_rule(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            result = self.recorder.record_event(base_payload(), notes_dir)

            created_path = Path(result["target_note"])
            content = created_path.read_text(encoding="utf-8")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["action"], "create")
        self.assertTrue(created_path.name.startswith("2026-03-21-qa-qa-defect-pytest-login-seeded-admin-failure"))
        self.assertIn("note_kind: pending-review-note", content)
        self.assertIn("# Symptom Summary", content)
        self.assertIn("seeded admin login 在 QA 環境持續失敗", content)

    def test_record_event_updates_existing_matching_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            first_result = self.recorder.record_event(base_payload(), notes_dir)

            payload = base_payload()
            payload["evidence_refs"] = [
                "pytest tests/test_login.py::test_seeded_admin_login",
                "ci run #1234",
            ]
            payload["impact_level"] = "high"
            payload["symptom_summary"] = "同一 QA 問題再次出現"

            second_result = self.recorder.record_event(payload, notes_dir)

            target_path = Path(second_result["target_note"])
            content = target_path.read_text(encoding="utf-8")
            frontmatter, _body = self.recorder.parse_frontmatter(content)

        self.assertEqual(first_result["target_note"], second_result["target_note"])
        self.assertEqual(second_result["action"], "update")
        self.assertEqual(frontmatter["occurrence_count"], 2)
        self.assertEqual(frontmatter["impact_level"], "high")
        self.assertIn("ci run #1234", frontmatter["evidence_refs"])
        self.assertIn("## Update History", content)

    def test_record_event_skips_when_sensitive_data_flag_is_set(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            notes_dir = Path(temp_dir)
            payload = base_payload()
            payload["contains_sensitive_data"] = True

            result = self.recorder.record_event(payload, notes_dir)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["action"], "skip")
        self.assertIn("sensitive", result["reason"])
        self.assertEqual(list(notes_dir.glob("*.md")), [])


if __name__ == "__main__":
    unittest.main()
