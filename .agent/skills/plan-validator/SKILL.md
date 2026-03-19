---
name: plan-validator
description: "Use when validating a Plan document, checking required sections and EXECUTION_BLOCK fields, or running the Plan gate canonical script."
---

# Plan Validator

## 用途

驗證 Plan 文件是否包含必要段落與 `EXECUTION_BLOCK` 關鍵欄位。

## Canonical 結構

- canonical script: `.agent/skills/plan-validator/scripts/plan_validator.py`

## 使用方式

```bash
python .agent/skills/plan-validator/scripts/plan_validator.py <plan_file_path>
```
