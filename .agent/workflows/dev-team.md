---
description: 艾薇虛擬開發團隊工作流程 - 自動化 Plan → Consult → Implement → Review
---
# 🤖 艾薇虛擬開發團隊工作流程

當使用者輸入 `/dev`（或相容別名 `/dev-team`）或請求「啟動開發團隊」時，請依照以下步驟執行。

> 📌 **Slash 指令說明**：
> - `/dev` 或 `/dev-team`：啟動本 repo 的 dev-team workflow（Ivy Coordinator 流程）
> - 如果你有個人的 Copilot prompt file 使用 `/dev`，建議改用其他名稱（如 `/devchat`）以避免衝突

---

## 📋 前置準備

1. **確認需求**：先請使用者說明他們的開發需求是什麼。
2. **閱讀規則**：在開始任何工作前，先依 `.agent/workflows/AGENT_ENTRY.md` 判定本次應讀 `./.agent/workflow_baseline_rules.md`（template repo 維護）或 `./project_rules.md`（下游/新專案）作為核心規範。

> ⚠️ 在 `READ_BACK_REPORT` 確認之前，Coordinator 必須先完成入口讀檔；在 `READ_BACK_REPORT` 確認之後，必須先執行 PTY bootstrap：`ivyhouseTerminalPty.rotateArtifacts`（`reason="new-workflow"`，不指定 `kind`），再進 Mode Selection Gate。只有選定 `formal-workflow` 時，才進入本檔後續 Step 1 ~ Step 5。

---

## 🔄 工作流程（依序執行）

### Step 1️⃣ 艾薇規劃師 (Planner)
**角色定義**：參考 `.agent/roles/planner.md`

**任務**：
1. 掃描專案目錄結構，理解現有檔案。
2. 閱讀相關程式碼（如 `app.py`, `.agent/runtime/scripts/`）。
3. 若任務涉及多階段拆解、dependency、估時或風險盤點，先載入：
  ```bash
  cat .agent/skills/project-planner/SKILL.md
  cat .agent/skills/project-planner/references/planning-framework.md
  cat .agent/skills/project-planner/references/task-sizing-and-dependencies.md
  cat .agent/skills/project-planner/references/estimation-and-risk.md
  ```
4. 產出一份 Markdown 格式的 **開發規格書 (Spec)**，包含：
   - 目標描述
   - 需要修改/新增的檔案清單
   - 每個檔案的邏輯細節
   - 注意事項與風險提示
5. **保存 Spec 為獨立文件**：
  - 所有 active workflow / 治理 / 專案功能任務一律使用 `doc/plans/Idx-NNN_plan.md`
6. **Plan 固定段落（必須存在）**：
   - `## 📋 SPEC`
   - `## 🔍 RESEARCH & ASSUMPTIONS`（至少包含 `research_required: true/false`）
   - `## 🔒 SCOPE & CONSTRAINTS`（含 File whitelist / Done 定義 / Rollback / Max rounds）

**產出格式**：參考模板 `doc/plans/Idx-000_plan.template.md`

```markdown
## 📄 開發規格書

### 目標
[描述]

### 檔案變更
| 檔案 | 動作 | 說明 |
|------|------|------|
| xxx.py | 修改 | ... |

### 邏輯細節
...

### 注意事項
...
```

> 🛑 **必要停頓點**：Spec 產出後，必須等待用戶確認才能進入 Step 2。

---

### Step 2️⃣ 領域專家 (Domain Expert)
**角色定義**：參考 `.agent/roles/domain_expert.md`

**任務**：
1. 檢視 Planner 的 Spec。
2. 若任務涉及特定領域邏輯，提供專業建議與風險提示。
3. 確認業務規則、計算邏輯、合規邊界是否正確。
4. 若這次任務不涉及特定領域邏輯，可以明確回覆 `N/A` 並跳過。

