# AGENT_ENTRY.md（VS Code 多代理 Workflow 唯一入口）

> 本檔案是此 repo 的「唯一入口文件」。
> 任何工作在開始 **產出 Plan** 前，必須先完成「必讀檔案逐檔閱讀」並回報「已讀驗收回報」。
> 未完成者：不得出 Plan、不得執行、不得 QA。

---

## 0) 一條不可妥協的鐵律
**在你完成「1) 必讀檔案」並輸出「2) 已讀驗收回報」之前，禁止產出任何 Plan。**

若任一必讀檔找不到：必須立刻停下並詢問使用者確認檔名/路徑與目前是「template repo 維護」還是「下游專案工作區」（不得自行猜測或跳過）。

---

## 1) 必讀檔案（必須逐檔「開啟並閱讀」，不可只提到檔名）
請依序「開啟並閱讀」以下檔案：

1. `./.agent/workflows/dev-team.md`
2. **規則檔（依工作區型態擇一）**：
  - 若目前在維護 `agent-workflow-template` 本身 → 必讀 `./.agent/workflow_baseline_rules.md`
  - 若目前在下游/新專案工作區內執行 workflow → 必讀 `./project_rules.md`
3. **Index 檔案**：`./doc/implementation_plan_index.md`

> 注意：
> - 「提到」不等於「已讀」；你必須實際打開檔案並萃取重點。
> - 缺任一檔案，或無法判定目前是 template repo 維護 / 下游專案工作區時，先停下詢問，不得自行跳過。

---

## 2) 已讀驗收回報（必須照格式輸出）
完成必讀檔逐檔閱讀後，請輸出以下 **完全一致** 的段落格式（不得省略欄位）：

### ===READ_BACK_REPORT===
- 本機時間（local）：
- 已開啟閱讀的檔案（含路徑）：
  - [ ] ./.agent/workflows/dev-team.md
  - [ ] 規則檔：./.agent/workflow_baseline_rules.md（template repo 維護）或 ./project_rules.md（下游/新專案）
  - [ ] ./doc/implementation_plan_index.md

- 從「規則/流程」萃取的 Top 5 硬約束（請用條列）：
  1.
  2.
  3.
  4.
  5.

- 與 Index 對照（根據任務類型選擇對應 Index）：
  - 這次任務是否已存在於 Index？（YES / NO / UNCLEAR）
  - 若 YES：請寫出 Index 中的 Task ID / Task 名稱（照 Index 原文）
  - 若 NO：請寫「NEW TASK - 需先登記 Index 才能進入執行」

- 風險旗標（若有）：
  - None /（列出風險）

### ===END_READ_BACK_REPORT===

**輸出後必須停下，優先使用 VS Code `#askQuestions` 等待使用者確認/回覆。** 只有工具不可用、需要自由文字理由、或選項不足時，才可退回一般聊天輸入；不得自行進入 Plan。

**Bootstrap（新 /dev 任務）**：READ_BACK_REPORT 通過、且 Coordinator 準備進入本次 `/dev` 任務時，必須先執行 `ivyhouseTerminalPty.rotateArtifacts`，並帶 `reason="new-workflow"`；未指定 `kind` 時，視為一次 rotate `codex` 與 `copilot` 的 current PTY artifact，避免新任務混入上一輪 evidence。若 PTY command surface 暫不可用，先記錄風險並停在 Gate；一旦 PTY 可用，必須先補做 bootstrap rotate，再進 Mode Selection Gate。

---

## 3) Workflow 合約（高層順序）

> **單一來源規則**：本節是 active workflow 中所有 Gate 規格、欄位回填契約與 Security Review 觸發規則的唯一來源。
> `.agent/workflows/dev-team.md` 與 `.agent/roles/coordinator.md` 只可保留摘要、角色責任與操作順序，不得另行定義不同題組、不同欄位或不同 trigger 規則。

