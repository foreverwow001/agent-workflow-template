# Template Workflow Analysis

> 建立日期：2026-03-11
> 狀態：Archived - superseded in terminal-tooling scope by `2026-03-13-terminal-pty-target-architecture-and-migration-principles.md`
> 用途：整理 `agent-workflow-template` 目前實際採用的 workflow 結構、角色分工、skills、tools、gates、執行步驟，以及文件中仍存在的 legacy 殘留與落差。
>
> 2026-03-13 補註：本文件在 workflow / gate / 角色治理層仍可參考，但 terminal tooling 的主架構、fallback 定位與遷移方向，已由 `2026-03-13-terminal-pty-target-architecture-and-migration-principles.md` 取代；不要再以本文件中的 sendText / Monitor / Orchestrator 主路徑描述作為新實作決策基準。

---

## 1. 整體結論

目前這個 template 的 workflow，本質上是一個「由 GitHub Copilot Chat 擔任 Coordinator，去協調 Planner / Expert / Engineer / QA 的治理型流程」，而不是單純的 prompt。

它的正式流程主幹主要寫在：

- [.agent/workflows/AGENT_ENTRY.md](../../../.agent/workflows/AGENT_ENTRY.md)
- [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md)
- [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md)

再由以下 VS Code 系統檔補成實際操作規約：

- [.agent/VScode_system/Ivy_Coordinator.md](../../../.agent/VScode_system/Ivy_Coordinator.md)
- [.agent/VScode_system/prompt_dev.md](../../../.agent/VScode_system/prompt_dev.md)
- [.agent/VScode_system/tool_sets.md](../../../.agent/VScode_system/tool_sets.md)
- [.agent/VScode_system/chat_instructions_ivy_house_rules.md](../../../.agent/VScode_system/chat_instructions_ivy_house_rules.md)

如果把整條流程壓成一句話，現在的設計是：

> 先讀規則與索引，先出 Plan，經過使用者核准與多個 Gate，再由 Codex CLI 或 OpenCode 在 VS Code terminal 實作，最後做 Cross-QA、寫 Log、收尾。

---

## 2. Workflow 主流程

### 2.1 觸發方式

- 使用者輸入 `/dev` 或 `/dev-team`
- 入口定義見：
  - [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md)
  - [.agent/VScode_system/prompt_dev.md](../../../.agent/VScode_system/prompt_dev.md)

Coordinator 的固定身份是 GitHub Copilot Chat，定義見：

- [.agent/VScode_system/Ivy_Coordinator.md](../../../.agent/VScode_system/Ivy_Coordinator.md)
- [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md)

### 2.2 入口 Gate：必讀檔案 + 已讀驗收回報

理論上，任何工作在開始產出 Plan 前，必須先走 [AGENT_ENTRY.md](../../../.agent/workflows/AGENT_ENTRY.md) 的入口流程：

1. 逐檔打開必讀文件
2. 輸出 `READ_BACK_REPORT`
3. 等使用者確認
4. 未完成前，不得出 Plan、不得執行、不得 QA

### 2.3 Goal / SPEC 階段

Coordinator 先做目標釐清，輸出：

- 你理解的目標
- Out of Scope
- 驗收條件草案

這套雙模式在下列檔案中定義：

- [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md)
- [.agent/VScode_system/Ivy_Coordinator.md](../../../.agent/VScode_system/Ivy_Coordinator.md)

模式分為：

- `SPEC_MODE`：只做需求釐清、Plan 品質、風險與驗收標準
- `ORCH_MODE`：Plan 核准後才做 terminal 注入、監控、Gate 判定、Log 回填

### 2.4 Planner 階段

Planner 角色由以下檔案定義：

- [.agent/roles/planner.md](../../../.agent/roles/planner.md)

Planner 要做的事：

1. 理解需求
2. 先讀相關 code，不可憑空規劃
3. 產出 Plan / Spec
4. Plan 必須符合模板

Plan 模板在：

- [doc/plans/Idx-000_plan.template.md](../../../doc/plans/Idx-000_plan.template.md)

Plan 必備結構：

- `## 📋 SPEC`
- `## 🔍 RESEARCH & ASSUMPTIONS`
- `## 🔒 SCOPE & CONSTRAINTS`
- `## 📁 檔案變更`
- `EXECUTION_BLOCK`

### 2.5 Expert Review 階段

正式流程文本目前寫的是 Meta Expert（現已由 Domain Expert 角色承接）：

- [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md)
- [.agent/roles/domain_expert.md](../../../.agent/roles/domain_expert.md)

但 repo 也有一份泛用的 Domain Expert：

