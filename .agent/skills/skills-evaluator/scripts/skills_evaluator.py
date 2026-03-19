# -*- coding: utf-8 -*-
"""
.agent/skills/skills-evaluator/scripts/skills_evaluator.py
=====================================
用途：解析 Log 中的 SKILLS_EXECUTION_REPORT，產生統計報告
職責：
  - 解析 Log 表格並彙整狀態分布與技能執行次數
  - 輸出 JSON（預設）或 Markdown（--format markdown）
=====================================

使用方式：
    python .agent/skills/skills-evaluator/scripts/skills_evaluator.py <log_file_path> [--format json|markdown]
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


SKILLS_ROOT = Path(__file__).resolve().parents[2]


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


def _strip_ticks(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith("`") and stripped.endswith("`") and len(stripped) >= 2:
        return stripped[1:-1].strip()
    return stripped


def parse_skills_execution_report(log_content: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    lines = log_content.splitlines()

    header_index = None
    for index, line in enumerate(lines):
        if line.strip().startswith("## 🛠️ SKILLS_EXECUTION_REPORT"):
            header_index = index
            break

    if header_index is None:
        return records

    section_lines: List[str] = []
    for line in lines[header_index + 1 :]:
        if line.startswith("## "):
            break
        section_lines.append(line)

    for raw in section_lines:
        row = raw.strip()
        if not row.startswith("|"):
            continue
        parts = [part.strip() for part in row.strip("|").split("|")]
        if len(parts) < 5:
            continue
        skill, target, status, summary, timestamp = parts[:5]
        if skill.strip().lower() in {"skill", "---", ""}:
            continue
        if re.fullmatch(r"-{3,}", _strip_ticks(skill)):
            continue

        records.append(
            {
                "skill": _strip_ticks(skill),
                "target": _strip_ticks(target),
                "status": _strip_ticks(status).lower(),
                "summary": summary.strip(),
                "timestamp": timestamp.strip(),
            }
        )

    return records


def compute_statistics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        return {
            "total_executions": 0,
            "success_rate": 0.0,
            "status_distribution": {},
            "skill_counts": {},
            "failed_skills": [],
            "summary": "未找到 skills 執行記錄",
        }

    status_counter = Counter(record.get("status", "") for record in records)
    skill_counter = Counter(record.get("skill", "") for record in records)
    failed_skills = [
        {
            "skill": record.get("skill", ""),
            "target": record.get("target", ""),
            "summary": record.get("summary", ""),
        }
        for record in records
        if record.get("status") in {"fail", "error"}
    ]

    success_count = (
        status_counter.get("pass", 0)
        + status_counter.get("warning", 0)
        + status_counter.get("no_tests", 0)
    )
    total_count = len(records)
    success_rate = (success_count / total_count * 100.0) if total_count else 0.0

    return {
        "total_executions": total_count,
        "success_rate": round(success_rate, 2),
        "status_distribution": dict(status_counter),
        "skill_counts": dict(skill_counter.most_common()),
        "failed_skills": failed_skills,
        "summary": f"{total_count} 次執行，成功率 {success_rate:.1f}%",
    }


def generate_markdown_report(stats: Dict[str, Any]) -> str:
    md_lines: List[str] = [
        "# Skills Evaluation Report",
        "",
        f"**總執行次數**: {stats.get('total_executions', 0)}",
        f"**成功率**: {stats.get('success_rate', 0.0)}%",
        "",
        "## Status 分布",
        "",
        "| Status | Count |",
        "|--------|-------|",
    ]

    for status, count in (stats.get("status_distribution") or {}).items():
        md_lines.append(f"| {status} | {count} |")
    md_lines.extend(["", "## Skills 執行次數", "", "| Skill | Count |", "|-------|-------|"])

    for skill, count in (stats.get("skill_counts") or {}).items():
        md_lines.append(f"| {skill} | {count} |")
    md_lines.append("")

    failed = stats.get("failed_skills") or []
    if failed:
        md_lines.extend(["## 失敗的 Skills", "", "| Skill | Target | Summary |", "|-------|--------|----------|"])
        for item in failed:
            md_lines.append(f"| {item.get('skill','')} | {item.get('target','')} | {item.get('summary','')} |")
        md_lines.append("")

    return "\n".join(md_lines).rstrip() + "\n"


def _parse_format(argv: List[str]) -> str:
    if "--format" not in argv:
        return "json"
    try:
        index = argv.index("--format")
        return argv[index + 1].strip().lower()
    except Exception:
        return "json"


def main(argv: List[str] | None = None) -> int:
    args = argv or sys.argv
    usage = "python .agent/skills/skills-evaluator/scripts/skills_evaluator.py <log_file_path> [--format json|markdown]"

    if len(args) < 2:
        result = {
            "status": "error",
            "log_path": "",
            "statistics": {},
            "message": "缺少 Log 檔案路徑參數",
            "suggestion": "請提供 Log 檔案路徑，例如：python .agent/skills/skills-evaluator/scripts/skills_evaluator.py doc/logs/Idx-012_log.md",
            "usage": usage,
        }
        result = validate_output_schema(result, "skills_evaluator")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    log_path = Path(args[1])
    output_format = _parse_format(args)

    if not log_path.exists():
        result = {
            "status": "error",
            "log_path": str(log_path),
            "statistics": {},
            "message": f"Log 檔案不存在：{log_path}",
            "suggestion": "請確認路徑正確；active workflow / 治理 / 專案功能任務的 Log 一律使用 doc/logs。",
            "usage": usage,
        }
        result = validate_output_schema(result, "skills_evaluator")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    try:
        log_content = log_path.read_text(encoding="utf-8")
    except Exception as exc:
        result = {
            "status": "error",
            "log_path": str(log_path),
            "statistics": {},
            "message": f"無法讀取 Log 檔案：{exc}",
            "suggestion": "請確認檔案權限正確，或改用文字編輯器檢查檔案內容。",
            "usage": usage,
        }
        result = validate_output_schema(result, "skills_evaluator")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    records = parse_skills_execution_report(log_content)
    if not records:
        result = {
            "status": "warning",
            "log_path": str(log_path),
            "statistics": {
                "total_executions": 0,
                "success_rate": 0.0,
                "status_distribution": {},
                "skill_counts": {},
                "failed_skills": [],
                "summary": "未找到 skills 執行記錄",
            },
            "message": "Log 中未找到 SKILLS_EXECUTION_REPORT 段落",
            "suggestion": "請確認 Log 檔案格式正確，或補上 SKILLS_EXECUTION_REPORT 表格後再執行。",
            "usage": usage,
        }
        result = validate_output_schema(result, "skills_evaluator")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    stats = compute_statistics(records)
    if output_format == "markdown":
        print(generate_markdown_report(stats), end="")
        return 0

    result = {"status": "pass", "log_path": str(log_path), "statistics": stats, "summary": stats.get("summary", "")}
    result = validate_output_schema(result, "skills_evaluator")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


__all__ = [
    "validate_output_schema",
    "parse_skills_execution_report",
    "compute_statistics",
    "generate_markdown_report",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