在使用者確認 READ_BACK_REPORT 後，才可依序執行：

1) **Interaction Contract（askQuestions-first）**
- 所有 user-facing Gate 預設使用 VS Code `#askQuestions`。
- 只有 `#askQuestions` 工具不可用、需要自由文字理由/補充、或選項不足時，才可退回一般聊天輸入。
- askQuestions-first 節點至少包含：
  - READ_BACK_REPORT 是否通過
  - Mode Selection Gate
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

2) **Mode Selection Gate**
- 預設模式為 `formal-workflow`
- 只有同時符合以下條件，Coordinator 才可提供 `lightweight-direct-edit`：
  - 單檔或極少數檔案的小修正
  - 不涉及 dependency、runtime、preflight 或長流程 terminal 執行
  - 不命中安全敏感路徑與 deterministic Security Review trigger
  - 不需要獨立 QA log、Cross-QA、completion marker 或 PTY artifact 稽核
- 若使用者選擇 `lightweight-direct-edit`，由 GitHub Copilot Chat 直接處理，不進 formal Plan / Engineer / QA / Log 鏈。
- 若後續 scope 擴張或命中上述禁制條件，必須立刻升級回 `formal-workflow`，並從 Plan Gate 重新開始。

3) **Plan**
- 輸出可審核、可落地的計畫（可含里程碑與驗收條件）
- 此階段不得改 code、不得下執行命令

4) **Approve Gate（使用者審核）**
- 必須詢問使用者：`Approve / Reject / Revise`
- 必須一併確認並回填：`expert_required`、`scope_policy`，以及 user 是否額外要求 Security Review
- 若 deterministic trigger 已命中，`security_review_required` 最終值仍必須為 `true`
- 未明確 Approve：不得執行

5) **角色選擇 Gate**
必須詢問使用者選擇：
- **Engineer Tool（執行者）**：`codex-cli` / `copilot-cli`（VS Code Terminals）
- **Security Reviewer Tool（條件式）**：
  - 若 `security_review_required=false` → `security_reviewer_tool = N/A`
  - 若 `security_review_required=true` → 必須詢問 `codex-cli` / `copilot-cli`
  - 若 workflow 進行中才從 `false` 轉為 `true`，必須補做一次 askQuestions，不得沿用預設值
- **QA Tool（驗收者）**：`codex-cli` / `copilot-cli`（VS Code Terminals）
  - **Cross-QA 硬規則**：`qa_tool ≠ last_change_tool`（例外需記錄在 `qa_compliance` 並由 user 明確允許）
- **Execution Backend Policy（執行後端策略）**：`pty-primary-with-consented-fallback`
  - `pty-primary-with-consented-fallback`（固定）：workflow 的 prompt send / submit / verify / smoke / monitor 一律以 `.agent/runtime/tools/vscode_terminal_pty` 為主路徑
  - 只有 PTY 無法工作，且 user 明確同意後，才允許改走 `.agent/runtime/tools/vscode_terminal_fallback`
- **Monitor Backend Policy（監測後端策略）**：`pty-runtime-primary`
  - `pty-runtime-primary`（預設）：主證據使用 PTY runtime artifact，例如 `*_pty_debug.jsonl` 與 `*_pty_live.txt`
  - `fallback-runtime-monitor`（條件式）：只有 PTY 不可用且 user 同意 fallback 後，才使用 fallback runtime 的 capture / verify
  - 主要命令範例：`ivyhouseTerminalPty.startCodex`、`ivyhouseTerminalPty.sendToCodex`、`ivyhouseTerminalPty.submitCodex`、`ivyhouseTerminalPty.verifyCodex`

> Gate 完成後，必須在 Plan 的 `EXECUTION_BLOCK` 回填：
> `scope_policy`、`expert_required`、`security_review_required`、`executor_tool`、`security_reviewer_tool`、`qa_tool`、`execution_backend_policy`、`executor_backend`、`monitor_backend`、`security_review_trigger_source`、`security_review_trigger_matches`。

