# /dev Workflow 現況與優化地圖

> 建立日期：2026-03-17
> 狀態：Archived - merged into 2026-03-18-workflow-optimization-plan.md
> 用途：保留 2026-03-17 當下對 `/dev` workflow 的 maintainer 分析快照。後續內容已收斂進 `maintainers/archive/2026-03-18-workflow-optimization-plan.md`，本檔不再作為現行維護入口。
>
> 這份文件是歷史快照，不是新的規格來源。真正的 Gate、欄位契約與 Security Review trigger，仍以 `.agent/workflows/AGENT_ENTRY.md` 第 3 節為唯一來源。

---

## 0. 文件定位

若你是第一次接手這個 repo 的 workflow 維護，應這樣理解文件層級：

1. `.agent/workflows/AGENT_ENTRY.md`
   - workflow 的唯一入口與唯一 Gate/trigger/`EXECUTION_BLOCK` 契約來源
2. `.agent/workflows/dev-team.md`
   - `/dev` 的流程摘要與角色分工說明
3. `.agent/roles/coordinator.md`
   - Coordinator 的操作責任、監控責任與失敗處置細節
4. `doc/plans/Idx-000_plan.template.md`
   - Plan 與 `EXECUTION_BLOCK` 的實際欄位模板
5. `maintainers/archive/2026-03-18-workflow-optimization-plan.md`
   - 目前 workflow 文件收斂工作的執行計畫

這份文件的任務，是把上述幾份內容串成一條目前真的在運作的 `/dev` 流程線，並指出還有哪些地方雖然能跑，但維護成本偏高。

---

## 1. 一句話總結

目前的 `/dev` workflow，本質上是「GitHub Copilot Chat 固定擔任 Coordinator，先做讀檔與 Plan Gate，之後再透過 PTY command surface 協調 `codex-cli` 或 `copilot-cli` 完成 Engineer / QA / Security Review 的治理型流程」。

它不是單純 prompt，也不是讓 Coordinator 直接改 code 的 workflow。

---

## 2. 目前參與的角色與工具

### 固定角色

- Coordinator：GitHub Copilot Chat
- Planner：產出 Plan 與 `EXECUTION_BLOCK` 初稿
- Domain Expert：條件式審核業務/領域邏輯
- Engineer：由 `codex-cli` 或 `copilot-cli` 擔任
- Security Reviewer：條件式審查可利用的攻擊面與漏洞路徑
- QA：由與 `last_change_tool` 不同的終端工具擔任

### 固定工具邊界

- Workflow 主路徑：`.agent/runtime/tools/vscode_terminal_pty`
- 條件式備援：`.agent/runtime/tools/vscode_terminal_fallback`
- Git / diff / numstat：只能在 Project terminal 或 VS Code SCM 執行
- Coordinator 不做實作，不直接改 code，也不把 git 指令注入 Codex/Copilot session

### 固定 artifact

- Plan：`doc/plans/Idx-NNN_plan.md`
- Index：`doc/implementation_plan_index.md`
- PTY 主證據：`.service/terminal_capture/*_pty_debug.jsonl`
- PTY transcript：`.service/terminal_capture/*_pty_live.txt`
- fallback 相容 artifact：`monitor_debug.jsonl`、`codex_live.txt`、`copilot_live.txt`、bridge token/events

---

## 3. `/dev` 現行流程步驟

### Step 0. 觸發

- 使用者輸入 `/dev` 或 `/dev-team`
- `Ivy_Coordinator.md` 視這為 workflow 啟動訊號
- Coordinator 預設先進 `SPEC_MODE`

### Step 1. 必讀檔案與 READ_BACK_REPORT

來源：`.agent/workflows/AGENT_ENTRY.md`

Coordinator 必須先逐檔閱讀：

- `.agent/workflows/dev-team.md`
- `project_rules.md`
- `doc/implementation_plan_index.md`

然後輸出固定格式的 `READ_BACK_REPORT`，包含：

- 本機時間
- 已開啟閱讀的檔案清單
- 從規則/流程萃取的 Top 5 硬約束
- Index 對照結果
- 風險旗標

在 user 確認前，不得直接進 Plan。

### Step 2. Goal Alignment

來源：`.agent/roles/coordinator.md`

Coordinator 先用對話形式輸出：

- 你理解的目標
- Out of Scope
- 驗收條件草案

這一步仍屬 `SPEC_MODE`，目的不是執行，而是把任務邊界鎖清楚。

### Step 3. Planner 產出 Plan

來源：`.agent/workflows/dev-team.md`、`.agent/roles/planner.md`、`doc/plans/Idx-000_plan.template.md`

