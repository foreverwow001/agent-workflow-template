# Tool Usage Guide

> 用途：記錄在這個 workflow template 中已驗證可用的 CLI 使用方式，避免角色文件引用不存在的操作說明。

## 原則

- 先跑 `<tool> --help`，再決定參數。
- 第一次使用新工具時，先做最小可行測試。
- 不要憑印象猜測參數名稱。
- 若確認了穩定用法，再把指令補回本檔。

## Codex CLI

常見用法：

```bash
codex exec "請扮演 QA，審查 path/to/file.py"
codex review --uncommitted
```

注意：

- `codex exec` 直接接受 prompt 字串。
- `codex review --uncommitted` 適合審查目前未提交變更。

## Python Skills

常見 canonical scripts：

```bash
python .agent/skills/code-reviewer/scripts/code_reviewer.py <file_path|directory|diff>
python .agent/skills/test-runner/scripts/test_runner.py [test_path]
python .agent/skills/plan-validator/scripts/plan_validator.py <plan_file_path>
python .agent/skills/skills-evaluator/scripts/skills_evaluator.py <log_file_path>
```

## 新工具探索流程

若工具尚未出現在本檔，請先依下列順序操作：

1. 執行 `<tool> --help`
2. 若有子命令，再執行 `<tool> <subcommand> --help`
3. 先做最小測試
4. 確認成功後，再把穩定用法記回本檔

延伸 SOP：見 [explore-cli-tool skill](../.agent/skills/explore-cli-tool/SKILL.md)
