# -*- coding: utf-8 -*-
"""
tests/test_code_reviewer_skill.py
=====================================
用途：驗證 code-reviewer skill 的自動審查規則與輸出狀態
職責：
  - 驗證 API key / syntax error 會觸發 fail
  - 驗證 style / maintainability 問題會產生 warning
  - 驗證乾淨檔案會維持 pass
=====================================
"""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_REVIEWER_FILE = REPO_ROOT / ".agent" / "skills" / "code-reviewer" / "scripts" / "code_reviewer.py"


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入模組：{file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CodeReviewerSkillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.code_reviewer = load_module("test_code_reviewer_module", CODE_REVIEWER_FILE)

    def write_temp_python(self, content: str) -> Path:
        temp_file = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8")
        path = Path(temp_file.name)
        temp_file.write(content)
        temp_file.close()
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def test_review_file_returns_warning_for_style_and_maintainability_issues(self) -> None:
        long_function_body = "\n".join("    total += 1" for _ in range(55))
        file_path = self.write_temp_python(
            "# 用途：測試 style warning\n"
            "import subprocess\n\n"
            "def huge_function():\n"
            "    total = 0    \n"
            "    very_long_value = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'\n"
            "    try:\n"
            "        subprocess.run('echo hi', shell=True)\n"
            "    except:\n"
            "        pass\n"
            f"{long_function_body}\n"
            "    return total\n"
        )

        result = self.code_reviewer.review_file(str(file_path))

        self.assertEqual(result["status"], "warning")
        issue_types = {issue["type"] for issue in result["issues"]}
        self.assertTrue({"trailing_whitespace", "line_too_long", "function_too_long", "bare_except", "shell_true"}.issubset(issue_types))

    def test_review_file_returns_fail_for_api_key_leak(self) -> None:
        file_path = self.write_temp_python(
            "# 用途：測試 API key fail\n"
            "OPENAI_API_KEY = 'sk-abcdefghijklmnopqrstuvwxyz123456'\n"
        )

        result = self.code_reviewer.review_file(str(file_path))

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["summary"]["api_key_leak"], 1)

    def test_review_file_returns_fail_for_syntax_error(self) -> None:
        file_path = self.write_temp_python(
            "# 用途：測試 syntax fail\n"
            "def broken(:\n"
            "    return 1\n"
        )

        result = self.code_reviewer.review_file(str(file_path))

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["summary"]["syntax_error"], 1)

    def test_review_file_returns_pass_for_clean_python_file(self) -> None:
        file_path = self.write_temp_python(
            "# 用途：測試 clean pass\n"
            "def add_numbers(left: int, right: int) -> int:\n"
            "    return left + right\n"
        )

        result = self.code_reviewer.review_file(str(file_path))

        self.assertEqual(result["status"], "pass")
        self.assertEqual(sum(result["summary"].values()), 0)

    def test_review_directory_aggregates_python_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "clean.py").write_text(
                "# 用途：乾淨檔案\ndef add(left: int, right: int) -> int:\n    return left + right\n",
                encoding="utf-8",
            )
            (root / "warn.py").write_text(
                "# 用途：警告檔案\nimport subprocess\n\ndef run_cmd():\n    subprocess.run('echo hi', shell=True)\n",
                encoding="utf-8",
            )
            (root / "README.md").write_text("not python", encoding="utf-8")

            result = self.code_reviewer.review_directory(str(root))

        self.assertEqual(result["target_type"], "directory")
        self.assertEqual(result["files_reviewed"], 2)
        self.assertEqual(result["summary"]["total_files"], 2)
        self.assertEqual(result["summary"]["shell_true"], 1)
        self.assertEqual(result["status"], "warning")

    def test_review_diff_reviews_only_changed_python_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / "src").mkdir()
            changed_file = project_root / "src" / "changed.py"
            changed_file.write_text(
                "# 用途：diff 審查\nimport subprocess\n\ndef run_cmd():\n    subprocess.run('echo hi', shell=True)\n",
                encoding="utf-8",
            )
            untouched_file = project_root / "src" / "untouched.py"
            untouched_file.write_text(
                "# 用途：未變更檔案\ndef ok() -> int:\n    return 1\n",
                encoding="utf-8",
            )
            diff_file = project_root / "changes.diff"
            diff_file.write_text(
                "diff --git a/src/changed.py b/src/changed.py\n"
                "index 123..456 100644\n"
                "--- a/src/changed.py\n"
                "+++ b/src/changed.py\n"
                "@@ -1 +1 @@\n"
                "+changed\n"
                "diff --git a/README.md b/README.md\n"
                "--- a/README.md\n"
                "+++ b/README.md\n",
                encoding="utf-8",
            )

            result = self.code_reviewer.review_diff(str(diff_file), str(project_root))

        self.assertEqual(result["target_type"], "diff")
        self.assertEqual(result["files_reviewed"], 1)
        self.assertEqual(len(result["results"]), 1)
        self.assertTrue(result["results"][0]["file"].endswith("src/changed.py"))
        self.assertEqual(result["summary"]["shell_true"], 1)
        self.assertEqual(result["status"], "warning")

    def test_review_staged_diff_uses_git_command_without_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / "src").mkdir()
            changed_file = project_root / "src" / "changed.py"
            changed_file.write_text(
                "# 用途：staged 審查\nimport subprocess\n\ndef run_cmd():\n    subprocess.run('echo hi', shell=True)\n",
                encoding="utf-8",
            )
            diff_text = (
                "diff --git a/src/changed.py b/src/changed.py\n"
                "index 123..456 100644\n"
                "--- a/src/changed.py\n"
                "+++ b/src/changed.py\n"
                "@@ -1 +1 @@\n"
                "+changed\n"
            )
            completed = subprocess.CompletedProcess(
                args=["git", "--no-pager", "diff", "--no-color", "--staged"],
                returncode=0,
                stdout=diff_text,
                stderr="",
            )

            with patch.object(self.code_reviewer.subprocess, "run", return_value=completed):
                result = self.code_reviewer.review_staged_diff(str(project_root))

        self.assertEqual(result["target"], "git diff --staged")
        self.assertEqual(result["target_type"], "diff")
        self.assertEqual(result["files_reviewed"], 1)
        self.assertEqual(result["summary"]["shell_true"], 1)
        self.assertEqual(result["status"], "warning")

    def test_review_cached_diff_uses_git_command_without_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / "src").mkdir()
            changed_file = project_root / "src" / "changed.py"
            changed_file.write_text(
                "# 用途：cached 審查\nimport subprocess\n\ndef run_cmd():\n    subprocess.run('echo hi', shell=True)\n",
                encoding="utf-8",
            )
            diff_text = (
                "diff --git a/src/changed.py b/src/changed.py\n"
                "index 123..456 100644\n"
                "--- a/src/changed.py\n"
                "+++ b/src/changed.py\n"
                "@@ -1 +1 @@\n"
                "+changed\n"
            )
            completed = subprocess.CompletedProcess(
                args=["git", "--no-pager", "diff", "--no-color", "--cached"],
                returncode=0,
                stdout=diff_text,
                stderr="",
            )

            with patch.object(self.code_reviewer.subprocess, "run", return_value=completed):
                result = self.code_reviewer.review_cached_diff(str(project_root))

        self.assertEqual(result["target"], "git diff --cached")
        self.assertEqual(result["target_type"], "diff")
        self.assertEqual(result["files_reviewed"], 1)
        self.assertEqual(result["summary"]["shell_true"], 1)
        self.assertEqual(result["status"], "warning")

    def test_review_git_diff_range_uses_git_command_without_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / "pkg").mkdir()
            changed_file = project_root / "pkg" / "module.py"
            changed_file.write_text(
                "# 用途：range 審查\ndef add(left: int, right: int) -> int:\n    return left + right\n",
                encoding="utf-8",
            )
            diff_text = (
                "diff --git a/pkg/module.py b/pkg/module.py\n"
                "index 123..456 100644\n"
                "--- a/pkg/module.py\n"
                "+++ b/pkg/module.py\n"
                "@@ -1 +1 @@\n"
                "+changed\n"
            )
            completed = subprocess.CompletedProcess(
                args=["git", "--no-pager", "diff", "--no-color", "main..HEAD"],
                returncode=0,
                stdout=diff_text,
                stderr="",
            )

            with patch.object(self.code_reviewer.subprocess, "run", return_value=completed):
                result = self.code_reviewer.review_git_diff_range("main..HEAD", str(project_root))

        self.assertEqual(result["target"], "git diff main..HEAD")
        self.assertEqual(result["target_type"], "diff")
        self.assertEqual(result["files_reviewed"], 1)
        self.assertEqual(result["status"], "pass")

    def test_review_git_diff_range_rejects_invalid_range(self) -> None:
        result = self.code_reviewer.review_git_diff_range("main..HEAD;rm -rf /", ".")

        self.assertEqual(result["status"], "error")
        self.assertIn("不支援的 git diff 範圍格式", result["message"])


if __name__ == "__main__":
    unittest.main()
