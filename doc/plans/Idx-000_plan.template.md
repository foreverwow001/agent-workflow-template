# Plan: Idx-NNN

**Index**: Idx-NNN
**Created**: YYYY-MM-DD
**Planner**: @AgentName

---

## 🎯 目標

[任務目標描述]

---

## 📋 SPEC

### Goal
[任務的主要目標，一句話總結]

### Non-goals
[明確排除的範圍，避免 scope 漂移]
- ❌ 不做：[具體排除項目]

### Acceptance Criteria
[可驗收的條件清單]
1. ✅ [驗收條件 1]
2. ✅ [驗收條件 2]

### Edge cases
[需要處理的邊界情況]
- [邊界情況 1] → [處理方式]

---

## 🔍 RESEARCH & ASSUMPTIONS

> Planner 在此用 `research_required: true/false` 做出明確標記。
> 若 `research_required: true`，則必須補齊 Sources/Assumptions（Link-required；無來源則標註 `RISK: unverified`）。

research_required: [true|false]

### Sources
[僅限 user 提供的官方連結或 repo 內文檔]
- [官方文檔連結]
- [repo 內參考文件路徑]

### Assumptions
[若無可驗證來源，列出假設並標注風險]
- ⚠️ RISK: unverified - [假設內容]
- ✅ VERIFIED - [已驗證的假設]

---

## 🔒 SCOPE & CONSTRAINTS

### File whitelist
[允許變更的文件/目錄清單]
- `path/to/file.py` - [變更原因]
- `path/to/dir/**` - [批次變更原因]

### Done 定義
[完成條件，用於判定任務是否完成]
1. ✅ [條件 1]
2. ✅ [條件 2]

### Rollback 策略
- **Level**: [L1|L2|L3|L4]
- **前置條件**: [執行前必須滿足的條件]
- **回滾動作**: [具體回滾命令或步驟]

### Max rounds
- **估計**: [預估執行回合數]
- **超過處理**: [超過時的處理方式]

---

## 📁 檔案變更

| 檔案 | 動作 | 說明 |
|------|------|------|
| path/to/file.py | 新增/修改/刪除 | 變更說明 |

---

## 📝 邏輯細節

### 1. [檔案名稱]
[具體修改說明，給 Engineer 足夠的實作指引]

### 2. [檔案名稱]
[具體修改說明]

---

## ⚠️ 注意事項

- **風險提示**：[可能會弄壞的地方]
- **資安考量**：[API Key、敏感資料處理]
- **相依性**：[與其他檔案或功能的關聯]

---

## 🔗 相關資源

- [相關文檔或 Issue]
- [參考資料]

---

## 🔧 執行資訊

<!-- EXECUTION_BLOCK_START -->
# Plan 狀態
plan_created: [YYYY-MM-DD HH:mm:ss]
plan_approved: [YYYY-MM-DD HH:mm:ss]
scope_policy: [strict|flexible]
expert_required: [true|false]
expert_conclusion: [N/A|結論摘要]
security_review_required: [true|false]
security_reviewer_tool: [N/A|待用戶確認: codex-cli|copilot-cli]
security_review_trigger_source: [none|user|coordinator|path-rule|keyword-rule|mixed]
security_review_trigger_matches: []
security_review_start: [N/A|YYYY-MM-DD HH:mm:ss]
security_review_end: [N/A|YYYY-MM-DD HH:mm:ss]
security_review_result: [N/A|PASS|PASS_WITH_RISK|FAIL]
security_review_conclusion: [N/A|結論摘要]
execution_backend_policy: [pty-primary-with-consented-fallback]
scope_exceptions: []

# Engineer 執行
executor_tool: [待用戶確認: codex-cli|copilot-cli]
executor_backend: [ivyhouse_terminal_pty|ivyhouse_terminal_fallback]
monitor_backend: [pty_runtime_monitor|fallback_runtime_monitor|manual_confirmation]
executor_tool_version: [version number]
executor_user: [github-account or email]
executor_start: [執行開始時間]
executor_end: [執行結束時間]
session_id: [terminal session ID if available]
last_change_tool: [codex-cli|copilot-cli]