Planner 需要產出 `doc/plans/Idx-NNN_plan.md`，其中最重要的固定段落有：

- `## 📋 SPEC`
- `## 🔍 RESEARCH & ASSUMPTIONS`
- `## 🔒 SCOPE & CONSTRAINTS`
- `## 📁 檔案變更`
- `EXECUTION_BLOCK`

這份 Plan 不只是規格書，也是後續狀態中心；`executor_tool`、`qa_tool`、`last_change_tool`、`security_review_*`、`log_file_path` 都會回填在這裡。

### Step 4. Plan Approval Gate

來源：`.agent/workflows/AGENT_ENTRY.md`

user 確認 `READ_BACK_REPORT` 後，Coordinator 才能進入 Plan Gate。這裡不是只問一句「要不要開始」，而是要完成一組固定決策：

- Approve / Reject / Revise
- 是否需要 Domain Expert Review
- 是否需要 Security Review
- `scope_policy` 是 `strict` 還是 `flexible`
- backend policy 固定為 `pty-primary-with-consented-fallback`

完成後，Coordinator 需把結果回填到 `EXECUTION_BLOCK`。

> 建議優化方向：這一組決策應改成 askQuestions-first，而不是輸出段落後再等 user 手打一段新 prompt。

### Step 5. Role Selection Gate

來源：`.agent/workflows/AGENT_ENTRY.md`、`.agent/workflows/dev-team.md`

Coordinator 要求 user 選擇：

- Engineer Tool：`codex-cli` 或 `copilot-cli`
- Security Reviewer Tool：`codex-cli` 或 `copilot-cli`（僅在 `security_review_required=true` 時必選）
- QA Tool：`codex-cli` 或 `copilot-cli`

並遵守硬規則：

- `qa_tool ≠ last_change_tool`

這一步完成後，Plan 內至少應已有：

- `executor_tool`
- `security_reviewer_tool`（若需要 Security Review）
- `qa_tool`
- `execution_backend_policy`
- `executor_backend`
- `monitor_backend`

> 建議優化方向：這一整組 tool selection 應由 askQuestions 一次收集，避免 user 在聊天中逐題重打。

### Step 6. Pre-execution Gates

在真正進 Engineer 前，還有四個前置 Gate：

1. Research Gate
   - 若 `research_required: true` 或命中依賴檔案變更，先補 Sources / Assumptions
2. Plan Validator Gate
   - 跑 `python .agent/skills/plan-validator/scripts/plan_validator.py <plan_file_path>`
3. Preflight Gate
   - 主路徑：`python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-pty --allow-pty-cold-start --json`
   - fallback 路徑：`python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-fallback --json`
4. Historical File Checkpoint
   - 防止對歷史 plan/log 做不必要改寫

只有全部通過，才進入執行。

### Step 7. Domain Expert Review（條件式）

若 user 在 Gate 中要求領域審核，才會進這一步。

目前 Domain Expert 的職責是保守審核：

- 規格是否遺漏業務規則
- 是否有領域特定的合規、資料品質或狀態流轉問題

完成後，Coordinator 會把結論回填到 `expert_conclusion`。

### Step 8. Engineer Execute

來源：`.agent/workflows/dev-team.md`、`.agent/roles/coordinator.md`

真正的程式碼修改只允許由終端工具執行。現行主路徑是：

- Coordinator 用 `.agent/runtime/tools/vscode_terminal_pty` 管理 PTY session
- 對 `codex-cli` 或 `copilot-cli` 做 start / send / submit / verify
- 用 PTY artifact 與 command result 監控執行

Engineer 完成時，必須在終端最後輸出 completion marker：

- `[ENGINEER_DONE]`
- `TIMESTAMP=...`
- `NONCE=...`
- `TASK_ID=Idx-XXX`
- `ENGINEER_RESULT=COMPLETE`

完成後，Coordinator 需回填：

- `executor_end`
- `last_change_tool`

### Step 9. Security Review（條件式）

若命中 deterministic trigger，先做 Security Review，再決定是否進 QA。

現行 trigger 來源是三種：

- explicit request
- path rule
- keyword rule

Security Reviewer 的職責不是單純掃 pattern，而是確認：

- trust boundary
- 危險 sink
- exploit path
- 修補建議

若要讓 Security Review 與 Engineer / QA 一樣具備完整稽核鏈，則它也應在 `security_review_required=true` 時要求 user 選擇執行工具，並把結果寫入 `EXECUTION_BLOCK.security_reviewer_tool`。

結果分為：

- `PASS`
- `PASS_WITH_RISK`
- `FAIL`

若 `FAIL`，直接回修，不進 QA。

