# -*- coding: utf-8 -*-
"""
tests/test_pty_bridge_launch_regression.py
===========================================
用途：驗證 PTY bridge 啟動 shebang wrapper script 時不會退回直接 exec 腳本
職責：
  - 驗證一般 binary command 不會被改寫
  - 驗證 shebang script 會改成 interpreter + script path 啟動
===========================================
"""

from __future__ import annotations

import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_FILE = REPO_ROOT / ".agent" / "runtime" / "tools" / "vscode_terminal_pty" / "codex_pty_bridge.py"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
      raise RuntimeError(f"無法載入模組：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PtyBridgeLaunchRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = load_module("test_pty_bridge_launch_regression_module", BRIDGE_FILE)

    def test_non_script_command_is_left_unchanged(self) -> None:
        command = ["copilot"]
        self.assertEqual(self.bridge.resolve_command_for_spawn(command), command)

    def test_shebang_script_uses_interpreter_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "copilot-wrapper"
            script_path.write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
            script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR)

            resolved = self.bridge.resolve_command_for_spawn([str(script_path), "--help"])

        self.assertEqual(resolved[:3], ["/usr/bin/env", "bash", str(script_path)])
        self.assertEqual(resolved[3:], ["--help"])
