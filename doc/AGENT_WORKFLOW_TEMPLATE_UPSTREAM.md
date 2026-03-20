# Template Repo 回推建議（不含 portable）

本文件目的：把本 repo（Ivyhousetw-META）已落地且穩定的 dev-team workflow / skills 強化，整理成可回推到 template repo（`foreverwow001/agent-workflow-template`）的「最小可行同步包」。

> ✅ 依使用者要求：**一鍵復原/自檢模組（portable）不回推**。

---

## 1) 建議回推的內容（高優先）

### A. Skills 系統強化（建議整包同步）
目標：讓 template repo 在「Plan 驗證、變更統計 Gate、skills manifest、skills 執行統計」上具備機械化能力。

建議同步：
- `.agent/skills/plan-validator/`：Plan Gate（必跑）
- `.agent/skills/git-stats-reporter/`：Maintainability/UI-UX Gate 判定依據
- `.agent/skills/manifest-updater/` + `.agent/state/skills/skill_manifest.json`：skills 清單同步（canonical manifest）
- `.agent/skills/skills-evaluator/`：從 Log 產生 skills 成功率/失敗統計
- `.agent/skills/github-explorer/`：安全的外部技能搜尋/預覽/下載流程（external/local install target: `.agent/skills_local/**`）
- `.agent/skills/skill-converter/`：下載後轉換流水線（overlay index target: `.agent/state/skills/INDEX.local.md`）
- `.agent/config/skills/skill_whitelist.json`：白名單 canonical 檔
- `.agent/skills/schemas/**`：skills JSON output schema（graceful degradation；保留 public path）
- `.agent/skills/INDEX.md`：builtin core 技能索引文件（external/local additions 改寫 `.agent/state/skills/INDEX.local.md`）

### B. Workflow 合約文件（建議同步）
目標：template repo 的「Gate/證據鏈/Role Selection/Cross-QA」可直接沿用。

建議同步：
- `.agent/workflows/AGENT_ENTRY.md`：唯一入口與 READ_BACK_REPORT Gate
- `.agent/workflows/dev-team.md`：Plan → Approve → Role Selection → Execute → QA → Log → Close 的主流程
- `.agent/roles/*.md`：planner/engineer/qa/coordinator/domain_expert/security（如有專案特定 expert，應在 downstream repo 自行擴充，而不是保留舊專案角色）

### C. VS Code 系統檔（建議同步）
目標：把「終端注入/監控」與 deterministic gates 的規範落地。

建議同步：
- `.agent/VScode_system/**`

### D. Template 初始化腳本（視 template 現況擇一同步）
目標：讓 template repo 的一鍵初始化能建立完整 `.agent/` 結構與必備檔案。

建議同步：
- `.agent/scripts/setup_workflow.sh`
- `.agent/scripts/run_codex_template.sh`

### E. VS Code 周邊（A+B：終端管理/編排 + sendText/監測）（建議同步）
目標：讓新專案從 template 開箱就具備「PTY 主路徑 + 條件式 fallback」能力。

建議同步：
- `.agent/runtime/tools/vscode_terminal_pty/**`：local VS Code extension（workflow 唯一主路徑）
- `.agent/runtime/tools/vscode_terminal_fallback/**`：條件式 legacy fallback adapter
- 相關套件的安裝命令或 symlink 腳本
- `.vscode/**`：workspace settings / tasks / extension recommendations（包含 Copilot terminal command debug 開關）

> 補充：injector / monitor / orchestrator 已在 2026-03-13 cleanup 中自 template repo 移除；若要保留其設計脈絡，請改用 maintainer 文檔描述來源，不要再把它們當同步資產。

---

## 2) 不回推的內容（本次明確排除）

- portable 自檢模組：目前 repo 未內建，且依使用者指示不回推
- `.agent/logs/**`、`.agent/plans/**`：稽核/任務紀錄屬於 repo 私有，避免污染 template
- `.agent/active_sessions.json`、`.agent/execution_log.jsonl`：runtime 狀態檔

---

## 3) 同步方式（目前無內建一鍵腳本）

目前 repo **沒有**內建 `sync_agent_workflow_to_template.py` 這類一鍵同步腳本。

建議操作流程：
1. 在本機 clone `foreverwow001/agent-workflow-template` 到某個資料夾
2. 依本文件列出的建議同步清單，手動挑選要回推的檔案或資料夾
3. 用 `git diff`、`cp -r`、`rsync` 或編輯器比對工具同步變更
4. 到 template repo 內跑 lint/tests（若有）並開 PR

---

## 4) 驗收清單（template repo）

- ✅ `AGENT_ENTRY.md` 的 READ_BACK_REPORT Gate 可正常要求「必讀檔案逐檔閱讀」
- ✅ `dev-team.md` 內的 Role Selection / Cross-QA / Skills Execution Gate 說明完整
- ✅ `plan-validator/scripts/plan_validator.py` 能對 template 的 plan 檔案通過/失敗給出明確 JSON
- ✅ `manifest-updater/scripts/manifest_updater.py --check` 在 template repo 可正常運作
