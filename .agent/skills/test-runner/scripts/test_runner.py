# -*- coding: utf-8 -*-
"""
.agent/skills/test-runner/scripts/test_runner.py
=====================================
用途：自動化測試執行工具
職責：在專案根目錄執行 pytest 並以 JSON 格式回報結果
=====================================

使用方式：
    python .agent/skills/test-runner/scripts/test_runner.py [test_path]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


SKILLS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SKILLS_ROOT.parent.parent


def validate_output_schema(result: Dict[str, Any], skill_name: str) -> Dict[str, Any]:
    """可選 JSON Schema 驗證（graceful degradation）"""
    try:
        import jsonschema
    except ImportError:
        return result

    schema_path = SKILLS_ROOT / "schemas" / f"{skill_name}_output.schema.json"
    if not schema_path.exists():
        return result

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(result, schema)
        return result
    except jsonschema.ValidationError as exc:
        result["validation_errors"] = [
            {"message": exc.message, "path": list(exc.path), "schema_path": list(exc.schema_path)}
        ]
        result.setdefault(
            "suggestion",
            f"輸出格式不符合 schema 規範。請檢查 {skill_name}_output.schema.json 並確認欄位正確性。",
        )
        return result
    except Exception:
        return result


def find_project_root() -> Path:
    """從 skills 根目錄往上找專案根目錄 (含有 pyproject.toml 或 requirements.txt)"""
    current = REPO_ROOT
    for _ in range(5):
        if (current / "pyproject.toml").exists() or (current / "requirements.txt").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return REPO_ROOT


def run_pytest(test_path: Optional[str] = None) -> Dict[str, Any]:
    """執行 pytest 並回傳結果"""
    project_root = find_project_root()
    cmd = [sys.executable, "-m", "pytest", "--tb=short", "-q", "--no-header"]
    if test_path:
        cmd.append(test_path)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "測試執行超時 (超過 5 分鐘)",
            "suggestion": "請縮小測試範圍（指定 test_path），或檢查是否有卡住的測試。",
            "usage": "python .agent/skills/test-runner/scripts/test_runner.py [test_path]",
            "project_root": str(project_root),
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "details": [],
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "找不到 pytest，請確認已安裝：pip install pytest",
            "suggestion": "若使用 uv/poetry，請確認虛擬環境已啟用並安裝 pytest。",
            "usage": "python .agent/skills/test-runner/scripts/test_runner.py [test_path]",
            "project_root": str(project_root),
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "details": [],
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": f"執行失敗：{str(exc)}",
            "suggestion": "請確認專案依賴已安裝，或嘗試先執行：python -m pytest -q",
            "usage": "python .agent/skills/test-runner/scripts/test_runner.py [test_path]",
            "project_root": str(project_root),
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "details": [],
        }

    output = result.stdout + result.stderr
    if "No module named pytest" in output or "No module named 'pytest'" in output:
        return {
            "status": "error",
            "message": "找不到 pytest，請確認已安裝（python -m pytest 失敗）",
            "suggestion": "請先安裝 pytest，例如：pip install pytest",
            "usage": "python .agent/skills/test-runner/scripts/test_runner.py [test_path]",
            "project_root": str(project_root),
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "exit_code": result.returncode,
            "output": output[:2000] if len(output) > 2000 else output,
            "details": [],
        }

    lines = output.strip().split("\n")
    passed = 0
    failed = 0
    errors = 0

    for line in reversed(lines):
        if "passed" in line or "failed" in line or "error" in line:
            import re

            passed_match = re.search(r"(\d+)\s*passed", line)
            failed_match = re.search(r"(\d+)\s*failed", line)
            error_match = re.search(r"(\d+)\s*error", line)
            if passed_match:
                passed = int(passed_match.group(1))
            if failed_match:
                failed = int(failed_match.group(1))
            if error_match:
                errors = int(error_match.group(1))
            break

    if result.returncode == 5 and passed == 0 and failed == 0 and errors == 0:
        status = "no_tests"
    elif failed > 0 or errors > 0:
        status = "fail"
    elif passed > 0:
        status = "pass"
    else:
        status = "no_tests"

    return {
        "status": status,
        "project_root": str(project_root),
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "exit_code": result.returncode,
        "output": output[:2000] if len(output) > 2000 else output,
        "details": [],
    }


def main(argv: List[str] | None = None) -> int:
    """主程式入口"""
    args = argv or sys.argv
    test_path = args[1] if len(args) > 1 else None
    result = run_pytest(test_path)
    result = validate_output_schema(result, "test_runner")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "fail":
        return 1
    if result["status"] == "error":
        return 2
    return 0


__all__ = ["validate_output_schema", "find_project_root", "run_pytest", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