- [.agent/roles/domain_expert.md](../../../.agent/roles/domain_expert.md)

因此概念上有「領域專家」這一層，但目前正式流程文件仍偏向舊的 Meta 廣告場景。

### 2.6 Role Selection Gate

這是整條 workflow 最核心的治理關卡之一，定義在：

- [.agent/workflows/AGENT_ENTRY.md](../../../.agent/workflows/AGENT_ENTRY.md)
- [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md)

這一步要決定：

1. `executor_tool` 是 `codex-cli` 或 `opencode`
2. `qa_tool` 是 `codex-cli` 或 `opencode`
3. `qa_tool` 必須不等於 `last_change_tool`
4. 命令注入固定走 extension sendText
5. 監測預設走 Proposed API，失敗才用 extension fallback

選擇結果會寫入 Plan 的 `EXECUTION_BLOCK`。

### 2.7 執行前前置 Gate

在正式 Execute 前，流程要求先通過多個 Gate：

#### Research Gate

若 `research_required: true`，或依賴檔案變更，則必須補齊來源或假設風險。

定義見：

- [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md)
- [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md)

#### Plan Validator Gate

用以下工具驗證 Plan 是否真的符合規範：

- [.agent/skills/plan-validator/scripts/plan_validator.py](../../../.agent/skills/plan-validator/scripts/plan_validator.py)

驗證重點：

- 必要段落是否存在
- `research_required:` 是否存在
- `EXECUTION_BLOCK` 是否存在
- `executor_tool:`、`qa_tool:`、`last_change_tool:` 是否存在

#### Preflight Gate

用以下腳本確認終端監控基礎設施是否可用：

- [.agent/runtime/scripts/vscode/workflow_preflight_check.py](../../../.agent/runtime/scripts/vscode/workflow_preflight_check.py)

它會檢查：

- Proposed API 狀態
- Bridge healthz
- Bridge token

#### 歷史檔保留 Checkpoint

禁止隨便改 `.agent/plans/**`、`.agent/logs/**` 類的歷史檔。

規則寫在：

- [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md)
- [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md)

### 2.8 Execute 階段

正式實作只允許由被選定的 Executor 動手。

Copilot Chat 不直接改 code，這點在以下文件中都是硬規則：

- [.agent/workflows/AGENT_ENTRY.md](../../../.agent/workflows/AGENT_ENTRY.md)
- [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md)
- [.agent/VScode_system/tool_sets.md](../../../.agent/VScode_system/tool_sets.md)

真正改碼的是：

- `codex-cli`
- `opencode`

而且這兩者都是在 VS Code terminal 中執行，不是在一般 bash 代送。

### 2.9 Completion Marker

Engineer / QA / Fix 完成時，必須輸出固定的 completion marker。

規則寫在：

- [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md)
- [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md)
- [.agent/roles/engineer.md](../../../.agent/roles/engineer.md)
- [.agent/roles/qa.md](../../../.agent/roles/qa.md)

核心要求：

- 5 行固定格式
- 必須是終端最後 5 個非空白行
- Coordinator 依據 marker 判定階段完成

### 2.10 QA 階段

QA 不是形式檢查，而是治理檢查 + 交叉審查。

核心規則定義於：

- [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md)
- [.agent/roles/qa.md](../../../.agent/roles/qa.md)

QA 內容包括：

- Cross-QA 規則檢查
- Checklist 檢查
- 問題表格
- PASS / PASS WITH RISK / FAIL 判定

### 2.11 Fix Loop / Rollback

若 QA FAIL，就回到 Engineer 修正，再重新 QA，形成 fix loop。

相關規則在：

- [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md)
- [.agent/roles/qa.md](../../../.agent/roles/qa.md)
- [doc/plans/Idx-000_plan.template.md](../../../doc/plans/Idx-000_plan.template.md)

Rollback 也有分級：

- L1 自我修正
- L2 回滾建議
- L3 Copilot 建議回滾
- L4 任務中止

### 2.12 Log 與 Close

QA 結束後必須寫 Log，保留 Plan，commit 與否由使用者決定。

流程規則在：

- [.agent/workflows/AGENT_ENTRY.md](../../../.agent/workflows/AGENT_ENTRY.md)
- [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md)

---

## 3. Agents / Roles

