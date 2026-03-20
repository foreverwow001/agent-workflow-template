# Workflow Optimization Plan

> 建立日期：2026-03-15
> 狀態：Archived - MT-003 closure record
> 用途：保留 MT-003 `/dev` workflow 文件收斂工作的計畫、決策與關帳快照。active 收斂工作已完成，本檔不再作為現行維護入口。

## 0. 2026-03-17 狀態刷新

這份文件原本偏向提案稿；在 MT-003 關帳期間改作執行中狀態文件，現已轉為 archive 歷史紀錄。

> 2026-03-17 補註：原 `maintainers/chat/2026-03-17-dev-workflow-current-flow-and-optimization-map.md` 中與 `/dev` 現況流程、friction 地圖、rotation patch 提案直接相關的內容，已先收斂進本檔；MT-003 關帳後，本檔與其 closure snapshot 一併存入 archive。

### 已完成的前置條件

- PTY primary / consented fallback 的主架構已落檔，相關 authoritative 文件已形成。
- `AGENT_ENTRY.md` 已成為 active workflow 中 Gate、Security Review trigger 與 `EXECUTION_BLOCK` 契約的單一來源。
- Copilot CLI migration 已完成，不再需要把 workflow friction 與 backend rename 混在一起處理。

### 2026-03-18 關帳結果

- active docs、template、skills 與 log template 已收斂到 `doc/implementation_plan_index.md`、`doc/plans/Idx-NNN_plan.md`、`doc/logs/Idx-NNN_log.md` 這條 artifact chain。
- `AGENT_ENTRY.md` 與 supporting docs 已落地 askQuestions-first、`security_reviewer_tool`、baseline rules split、Mode Selection Gate 與 `lightweight-direct-edit` 分流。
- PTY artifact rotation runtime、bootstrap `reason="new-workflow"` 契約與對應回歸測試都已落地。
- `planner.md` 與 `coordinator.md` 的殘留支援文件重複敘事已清理；不再保留舊專案領域語彙與重複 `EXECUTION_BLOCK` schema。
- 已完成真實互動層 smoke：先驗證 `READ_BACK_REPORT -> Mode Selection Gate -> lightweight-direct-edit` 分流，再補跑一輪 `formal-workflow -> Plan Gate Approve -> executor_tool=codex-cli -> qa_tool=copilot-cli`。

### 目前剩餘事項

- MT-003 目前沒有阻斷關帳的未完成項。
- 若之後還要繼續優化，屬於下一輪 UX 微調，而不是本輪 contract/文件收斂 blocker。

## 1. 目標

這份計畫只處理 workflow 契約層的優化，不處理 PTY runtime、fallback bridge 或 CLI 安裝問題。

本輪優化的核心目標只有三個：

1. 刪掉會造成多重真相來源的過期規則。
2. 統一 workflow / 治理任務與專案功能任務的 plan / log / index 路徑模型。
3. 簡化 `/dev` 流程中的 gate wording，保留必要治理，但降低互動摩擦。

## 2. 現況結論

目前底層工具鏈已足以支撐 workflow 文件收斂，真正的阻塞已縮小到 active 文件契約本身。

已確認可工作的部分：

- READ_BACK_REPORT 的必讀檔鏈可以完成。
- `plan_validator.py` 可成功驗證代表性計畫。
- PTY preflight 與 fallback bridge 已恢復為 `status=pass`。
- deterministic Security Review trigger 規則本身可判讀。
- `AGENT_ENTRY.md` 已可承擔單一 Gate/trigger 契約來源角色。

目前最大的阻塞不在工具，而在文件契約：

- READ_BACK_REPORT 的硬停頓會把「啟動 `/dev`」拆成至少兩輪互動，造成明顯的 UX friction
- `AGENT_ENTRY.md` 已把 index 收斂到 `doc/implementation_plan_index.md`
- `planner.md`、`Idx-000_plan.template.md` 與多數 active 文件把 plan/log 預設落點放在 `doc/`
- `dev-team.md`、`qa.md` 與部分舊角色/系統文件仍保留 `.agent/plans`、`.agent/logs` 的 workflow/治理任務分流

這使得 `/dev` 在真正落地時，Planner、Coordinator、QA 與 skills evaluator 對同一份任務的 artifact 路徑理解並不一致。

## 2.5 當前 /dev 流程快照