# QA 執行
qa_tool: [待用戶確認: codex-cli|copilot-cli]
qa_tool_version: [version number]
qa_user: [github-account or email]
qa_start: [QA 開始時間]
qa_end: [QA 結束時間]
qa_result: [PASS|PASS_WITH_RISK|FAIL]
qa_compliance: [✅ 符合|⚠️ 例外：原因]

# 任務注入提醒（Coordinator 派發時不可省略）
# Security Reviewer：必須附上
#   cat .agent/skills/security-review-helper/SKILL.md
#   cat .agent/skills/security-review-helper/references/security_checklist.md
# QA：必須附上至少一條 code-reviewer 命令
#   python .agent/skills/code-reviewer/scripts/code_reviewer.py <file_path|directory|diff>
#   或 python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff --staged|--cached|<base>..<head> .
# 若專案有測試，也必須附上
#   python .agent/skills/test-runner/scripts/test_runner.py [test_path]

# 收尾
log_file_path: [doc/logs/Idx-XXX_log.md]
commit_hash: [pending|hash]
rollback_at: [N/A|YYYY-MM-DD HH:mm:ss]
rollback_reason: [N/A|原因]
rollback_files: [N/A|檔案清單]
<!-- EXECUTION_BLOCK_END -->

> ⚠️ **注意**：`last_change_tool` 只允許 `codex-cli` 或 `copilot-cli`，不含 `GitHub Copilot Chat`（Copilot Chat 固定為 Coordinator，不做實作）。

### 執行模式建議

| 工具 | 適用場景 | 優勢 | 限制 | 需要監控 |
|------|---------|------|------|----------|
| **GitHub Copilot Chat（Coordinator）** | 目標確認、分派、更新 Plan/Log | PTY command surface 協調 + PTY artifact 監控 | 不直接執行/QA（由終端工具負責） | ✅ 是 |
| **Codex CLI（PTY-backed VS Code Terminal）** | 批次檔案操作、模板化工作、大規模重構 | 執行速度快、適合批次 | 需由 Coordinator 透過 PTY 管理/監控 | ✅ 是 |
| **Copilot CLI（PTY-backed VS Code Terminal）** | 需要互動式終端操作/實跑指令 | 終端整合強、適合互動 | 需由 Coordinator 透過 PTY 管理/監控 | ✅ 是 |

### 執行後端策略（主從）

| 策略 | 說明 | 使用時機 |
|------|------|---------|
| `pty-primary-with-consented-fallback` | workflow 的 prompt / submit / verify / monitor 以 PTY 為主；fallback 需經 user 同意 | 預設且固定 |
| `pty_runtime_monitor` | 監測主路徑使用 PTY structured artifact 與 command result | 預設 |
| `fallback_runtime_monitor` | PTY 不可用時，使用 fallback runtime（capture/polling/bridge） | 條件式啟用 |

> ✅ workflow 主路徑命令名稱建議：`ivyhouseTerminalPty.startCodex`、`ivyhouseTerminalPty.sendToCodex`、`ivyhouseTerminalPty.submitCodex`、`ivyhouseTerminalPty.verifyCodex`。
> ✅ 若 PTY 不可用且 user 同意 fallback，再改用 `ivyhouseTerminalFallback.*`。
> ✅ fallback-ready 不再只看 `proposed_api_true`；若 shell integration attachment + bridge/token/artifact compatibility 成立，也可視為可接手。

> ⚠️ 預設不使用 fallback HTTP bridge。若要啟用，必須先取得 user 明確同意，並在 Plan/Log 記錄原因。

### QA 模式建議

| Executor Tool | 建議 QA Tool | 理由 |
|---------------|--------------|------|
| Codex CLI | Copilot CLI | 避免同工具自審，保留交叉驗證 |
| Copilot CLI | Codex CLI | 避免同工具自審，保留交叉驗證 |

