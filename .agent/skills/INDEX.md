# Agent Skills 索引

> 本檔是 `.agent/skills/` 的**索引文件**，不是單一 skill 的入口。
> 若要看後續目錄調整方向，請先讀：`./RESTRUCTURE_BLUEPRINT.md`

目前這個資料夾已進入「package-only」階段：

- 文件型 skill 已完成 package 化
- 核心工具型 skill 已完成 package 化，root shim 已移除
- toolchain 已完成 canonical package 化：`github-explorer/`、`skill-converter/`、`manifest-updater/`
- `INDEX.md` 現在只承擔 builtin core catalog；external/local skill additions 改寫到 `.agent/state/skills/INDEX.local.md`
- external/local skill package 安裝目的地已改到 `.agent/skills_local/`
- shared helper code 維持在 `_shared/`，runtime state 與 project-local policy 已拆到 `.agent/state/skills/` / `.agent/config/skills/`；schema 仍維持 `schemas/` public path

---

## 📦 可用技能一覽

以下表格只列出 builtin core packages。若透過 `github-explorer` 安裝 external/local skill，package 會落在 `.agent/skills_local/`，並由 `.agent/state/skills/INDEX.local.md` 承接 overlay catalog。

| 技能名稱 | 用途 | 調用指令 |
|----------|------|----------|
| `code-reviewer` | 代碼品質審查 | 閱讀 `.agent/skills/code-reviewer/SKILL.md`；執行 `python .agent/skills/code-reviewer/scripts/code_reviewer.py <file_path|directory|diff>` 或 `python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff ...` |
| `doc-generator` | 文件自動生成 | 閱讀 `.agent/skills/doc-generator/SKILL.md`；執行 `python .agent/skills/doc-generator/scripts/doc_generator.py <file_path>` |
| `test-runner` | 測試執行器 | 閱讀 `.agent/skills/test-runner/SKILL.md`；執行 `python .agent/skills/test-runner/scripts/test_runner.py [test_path]` |
| `github-explorer` | GitHub 技能搜尋與下載 | 閱讀 `.agent/skills/github-explorer/SKILL.md`；執行 `python .agent/skills/github-explorer/scripts/github_explorer.py <command>` |
| `skill-converter` | 技能轉換流水線 | 閱讀 `.agent/skills/skill-converter/README.md`；預設由 github_explorer 內部調用 |
| `plan-validator` | Plan 格式驗證 | 閱讀 `.agent/skills/plan-validator/SKILL.md`；執行 `python .agent/skills/plan-validator/scripts/plan_validator.py <plan_file_path>` |
| `git-stats-reporter` | Git 變更統計與 Gate 觸發 | 閱讀 `.agent/skills/git-stats-reporter/SKILL.md`；執行 `python .agent/skills/git-stats-reporter/scripts/git_stats_reporter.py <diff_file_path>` |
| `manifest-updater` | Skills manifest 同步 | 閱讀 `.agent/skills/manifest-updater/SKILL.md`；執行 `python .agent/skills/manifest-updater/scripts/manifest_updater.py --check` / `--sync` |
| `skills-evaluator` | Skills 執行統計與回饋 | 閱讀 `.agent/skills/skills-evaluator/SKILL.md`；執行 `python .agent/skills/skills-evaluator/scripts/skills_evaluator.py <log_file_path> [--format json|markdown]` |
| `security-review-helper` | Security Review intake/checklist 輔助 | 閱讀 `.agent/skills/security-review-helper/SKILL.md` |
| `refactor` | 行為不變的既有程式碼重構 | 閱讀 `.agent/skills/refactor/SKILL.md` |
| `typescript-expert` | TypeScript / JavaScript / React / Node 開發標準 | 閱讀 `.agent/skills/typescript-expert/SKILL.md` |
| `python-expert` | Python correctness / type safety / performance / style 指南 | 閱讀 `.agent/skills/python-expert/SKILL.md` |
| `project-planner` | 複雜任務拆解、依賴、估時與風險規劃 | 閱讀 `.agent/skills/project-planner/SKILL.md` |
| `deep-research` | Coordinator 的研究整合與來源整理 | 閱讀 `.agent/skills/deep-research/SKILL.md` |
| `fact-checker` | Coordinator 的具體 claim 驗證 | 閱讀 `.agent/skills/fact-checker/SKILL.md` |
| `explore-cli-tool` | 新 CLI 工具探索 SOP | 閱讀 `.agent/skills/explore-cli-tool/SKILL.md` |
| `persistent-terminal` | 長效 CLI session 管理原則 | 閱讀 `.agent/skills/persistent-terminal/SKILL.md` |
| `codex-collaboration-bridge` | IDE Agent 與 Codex CLI 協作橋接 | 閱讀 `.agent/skills/codex-collaboration-bridge/SKILL.md` |