為避免 active 區同時維護「分析地圖」與「執行計畫」兩份高度重疊的文檔，這裡直接吸收目前 `/dev` workflow 的最小完整快照。

### 固定角色與工具邊界

- Coordinator：GitHub Copilot Chat
- Engineer：`codex-cli` 或 `copilot-cli`
- Security Reviewer：`codex-cli` 或 `copilot-cli`（條件式）
- QA：`codex-cli` 或 `copilot-cli`
- Workflow 主路徑：`.agent/runtime/tools/vscode_terminal_pty`
- 條件式備援：`.agent/runtime/tools/vscode_terminal_fallback`

### 固定 artifact

- Index：`doc/implementation_plan_index.md`
- Plan：`doc/plans/Idx-NNN_plan.md`
- PTY current artifact：`.service/terminal_capture/*_pty_debug.jsonl`、`.service/terminal_capture/*_pty_live.txt`
- fallback 相容 artifact：`monitor_debug.jsonl`、`codex_live.txt`、`copilot_live.txt`、bridge token/events

### 當前流程摘要

1. `/dev` 觸發後，Coordinator 先做讀檔與 `READ_BACK_REPORT`
2. user 確認後，Planner 產出 Plan 與 `EXECUTION_BLOCK`
3. 進入 Plan Gate，收集 approve / domain review / security review / scope policy / backend policy
4. 進入 tool selection gate，決定 Engineer / Security Reviewer / QA 使用的終端工具
5. 在 Research Gate、Plan Validator Gate、Preflight Gate、Historical File Checkpoint 全部通過後，才進入執行
6. Engineer 透過 PTY command surface 執行並輸出 completion marker
7. 若命中 deterministic trigger，先做 Security Review，再進 QA
8. QA 完成後產生 log 並回填 Plan

### 當前狀態中心

現行 workflow 不是靠聊天上下文記住狀態，而是靠 Plan 中的 `EXECUTION_BLOCK` 續接至少以下欄位：

- `scope_policy`
- `expert_required`
- `security_review_required`
- `executor_tool`
- `security_reviewer_tool`
- `qa_tool`
- `last_change_tool`
- `log_file_path`

## 3. 決策原則

本計畫採以下原則，後續 patch 應以此為準：

1. 優先維持單一真相來源，不保留「兩條都可」的模糊說法。
2. 優先修改 active workflow 文件與角色文件；歷史文件只做降級或保持存檔。
3. 若某條規則只是為了保護品質，但帶來明顯互動摩擦，先簡化 wording 與回填流程，而不是直接刪除治理需求。
4. maintainer 自己的治理計畫，不再用正在收斂中的 workflow plan path 承載；因此本計畫放在 `maintainers/`，避免再次強化既有歧義。

## 4. 要刪的規則

### A. 刪除 workflow/治理任務使用 `.agent/plans` / `.agent/logs` 的 active 規則

這是目前最直接的多重真相來源。下列 active 說法應刪除或改寫：

- `workflow/治理改善任務 -> .agent/plans/Idx-NNN_plan.md`
- `workflow/治理任務：log 通常位於 .agent/logs/`
- 任何把 `.agent/plans/**`、`.agent/logs/**` 描述成 active workflow 預設落點的文字

這些規則目前的問題：

- repo 內沒有對應的 active 目錄與模板
- 與 `doc/implementation_plan_index.md`、`doc/plans/Idx-000_plan.template.md`、`planner.md` 的主敘事衝突
- 讓 QA / skills evaluator / log 回填無法假設單一路徑

### B. 刪除重複定義 gate 題組的次要敘事

`AGENT_ENTRY.md` 已宣告自己是 Gate 與 `EXECUTION_BLOCK` 契約的唯一來源。凡是其他 active 文件仍重新描述同一套題組、但 wording 或欄位不同，應刪除重複內容，保留連結與摘要即可。

優先清理對象：

- `.agent/workflows/dev-team.md`
- `.agent/roles/coordinator.md`
- `.agent/roles/qa.md`

### C. 刪除模板化、但沒有實際約束力的 placeholder 規則

`project_rules.md` 目前仍是模板內容，會讓 READ_BACK_REPORT 的「Top 5 硬約束」變成半真半假的占位文字。這不是 workflow engine bug，但會直接降低 `/dev` 的治理可信度。

本計畫現已收斂出較穩定的處理方式：

