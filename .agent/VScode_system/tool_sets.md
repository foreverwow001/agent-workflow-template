# Tool Sets

Ivy House 共通指令（所有 Agent 必遵守）

---

## 1️⃣ 語言

所有回覆、Spec、Plan、Log、註解均使用**繁體中文**。

---

## 2️⃣ 確認機制

任何程式碼變更前，必須：
1. 複述需求
2. 等待用戶確認
3. user-facing Gate 預設使用 VS Code `#askQuestions`

只有在工具不可用、需要自由文字理由、或選項不足時，才可退回一般聊天輸入。

---

## 3️⃣ 角色邊界

- **Coordinator** 不做實作
- 程式碼變更只允許透過：
  - `codex-cli`
  - `copilot-cli`

---

## 4️⃣ git/diff 限制

所有 git/diff/行數計算只允許在：
- Project terminal
- VS Code SCM

**禁止**：
- 注入到 Codex/Copilot terminal
- 在 Codex CLI 中執行 git 指令

---

## 5️⃣ Workflow 觸發

使用者輸入 `/dev` 視為啟動（相容 `/dev-team`）。

`READ_BACK_REPORT` 確認後，先執行 PTY bootstrap：`ivyhouseTerminalPty.rotateArtifacts`（`reason="new-workflow"`，不指定 `kind`），再做 Mode Selection Gate：
- `formal-workflow`（預設）
- `lightweight-direct-edit`（僅限低風險、小範圍修正；一旦 scope 擴張必須升級回正式 workflow）

---

## 6️⃣ Completion Markers

以下 marker 未出現視為未完成：
- `[ENGINEER_DONE]`
- `[QA_DONE]`
- `[FIX_DONE]`

---

## 7️⃣ Cross-QA 規則

QA 工具不得等於 `last_change_tool`

**例外**：需明確記錄並由用戶確認。

---

## 8️⃣ Deterministic Gates

以下 Gate 必須按規範執行並寫入 Log：

### Research Gate
- 若 `research_required: true` 或依賴檔案變更
- 必須補 Sources（Link-required）或標 `RISK: unverified`

### Maintainability Gate
- 有 `.py` 變更且總行數>50 或命中 `core/**|utils/**|config.py`
- Log 必有 `MAINTAINABILITY REVIEW`（只給建議，不改 code）

### UI/UX Gate
- 命中 UI 路徑時
- Log 的 `SCOPE GATE` 記 `UI/UX triggered: YES/NO`
- YES 時 QA 必有 `UI/UX CHECK`

### Evidence Gate
- 只有在（變更行數>200）或（需要貼完整終端輸出且>80行）才允許新增 evidence

---

## 9️⃣ Security

- 不得硬寫任何 key/token
- 敏感資料只能用 `.env`

---

## 已可用的工具集

### Executor Tools
- **codex-cli** - 程式碼生成與執行
- **copilot-cli** - Copilot CLI 型終端執行工具

### Interaction Tools
- **VS Code `#askQuestions`** - user-facing Gate 的預設互動工具

### Terminal Tools
- **Project Terminal** - 執行 git/bash 指令
- **Codex CLI Terminal** - codex 指令執行
- **Copilot CLI Terminal** - copilot 指令執行

### Monitoring Tools
- **Terminal PTY Runtime** - workflow 主路徑的 start / send / submit / verify / smoke / monitor
- **PTY Debug Artifacts** - `*_pty_debug.jsonl` / `*_pty_live.txt` 作為主要監測證據
- **Terminal Fallback Runtime** - 僅在 PTY 不可用且 user 同意後啟用
- **Marker Detection** - 完成 marker 偵測

### Documentation Tools
- **Markdown Logger** - `.md` 格式日誌
- **Plan Generator** - `doc/plans/Idx-XXX_plan.md`
- **Log Generator** - `doc/logs/Idx-XXX_log.md`
- **Artifact Path Rule** - active workflow / 治理 / 專案功能任務統一使用 `doc/implementation_plan_index.md`、`doc/plans/Idx-XXX_plan.md`、`doc/logs/Idx-XXX_log.md`

---

## 使用限制速查表

| 工具 | 允許 | 禁止 |
|------|------|------|
| codex-cli | 程式碼變更 | git 操作 |
| copilot-cli | 程式碼變更 | git 操作 |
| Project Terminal | git / bash | 無 |
| Coordinator | Gate 判定、注入指令 | 直接執行程式碼 |

---

## 調用流程

1. **SPEC_MODE**：Coordinator 複述需求並等待確認
2. **READ_BACK_REPORT + Bootstrap + Mode Selection Gate**：先執行 `ivyhouseTerminalPty.rotateArtifacts`（`reason="new-workflow"`），再決定 `formal-workflow` 或 `lightweight-direct-edit`
3. **Plan 產出**：若為 formal workflow，要求 Planner 產出 `doc/plans/Idx-XXX_plan.md`
4. **Plan 確認**：以 `#askQuestions` 為主收集 Approve / Scope / Tool 決策
5. **ORCH_MODE**：記錄 `executor_tool`、`security_reviewer_tool`（條件式）、`qa_tool` 並開始執行
6. **終端操作**：使用 Terminal PTY command surface 對已啟動的工具做 start / send / submit / verify
7. **Marker 監控**：等待 `[*_DONE]` marker 出現
8. **Log 回填**：產生 `doc/logs/Idx-XXX_log.md`
