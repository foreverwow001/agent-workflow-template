---
name: github-explorer
description: "Use when safely searching, previewing, downloading, and rolling back external skill scripts from approved GitHub repositories."
---

# GitHub Explorer

## 用途

提供外部技能的安全搜尋、預覽、下載、轉換與回滾流程。下載後的 external/local package 會安裝到 `.agent/skills_local/`，並同步更新 `.agent/state/skills/INDEX.local.md`。

## Canonical 結構

- canonical script: `.agent/skills/github-explorer/scripts/github_explorer.py`

## 使用方式

```bash
python .agent/skills/github-explorer/scripts/github_explorer.py <command>
```