- template repo 自己的 active workflow baseline rule source 改由 `./.agent/workflow_baseline_rules.md` 承接
- root `project_rules.md` 保留在原位，作為新專案初始化時的預設規則模板
- `AGENT_ENTRY.md`、`setup_workflow.sh` 與移植文件必須清楚區分「template repo 維護時讀 baseline rules」與「新專案落地時使用 project_rules.md」

這代表本輪不再把 root `project_rules.md` 直接升格為 template repo 的 active authoritative 規則檔，而是將「template 自身規則」與「下游專案起始模板」正式拆開。

## 5. 要統一的路徑

### 目標模型

本輪建議直接收斂到單一路徑模型：

- Index：`doc/implementation_plan_index.md`
- Plan：`doc/plans/Idx-NNN_plan.md`
- Log：`doc/logs/Idx-NNN_log.md`

### 收斂理由

1. 現有模板、planner 說明與多數 skill 示例已主要指向 `doc/`
2. `AGENT_ENTRY.md` 已把兩種任務類型共用到同一份 index
3. 若保留 `.agent/plans` / `.agent/logs`，必須同步補齊目錄、模板、索引與 evaluator 預設值，成本較高且沒有明顯收益

### 需要同步修改的 active 文件

- `.agent/workflows/dev-team.md`
- `.agent/roles/qa.md`
- `.agent/roles/coordinator.md`
- `.agent/VScode_system/Ivy_Coordinator.md`
- `.agent/VScode_system/tool_sets.md`
- `.agent/skills/skills-evaluator/scripts/skills_evaluator.py`
- `doc/plans/Idx-000_plan.template.md`

### 需保留但降級為歷史/說明的對象

- `doc/AGENT_WORKFLOW_TEMPLATE_UPSTREAM.md`
- `maintainers/chat/archive/**`
- 舊 changelog 與過渡期 handoff

## 6. 要簡化的 gate wording

### A. READ_BACK_REPORT 保留，但改成「完成後等待確認」的最短說法

現在的 READ_BACK_REPORT 契約本身不是錯，但文字密度過高，會讓 `/dev` 啟動成本偏大。
更重要的是，現行硬停頓會把「啟動 `/dev`」拆成至少兩輪互動；這不是 bug，而是需要被明確決策的 UX checkpoint。

建議：

- 保留「先讀三份檔案再回報」的治理要求
- 精簡重複的禁止句與警告句
- 把輸出模板、停止條件與例外條件切成更短的段落
- 在本輪明確決定：是否保留 READ_BACK_REPORT 的硬停頓，或改成可由 user 一次確認後直接進 Plan 的較順暢模式

### B. Approve Gate / Role Selection Gate 改成單一題組摘要

現在多份文件都提到 Gate，但使用者真正需要面對的問題應該是一組固定題目，而不是在不同文件中看不同版本的敘事。

建議：

- `AGENT_ENTRY.md` 保留完整題組
- `dev-team.md` 與 `coordinator.md` 只保留一句摘要加連結
- 避免在多個地方重複列出 `executor_tool`、`qa_tool`、`execution_backend_policy` 等欄位描述

### C. Security Review wording 改成「何時必觸發」而不是大段重述

deterministic trigger 已成形，但目前相關文件仍有大量輔助說明。建議保留 trigger matrix 的單一來源，其他文件只回答兩個問題：

- 何時會進 Security Review
- 若進入後，Coordinator / Reviewer 各自必須做什麼

### D. Preflight wording 改成「必跑命令 + pass 條件」

目前 preflight 已有清楚腳本與狀態模型，文件可以再精簡：

- 必跑哪條命令
- 什麼結果可進 Engineer
- 什麼時候可切 fallback

避免在多處重複解釋整個 PTY / fallback 架構。

### E. User-facing Gate 改成 askQuestions-first

目前 `/dev` 的 major friction 不只來自 wording，也來自「同一輪 workflow 需要 user 反覆手打下一句 prompt」。

建議把 user-facing decision point 改成：

- 預設使用 VS Code Insider 內建 `#askQuestions`
- 只有在工具不可用、需要自由文字理由、或選項不足時，才退回一般聊天輸入

這項改動的本質是 workflow interaction contract，不是一般 repo coding rule，因此 authoritative 規格應落在 `AGENT_ENTRY.md`，而不是 `project_rules.md`。

### E-2. 輕量直改模式應作為正式 workflow 外的分流，而不是 Engineer 第三工具