6) **Pre-execution Gates（唯一規格來源）**
- **Research Gate**：若 Plan 的 `research_required: true` 或依賴檔案變更（`requirements.txt`、`pyproject.toml`、`*requirements*.txt`），必須先補齊 `RESEARCH & ASSUMPTIONS`；未完成不得進入 Engineer。
  - **Coordinator Research Skill Trigger Checklist（authoritative）**：見 [coordinator_research_skill_trigger_checklist.md](./references/coordinator_research_skill_trigger_checklist.md)
  - Coordinator 必須逐列檢查；任一列命中即載入對應 skill；若同時命中多列，必須全部載入
- **Plan Validator Gate**：必須先執行 `python .agent/skills/plan-validator/scripts/plan_validator.py <plan_file_path>`；若回傳 `status: fail|error`，退回 Planner 修正。
- **Preflight Gate**：
  - PTY 主路徑：`python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-pty --allow-pty-cold-start --json`
  - fallback 模式：`python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-fallback --json`
  - 未達 `status=pass`：不得進入 Engineer 注入。
  - fallback 模式的 `status=pass` 不要求 `proposed_api_true` 一定為 true；只要 shell integration attachment、bridge healthz、token 與 artifact compatibility 成立，也可視為 ready。
- **Historical File Checkpoint**：檢核 `git status --porcelain | awk '{print $2}' | grep -E '^\.agent/(plans|logs)/' || true`；若僅為命名一致性調整，禁止改寫歷史 plan/log。

> Execute 前必跑 preflight（Project terminal）：
> - PTY 主路徑：`python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-pty --allow-pty-cold-start --json`
> - fallback 模式：`python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-fallback --json`
> - 未達 `status=pass`：不得進入 Engineer 注入。
> - fallback 模式的 `status=pass` 不要求 `proposed_api_true` 一定為 true；只要 shell integration attachment、bridge healthz、token 與 artifact compatibility 成立，也可視為 ready。
> - 一旦 user 同意 fallback，Coordinator 應把它視為「真實接手路徑」：啟動 fallback terminal / bridge，並在安全情況下延續最後一步 send / submit，而不是只記錄一個 accepted 狀態。

> 注意：GitHub Copilot Chat 固定為 Coordinator（只做討論/分派/監控/回填 Plan），不作為 Engineer/QA 工具，也不得直接改 code。

7) **Security Review Trigger（deterministic）**
- `security_review_required=true` 的判定順序如下，命中任一條件即觸發：
  1. **Explicit Request**：user 或 Coordinator 明確要求安全審查。
  2. **Path Rule**：Plan 的 file whitelist、檔案變更清單或實際修改檔案命中任一安全敏感路徑規則。
  3. **Keyword Rule**：Goal / SPEC / 檔案變更表 / 變更摘要 / 檔名命中任一安全關鍵字規則。
- **Path Rule（大小寫不敏感，命中任一路徑片段即可）**：
  - `/auth/`
  - `/security/`
  - `/middleware/`
  - `/permission/` 或 `/permissions/`
  - `/api/`、`/routes/`、`/controllers/`、`/handlers/`
  - `/bridge/`
  - `/subprocess/`
  - `/upload/`
  - `/templates/`
  - 檔名含 `token`、`secret`、`session`、`credential`、`oauth`、`jwt`
- **Keyword Rule（大小寫不敏感，建議以完整詞或片語匹配）**：
  - `auth`、`authentication`、`authorization`
  - `token`、`secret`、`session`、`cookie`、`jwt`、`oauth`、`api key`
  - `permission`、`role`、`rbac`、`acl`
  - `bridge`、`subprocess`、`shell`、`command injection`、`exec`
  - `upload`、`path traversal`
  - `template`、`render`、`deserialize`
  - `sql`、`query`、`raw query`
  - `endpoint`、`webhook`
