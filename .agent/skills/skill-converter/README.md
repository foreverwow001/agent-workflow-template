# Skill Converter

內部 toolchain package。

## 用途

提供 `github_explorer` 下載後的轉換流程：加入中文 header、套用專案慣例、更新 local overlay index，並把外部技能整理成 `.agent/skills_local/` 下的 package-only 落點。

## Canonical 結構

- canonical script: `.agent/skills/skill-converter/scripts/skill_converter.py`

## 備註

這不是主要給使用者直接呼叫的 skill 入口；預設由 `github_explorer` 內部調用。