GitHub Copilot Chat 目前不適合直接納入正式 `/dev` workflow 的 Engineer / QA / Security Reviewer 工具選單；若直接把它加入 `executor_tool`，會破壞既有 terminal-backed execution、completion marker、PTY artifact、Cross-QA 與 `last_change_tool` 假設。

本輪收斂的方向是：

- 保留正式 workflow 的工具邊界不變：Engineer / QA / Security Reviewer 仍為 `codex-cli|copilot-cli`
- 新增一條 **輕量直改模式（lightweight direct-edit lane）**，由 GitHub Copilot Chat 直接處理低風險、小範圍修正
- 這條 lane 不併入正式 `executor_tool` 選單，也不把 Copilot Chat 定義成第三個 Engineer tool

為避免判斷點只存在聊天上下文，應在入口新增一個明確的 **Mode Selection Gate**：

- 位置：`READ_BACK_REPORT` 確認之後、正式 Plan 之前
- 決策：`formal-workflow` 或 `lightweight-direct-edit`
- 預設：`formal-workflow`
- 只有符合輕量條件時，Coordinator 才能提供 `lightweight-direct-edit` 作為選項

第一版建議的輕量條件：

- 單檔或極少數檔案的小修正
- 不涉及 dependency / runtime / preflight / 長流程 terminal 執行
- 不命中安全敏感路徑與 deterministic Security Review trigger
- 不需要獨立 QA log、Cross-QA 或多角色接力
- 一旦執行中 scope 擴張，必須立刻升級回正式 `/dev` workflow

### F. Security Reviewer 也應進入 tool selection model

目前 Engineer 與 QA 都需要 user 選工具，但 Security Reviewer 仍停留在「若被觸發就執行」的描述層。

若 Security Review 已是 active workflow 的正式條件式階段，則它也應與 Engineer / QA 一樣，進入明確的 tool selection 與欄位回填模型。

建議：

- 只有在 `security_review_required=true` 時，才要求 user 選擇 `security_reviewer_tool`
- 欄位值與其他角色一致，使用 `codex-cli|copilot-cli`
- 結果仍回填到 `EXECUTION_BLOCK`，避免只留在聊天上下文

### G. PTY current artifact 先做到 rotation

目前 PTY 主路徑的 `*_pty_debug.jsonl` / `*_pty_live.txt` 採固定檔名 append 模型，容易混入多輪舊內容。

本輪不直接停在 truncate current files，而是先做到 rotation 這一層：

- 每次 `start` / `restart` / 新 workflow 任務前，把 current artifact rotate 成歷史檔
- 固定檔名只保留 current view，避免 workflow / preflight / operator 讀到混雜的舊 run
- rotation 後的歷史檔採可預測命名，保留最近幾輪 session evidence

這樣能同時解掉「同檔混入舊 run」與「完全失去上一輪證據」兩個問題，而不需要一步到位引入完整 archive manager。

## 6.5 精確變更提案清單

以下提案是目前建議納入下一輪 workflow 契約收斂的具體提案。

### Proposal A. askQuestions-first Gate contract

#### authoritative 文件

- `.agent/workflows/AGENT_ENTRY.md`

#### supporting 文件

- `.agent/workflows/dev-team.md`
- `.agent/roles/coordinator.md`
- `.agent/VScode_system/Ivy_Coordinator.md`
- `.agent/VScode_system/tool_sets.md`
- `project_rules.md`（僅高層原則，可選）

#### 要新增或改寫的規則

- 在 `AGENT_ENTRY.md` 第 3 節新增 interaction contract：
	- 所有 user-facing Gate 預設使用 VS Code Insider 內建 `#askQuestions`
	- 只有工具不可用、需要自由文字說明、或選項不足時才退回一般 prompt

- 將下列節點明確列為 askQuestions-first：
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

#### authoritative 文件

- `.agent/workflows/AGENT_ENTRY.md`

#### supporting 文件

- `.agent/workflows/dev-team.md`
- `.agent/roles/coordinator.md`
- `.agent/roles/security.md`
- `doc/plans/Idx-000_plan.template.md`

#### 要新增或改寫的欄位

- 在 `EXECUTION_BLOCK` 新增：
	- `security_reviewer_tool: [N/A|待用戶確認: codex-cli|copilot-cli]`
	- `security_review_start: [YYYY-MM-DD HH:mm:ss]`
	- `security_review_end: [YYYY-MM-DD HH:mm:ss]`
	- `security_review_result: [N/A|PASS|PASS_WITH_RISK|FAIL]`

