---
name: test-runner
description: "Use when running pytest from the project root, validating Python changes with automated tests, or collecting a JSON test summary for workflow logs."
---

# Test Runner

## 用途

在專案根目錄執行 `pytest`，並輸出 JSON 格式測試摘要。

## Canonical 結構

- canonical script: `.agent/skills/test-runner/scripts/test_runner.py`

## 使用方式

```bash
python .agent/skills/test-runner/scripts/test_runner.py [test_path]
```