---

## 🔍 技能詳細說明

### 1. code-reviewer

**功能**：靜態分析 Python 檔案 / 目錄 / diff，檢查 security smell、語法、maintainability 與基本 style 問題。

**canonical package**：`.agent/skills/code-reviewer/SKILL.md`

**調用方式**：
```bash
python .agent/skills/code-reviewer/scripts/code_reviewer.py <file_path>

# 目錄
python .agent/skills/code-reviewer/scripts/code_reviewer.py src/

# diff 檔案
python .agent/skills/code-reviewer/scripts/code_reviewer.py /tmp/changes.diff .

# 直接 git diff
python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff --staged .
python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff --cached .
python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff main..HEAD .
```

**輸出格式**：JSON
```json
{
  "status": "pass | warning | fail",
  "file": "path/to/file.py",
  "line_count": 123,
  "issues": [
    {"type": "api_key_leak", "line": 10, "message": "..."}
  ],
  "summary": {
    "api_key_leak": 0,
    "file_too_long": 0,
    "missing_chinese_comment": 0
  }
}
```

---

### 2. doc-generator

**功能**：從 Python 檔案中提取 docstring，自動產生 Markdown 格式說明文件。

**canonical package**：`.agent/skills/doc-generator/SKILL.md`

**調用方式**：
```bash
python .agent/skills/doc-generator/scripts/doc_generator.py <file_path>
```

**輸出格式**：Markdown 純文字

---

### 3. test-runner

**功能**：在專案根目錄執行 `pytest`，擷取結果並以 JSON 格式回報。

**canonical package**：`.agent/skills/test-runner/SKILL.md`

**調用方式**：
```bash
python .agent/skills/test-runner/scripts/test_runner.py [test_path]
```

**輸出格式**：JSON
```json
{
  "status": "pass | fail | no_tests | error",
  "project_root": "/path/to/project",
  "passed": 5,
  "failed": 2,
  "errors": 0,
  "output": "..."
}
```

---

### 4. github-explorer

**功能**：從 GitHub 搜尋並下載外部技能，具備安全預覽機制；external/local package 會安裝到 `.agent/skills_local/`，並更新 `.agent/state/skills/INDEX.local.md`。

**canonical package**：`.agent/skills/github-explorer/SKILL.md`

**調用方式**：
```bash
# 搜尋技能
python .agent/skills/github-explorer/scripts/github_explorer.py search <keyword>

# 預覽技能內容 (下載前必做)
python .agent/skills/github-explorer/scripts/github_explorer.py preview <owner/repo> [skill_path]

# 下載技能 (需加 --confirm 確認)
python .agent/skills/github-explorer/scripts/github_explorer.py download <owner/repo> <file_path> --confirm

# 列出本地技能
python .agent/skills/github-explorer/scripts/github_explorer.py list
```

**安全機制**：
1. ⚠️ 下載前**必須**先執行 `preview` 查看內容
2. ⚠️ 下載時**必須**加上 `--confirm` 參數確認
3. ✅ 下載後自動執行 `code-reviewer` canonical script 安全掃描
4. 🚨 若掃描發現問題，已下載檔案會被自動刪除