#### 規則建議

- 若 `security_review_required=false`
	- `security_reviewer_tool = N/A`
- 若 `security_review_required=true`
	- Coordinator 必須以 askQuestions 要求 user 選擇 `codex-cli` 或 `copilot-cli`
- 若 workflow 一開始未觸發 Security Review，但在 scope 變更後觸發
	- 需補做一次 askQuestions，而不是沿用預設值

### Proposal C. PTY artifact rotation

#### 要改的 runtime 文件

- `.agent/runtime/tools/vscode_terminal_pty/extension.js`
- `.agent/runtime/tools/vscode_terminal_pty/package.json`
- `.agent/runtime/tools/vscode_terminal_pty/README.md`
- `maintainers/chat/2026-03-13-pty-monitor-and-capture-contract.md`

#### 要新增或改寫的設定

- 在 PTY 設定加入：
	- `ivyhouseTerminalPty.rotateArtifactsOnStart`
	- `ivyhouseTerminalPty.rotateArtifactsOnRestart`
	- `ivyhouseTerminalPty.rotateArtifactsOnNewWorkflow`
	- `ivyhouseTerminalPty.rotationMaxHistory`

第一版建議預設：

- `rotateArtifactsOnStart = true`
- `rotateArtifactsOnRestart = true`
- `rotateArtifactsOnNewWorkflow = true`
- `rotationMaxHistory = 5`

#### 要做 rotation 的 current files

- `codex_pty_debug.jsonl`
- `codex_pty_live.txt`
- `copilot_pty_debug.jsonl`
- `copilot_pty_live.txt`

#### 建議掛點

- `ivyhouseTerminalPty.startCodex`
- `ivyhouseTerminalPty.startCopilot`
- `ivyhouseTerminalPty.restartCodex`
- `ivyhouseTerminalPty.restartCopilot`
- workflow coordinator 在開始新 `/dev` 任務前的 bootstrap hook

#### 建議命名與保留策略

- current 檔仍維持：
	- `codex_pty_debug.jsonl`
	- `codex_pty_live.txt`
	- `copilot_pty_debug.jsonl`
	- `copilot_pty_live.txt`
- rotation 檔建議採：
	- `<backend>_pty_debug.<timestamp>.jsonl`
	- `<backend>_pty_live.<timestamp>.txt`
- 每個 backend 只保留最近 `rotationMaxHistory` 組 rotation 檔，超過時刪最舊的 rotation artifact

#### 建議的 runtime patch 順序

1. 先改 `.agent/runtime/tools/vscode_terminal_pty/package.json`
	- 先把 rotation 設定與預設值定型，避免 extension 先落地但設定面仍不穩定
2. 再改 `.agent/runtime/tools/vscode_terminal_pty/extension.js` 的 artifact helper 區
	- 以 `resolveCaptureDir`、`resolveCapturePath`、`resolveArtifactNames` 為核心，先新增 rotation helper
3. 再把 rotation hook 掛進 `startCommand(context, kind)`
	- 新 session 啟動前先 rotate current files
4. 再把 rotation hook 掛進 `restartCommand(context, kind)`
	- 建議在舊 session close barrier 完成後再 rotate，避免切斷舊 session 的結尾證據
5. 再處理 `smokeTestCommand(context, kind, args)`
	- 第一版建議以整次 smoke run 為單位 rotate 一次，不要每個 iteration 都 rotate
6. 最後補 `.agent/runtime/tools/vscode_terminal_pty/README.md` 與 `2026-03-13-pty-monitor-and-capture-contract.md`
	- 明確定義 current 與 rotated artifact 的判讀邊界

#### 建議新增的 helper 函式

- `ensureCaptureDir()`
- `resolveRotatedCapturePath(kind, fileType, timestamp)`
- `rotateArtifactFile(currentPath, rotatedPath)`
- `pruneRotatedArtifacts(kind, fileType, maxHistory)`
- `rotateCurrentArtifacts(kind, reason, options)`
- `touchCurrentArtifacts(kind)`

#### 建議的 command / hook 掛點

- `startCommand(context, kind)`
- `restartCommand(context, kind)`
- `smokeTestCommand(context, kind, args)`
- `registerKindedCommand(...)`

#### 建議新增的顯式 command

- `ivyhouseTerminalPty.rotateArtifacts`

用途：