| 角色 | 目前定位 | 主要來源 |
|------|----------|----------|
| Coordinator | 固定是 GitHub Copilot Chat，只做協調、Gate、Plan/Log 回填、終端監控，不做實作 | [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md), [.agent/VScode_system/Ivy_Coordinator.md](../../../.agent/VScode_system/Ivy_Coordinator.md) |
| Planner | 產出 Spec / Plan | [.agent/roles/planner.md](../../../.agent/roles/planner.md) |
| Expert | 正式流程文本歷史上是 Meta Expert；現況由 generic Domain Expert 承接 | [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md), [.agent/roles/domain_expert.md](../../../.agent/roles/domain_expert.md) |
| Engineer | 真正改 code 的執行者 | [.agent/roles/engineer.md](../../../.agent/roles/engineer.md) |
| QA | 真正做驗收與 Cross-QA 檢查的審查者 | [.agent/roles/qa.md](../../../.agent/roles/qa.md) |

---

## 4. Skills

技能索引在：

- [.agent/skills/INDEX.md](../../../.agent/skills/INDEX.md)

### 4.1 強制或核心技能

| Skill | 作用 | 在流程中的地位 |
|------|------|----------------|
| `plan_validator.py` | 驗證 Plan 段落與 `EXECUTION_BLOCK` 欄位 | 強制 Gate |
| `code_reviewer.py` | 檢查 API key 洩漏、檔案過長、缺中文註釋 | Python 變更時必跑 |
| `test_runner.py` | 執行 pytest，輸出 JSON 結果 | 有測試時必跑 |
| `git_stats_reporter.py` | 解析 numstat，決定 Maintainability / UI-UX Gate 是否觸發 | Gate 判定工具 |
| `skills_evaluator.py` | 從 Log 的技能報告表格產出統計 | 收尾與稽核輔助 |

### 4.2 輔助技能

| Skill | 作用 |
|------|------|
| `doc_generator.py` | 從 Python 檔產生 Markdown 說明 |
| `github_explorer.py` | 從 GitHub 搜尋、預覽、下載外部技能 |
| `manifest_updater.py` | 同步 skill manifest |
| `explore-cli-tool/SKILL.md` | 新 CLI 工具探索 SOP |

### 4.3 各技能實際檢查內容

#### plan_validator.py

來源：

- [.agent/skills/plan-validator/scripts/plan_validator.py](../../../.agent/skills/plan-validator/scripts/plan_validator.py)

檢查內容：

- `## 📋 SPEC`
- `## 🔍 RESEARCH & ASSUMPTIONS`
- `## 🔒 SCOPE & CONSTRAINTS`
- `## 📁 檔案變更`
- `EXECUTION_BLOCK_START / END`
- `research_required:`
- `executor_tool:`
- `qa_tool:`
- `last_change_tool:`

#### code_reviewer.py

來源：

- [.agent/skills/code-reviewer/scripts/code_reviewer.py](../../../.agent/skills/code-reviewer/scripts/code_reviewer.py)

檢查內容：

- API key 洩漏
- 檔案是否超過 500 行
- 前幾行是否有繁體中文用途註釋

#### test_runner.py

來源：

- [.agent/skills/test-runner/scripts/test_runner.py](../../../.agent/skills/test-runner/scripts/test_runner.py)

功能：

- 在專案根目錄執行 pytest
- 輸出 pass / fail / no_tests / error JSON

#### git_stats_reporter.py

來源：

- [.agent/skills/git-stats-reporter/scripts/git_stats_reporter.py](../../../.agent/skills/git-stats-reporter/scripts/git_stats_reporter.py)

功能：

- 解析 `git diff --numstat`
- 計算總變更行數
- 決定是否觸發：
  - `maintainability_gate`
  - `ui_ux_gate`

#### skills_evaluator.py

來源：

- [.agent/skills/skills-evaluator/scripts/skills_evaluator.py](../../../.agent/skills/skills-evaluator/scripts/skills_evaluator.py)

功能：

- 解析 Log 裡的 `SKILLS_EXECUTION_REPORT`
- 計算技能執行次數
- 統計成功率與失敗清單

---

## 5. Tools

### 5.1 協調工具

- GitHub Copilot Chat
- Slash command `/dev` / `/dev-team`

來源：

- [.agent/VScode_system/prompt_dev.md](../../../.agent/VScode_system/prompt_dev.md)

### 5.2 執行工具

- `codex-cli`
- `opencode`

來源：

- [.agent/VScode_system/tool_sets.md](../../../.agent/VScode_system/tool_sets.md)

### 5.3 Terminal 注入工具

以下內容反映的是當時分析時的架構狀態；legacy injector/monitor/orchestrator 已於後續 migration cleanup 中移除。

安裝腳本：

- [.agent/runtime/scripts/vscode/install_terminal_orchestrator.sh](../../../.agent/runtime/scripts/vscode/install_terminal_orchestrator.sh)

