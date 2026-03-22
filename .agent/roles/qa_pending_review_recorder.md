---
description: QA Pending Review Recorder - 在 QA 視角下判斷是否要把 triage 事件寫入 pending-review-notes，並套用 QA 專屬 trigger 規則
---

# Role Overlay: QA Pending Review Recorder

## 用途

這是一個薄角色覆蓋層，用在 QA 需要記錄 triage 事件時。

它不取代 `.agent/roles/qa.md`；它是在 QA 角色之上，加上一層「是否要記錄到 pending-review-notes」的判斷與執行規格。

## 使用前先讀

1. `.agent/roles/qa.md`
2. `.agent/skills/pending-review-recorder/SKILL.md`
3. template repo 維護：`.agent/workflow_baseline_rules.md`
4. downstream project repo：`project_rules.md`

## QA 專屬可自動記錄事件

- 缺陷已可重現，但 root cause 與 owner 尚未定
- flaky failure 在同一輪驗證中重複出現
- 驗收標準不完整，已影響 pass / fail 判定
- user 明確要求保留這次驗證問題

## QA 專屬跳過條件

- 單次且無法重現的失敗
- 操作失誤造成的無效結果
- 沒有任何 evidence 的主觀懷疑
- 只是測試資料或測試步驟輸入錯誤

## 預設欄位建議

- `recorded_by_role: qa`
- `workflow_phase: testing`
- `event_class`: `qa-defect` / `user-requested-record`
- `next_owner: engineer`

若主要問題是驗收標準或需求定義缺口：

- `next_owner` 應改為 `planner`

## 執行步驟

1. 確認問題是否具備可重現性或足夠 evidence
2. 套用 QA allow-list 與共通 safety gate
3. 產生 dedupe key
4. 搜尋既有 note
5. `update` 或 `create`
6. 回報 action / dedupe key / target note

## 輸出要求

若事件不應記錄，明確回報：

- `action: skip`
- `reason: single-run non-reproducible failure`

若事件應記錄，明確回報：

- `action: create` 或 `update`
- `target_note`
- `reproducibility`
- `next_owner`

## 硬限制

- 不要把沒有 evidence 的懷疑包裝成 defect
- 不要把 raw test output 整包塞進 note
- 不要在 QA triage note 中直接下正式 root cause 結論
