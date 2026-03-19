---
name: git-stats-reporter
description: "Use when parsing git diff --numstat output, calculating line-change totals, or deciding whether Maintainability and UI/UX gates should trigger."
---

# Git Stats Reporter

## 用途

解析 `git diff --numstat` 輸出，產生變更統計與 Gate 觸發建議。

## Canonical 結構

- canonical script: `.agent/skills/git-stats-reporter/scripts/git_stats_reporter.py`

## 使用方式

```bash
git diff --numstat > /tmp/diff_stats.txt
python .agent/skills/git-stats-reporter/scripts/git_stats_reporter.py /tmp/diff_stats.txt
```