### Step 10. QA

來源：`.agent/roles/qa.md`

QA 階段需要：

- 先檢查 Cross-QA 規則
- 依範圍執行至少一條 `code-reviewer`
- 若有測試，再執行 `test-runner`
- 視變更內容補 `UI/UX CHECK` 或 `MAINTAINABILITY REVIEW`

QA 完成也要輸出固定 5 行 marker，並將結果回填到：

- `qa_result`
- `qa_end`
- `qa_compliance`

### Step 11. Fix Loop / Rollback

若 Security Review 或 QA 失敗，流程不會直接結束，而是回到修正迴圈：

- 由 user 決定是讓當前工具修、重選 Engineer，或回滾
- 修完後要再次 Cross-QA
- `last_change_tool` 必須隨本輪修正更新

### Step 12. Log / Close

最後，Coordinator 需：

- 產生 `doc/logs/Idx-XXX_log.md`
- 寫回 commit / rollback / QA / skills evidence
- 對 user 總結完成內容、風險與後續事項

---

## 4. 這條流程目前依賴哪些實體欄位與證據

### Plan / State center

現行 workflow 的狀態中心就是 `EXECUTION_BLOCK`。這代表 workflow 並不是靠聊天上下文記住狀態，而是靠 Plan 檔中的欄位續接：

- `scope_policy`
- `expert_required`
- `security_review_required`
- `executor_tool`
- `executor_backend`
- `monitor_backend`
- `last_change_tool`
- `qa_tool`
- `qa_result`
- `log_file_path`

### Runtime evidence

主證據面現在已是 PTY artifact：

- `codex_pty_debug.jsonl`
- `copilot_pty_debug.jsonl`
- `codex_pty_live.txt`
- `copilot_pty_live.txt`

目前這四份檔案採固定檔名 append 模型；若不先清 current files，很容易把多輪舊 run 混在同一份 evidence 內。

因此目前更合理的下一步已不是單純 truncate，而是先做到 rotation：current 檔維持固定檔名給 workflow / preflight 讀取，舊內容則在新一輪工作開始前轉成帶 timestamp 的歷史檔。

fallback evidence 只在 PTY 不可用且 user 同意 fallback 時才升格使用。

### Workflow index

Index 目前統一是：

- `doc/implementation_plan_index.md`

也就是說，workflow/治理任務與專案功能任務，現在都共用同一份 index。

---

## 5. 目前最值得優化的步驟

下面這些不是「整條 workflow 不能跑」的 blocker，但都是目前實際存在的 friction。

### 1. `project_rules.md` 仍是 placeholder

這是現在最明顯的入口品質問題。

`READ_BACK_REPORT` 要求萃取 Top 5 硬約束，但 `project_rules.md` 目前仍保留大量 placeholder：

- 語言規範未定
- 技術棧未填
- 架構模式未填
- 視覺規範未填

結果是：入口流程有形式上的治理，但缺少可信的專案約束內容。

### 2. active docs 仍有 plan/log path 分裂

目前真實狀態是：

- Plan 模板與 index 已收斂到 `doc/`
- 但 `dev-team.md`、`qa.md`、`skills_evaluator.py` 仍保留 `.agent/plans` / `.agent/logs` 敘事

更直接的 friction 是：

- repo 內目前沒有 `doc/logs/**` 實體模板
- repo 內也沒有 `.agent/logs/**` 實體模板
- `dev-team.md` 還引用了 `.agent/logs/Idx-010_log_template_example.md`，但這個檔案不存在

這會讓 workflow 到最後一段 log/close 時，仍需要人工解釋「log 應該放哪裡」。

### 3. Gate 單一來源已建立，但摘要層仍偏厚

`AGENT_ENTRY.md` 已是唯一 Gate 來源，這是正確方向。

但目前：

- `dev-team.md`
- `coordinator.md`
- `qa.md`
- `Ivy_Coordinator.md`

仍保留不少操作型敘事與近似重述。它們未必直接衝突，但已經開始提高漂移風險。

更細一層的 friction 是：目前多數 Gate 仍寫成「停下等待 user 再輸入 prompt」，還沒有正式切到 askQuestions-first 互動模型。

### 4. `READ_BACK_REPORT` 的硬停頓仍有 UX friction

現在 `/dev` 啟動至少會拆成：

1. 讀檔與 `READ_BACK_REPORT`
2. user 確認
3. Goal alignment
4. Plan
5. 再次進 Gate

這對治理是安全的，但互動成本偏高。下一步應該明確決定：

- 保留硬停頓
- 或改成更短的 readback + 一次確認進 Plan