**Cross-QA 例外情況**：

| 例外類型 | 條件 | 審批流程 | 記錄格式 |
|---------|------|---------|----------|
| **小修正** | ≤20 行程式碼變更 | 1. Copilot 詢問用戶確認<br/>2. 用戶明確回覆「允許」<br/>3. 記錄變更行數 | `qa_compliance: ⚠️ 例外（小修正）- 變更：[X 行] - 用戶：已確認` |
| **緊急修復** | P0 級別 bug<br/>影響生產環境 | 1. 確認優先級為 P0<br/>2. 用戶說明緊急原因<br/>3. 記錄 issue/ticket 編號 | `qa_compliance: ⚠️ 例外（緊急修復）- Issue: [#NNN] - 理由：[說明]` |
| **文件修正** | 無程式碼變更<br/>僅修改 .md/.txt | 自動豁免<br/>無需用戶確認 | `qa_compliance: ✅ 豁免（文件修正）- 檔案：[列表]` |

**違規處理流程**：
1. QA 工具檢測到 `last_change_tool == qa_tool`（或舊版 fallback：`executor_tool == qa_tool`）
2. 檢查是否符合例外條件（小修正/緊急修復/文件修正）
3. 若不符合例外，**拒絕執行** QA 並要求用戶重新選擇工具
4. 若符合例外，詢問用戶確認並記錄到 plan 的 EXECUTION_BLOCK
5. 所有例外情況必須在最終 Log 檔中說明

---

## 🔄 Rollback 策略

**L1 (自我修正)**: Engineer 發現錯誤，立即修正

**L2 (回滾建議)**: 執行失敗/超範圍時提供回滾建議（任何破壞性操作必須用戶明確確認）
  - 前置條件：乾淨 worktree（`git status --porcelain` 為空）
  - 回滾動作：
    - 還原 tracked 變更：`git restore --worktree --staged -- .`
    - 刪除新增的 untracked 檔案（不含 `.agent/`）
    - 若 HEAD 改變，執行 `git reset --hard <PRE_HEAD>`
  - 保留審計證據：`.agent/` 目錄始終保留

**L3 (Copilot 建議)**: QA 不通過時，Copilot 分析 git log 並提供回滾建議
  - `git revert <commit>`（推薦，保留歷史）
  - 或 `git reset --soft HEAD~N`（保留變更於 staging）

**L4 (任務中止)**: User 確認後執行
  - `git reset --soft HEAD~N`（保留變更）
  - 或 `git reset --hard`（完全捨棄，需明確確認）

**預期 Rollback Level**: [L1|L2|L3|L4]

---

## ✅ 用戶確認

> 🛑 **必要停頓點**：Planner 產出 Spec 後，必須等待用戶確認才能進入 Step 2。

- [ ] Spec 已確認，可進入 Step 2 (Domain Expert)
- [ ] Security Review Policy 已確認：`[true|false]`（並已寫入 EXECUTION_BLOCK）
- [ ] Security Reviewer Tool 已確認：`[N/A|codex-cli|copilot-cli]`（若 `security_review_required=true` 則必填，並已寫入 EXECUTION_BLOCK）
- [ ] Engineer Tool 已選擇：`[codex-cli|copilot-cli]`（並已寫入 EXECUTION_BLOCK）
- [ ] QA Tool 已選擇：`[codex-cli|copilot-cli]`（必須 ≠ last_change_tool，並已寫入 EXECUTION_BLOCK）
- [ ] Execution Backend Policy 已確認：`[pty-primary-with-consented-fallback]`（並已寫入 EXECUTION_BLOCK）
- [ ] Monitor Backend Policy 已確認：`[pty-runtime-primary]`（並已寫入 EXECUTION_BLOCK）
- [ ] Terminal 管理策略已確認

---

**Template Version**: 2.6.1
**Last Updated**: 2026-03-14
**Synced With**: .agent/roles/coordinator.md v1.8.0