**產出格式**：
```markdown
## 📊 領域專家審核

### 涉及的專業邏輯
- [列出相關邏輯、公式、規則]

### 專業建議
- [任何改進或注意事項]

### 結論
✅ 通過 / ⚠️ 需要修正 / N/A
```

---

### Step 2.5️⃣ 執行工具選擇 (Role Selection Gate) 🚦

**執行者**: GitHub Copilot Chat（固定作為 Coordinator）

**觸發條件**: Plan 通過 User Approval Gate 且 Domain Expert Review 完成

**任務**: 由 Coordinator 依 `AGENT_ENTRY.md` 的 askQuestions-first 契約，收集 Gate 決策與正式工具選擇，並更新 Plan 的 `EXECUTION_BLOCK`。

> **單一來源規則**：Approve Gate、Role Selection Gate、Research Gate、Plan Validator Gate、Preflight Gate、Historical File Checkpoint、Security Review Trigger 與 `EXECUTION_BLOCK` 欄位契約，一律以 `.agent/workflows/AGENT_ENTRY.md` 第 3 節為準；本檔只保留流程順序與角色責任摘要，不再重複定義另一套規格。

**本步最少要完成的事**：
1. 依 `AGENT_ENTRY.md` 問完唯一題組：Approve / Domain Review / Security Review / Scope Policy / Backend Policy / `executor_tool` / `security_reviewer_tool` / `qa_tool`。
2. 在 Plan 的 `EXECUTION_BLOCK` 回填：
  - `scope_policy`
  - `expert_required`
  - `security_review_required`
  - `executor_tool`
  - `security_reviewer_tool`
  - `qa_tool`
   - `execution_backend_policy`
   - `executor_backend`
   - `monitor_backend`
   - `security_review_trigger_source`
   - `security_review_trigger_matches`
3. 僅在 `Research Gate`、`Plan Validator Gate`、`Preflight Gate`、`Historical File Checkpoint` 全部通過後，才可進入 Engineer。
4. 若目前在 downstream / 新專案工作區，且存在 Obsidian access surface，還必須先依 `AGENT_ENTRY.md` 完成 `Obsidian Knowledge Intake Gate`：先檢閱 `00-indexes/`，再受控讀取最小必要的 `20-reviewed/` 文件；若採用 core-shipped restricted mount generator，預設 surface 應是 `obsidian-knowledge/00-indexes/` 與 `obsidian-knowledge/20-reviewed/`；不得在啟動階段掃描其他 vault 區域。

**Research Gate 補充（Coordinator 必須落地）**：
- 判定方式與載入命令：直接對照 [coordinator_research_skill_trigger_checklist.md](./references/coordinator_research_skill_trigger_checklist.md)

**現行主命令面**：
- PTY Bootstrap：`ivyhouseTerminalPty.rotateArtifacts`（`reason="new-workflow"`）
- PTY：`ivyhouseTerminalPty.startCodex` / `ivyhouseTerminalPty.startCopilot`
- PTY：`ivyhouseTerminalPty.sendToCodex` / `ivyhouseTerminalPty.sendToCopilot`
- PTY：`ivyhouseTerminalPty.submitCodex` / `ivyhouseTerminalPty.submitCopilot`
- PTY：`ivyhouseTerminalPty.verifyCodex` / `ivyhouseTerminalPty.verifyCopilot`
- Fallback（條件式）：`ivyhouseTerminalFallback.*`

---

### Step 3️⃣ 全端工程師 (Engineer)
**角色定義**：參考 `.agent/roles/engineer.md`

**任務**：根據 Planner 的 Spec、Domain Expert 的建議與 Plan 的 `EXECUTION_BLOCK.executor_tool`，由選定的終端工具完成實作。

**執行方式**（由 Step 2.5 決定）：