若採 askQuestions-first，較合理的方向不是直接刪掉確認點，而是把確認點改成 UI 決策收集，不再要求 user 再打一輪 prompt。

### 4.5. Security Reviewer 尚未進入完整 tool-selection model

目前 Engineer / QA 都有明確的 tool selection，但 Security Reviewer 還沒有對稱欄位與 selection step。

這會帶來兩個問題：

- Security Review 的執行工具選擇不夠顯性
- `EXECUTION_BLOCK` 對 Security Review 的執行鏈記錄不完整

若 Security Review 持續是 workflow 正式階段，就應補上：

- `security_reviewer_tool`
- `security_review_start`
- `security_review_end`
- `security_review_result`

### 4.6. PTY current artifact 缺少 hygiene 策略

目前 fallback 已有 `captureMaxBytes` 與 rolling capture 概念，但 PTY 主路徑沒有對等的 retention 或 rolling 設定。

因此目前更合理的第一階段，不是只做 truncate current files，而是先做到 rotation：

- 每次 `start` 前 rotate 當前 backend 的 PTY current files
- 每次 `restart` 前 rotate 當前 backend 的 PTY current files
- 每次開始新 workflow 任務前，rotate 兩個 backend 的 PTY current files
- rotation 檔只保留最近幾輪，避免 `.service/terminal_capture/` 無限制堆積

這樣能先解掉 evidence 混雜問題，同時保留最近幾輪可追溯證據，複雜度也仍明顯低於完整 archive manager。

### 5. Planner / Domain Expert 仍有舊領域殘留

目前 `.agent/roles/planner.md` 還保留：

- `BOM`
- `庫存`
- `效期`

這類前專案背景。`domain_expert.md` 雖然已泛化，但仍有大量 placeholder。

這代表流程骨架已通用化，但部分角色說明還沒完全 template 化。

### 6. 任務類型分流仍有表面分支、實際單一路徑

`AGENT_ENTRY.md` 現在仍保留「workflow/治理改善」與「專案功能開發」的分支說明，但兩者最後都指向同一份：

- `doc/implementation_plan_index.md`

這不是 bug，但會讓讀者以為存在兩套 index 邏輯。若短期不打算重新拆分 index，這段分支可以再簡化。

---

## 6. 建議的優化優先順序

### Priority 1

- 把 active docs 的 plan/log path 全部收斂到 `doc/`
- 補齊或明確定義 `doc/logs/` 的模板與落點

### Priority 2

- 縮減 `dev-team.md`、`coordinator.md`、`qa.md`、`Ivy_Coordinator.md` 的重複 Gate 敘事
- 讓它們明確退回「摘要與責任說明」層
- 把 user-facing decision point 收斂成 askQuestions-first interaction model

### Priority 3

- 決定 `READ_BACK_REPORT` 是否保留硬停頓
- 若保留，精簡 wording；若不保留，寫明新的確認節點
- 把 Security Review 納入完整 tool-selection 與欄位回填模型

### Priority 4

- 將 `project_rules.md` 真正客製化
- 清掉 Planner / Domain Expert 中仍殘留的舊業務語境與 placeholder
- 在 PTY 主路徑先做到 artifact rotation，再視需要評估完整 archive manager

---

## 6.5 精確變更提案清單

### Proposal A. askQuestions-first Gate contract

#### authoritative 檔案

- `.agent/workflows/AGENT_ENTRY.md`

#### supporting 檔案

- `.agent/workflows/dev-team.md`
- `.agent/roles/coordinator.md`
- `.agent/VScode_system/Ivy_Coordinator.md`
- `.agent/VScode_system/tool_sets.md`
- `project_rules.md`（僅高層原則，可選）

#### 建議新增/改寫的規則

- 將下列 user-facing decision point 改成 askQuestions-first：
   - `READ_BACK_REPORT` 是否通過
   - Plan `Approve / Reject / Revise`
   - `expert_required`
   - `security_review_required`
   - `scope_policy`
   - `executor_tool`
   - `security_reviewer_tool`
   - `qa_tool`
   - fallback consent
   - timeout action
   - rollback confirm
   - scope break decision

### Proposal B. Security Reviewer tool selection

#### authoritative 檔案

- `.agent/workflows/AGENT_ENTRY.md`

#### supporting 檔案

- `.agent/workflows/dev-team.md`
- `.agent/roles/coordinator.md`
- `.agent/roles/security.md`
- `doc/plans/Idx-000_plan.template.md`

#### 建議新增的 `EXECUTION_BLOCK` 欄位