當時的主注入元件：legacy injector extension（現已刪除）

責任：

- 啟動 `Codex CLI` / `OpenCode CLI` terminal
- 送 `sendText`
- 送 Enter

### 5.4 Terminal 監測工具

監測主路徑：

- VS Code Proposed API

Fallback：

當時是 monitor extension（現已刪除）

來源：

- [.agent/runtime/scripts/vscode/workflow_preflight_check.py](../../../.agent/runtime/scripts/vscode/workflow_preflight_check.py)

### 5.5 VS Code 工作區支撐

工作區設定檔：

- [.vscode/settings.json](../../../.vscode/settings.json)
- [.vscode/extensions.json](../../../.vscode/extensions.json)
- [.vscode/tasks.json](../../../.vscode/tasks.json)

實際作用：

- 推薦安裝必要 extensions
- 關閉過度自動化 save 行為
- 保留較安全的 Git / review / editor 行為
- 支援 Copilot terminal command 功能

---

## 6. Gates

| Gate | 目的 | 觸發位置 |
|------|------|----------|
| READ_BACK_REPORT Gate | 沒讀完規則與索引前，不准出 Plan | [.agent/workflows/AGENT_ENTRY.md](../../../.agent/workflows/AGENT_ENTRY.md) |
| Goal Confirmation Gate | 先確認目標與 out-of-scope | [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md) |
| Plan Approval Gate | 使用者未明確核准，不准執行 | [.agent/workflows/AGENT_ENTRY.md](../../../.agent/workflows/AGENT_ENTRY.md) |
| Role Selection Gate | 選 Engineer / QA 工具與 backend policy | [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md) |
| Research Gate | 要研究就必須補來源或風險假設 | [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md), [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md) |
| Plan Validator Gate | Plan 不合格，不准進 Engineer | [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md), [.agent/skills/plan-validator/scripts/plan_validator.py](../../../.agent/skills/plan-validator/scripts/plan_validator.py) |
| Preflight Gate | Proposed API / bridge 狀態不合格，不准注入 | [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md), [.agent/runtime/scripts/vscode/workflow_preflight_check.py](../../../.agent/runtime/scripts/vscode/workflow_preflight_check.py) |
| Scope Gate | 變更超出檔案白名單就停下 | [.agent/workflows/AGENT_ENTRY.md](../../../.agent/workflows/AGENT_ENTRY.md), [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md) |
| Skill Execution Gate | 每次 Python 變更都要跑 reviewer / test | [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md) |
| Cross-QA Gate | `qa_tool ≠ last_change_tool` | [.agent/workflows/AGENT_ENTRY.md](../../../.agent/workflows/AGENT_ENTRY.md), [.agent/roles/qa.md](../../../.agent/roles/qa.md) |
| Maintainability Gate | 大量或核心程式碼變更，要補 maintainability review | [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md) |
| UI/UX Gate | 命中 UI 路徑，要補 UI/UX check | [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md) |
| Evidence Gate | 只有大變更或大量終端證據才允許 evidence | [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md) |

---

## 7. 狀態資料與執行資料如何保存

### 7.1 單一真相來源：EXECUTION_BLOCK

Plan 不是只寫規格，也承載執行狀態。

模板位置：

- [doc/plans/Idx-000_plan.template.md](../../../doc/plans/Idx-000_plan.template.md)

這裡會記錄：

- `executor_tool`
- `qa_tool`
- `monitor_backend`
- `last_change_tool`
- `qa_result`
- `rollback_reason`
- `log_file_path`

### 7.2 終端監測資料

Monitor 會寫入：

- `.service/terminal_capture/monitor_debug.jsonl`
- `.service/terminal_capture/codex_live.txt`
- `.service/terminal_capture/opencode_live.txt`
- `.service/terminal_capture/codex_last.txt`

這些檔案是 preflight 與 fallback 機制的重要依據。

### 7.3 Skills 執行統計

Log 中理論上應有 `SKILLS_EXECUTION_REPORT` 區段，再由 `skills_evaluator.py` 做二次統計。

---

## 8. 目前這個 template 的真實狀態

如果問的是「這個 template 在設計上想怎麼跑」，答案就是上面那整套。

如果問的是「現在這個 template 嚴格照文件跑，是否 100% 自洽」，答案是否定的。目前仍有明顯的過渡期殘留。

### 8.1 AGENT_ENTRY 仍指向不存在的檔案

[.agent/workflows/AGENT_ENTRY.md](../../../.agent/workflows/AGENT_ENTRY.md) 目前仍要求先讀：

