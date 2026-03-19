---
name: code-reviewer
description: "Use when reviewing Python files or Python code changes for security, syntax, maintainability, style regressions, review checklists, or when validating downloaded external scripts before adoption."
---

# Code Reviewer

## 用途

對 Python 檔案、Python 目錄、或 git/unified diff 代表的 Python 變更做自動化靜態審查，並搭配人工 checklist 做完整 review。自動檢查包含：

- API Key 洩漏
- Python 語法錯誤
- `subprocess(..., shell=True)` / `eval` / `exec` 這類高風險模式
- 檔案是否過長
- 函式是否過長
- 行長與尾端空白
- `bare except` 這類可維護性風險
- 檔案開頭是否缺少繁體中文用途註釋

人工 review 則補足這些面向：

- Correctness / edge cases
- Error handling
- Test coverage / regression risk
- Maintainability / readability

## Canonical 結構

- canonical script: `.agent/skills/code-reviewer/scripts/code_reviewer.py`
- review checklist: `.agent/skills/code-reviewer/references/review_checklist.md`

## Review Workflow

1. 先對目標 Python 檔案執行 canonical script。
	- 若是目錄：遞迴掃描其中所有 `*.py`
	- 若是 diff：只審查 diff 中命中的 Python 檔案
2. 若結果是 `fail`：優先處理 security / syntax 類 findings，再決定是否繼續人工 review。
3. 若結果是 `warning`：把 script findings 與 checklist 一起整合成 review comment。
4. 若結果是 `pass`：仍需用 checklist 補看 correctness、測試缺口與可維護性。

## Findings 分級

- `fail`：會造成安全或可執行性風險，應先修正。
- `warning`：屬於 maintainability / style / review hygiene 問題，通常不一定 blocking，但應說明是否建議修正。
- `pass`：腳本未發現明顯靜態問題，仍不代表功能邏輯一定正確。

## 使用方式

```bash
python .agent/skills/code-reviewer/scripts/code_reviewer.py <file_path>

# review 整個 Python 目錄
python .agent/skills/code-reviewer/scripts/code_reviewer.py src/

# review unified diff / git diff 輸出
git diff --no-color > /tmp/changes.diff
python .agent/skills/code-reviewer/scripts/code_reviewer.py /tmp/changes.diff .

# 直接 review staged changes
python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff --staged .
python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff --cached .

# 直接 review 某段 git range
python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff main..HEAD .
```

## 輸出解讀

- `issues`: 逐條 findings，含 `type`、`line`、`message`、`severity`
- `summary`: 各類 issue 計數
- `status=fail`: 代表至少存在一個 critical finding
- 目錄 / diff 模式會回傳 `results[]`，每個元素是一個單檔 review 結果
