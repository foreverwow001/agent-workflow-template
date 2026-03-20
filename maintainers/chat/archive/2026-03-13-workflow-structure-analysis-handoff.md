# SESSION-HANDOFF

> 建立日期：2026-03-13
> 狀態：Archived - milestone handoff

## Current goal

完成第二版 workflow 收斂實作：把 `AGENT_ENTRY.md` 收斂成 active workflow 的 gate / trigger / `EXECUTION_BLOCK` 單一規格來源，讓 `dev-team.md` 與 `coordinator.md` 改成摘要與責任說明；同時把 Security Review 觸發條件改成 deterministic 的 path / keyword 規則，並做過一次 `/dev` 文件化 smoke，確認 READ_BACK_REPORT → Approve Gate → Role Selection → Security Review → EXECUTION_BLOCK 回填可串接。

## Current branch

main

## Active container mode

- Standard Dockerfile mode
- Debian GNU/Linux 12 dev container

## Files touched

- .agent/workflows/AGENT_ENTRY.md
- .agent/workflows/dev-team.md
- .agent/roles/coordinator.md
- .agent/roles/security.md
- doc/plans/Idx-000_plan.template.md
- maintainers/chat/archive/2026-03-13-workflow-structure-analysis-handoff.md

## What has been confirmed

- active generic agents 維持為：Coordinator、Planner、Domain Expert、Security Reviewer、Engineer、QA。
- `AGENT_ENTRY.md` 現在是 active workflow 中 Gate 規格、Security Review trigger 規格與 `EXECUTION_BLOCK` 回填契約的**唯一來源**。
- `dev-team.md` 已把 Step 2.5 收斂成摘要層：只保留流程順序、最小責任與命令面，不再重複定義 Approve / Research / Validator / Preflight / Historical Checkpoint 的另一套規格。
- `coordinator.md` 已同步改成「引用 `AGENT_ENTRY.md` 的唯一 Gate 題組」，並把 Security Review 的記錄責任明確化。
- `security.md` 已新增 deterministic trigger matrix：區分 explicit request、path rules、keyword rules，並要求審查前先檢查 Plan 是否已回填 trigger source / matches。
- `Idx-000_plan.template.md` 已擴充成可承接 deterministic trigger 的狀態中心，新增：
  - `security_review_trigger_source`
  - `security_review_trigger_matches`
- 這輪已修掉一個 trigger false positive：原本若把 `/roles/` 當 path rule，會把 `.agent/roles/*.md` 這類 workflow 文件也誤判成安全敏感變更；現在已移除這條過寬規則。
- 已完成一次 `/dev` 文件化 smoke：
  - READ_BACK_REPORT 必讀檔鏈可成立
  - Approve Gate 與 Role Selection Gate 之間沒有新的規格衝突
  - Security Review 觸發結果可回填到 `EXECUTION_BLOCK`
  - `security_review_trigger_source` / `security_review_trigger_matches` / `security_review_conclusion` 之間的記錄鏈已接通

## Workflow Stages

1. Trigger：user 啟動 `/dev` 或 `/dev-team`。
2. Entry Gate：依 `AGENT_ENTRY.md` 逐檔讀必讀文件並輸出 `READ_BACK_REPORT`。
3. Goal Alignment：Coordinator 對齊目標、Out of Scope、驗收條件。
4. Plan：Planner 產出含 `EXECUTION_BLOCK` 的 Plan。
5. Plan Approval Gate：Coordinator 依 `AGENT_ENTRY.md` 的唯一題組詢問 Approve / Domain Review / Security Review / Scope Policy / Backend Policy。
6. Domain Review：若 Gate 決策要求，才進 Domain Expert。
7. Role Selection + Pre-execution Gates：由 Coordinator 回填 tool/backend 欄位，並依單一規格完成 Research / Validator / Preflight / Historical Checkpoint。
8. Execute：Engineer 在 PTY 主路徑下實作，Coordinator 做 orchestration 與 scope 監控。
9. Security Review：若 deterministic trigger 命中，先由 Security Reviewer 審查，再決定是否進 QA。
10. QA：由不同於 `last_change_tool` 的 QA tool 進行最終審查。
11. Fix Loop / Rollback：若 QA 或 Security Review 失敗，回 Engineer 修正或進 rollback 決策。
12. Log / Close：Coordinator 收尾並由 user 決定是否提交。

## What was rejected

- 不再讓 `dev-team.md` 與 `coordinator.md` 各自維護一套 Gate 問題集或 trigger 規格；這些內容已收斂到 `AGENT_ENTRY.md`。
- 不把 `/roles/` 視為 Security Review path rule；這會讓 `.agent/roles/*.md` 這類 workflow 文件產生大量 false positive。
- 不把 Security Review 放成永遠必跑；仍維持條件式觸發，但現在改成 deterministic rule，而不是只靠語意判斷。

## Next exact prompt

請先讀這份 handoff。第二版文件收斂與 deterministic trigger 已完成，下一步不要再回頭重寫同一批 Gate。若要繼續推進，請直接做真實互動層面的 `/dev` smoke：1. 嚴格照 `AGENT_ENTRY.md` 輸出 READ_BACK_REPORT 並停下；2. 檢查 user confirmation → Plan → Approve Gate → Role Selection → Preflight → Security Review 回填是否真的能在聊天流程中順序成立；3. 若過程中還有文件與實際操作不一致，再把差異收斂回 active workflow docs。若不做真實 smoke，另一條路是評估是否新增 `security_review_helper` 類 skill，降低 Security Reviewer 的執行摩擦。

## Risks

- 雖然 active workflow 的 Gate 規格已收斂成單一來源，但 `coordinator.md` 仍保留較多流程型說明；後續若再新增規則，仍需優先改 `AGENT_ENTRY.md`，否則可能再次漂移。
- deterministic Security Review trigger 已大幅降低自由裁量，但 keyword rule 仍可能在邊界案例上偏保守；如果後續誤觸發仍偏多，應優先微調關鍵字集，而不是回到純語意判斷。
- 這一輪做的是文件化 smoke，不是真實 slash-command end-to-end；聊天互動層是否還有停頓點或 wording friction，仍要靠下一輪真實 smoke 才能驗證。

## Verification status

- 已驗證：`AGENT_ENTRY.md`、`dev-team.md`、`coordinator.md`、`security.md`、`Idx-000_plan.template.md` 都通過基本文件錯誤檢查。
- 已驗證：active workflow 中的 Gate 規格與 Security Review trigger 已集中到 `AGENT_ENTRY.md`；另外兩份文件只保留摘要與角色責任。
- 已驗證：Plan schema 已可承接 `security_review_trigger_source` / `security_review_trigger_matches` / `security_review_conclusion` 的完整記錄鏈。
- 已驗證：做過一次 `/dev` 文件化 smoke，READ_BACK_REPORT、Approve Gate、Role Selection、Security Review 與 `EXECUTION_BLOCK` 回填在文件層可以串起來。
- 尚未驗證：尚未執行真正的 slash-command `/dev` 互動 smoke；因此目前只能確認文件鏈成立，不能宣稱聊天操作層已 end-to-end 綠燈。
