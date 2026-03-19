---
name: project-planner
description: "Planning skill for Planner. Use when a request needs milestones, phases, dependency mapping, task breakdown, estimates, risk analysis, rollout sequencing, or a more execution-ready plan before implementation begins."
---

# Project Planner

幫助 Planner 把複雜任務拆成可執行、可追蹤、可驗證的規劃，而不是只有高層願景。

## 何時使用

當任務符合任一條件時，Planner 應載入本 skill：

- 需求涉及多個檔案、階段或角色協作
- 需要釐清 deliverables、milestones、dependency 或 critical path
- 需求規模已超出「一段簡短 Spec」可安全承載的範圍
- User 要求 roadmap、task breakdown、phase plan、估時或風險拆解

## 核心要求

- Plan 必須服務執行，不是只寫好看的大綱
- 任務粒度要讓 Engineer / QA 能獨立理解與驗證
- 每個 task 都要有 done criteria 或可驗證結果
- 估時必須包含 review / QA / buffer，不可只寫理想工時
- 依賴關係要顯式寫出，不要只靠敘述暗示

## Planner 工作流

1. 先讀 [references/planning-framework.md](./references/planning-framework.md) 確認拆解順序。
2. 再用 [references/task-sizing-and-dependencies.md](./references/task-sizing-and-dependencies.md) 校正 task 粒度與 dependency。
3. 若任務有明顯不確定性，讀 [references/estimation-and-risk.md](./references/estimation-and-risk.md) 補估時與風險策略。
4. 將結果轉譯為本 repo 的 plan template，而不是輸出另一套格式。
5. 若任務其實很小，不要為了完整性硬拆過多 phase。

## 輸出期待

- 明確 Goal、Non-goals、Acceptance Criteria
- 檔案變更與邏輯細節可交付給 Engineer
- 任務切分合理，dependency 清楚
- 風險與 rollback 思路明確
- 可直接寫入 `doc/plans/Idx-NNN_plan.md`

## 參考資料

- [references/planning-framework.md](./references/planning-framework.md)
- [references/task-sizing-and-dependencies.md](./references/task-sizing-and-dependencies.md)
- [references/estimation-and-risk.md](./references/estimation-and-risk.md)