#### 共同規則（Coordinator 必須落地）
- **Plan 執行方式**：由 Coordinator 透過 PTY command surface 對「已啟動的 Codex/Copilot PTY session」送出 prompt / submit / verify
- **完成條件（Idx-030 格式）**：Engineer/QA/Fix 結束時在終端輸出 5 行 completion marker：
  ```
  [ENGINEER_DONE] 或 [QA_DONE] 或 [FIX_DONE]
  TIMESTAMP=YYYY-MM-DDTHH:mm:ssZ
  NONCE=<從環境變數 WORKFLOW_SESSION_NONCE 讀取>
  TASK_ID=Idx-XXX
  <角色特定結果行>
  ```
  - Engineer: `ENGINEER_RESULT=COMPLETE`
  - QA: `QA_RESULT=PASS` 或 `QA_RESULT=FAIL`
  - Fix: `FIX_ROUND=N`
  - **⚠️ 硬性規則**：這 5 行必須是輸出的**最後 5 個非空白行**。完成標記後不可再輸出任何文字（包括確認訊息、說明等）。
- **即時監控**：Coordinator 以 PTY structured event、command result 與 live transcript 監測進度，直到偵測 completion marker 或 timeout
- **監控備援**：若 PTY 不可用，先詢問 user 是否同意切換 fallback；若 user 拒絕才改人工回報
- **Scope Gate**：偵測到變更後，Coordinator 必須先確認變更檔案未超出 Plan 的檔案清單（超出則停下來請用戶決策）

- **執行記錄**:
  - ✅ 每次執行追加到 `.agent/execution_log.jsonl`
  - ✅ 失敗/超範圍時，先由 Coordinator 詢問用戶是否回滾/拆分（禁止自動執行破壞性操作）
- **產出格式**:
  ```markdown
  ## 🔧 實作報告 (Executor Tool)

  ### 已修改/新增的檔案
  [由 Codex 輸出]
  ```

**通用規範**（兩種模式都必須遵守）：
- 每個檔案開頭有中文用途註釋
- 單檔不超過 500 行
- 無 Hard-code API Key
- 遵循本次工作區對應的 active 規則檔（template repo 維護讀 `./.agent/workflow_baseline_rules.md`；下游/新專案讀 `./project_rules.md`）

**實作前技能載入（條件式必做）**：
- 判定方式與載入命令：直接對照 [engineer_skill_trigger_checklist.md](./references/engineer_skill_trigger_checklist.md)
- 若同時符合多個條件，Engineer 必須全部載入。

**Skill Execution Gate（每次變更必執行，且需留證據）**：
- 對每個新建/修改的 `.py` 檔案或對應變更範圍，執行至少一條：
  ```bash
  python .agent/skills/code-reviewer/scripts/code_reviewer.py <file_path>

  # 或以目錄 / diff / git diff 模式執行
  python .agent/skills/code-reviewer/scripts/code_reviewer.py <directory_path>
  python .agent/skills/code-reviewer/scripts/code_reviewer.py <diff_file> .
  python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff --staged .
  python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff --cached .
  python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff <base>..<head> .
  ```
- 若專案有測試，執行：
  ```bash
  python .agent/skills/test-runner/scripts/test_runner.py [test_path]
  ```
- **Coordinator 收集流程（PTY 主路徑）**：
  - Copilot Chat 透過 `.agent/runtime/tools/vscode_terminal_pty` command surface 管理 PTY session 與 prompt / submit
  - 使用 PTY runtime artifact 與 command result 監測終端狀態
  - 若 PTY 不可用：先詢問 user 是否同意切到 `.agent/runtime/tools/vscode_terminal_fallback`
  - 從 stdout 擷取 JSON 結果
  - 將結果寫入 Log 的 `## 🛠️ SKILLS_EXECUTION_REPORT` 段落
- **Skills Evaluation（建議每回合一次，產生可追溯統計）**：
  - 若 Log 已包含 `SKILLS_EXECUTION_REPORT`，執行：
    ```bash
    python .agent/skills/skills-evaluator/scripts/skills_evaluator.py <log_file_path>
    ```
  - 將輸出摘要/統計寫入 Log 的 `## 📈 SKILLS_EVALUATION` 段落