- `ivy_house_rules.md`
- `.agent/Workflow_Plan_index.md`

但這兩個檔案在目前 repo 中不存在。

repo 現在實際存在的是：

- [project_rules.md](../../../project_rules.md)
- [doc/implementation_plan_index.md](../../../doc/implementation_plan_index.md)

所以如果完全照 AGENT_ENTRY 字面執行，流程會在第一個 Gate 就卡死。

### 8.2 Expert 層仍混有 Meta 專案殘留

[.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md) 的 Step 2 還是 Meta Expert，但 repo 同時又新增了泛用的 [domain_expert.md](../../../.agent/roles/domain_expert.md)。

這表示 template 正在往通用化走，但正式流程文本還沒完全切乾淨。

### 8.3 多個角色檔仍帶舊專案語境

以下角色檔仍含大量舊語境：

- [.agent/roles/planner.md](../../../.agent/roles/planner.md)
- [.agent/roles/engineer.md](../../../.agent/roles/engineer.md)
- [.agent/roles/qa.md](../../../.agent/roles/qa.md)
- [.agent/roles/domain_expert.md](../../../.agent/roles/domain_expert.md)（承接歷史上的 Meta Expert 語境）

殘留內容包括：

- `ivy_house_rules.md`
- Meta 廣告
- 舊的商業背景描述

### 8.4 workflow / 治理任務路徑仍不完整

文件經常提到 workflow / 治理任務可以落在：

- `.agent/plans/`
- `.agent/logs/`

但目前 repo 裡並沒有這些資料夾。

現在真正存在且可用的模板與索引主要仍是：

- [doc/plans/Idx-000_plan.template.md](../../../doc/plans/Idx-000_plan.template.md)
- [doc/implementation_plan_index.md](../../../doc/implementation_plan_index.md)

### 8.5 目前最可信的 authoritative 層

如果要判斷現階段「最應該當成權威來源」的是哪些檔案，優先順序應是：

1. [.agent/workflows/dev-team.md](../../../.agent/workflows/dev-team.md)
2. [.agent/roles/coordinator.md](../../../.agent/roles/coordinator.md)
3. [.agent/VScode_system/Ivy_Coordinator.md](../../../.agent/VScode_system/Ivy_Coordinator.md)
4. [doc/plans/Idx-000_plan.template.md](../../../doc/plans/Idx-000_plan.template.md)
5. `.agent/skills/*.py` 腳本本身

而不是把所有角色檔一視同仁視為同樣新鮮。

---

## 9. 實際上應如何理解這個 template

最實際的理解方式如下：

1. 它不是「讓 Copilot 自己寫完全部」的 template。
2. 它是「讓 Copilot 當流程管制器」的 template。
3. 真正執行改碼的是 Codex CLI 或 OpenCode。
4. 整套流程最重視的是可稽核性：
   - 先讀規則
   - 先出 Plan
   - 使用者核准
   - 有 Gate
   - 有 completion marker
   - 有 Cross-QA
   - 有 Log
5. 它同時想做到工具分權：
   - Coordinator 不改 code
   - Engineer 才改 code
   - QA 必須跟最後改碼工具分離
   - git 指令只能留在 Project terminal 或 SCM

---

## 10. 後續整理建議

若要讓這個 template 真的完全自洽，優先建議是：

1. 修正 [AGENT_ENTRY.md](../../../.agent/workflows/AGENT_ENTRY.md) 中不存在的檔名與索引路徑。
2. 決定正式 Expert 應該是 Meta Expert 還是 generic Domain Expert，並刪除另一套的主流程地位。
3. 清理各角色檔中的舊專案語境，統一改用 `project_rules.md`。
4. 明確定義 workflow / 治理任務到底是否真的要使用 `.agent/plans`、`.agent/logs`，若要就補齊資料夾與模板；若不要就統一收斂到 `doc/`。
5. 把 authoritative 文件層級寫清楚，避免未來維護時被舊檔誤導。

---

## 11. 摘要版結論

這個 template 已經不是單純 prompt，而是一套「Coordinator 驅動的治理型開發流程」。

它的主體能力已經具備：

- 明確入口
- 角色分工
- 可驗證的 Plan 模板
- Skills 驗證工具
- Terminal 注入與監控
- 多重 Gate
- Completion marker
- Cross-QA

但它目前仍處於「新治理模型已經成形，舊專案殘留尚未完全清乾淨」的狀態。

因此，現在最合理的判讀是：

> 這是一套骨架很完整、執行邏輯已經相當清楚，但文件層仍需要一次系統性收斂的 workflow template。