**輸出格式**：JSON
```json
{
  "status": "success | error | blocked",
  "message": "操作結果說明",
  "results": []
}
```

---

### 5. plan-validator

**功能**：驗證 Plan 文件是否包含必要段落與 `EXECUTION_BLOCK` 關鍵欄位。

**canonical package**：`.agent/skills/plan-validator/SKILL.md`

**調用方式**：
```bash
python .agent/skills/plan-validator/scripts/plan_validator.py doc/plans/Idx-XXX_*.md
```

**輸出格式**：JSON（status 小寫）
```json
{
  "status": "pass | fail | error",
  "plan_path": "doc/plans/Idx-XXX_*.md",
  "missing_sections": [],
  "format_errors": [],
  "summary": "Plan 驗證通過"
}
```

---

### 6. git-stats-reporter

**功能**：解析 `git diff --numstat` 輸出，產生變更統計並輸出 Gate 觸發建議（Maintainability / UI/UX）。

**canonical package**：`.agent/skills/git-stats-reporter/SKILL.md`

**調用方式**：
```bash
git diff --numstat > /tmp/diff_stats.txt
python .agent/skills/git-stats-reporter/scripts/git_stats_reporter.py /tmp/diff_stats.txt
```

**輸出格式**：JSON（status 小寫）
```json
{
  "status": "pass | error",
  "total_files_changed": 3,
  "total_lines_added": 10,
  "total_lines_deleted": 2,
  "total_lines_changed": 12,
  "affected_paths": ["app.py", "ui/foo.py"],
  "triggers": { "maintainability_gate": false, "ui_ux_gate": true },
  "summary": "3 files, +10/-2 lines"
}
```

---

### 7. manifest-updater

**功能**：同步 skills manifest 的 builtin skills 清單，並更新 canonical `.agent/state/skills/skill_manifest.json`。

**canonical package**：`.agent/skills/manifest-updater/SKILL.md`

**調用方式**：
```bash
# 僅檢查（不寫入）
python .agent/skills/manifest-updater/scripts/manifest_updater.py --check

# 寫入更新
python .agent/skills/manifest-updater/scripts/manifest_updater.py --sync
```

**輸出格式**：JSON（status 小寫）

---

### 8. skills-evaluator

**功能**：解析 Log 的 `## 🛠️ SKILLS_EXECUTION_REPORT` 表格，產生統計報告（執行次數、狀態分布、失敗清單、成功率）。

**canonical package**：`.agent/skills/skills-evaluator/SKILL.md`

**調用方式**：
```bash
# JSON（預設）
python .agent/skills/skills-evaluator/scripts/skills_evaluator.py doc/logs/Idx-XXX_log.md

# Markdown
python .agent/skills/skills-evaluator/scripts/skills_evaluator.py doc/logs/Idx-XXX_log.md --format markdown
```

**輸出格式**：JSON（預設）或 Markdown（--format markdown）

---

### Shared Metadata

**canonical shared metadata**：

- `.agent/state/skills/skill_manifest.json`
- `.agent/config/skills/skill_whitelist.json`
- `.agent/skills/_shared/__init__.py`

**public metadata surface**：

- `.agent/state/skills/skill_manifest.json`
- `.agent/config/skills/skill_whitelist.json`
- `.agent/skills/schemas/*.json`

說明：`_shared/` 現在只保留 path resolver 與 shared helper code；manifest 寫入改走 overlay state，whitelist 改走 project-local config，schema 路徑暫時維持在 root `schemas/`，避免影響既有 skill output validator 與文件引用。

---

### 9. security-review-helper

**功能**：提供 Security Reviewer 固定 intake 順序、攻擊面盤點表、finding 假說模板、Severity/Confidence 準則與最終輸出骨架，降低安全審查的執行摩擦。

**使用方式**：
```bash
# 這是文件型 skill，直接閱讀內容後依序執行
cat .agent/skills/security-review-helper/SKILL.md

# 詳細 checklist / evidence rubric
cat .agent/skills/security-review-helper/references/security_checklist.md
```