- 讓 workflow bootstrap 或 operator 在需要時主動 rotate
- 避免 rotation 只能被 `start` / `restart` 被動觸發

#### current 與 rotated artifact 的判讀邊界

- current files
  - workflow / preflight / operator 的主判讀面
- rotated files
  - 只作最近幾輪歷史回溯
  - 不應成為 preflight 或 workflow 的預設主判讀面

### Proposal D. Baseline rules split for template repo vs new project

#### authoritative 文件

- `.agent/workflows/AGENT_ENTRY.md`

#### supporting 文件

- `.agent/workflow_baseline_rules.md`
- `project_rules.md`
- `.agent/scripts/setup_workflow.sh`
- `README.md`
- `.agent/PORTABLE_WORKFLOW.md`
- `.agent/PR_PREPARATION.md`

#### 已收斂決策

- template repo 維護時，active baseline rule source 改讀 `./.agent/workflow_baseline_rules.md`
- root `project_rules.md` 保留為新專案初始化時的 starter template
- 新專案若沒有額外規則，可直接沿用 `project_rules.md`；若有差異，再在該檔增補

#### 要新增或改寫的規則

- `AGENT_ENTRY.md` 的必讀清單在 template repo 內改為讀 `./.agent/workflow_baseline_rules.md`
- `README.md`、移植文件與 setup script 必須明寫：
	- template repo 維護時讀 baseline rules
	- 新專案落地時使用 root `project_rules.md`
- root `project_rules.md` 不再承擔 template repo 自己的 active authoritative 規則來源角色

#### 目的

- 解掉「同一份 `project_rules.md` 同時扛 active rule source 與下游模板」的角色衝突
- 保留新專案可直接複用的規則模板
- 避免 READ_BACK_REPORT 讀到 placeholder 規則而降低治理可信度

### Proposal E. Lightweight direct-edit lane

#### authoritative 文件

- `.agent/workflows/AGENT_ENTRY.md`

#### supporting 文件

- `.agent/workflows/dev-team.md`
- `.agent/roles/coordinator.md`
- `.agent/VScode_system/Ivy_Coordinator.md`
- `.agent/VScode_system/tool_sets.md`
- `project_rules.md`（僅高層原則）

#### 已收斂決策

- GitHub Copilot Chat 不納入正式 `/dev` workflow 的 Engineer / QA / Security Reviewer 工具選單
- 另開一條正式 workflow 外的 `lightweight-direct-edit` 分流，用於低風險、小範圍修正
- 輕量分流不改寫既有 `executor_tool|qa_tool|last_change_tool` 的正式工具模型

#### 要新增或改寫的 gate

- 在 `READ_BACK_REPORT` 確認之後、Plan 之前新增 **Mode Selection Gate**
- Coordinator 必須先判斷任務是否符合輕量條件；符合時，才可詢問 user：
	- `formal-workflow`
	- `lightweight-direct-edit`
- 若 user 選擇 `lightweight-direct-edit`，由 GitHub Copilot Chat 直接處理，不進 formal Plan / Engineer / QA / Log 鏈
- 若不符合條件或執行中 scope 擴張，必須升級回正式 `/dev` workflow

#### 第一版建議條件

- 單檔或極少數檔案修正
- 不涉及 dependency、preflight、終端長流程執行
- 不命中安全敏感路徑或 deterministic Security Review trigger
- 不要求獨立 QA、Cross-QA、completion marker、PTY artifact 稽核

#### 目的

- 讓簡單修正可由 GitHub Copilot Chat 直接完成，避免每次都進完整 `/dev`
- 同時維持正式 workflow 的 terminal-backed contract 不被破壞

## 7. 分階段實作狀態

### Phase 0: 前置收斂

狀態：**已完成**

- PTY-primary / consented-fallback 心智模型已落成 active docs
- Gate 與 Security Review trigger 已集中到 `AGENT_ENTRY.md`
- Copilot CLI migration 已完成，active truth 已改成 `codex-cli|copilot-cli`

### Phase 1: 路徑收斂

狀態：**已完成**

目標：先消除 `.agent/` 與 `doc/` 的 active path 分裂。

要做的事：

- 改寫 `dev-team.md` 中 workflow/治理任務使用 `.agent/plans` / `.agent/logs` 的敘事
- 改寫 `qa.md` 中 skills-evaluator 的預設 log 路徑敘事
- 更新 `coordinator.md`、`Ivy_Coordinator.md`、`tool_sets.md` 的 plan/log 路徑描述

