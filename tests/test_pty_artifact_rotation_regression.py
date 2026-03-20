# -*- coding: utf-8 -*-
"""
tests/test_pty_artifact_rotation_regression.py
==============================================
用途：驗證 PTY artifact rotation 的 command、設定與掛點不會退化
職責：
  - 驗證 package.json 暴露 rotateArtifacts command 與 rotation settings
  - 驗證 extension.js 已有 rotation helper 與 start/restart 掛點
==============================================
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_FILE = REPO_ROOT / ".agent" / "runtime" / "tools" / "vscode_terminal_pty" / "package.json"
EXTENSION_FILE = REPO_ROOT / ".agent" / "runtime" / "tools" / "vscode_terminal_pty" / "extension.js"


class PtyArtifactRotationRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.package = json.loads(PACKAGE_FILE.read_text(encoding="utf-8"))
        cls.source = EXTENSION_FILE.read_text(encoding="utf-8")

    def test_package_json_exposes_rotation_command_and_settings(self) -> None:
        commands = {item["command"] for item in self.package["contributes"]["commands"]}
        self.assertIn("ivyhouseTerminalPty.rotateArtifacts", commands)

        properties = self.package["contributes"]["configuration"]["properties"]
        for setting in [
            "ivyhouseTerminalPty.rotateArtifactsOnStart",
            "ivyhouseTerminalPty.rotateArtifactsOnRestart",
            "ivyhouseTerminalPty.rotateArtifactsOnNewWorkflow",
            "ivyhouseTerminalPty.rotationMaxHistory",
        ]:
            with self.subTest(setting=setting):
                self.assertIn(setting, properties)

    def test_extension_rotates_artifacts_on_start_and_restart(self) -> None:
        self.assertIn("function rotateCurrentArtifacts(kind, reason)", self.source)
        self.assertIn('rotateCurrentArtifacts(kind, "start");', self.source)
        self.assertIn('rotateCurrentArtifacts(kind, "restart");', self.source)
        self.assertIn('"ivyhouseTerminalPty.rotateArtifacts"', self.source)
        self.assertIn("pty.artifacts.rotated", self.source)


if __name__ == "__main__":
    unittest.main()