**適用時機**：
- 已命中 Security Review trigger
- user / Coordinator 明確要求安全審查
- Security Reviewer 需要先確認 Plan 的 trigger 欄位是否已回填

**重要限制**：
- 本 helper 不是新的 trigger/gate 規格來源
- `security_review_required`、`security_review_trigger_source`、`security_review_trigger_matches` 仍以 `.agent/workflows/AGENT_ENTRY.md` 第 3 節為準

---

### 10. refactor

**功能**：提供 Engineer 在既有程式碼上做 behavior-preserving refactor 時的安全流程、code smell 對照與停止條件。

**使用方式**：
```bash
cat .agent/skills/refactor/SKILL.md
cat .agent/skills/refactor/references/refactor-workflow.md
cat .agent/skills/refactor/references/refactor-smells.md
cat .agent/skills/refactor/references/refactor-typescript-javascript.md
cat .agent/skills/refactor/references/refactor-python.md
```

**適用時機**：
- 需要拆大函式、消除重複、改善命名或模組邊界
- User / Planner 明確要求 refactor / cleanup
- 不應改變外部行為，只改善結構

---

### 11. typescript-expert

**功能**：提供 Engineer 在 TypeScript / JavaScript / React / Node 任務中的實作標準，涵蓋命名、不可變性、錯誤處理、async、型別安全、API 與測試。

**使用方式**：
```bash
cat .agent/skills/typescript-expert/SKILL.md
cat .agent/skills/typescript-expert/references/typescript-javascript-core.md
cat .agent/skills/typescript-expert/references/typescript-react-patterns.md
cat .agent/skills/typescript-expert/references/typescript-api-and-testing.md
```

**適用時機**：
- 新增或修改 `.ts` / `.tsx` / `.js` / `.jsx`
- 撰寫 React component、hook、Node service、API handler
- 需要更清楚的型別與前後端邊界

---

### 12. python-expert

**功能**：提供 Engineer 在 Python 任務中的優先級明確指南，聚焦 correctness、type safety、performance、style 與 documentation。

**使用方式**：
```bash
cat .agent/skills/python-expert/SKILL.md
cat .agent/skills/python-expert/references/python-correctness.md
cat .agent/skills/python-expert/references/python-type-safety.md
cat .agent/skills/python-expert/references/python-performance.md
cat .agent/skills/python-expert/references/python-style-and-documentation.md
```

**適用時機**：
- 新增或修改 `.py`
- 撰寫 Python script、module、CLI、service
- 需要補 type hints、error handling、docstring 或 Pythonic 寫法

---

### 13. project-planner

**功能**：幫助 Planner 把複雜任務拆成 milestones、phases、task dependencies、估時與風險，避免只產出高層口號式 Spec。

**使用方式**：
```bash
cat .agent/skills/project-planner/SKILL.md
cat .agent/skills/project-planner/references/planning-framework.md
cat .agent/skills/project-planner/references/task-sizing-and-dependencies.md
cat .agent/skills/project-planner/references/estimation-and-risk.md
```

**適用時機**：
- 任務涉及多檔案、多階段或多角色協作
- 需要 phase / milestone / dependency / critical path
- 需要估時、buffer 與風險緩解

---

### 14. deep-research

**功能**：提供 Coordinator 在 Research Gate 中做多來源研究整合，並把結果回填到 Plan 的 `RESEARCH & ASSUMPTIONS`。

**使用方式**：
```bash
cat .agent/skills/deep-research/SKILL.md
cat .agent/skills/deep-research/references/research-process.md
cat .agent/skills/deep-research/references/source-policy-and-output.md
```

**適用時機**：
- `research_required: true`
- 需要整合官方來源或 repo 文檔
- 需要在執行前釐清版本、方案或外部能力差異