Acceptance：

- active 文件不再把 `.agent/plans` / `.agent/logs` 當成預設 workflow artifact path

### Phase 2: Gate 單一來源化

狀態：**已完成**

目標：真正讓 `AGENT_ENTRY.md` 成為唯一 Gate 契約來源。

要做的事：

- 刪掉 `coordinator.md`、`qa.md` 中仍會讓讀者誤以為另有 Gate 規格的重複敘事
- 把 askQuestions-first 與 `security_reviewer_tool` 一併收斂到 `AGENT_ENTRY.md` 單一來源
- 保留角色責任、操作順序與必做命令
- 補明「引用 AGENT_ENTRY 單一來源」的短句

Acceptance：

- active 文件中不再出現互相競爭的 Gate 題組

### Phase 3: Wording 瘦身

狀態：**已完成**

目標：降低 `/dev` 啟動與 Gate 互動的閱讀成本。

要做的事：

- 精簡 READ_BACK_REPORT 與 Gate 禁止句的重複段落
- 明確決定 READ_BACK_REPORT 的硬停頓是否保留，並把決策寫回入口文件
- 將 user-facing Gate 改寫成 askQuestions-first，而不是要求 user 反覆手打下一句 prompt
- 決定並落地 Mode Selection Gate，明確區分 `formal-workflow` 與 `lightweight-direct-edit`
- 把 Security Review / Preflight 文字收斂成最少必要說明
- 檢查 user-facing wording 是否仍清楚、但不冗長

Acceptance：

- `/dev` 入口、Gate、Role Selection 的說明可在更短篇幅內完整成立
- `/dev` 的第一段互動不再讓 user 對「現在只是讀檔、還是已正式進入任務」產生不必要歧義

### Phase 4: 模板與技能對齊

狀態：**已完成**

目標：讓 Plan/Log 模板與 skills 命令示例跟新的單一路徑完全一致。

要做的事：

- 更新 `Idx-000_plan.template.md`
- 新增 `security_reviewer_tool` 與 Security Review 執行欄位
- 更新 `skills-evaluator.py` 的 suggestion 與 README / INDEX 示例
- 將 template repo baseline rules 與新專案 `project_rules.md` 的分工寫回 setup / portable 文件
- 視需要調整 `planner.md`、`qa.md`

Acceptance：

- Planner、QA、skills evaluator、template 之間不再互相指向不同 artifact path

### Phase 5: PTY artifact rotation

狀態：**已完成**

目標：把 PTY current artifact 從 append-only 固定檔，提升成 current + rotated history 的雙層模型。

要做的事：

- 在 `.agent/runtime/tools/vscode_terminal_pty/extension.js` 加入 artifact rotation hook
- 在 `package.json` 暴露 rotation 相關設定
- 在 PTY README 與 maintainer 契約文檔補明 current / rotated artifact 行為

Acceptance：

- `start` / `restart` / 新 workflow 任務前，current PTY artifact 會先 rotate，再開始新一輪 current evidence
- current 檔只承載最新 session evidence
- rotated 檔可保留最近幾輪 session evidence，且不影響 workflow / preflight 對 current 檔的判讀

## 8. 不在本輪處理的事項

- PTY runtime 的完整 archive manager
- 新增真正的 slash-command 自動化 runner
- 重新設計 Security Review trigger 規則本身
- 大幅改寫整套角色 persona 文案

## 9. 後續建議

本輪 MT-003 已可視為關帳。

若要再開下一輪，建議只做「非阻斷性的 UX 微調」，不要再把已落地的 contract/路徑收斂重新打散。

較合理的 follow-up 題目只有兩類：

- 進一步縮短 `READ_BACK_REPORT` 與 supporting docs 的 wording
- 視實際使用經驗再決定是否需要額外的 slash-command 自動化 runner

## 10. 完成定義

當以下條件同時成立，這份優化計畫可視為完成：

1. active workflow 文件對 plan/log/index path 只剩單一說法
2. `AGENT_ENTRY.md` 以外的 active 文件不再重複定義另一套 Gate 題組
3. `/dev` smoke 不再因文件契約漂移而需要人工解釋「這個 plan 應該放哪裡」
4. workflow friction list 中與路徑分裂、Gate wording 重複直接相關的項目已關帳

2026-03-18 補註：以上四項已達成；MT-003 依目前範圍可視為完成。