- **回填規則**：
  - `security_review_trigger_source`: `none|user|coordinator|path-rule|keyword-rule|mixed`
  - `security_review_trigger_matches`: 寫入命中的路徑片段、檔名或關鍵字
  - 若 user 明確豁免已命中的 Security Review，必須在 `security_review_conclusion` 寫明豁免理由

8) **Execute（只允許被選定的 Executor 動手）**
- 僅能依照已核准 Plan 執行
- 變更應最小化，避免無關改動
- Coordinator 在注入 Engineer 任務時，**必須**對照 [engineer_skill_trigger_checklist.md](./references/engineer_skill_trigger_checklist.md) 逐列檢查，並附上所有命中的 skill 載入命令；若同時命中多列，必須全部附上，不得擇一省略。

9) **Security Review（條件式）**
- 若 `security_review_required=true`，先進行 Security Review
- Security Review 的目標是找出可被利用的漏洞、攻擊路徑與修補建議
- 若 Security Review 結果為高風險 `FAIL`，不得直接進 QA
- Security Review 完成後，必須回填：`security_reviewer_tool`、`security_review_start`、`security_review_end`、`security_review_result`、`security_review_conclusion`
- Coordinator 在注入 Security Reviewer 任務時，**必須**明確附上 helper 命令：`cat .agent/skills/security-review-helper/SKILL.md` 與 `cat .agent/skills/security-review-helper/references/security_checklist.md`；不得只寫「參考 security.md」。

10) **QA（必須對照 Plan 與硬約束）**
- QA 必須分級：PASS / PASS WITH RISK / FAIL
- 若非 PASS：必須指出風險與原因
- Coordinator 在注入 QA 任務時，**必須**依審查範圍明確附上至少一條 `code-reviewer` canonical script 命令（單檔 / 目錄 / diff / `git diff --staged|--cached|<base>..<head>`）；若專案有測試，也必須一併附上 `test-runner` 命令。

11) **Log（QA 後必寫）**
- QA 結束後必須產出 log
- log 若已 commit，需包含 commit hash
- 是否提交（含 log）由使用者決策；若有提交，Log 應與變更一起納入版本控管以利稽核追蹤

12) **Close**
- 總結完成內容、變更範圍、風險、後續事項

---

## 4) Scope Break（停止條件）
若執行中出現「Plan 未包含的新需求」：
- 立即停止
- 回報：`SCOPE BREAK`
- 詢問使用者決策：
  - 回到原 scope，或
  - 新增/更新 Index 並開新 plan

---

## 5) 並行任務（停止條件）
**一個任務 = 一份 plan = 一份 log = 一組（或一串）commit。**
不得把不同任務混寫在同一份 plan/log/commit 鏈。

---

## 6) 小修正例外（暫定政策，稍後用 git hooks / lint-staged 落地）
小修正可能允許「較簡化流程」，但需同時符合：
- 變更行數 ≤ 20 行
- 僅限 doc / README / 註解 / formatting
- 仍需使用者明確允許（例如使用者說「這次是小修正可簡化」）

> 之後會用 git hooks / lint-staged 在 commit 時做硬性卡控。

---

## 7) 相關 References

若你需要查看 workflow skill trigger 的補充說明，請使用下列 reference 文件：

- [README.md](./references/README.md)：`references/` 目錄導覽入口
- [coordinator_research_skill_trigger_checklist.md](./references/coordinator_research_skill_trigger_checklist.md)：Coordinator 的權威 checklist
- [engineer_skill_trigger_checklist.md](./references/engineer_skill_trigger_checklist.md)：Engineer 的權威 checklist
- [workflow_skill_trigger_design_principles.md](./references/workflow_skill_trigger_design_principles.md)：哪些角色該用 checklist、哪些不該用的設計原則
- [workflow_skill_trigger_index.md](./references/workflow_skill_trigger_index.md)：各角色 checklist 的導航索引（非權威來源）