- 若 `code-reviewer` 回傳 `status: fail`（例如 API key 洩漏）→ 立即停止並回報 user

**產出格式** (若為模式 A)：
```markdown
## 🔧 實作報告 (Antigravity Direct)

### 已修改/新增的檔案
...完整程式碼...
```

---

### Step 3.5️⃣ 安全審查員 (Security Reviewer)
**角色定義**：參考 `.agent/roles/security.md`

**觸發時機**:
- Engineer completion marker 被偵測後
- 且 `AGENT_ENTRY.md` 第 3 節定義的 deterministic trigger 命中（explicit request / path rule / keyword rule）
- 或 Plan 的 `EXECUTION_BLOCK.security_review_required=true`

**任務**：
1. 從防禦者視角審查變更與關聯模組的攻擊面。
2. 分析資料流、權限邊界、危險 sink 與 exploit path。
3. 對 findings 做二次驗證，降低 false positive。
4. 為 findings 標記 `Severity` 與 `Confidence`。
5. 只提出修補建議，不直接改 code。

**必做命令**：
```bash
cat .agent/skills/security-review-helper/SKILL.md
cat .agent/skills/security-review-helper/references/security_checklist.md
```

- Security Reviewer 不是選擇性參考 helper；開始審查前必須先讀完上述兩份文件。

**結果處理**：
| 結果 | 處理 |
|------|------|
| `PASS` | 進入 QA |
| `PASS_WITH_RISK` | 記錄風險後進入 QA |
| `FAIL` | 先回 Engineer 修正，不直接進 QA |

> `security_review_trigger_source`、`security_review_trigger_matches` 與是否可豁免，均以 `AGENT_ENTRY.md` 的單一規格來源為準。

---

### Step 4️⃣ 艾薇品管員 (QA)
**角色定義**：參考 `.agent/roles/qa.md`

**觸發時機**:
- Engineer completion marker 被偵測後立即執行

**Cross-QA 工具檢測（在審查前執行）**：
1. 讀取 Plan 的 `EXECUTION_BLOCK.last_change_tool`
2. 用戶選擇 `qa_tool`（`codex-cli|copilot-cli`）
3. 若 `qa_tool == last_change_tool` → **拒絕執行 QA**，要求改選另一個工具（除非符合例外並記錄）

**記錄格式**:
- 違規: `qa_compliance: ⚠️ 違規（同工具）- 理由：[用戶說明]`
- 例外: `qa_compliance: ⚠️ 例外（小修正）- 變更：[X 行]`
- 豁免: `qa_compliance: ✅ 豁免（文件修正）- 檔案：[列表]`
**任務**：
1. 審查工程師的程式碼。
2. **確認 Cross-QA 規則**：QA 工具必須與 `last_change_tool` 不同
  - last_change_tool: codex-cli → QA: copilot-cli
  - last_change_tool: copilot-cli → QA: codex-cli
3. **必做命令**：先依審查範圍執行至少一條 `code-reviewer` 命令
  ```bash
  python .agent/skills/code-reviewer/scripts/code_reviewer.py <file_path>
  python .agent/skills/code-reviewer/scripts/code_reviewer.py <directory_path>
  python .agent/skills/code-reviewer/scripts/code_reviewer.py <diff_file> .
  python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff --staged .
  python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff --cached .
  python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff <base>..<head> .
  ```
  - 若專案有測試，也必須執行 `python .agent/skills/test-runner/scripts/test_runner.py [test_path]`
4. **條件式 Gate（輸出到 Log）**：
   - **UI/UX Gate**：若 Scope Gate 判定 `UI/UX triggered: YES`（基於變更檔案清單）
     - QA 報告後必須補 `## UI/UX CHECK`（code review 為主；不跑獨立工具）
   - **Maintainability Gate**：若存在程式碼變更（例如 `.py`）且（變更行數 > 50 或命中核心路徑 `core/**`/`utils/**`/`config.py`）
     - QA 報告後必須補 `## MAINTAINABILITY REVIEW`（Must/Should/Nice；Reviewer 永不改 code）
