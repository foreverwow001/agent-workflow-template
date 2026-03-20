# Curated Core V1 Minimal Release Candidate Batch

> 建立日期：2026-03-19
> 狀態：Active Supporting Doc
> 用途：把 `curated-core-v1` 從 `warn` 收斂到 `pass` 所需的最小 release-candidate 補集固定成可直接執行的批次定義。

---

## Summary

- base_source_ref: `9b8a55234db835dea2ee00be18bede8546c02d0d`
- batch_type: `minimal-worktree-only-landing-batch`
- include_pattern_count: `17`
- copied_file_count: `68`
- validation_method: `在隔離 temporary clone 上，以 base source ref 為基底，只加入本文件列出的 17 個 include patterns 對應檔案後，再執行 landing-checklist 與 export materialize 驗證`
- landing_checklist_status_after_batch: `pass`
- materialize_status_after_batch: `pass`
- materialized_path_count_after_batch: `87`

## Why This Is The Minimal Batch

目前 `curated-core-v1-landing-checklist` 顯示：

- `missing_include_patterns = 0`
- `worktree_only_include_patterns = 17`

因此只要把這 17 個 `worktree-only` include patterns 一次落進下一個 source ref，`curated-core-v1` 就會從 `warn` 轉成 `pass`；不需要再加其他 pattern，也不需要改動 export profile。

## Batch Contents

### 1. `core_ownership_manifest.yml`

- `core_ownership_manifest.yml`

### 2. `.agent/runtime/**`

- `.agent/runtime/scripts/devcontainer/post_create.sh`
- `.agent/runtime/scripts/portable_smoke/workflow_core_smoke.py`
- `.agent/runtime/scripts/sendtext_bridge_client.py`
- `.agent/runtime/scripts/vscode/install_terminal_orchestrator.sh`
- `.agent/runtime/scripts/vscode/install_terminal_tooling.sh`
- `.agent/runtime/scripts/vscode/workflow_preflight_check.py`
- `.agent/runtime/scripts/vscode/workflow_preflight_fallback.py`
- `.agent/runtime/scripts/vscode/workflow_preflight_pty.py`
- `.agent/runtime/scripts/workflow_core_contracts.py`
- `.agent/runtime/scripts/workflow_core_export_landing_checklist.py`
- `.agent/runtime/scripts/workflow_core_export_materialize.py`
- `.agent/runtime/scripts/workflow_core_manifest.py`
- `.agent/runtime/scripts/workflow_core_projection.py`
- `.agent/runtime/scripts/workflow_core_release_create.py`
- `.agent/runtime/scripts/workflow_core_release_precheck.py`
- `.agent/runtime/scripts/workflow_core_release_publish_notes.py`
- `.agent/runtime/scripts/workflow_core_sync_apply.py`
- `.agent/runtime/scripts/workflow_core_sync_precheck.py`
- `.agent/runtime/scripts/workflow_core_sync_verify.py`
- `.agent/runtime/tools/vscode_terminal_fallback/README.md`
- `.agent/runtime/tools/vscode_terminal_fallback/extension.js`
- `.agent/runtime/tools/vscode_terminal_fallback/package.json`
- `.agent/runtime/tools/vscode_terminal_pty/README.md`
- `.agent/runtime/tools/vscode_terminal_pty/codex_pty_bridge.py`
- `.agent/runtime/tools/vscode_terminal_pty/extension.js`
- `.agent/runtime/tools/vscode_terminal_pty/package.json`

### 3. `.agent/roles/security.md`

- `.agent/roles/security.md`

### 4. `.agent/skills/code-reviewer/**`

- `.agent/skills/code-reviewer/SKILL.md`
- `.agent/skills/code-reviewer/references/review_checklist.md`
- `.agent/skills/code-reviewer/scripts/code_reviewer.py`

### 5. `.agent/skills/doc-generator/**`

- `.agent/skills/doc-generator/SKILL.md`
- `.agent/skills/doc-generator/scripts/doc_generator.py`

### 6. `.agent/skills/test-runner/**`

- `.agent/skills/test-runner/SKILL.md`
- `.agent/skills/test-runner/scripts/test_runner.py`

### 7. `.agent/skills/plan-validator/**`

- `.agent/skills/plan-validator/SKILL.md`
- `.agent/skills/plan-validator/scripts/plan_validator.py`

### 8. `.agent/skills/git-stats-reporter/**`

- `.agent/skills/git-stats-reporter/SKILL.md`
- `.agent/skills/git-stats-reporter/scripts/git_stats_reporter.py`

### 9. `.agent/skills/skills-evaluator/**`

- `.agent/skills/skills-evaluator/SKILL.md`
- `.agent/skills/skills-evaluator/scripts/skills_evaluator.py`

### 10. `.agent/skills/project-planner/**`

- `.agent/skills/project-planner/SKILL.md`
- `.agent/skills/project-planner/references/estimation-and-risk.md`
- `.agent/skills/project-planner/references/planning-framework.md`
- `.agent/skills/project-planner/references/task-sizing-and-dependencies.md`

### 11. `.agent/skills/deep-research/**`

- `.agent/skills/deep-research/SKILL.md`
- `.agent/skills/deep-research/references/research-process.md`
- `.agent/skills/deep-research/references/source-policy-and-output.md`

### 12. `.agent/skills/fact-checker/**`

- `.agent/skills/fact-checker/SKILL.md`
- `.agent/skills/fact-checker/references/verdict-and-context.md`
- `.agent/skills/fact-checker/references/verification-process.md`

### 13. `.agent/skills/refactor/**`

- `.agent/skills/refactor/SKILL.md`
- `.agent/skills/refactor/references/refactor-python.md`
- `.agent/skills/refactor/references/refactor-smells.md`
- `.agent/skills/refactor/references/refactor-typescript-javascript.md`
- `.agent/skills/refactor/references/refactor-workflow.md`

### 14. `.agent/skills/python-expert/**`

- `.agent/skills/python-expert/SKILL.md`
- `.agent/skills/python-expert/references/python-correctness.md`
- `.agent/skills/python-expert/references/python-performance.md`
- `.agent/skills/python-expert/references/python-style-and-documentation.md`
- `.agent/skills/python-expert/references/python-type-safety.md`

### 15. `.agent/skills/typescript-expert/**`

- `.agent/skills/typescript-expert/SKILL.md`
- `.agent/skills/typescript-expert/references/typescript-api-and-testing.md`
- `.agent/skills/typescript-expert/references/typescript-javascript-core.md`
- `.agent/skills/typescript-expert/references/typescript-react-patterns.md`

### 16. `.agent/skills/security-review-helper/**`

- `.agent/skills/security-review-helper/SKILL.md`
- `.agent/skills/security-review-helper/references/security_checklist.md`

### 17. `doc/logs/Idx-000_log.template.md`

- `doc/logs/Idx-000_log.template.md`

## Validation Result

在隔離驗證中，以上 17 個 include patterns 與 68 個檔案一起落地後，結果為：

- landing checklist: `pass`
- ready_include_patterns: `26`
- worktree_only_include_patterns: `0`
- missing_include_patterns: `0`
- export materialize: `pass`
- materialized selected paths: `87`

## Release Use

下一個真正的 release candidate 只要完整包含本批次，即可預期：

1. `workflow_core_export_landing_checklist.py` 對 `curated-core-v1` 回傳 `pass`
2. `workflow_core_export_materialize.py` 對 `curated-core-v1` 回傳 `pass`
3. 第一波 curated export scope 不再停留在 `worktree-only` landing gap