- `security_reviewer_tool: [N/A|待用戶確認: codex-cli|copilot-cli]`
- `security_review_start: [YYYY-MM-DD HH:mm:ss]`
- `security_review_end: [YYYY-MM-DD HH:mm:ss]`
- `security_review_result: [N/A|PASS|PASS_WITH_RISK|FAIL]`

### Proposal C. PTY artifact rotation

#### runtime 檔案

- `.agent/runtime/tools/vscode_terminal_pty/extension.js`
- `.agent/runtime/tools/vscode_terminal_pty/package.json`
- `.agent/runtime/tools/vscode_terminal_pty/README.md`
- `maintainers/chat/2026-03-13-pty-monitor-and-capture-contract.md`

#### 建議新增的設定

- `ivyhouseTerminalPty.rotateArtifactsOnStart`
- `ivyhouseTerminalPty.rotateArtifactsOnRestart`
- `ivyhouseTerminalPty.rotateArtifactsOnNewWorkflow`
- `ivyhouseTerminalPty.rotationMaxHistory`

#### 建議 rotation 的 current files

- `codex_pty_debug.jsonl`
- `codex_pty_live.txt`
- `copilot_pty_debug.jsonl`
- `copilot_pty_live.txt`

#### 建議的 rotation 命名

- `codex_pty_debug.<timestamp>.jsonl`
- `codex_pty_live.<timestamp>.txt`
- `copilot_pty_debug.<timestamp>.jsonl`
- `copilot_pty_live.<timestamp>.txt`

其中固定檔名保留給 current view，rotation 檔保留最近幾輪歷史。

#### 建議的 runtime patch 順序

1. 先改 `.agent/runtime/tools/vscode_terminal_pty/package.json`
   - 先把 `rotateArtifactsOnStart`、`rotateArtifactsOnRestart`、`rotateArtifactsOnNewWorkflow`、`rotationMaxHistory` 定型
2. 再改 `.agent/runtime/tools/vscode_terminal_pty/extension.js` 的 artifact helper 區
   - 在 `resolveCaptureDir()`、`resolveCapturePath()`、`resolveArtifactNames()` 附近新增 rotation helper
3. 再把 rotation hook 掛進 `startCommand(context, kind)`
   - 新 session 啟動前 rotate current files
4. 再把 rotation hook 掛進 `restartCommand(context, kind)`
   - 舊 session close barrier 完成後 rotate，再啟動新 session
5. 再處理 `smokeTestCommand(context, kind, args)`
   - 第一版建議先以整次 smoke run 為單位 rotate，一次即可
6. 最後才補 README 與 maintainer contract
   - 把 current / rotated artifact 的用途與邊界寫清楚

#### 建議的 runtime 函式掛點清單

##### helper 區

- `resolveCaptureDir()`
- `resolveCapturePath(fileName)`
- `resolveArtifactNames(kind)`

建議在這一區旁邊新增：

- `ensureCaptureDir()`
- `resolveRotatedCapturePath(kind, fileType, timestamp)`
- `rotateArtifactFile(currentPath, rotatedPath)`
- `pruneRotatedArtifacts(kind, fileType, maxHistory)`
- `rotateCurrentArtifacts(kind, reason, options)`
- `touchCurrentArtifacts(kind)`

##### command 區

- `startCommand(context, kind)`
- `restartCommand(context, kind)`
- `smokeTestCommand(context, kind, args)`

##### registration 區

- `registerKindedCommand(...)`

建議補一個顯式 command，例如：

- `ivyhouseTerminalPty.rotateArtifacts`

讓 workflow bootstrap 或 operator 可以在需要時主動 rotate，而不是只能被 `start` / `restart` 被動觸發。

#### current 與 rotated 的判讀邊界

- current files
  - `codex_pty_debug.jsonl`
  - `codex_pty_live.txt`
  - `copilot_pty_debug.jsonl`
  - `copilot_pty_live.txt`
  - 供 workflow / preflight / operator 的主判讀面使用

- rotated files
  - 只保留最近幾輪 session evidence
  - 供人工回溯與 debug lineage 使用
  - 不應成為 preflight 或 workflow 的預設主判讀面

---

## 7. 摘要結論

目前 `/dev` workflow 已經具備完整主幹：

- 唯一入口
- 單一 Gate 來源
- Plan 狀態中心
- PTY 主路徑
- 條件式 Security Review
- Cross-QA
- Log / Close

所以現在的優化重點，已不是「流程不存在」，而是「哪些文件與 artifact 仍讓這條流程看起來比它實際上更混亂」。

對 maintainer 來說，下一個最值得做的 patch 仍然是：

> 以 `doc/` 作為單一 active artifact path，收斂 `/dev` workflow 文件中的 plan/log 路徑分裂。