5. 執行 Checklist：
   - [ ] 無 Hard-code API Key？
   - [ ] 有中文檔案註釋？
  - [ ] 符合本次工作區對應的 active 規則檔？
   - [ ] 邏輯正確？
   - [ ] **Cross-QA 規則已遵守？**
   - [ ] **若使用新的 CLI 工具，是否已遵循探索流程？**
4. 產出審查報告。

> 💡 **工具探索流程**：首次使用新工具時，必須執行 `<tool> --help` 確認參數，禁止憑經驗臆測。詳見 [`.agent/skills/explore-cli-tool/SKILL.md`](../skills/explore-cli-tool/SKILL.md)

> ⚠️ **Cross-QA 違規處理**：如果 `last_change_tool == qa_tool`，必須在 Log 中標記 `qa_compliance: ⚠️ 違規` 並說明原因。

**產出格式**：
```markdown
## ✅ 品管審查報告

### Cross-QA 檢核
- Last Change Tool: [codex-cli | copilot-cli]
- QA Tool: [codex-cli | copilot-cli]
- Compliance: [✅ 符合 | ⚠️ 違規：原因]

### Checklist
- [x] 無 Hard-code API Key
- [x] 有中文檔案註釋
- [x] Cross-QA 規則已遵守
- [ ] 符合 active 規則檔（問題：...）

### 發現的問題
| 檔案 | 行號 | 問題描述 | 建議修正 |
|------|------|----------|----------|
| ... | ... | ... | ... |

### 結論
🟢 通過 / 🟡 通過但有風險 / 🔴 需要修正
```

---

## 🏁 完成

當 QA 審查通過後：
1. **建立執行記錄**: 由 Coordinator 產生執行記錄：
  - 所有 active workflow / 治理 / 專案功能任務一律使用 `doc/logs/Idx-XXX_log.md`（引用 `doc/plans/Idx-XXX_plan.md`）
2. **保留 Plan 檔案**: Plan 檔案不刪除（作為規格與決策留存）
3. **提交變更（選用）**: 是否 `git commit` 由用戶決策

如果 QA 發現問題，請回到 **Step 3 (Engineer)** 修正後再次審查。

---

## 📊 執行模式比較

| 模式 | 適用情境 | 啟動方式 | 監測 | QA 觸發 |
|------|---------|---------|------|---------|
| Codex CLI（PTY-backed VS Code Terminal） | 批次處理、檔案操作、快速執行 | Coordinator 以 PTY command surface 驅動 | PTY artifact（主）→ fallback runtime（條件式） | marker 偵測後 |
| Copilot CLI（PTY-backed VS Code Terminal） | 需要互動式終端操作/實跑指令 | Coordinator 以 PTY command surface 驅動 | PTY artifact（主）→ fallback runtime（條件式） | marker 偵測後 |

### 後端策略（主從）

| 後端策略 | 說明 | 何時使用 |
|---------|------|---------|
| `pty-primary-with-consented-fallback` | workflow 的 prompt / submit / verify / monitor 以 PTY 為主；fallback 需經 user 同意 | 預設且固定 |
| `pty_runtime_monitor` | 監測主路徑使用 PTY structured artifact 與 command result | 預設主路徑 |
| `fallback_runtime_monitor` | PTY 不可用且 user 同意後，啟用 fallback runtime monitor | 條件式啟用 |

**主從模型（允許）**：
- `Terminal PTY`：workflow 主路徑，承接 send / submit / monitor / verify / smoke
- `Terminal Fallback`：僅在 PTY 不可用且 user 同意後才接手

---

## ⚠️ 必須遵守的規則
在整個流程中，所有角色都必須嚴格遵守：
- 📜 `.agent/workflow_baseline_rules.md` - template repo 維護時的 active baseline rules
- 📜 `project_rules.md` - 下游/新專案使用的 starter template / 專案核心守則
