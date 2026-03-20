# -*- coding: utf-8 -*-
"""
tests/test_copilot_composer_gate_regression.py
==============================================
用途：驗證 Copilot PTY fresh-session composer gate 的關鍵 wiring 不會退化
職責：
  - 驗證 Copilot profile 仍維持 direct-text + carriage-return
  - 驗證 fresh prompt delay 已回落到 1500ms
  - 驗證 fresh smoke session 仍會執行 focused probe-echo gate
==============================================
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXTENSION_FILE = REPO_ROOT / ".agent" / "runtime" / "tools" / "vscode_terminal_pty" / "extension.js"


class CopilotComposerGateRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = EXTENSION_FILE.read_text(encoding="utf-8")

    def test_copilot_profile_keeps_direct_text_and_carriage_return(self) -> None:
        self.assertRegex(
            self.source,
            re.compile(
                r"\[BACKEND_KINDS\.COPILOT\][\s\S]*?inputPolicy:\s*\{[\s\S]*?textMode:\s*\"direct-text\"[\s\S]*?submitMode:\s*\"carriage-return\"",
                re.MULTILINE,
            ),
        )

    def test_copilot_profile_uses_reduced_fresh_prompt_delay(self) -> None:
        self.assertRegex(
            self.source,
            re.compile(
                r"\[BACKEND_KINDS\.COPILOT\][\s\S]*?startup:\s*\{[\s\S]*?requireCsiU:\s*false[\s\S]*?freshPromptDelayMs:\s*1500",
                re.MULTILINE,
            ),
        )

    def test_copilot_composer_gate_requires_focus_and_probe_echo(self) -> None:
        self.assertRegex(
            self.source,
            re.compile(
                r"\[BACKEND_KINDS\.COPILOT\][\s\S]*?composerInputGate:\s*\{[\s\S]*?attempts:\s*Math\.max\(1, Number\(cfg\.get\(\"copilotComposerInputGateAttempts\", 4\)\) \|\| 4\)[\s\S]*?timeoutMs:\s*Math\.max\(250, Number\(cfg\.get\(\"copilotComposerInputGateTimeoutMs\", 1800\)\) \|\| 1800\)[\s\S]*?retryDelayMs:\s*Math\.max\(0, Number\(cfg\.get\(\"copilotComposerInputGateRetryDelayMs\", 500\)\) \|\| 500\)",
                re.MULTILINE,
            ),
        )
        self.assertIn('session.terminal.show(false);', self.source)
        self.assertIn('matchReason = "probe_echo";', self.source)
        self.assertIn('await waitForCopilotComposerInputReady(kind);', self.source)


if __name__ == "__main__":
    unittest.main()
