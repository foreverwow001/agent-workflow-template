# -*- coding: utf-8 -*-
"""
tests/test_workflow_bootstrap_rotation_contract.py
=================================================
用途：驗證 /dev bootstrap 已接上 PTY artifact rotation 契約
職責：
  - 驗證 AGENT_ENTRY 在 Mode Selection Gate 前要求 new-workflow rotate
  - 驗證 supporting docs 也同步描述 bootstrap rotation
=================================================
"""

from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRY_FILE = REPO_ROOT / ".agent" / "workflows" / "AGENT_ENTRY.md"
DEV_TEAM_FILE = REPO_ROOT / ".agent" / "workflows" / "dev-team.md"
PROMPT_DEV_FILE = REPO_ROOT / ".agent" / "VScode_system" / "prompt_dev.md"
TOOL_SETS_FILE = REPO_ROOT / ".agent" / "VScode_system" / "tool_sets.md"


class WorkflowBootstrapRotationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entry = ENTRY_FILE.read_text(encoding="utf-8")
        cls.dev_team = DEV_TEAM_FILE.read_text(encoding="utf-8")
        cls.prompt_dev = PROMPT_DEV_FILE.read_text(encoding="utf-8")
        cls.tool_sets = TOOL_SETS_FILE.read_text(encoding="utf-8")

    def test_entry_requires_new_workflow_rotation_before_mode_selection(self) -> None:
        self.assertIn("Bootstrap（新 /dev 任務）", self.entry)
        self.assertIn("ivyhouseTerminalPty.rotateArtifacts", self.entry)
        self.assertIn('reason="new-workflow"', self.entry)
        self.assertLess(
            self.entry.index("ivyhouseTerminalPty.rotateArtifacts"),
            self.entry.index("2) **Mode Selection Gate**"),
        )

    def test_supporting_docs_reference_same_bootstrap_rotation(self) -> None:
        for content in [self.dev_team, self.prompt_dev, self.tool_sets]:
            with self.subTest(document=content[:40]):
                self.assertIn("ivyhouseTerminalPty.rotateArtifacts", content)
                self.assertIn('reason="new-workflow"', content)


if __name__ == "__main__":
    unittest.main()