**deterministic trigger**：
- `research_required: true`
- 依賴檔案變更
- Goal / SPEC / 研究摘要含 `research`、`investigate`、`compare`、`evaluate`、`migration`、`version compatibility`、`official docs`、`upstream behavior`
- Plan 需要 repo 外可驗證事實才能成立

---

### 15. fact-checker

**功能**：提供 Coordinator 對單一或少量具體 claim 做 evidence-based 驗證，避免把未核實說法寫進 Plan 或 Gate 決策。

**使用方式**：
```bash
cat .agent/skills/fact-checker/SKILL.md
cat .agent/skills/fact-checker/references/verification-process.md
cat .agent/skills/fact-checker/references/verdict-and-context.md
```

**適用時機**：
- 研究內容含具體 claim、版本號、API capability、數值或安全聲明
- 需要把某個技術說法從「印象」升級成可引用事實

**deterministic trigger**：
- 版本相容性、最低版本、發布/移除/棄用時點
- API capability、支援與否、限制、required configuration
- 數值聲明：配額、限制、timeout、latency、benchmark、size limit、throughput
- 安全、政策、法遵、官方保證、CVE、permission / auth / compliance 聲明
- 平台、作業系統、runtime、provider support matrix 或 environment compatibility 聲明

---

### 16. explore-cli-tool

**功能**：提供首次使用新 CLI 工具時的固定探索順序，避免憑經驗臆測參數導致失敗。

**使用方式**：
```bash
cat .agent/skills/explore-cli-tool/SKILL.md
```

**適用時機**：
- 第一次使用新的 CLI 工具
- 不確定 subcommand / flag 語法
- 想把工具探索步驟標準化

---

### 17. persistent-terminal

**功能**：提供持久化 CLI session 的識別與重用策略，避免每次互動都新開終端。

**使用方式**：
```bash
cat .agent/skills/persistent-terminal/SKILL.md
```

**適用時機**：
- 需要重用 Codex / Claude 等長效 CLI session
- 需要在 agent 重啟後恢復 session 對照

---

### 18. codex-collaboration-bridge

**功能**：描述 IDE Agent 與 Codex CLI 的協作分工，適合把大規模實作交給終端 agent。

**使用方式**：
```bash
cat .agent/skills/codex-collaboration-bridge/SKILL.md
```

**適用時機**：
- 使用者要求用 Codex CLI 執行大規模改碼
- 需要先產出可交付給終端 agent 的 Spec / instruction

---

## 🧭 目錄重構方向

- 目前已完成文件型 skill 與核心工具型 skill 的 package 化
- 所有官方調用已收斂到 package script；root shim 已移除
- 後續重構目標是「一個 skill 一個資料夾，一份 `SKILL.md` 當入口」
- 詳細分類與搬遷規劃見 `./RESTRUCTURE_BLUEPRINT.md`

---

## 🔒 Output Schema Validation（Phase 2）

本 repo 會在 `.agent/skills/schemas/` 內提供 JSON Schema 檔案，供對 skills 輸出做機械化驗證。

- Phase 1：建立 schema 檔案（不強制驗證）
- Phase 2：skills 會在輸出 JSON 前嘗試執行 **optional** schema 驗證（graceful degradation）
  - 若 `jsonschema` 不可用 → 跳過驗證（不影響執行）
  - 若 schema 檔案不存在 → 跳過驗證（不影響執行）
  - 若 schema 驗證失敗 → 在輸出 JSON 加上 `validation_errors` + `suggestion`（**不強制改動原本 status/exit code**）



---

## 🚧 未來技能 (規劃中)

| 技能名稱 | 用途 | 狀態 |
|----------|------|------|
| `security_scan` | 深度安全漏洞掃描 | ⏳ 規劃中 |
| `dependency_check` | 依賴套件版本與安全檢查 | ⏳ 規劃中 |

---

## 📜 使用規範

1. **資安紅線**：技能腳本本身絕對不能包含任何 API Key。
2. **獨立性**：技能腳本應盡量減少對專案核心代碼的依賴。
3. **繁體中文**：所有輸出訊息皆須為繁體中文。
