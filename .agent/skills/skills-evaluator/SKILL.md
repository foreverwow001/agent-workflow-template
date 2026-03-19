---
name: skills-evaluator
description: "Use when parsing SKILLS_EXECUTION_REPORT tables from logs, calculating execution statistics, or generating JSON or Markdown summaries of skill outcomes."
---

# Skills Evaluator

## 用途

解析 Log 的 `SKILLS_EXECUTION_REPORT` 表格，產生技能執行統計與成功率摘要。

## Canonical 結構

- canonical script: `.agent/skills/skills-evaluator/scripts/skills_evaluator.py`

## 使用方式

```bash
python .agent/skills/skills-evaluator/scripts/skills_evaluator.py <log_file_path> [--format json|markdown]
```
