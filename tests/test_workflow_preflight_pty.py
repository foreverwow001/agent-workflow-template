# -*- coding: utf-8 -*-
"""
tests/test_workflow_preflight_pty.py
=====================================
用途：驗證 PTY preflight 會明確辨識缺少 backend CLI 的情況
職責：
    - 驗證缺少 codex/copilot 執行檔時，backend summary 會標成 failed
  - 驗證 workspace settings 的自訂 command 會被 preflight 讀取
=====================================
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
PRECHECK_FILE = REPO_ROOT / ".agent" / "runtime" / "scripts" / "vscode" / "workflow_preflight_pty.py"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入模組：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkflowPreflightPtyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preflight = load_module("test_workflow_preflight_pty_module", PRECHECK_FILE)

    def test_missing_default_backend_command_marks_backend_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            with patch.object(self.preflight.shutil, "which", return_value=None):
                result = self.preflight.summarize_backend_pty(repo_root, "codex")

        self.assertEqual(result["command"], "codex")
        self.assertFalse(result["command_available"])
        self.assertIsNone(result["command_path"])
        self.assertEqual(result["status"], "failed")

    def test_workspace_settings_override_backend_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            vscode_dir = repo_root / ".vscode"
            vscode_dir.mkdir(parents=True, exist_ok=True)
            (vscode_dir / "settings.json").write_text(
                json.dumps({"ivyhouseTerminalPty.copilotCommand": "custom-copilot"}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            def fake_which(command: str):
                return "/usr/local/bin/custom-copilot" if command == "custom-copilot" else None

            with patch.object(self.preflight.shutil, "which", side_effect=fake_which):
                result = self.preflight.summarize_backend_pty(repo_root, "copilot")

        self.assertEqual(result["command"], "custom-copilot")
        self.assertTrue(result["command_available"])
        self.assertEqual(result["command_path"], "/usr/local/bin/custom-copilot")
        self.assertEqual(result["status"], "cold")


if __name__ == "__main__":
    unittest.main()
