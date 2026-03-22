---
description: Engineer Pending Review Recorder - 在 engineer 視角下判斷是否要把 triage 事件寫入 pending-review-notes，並套用 engineer 專屬 trigger 規則
---

# Role Overlay: Engineer Pending Review Recorder

## 用途

這是一個薄角色覆蓋層，用在 Engineer 需要記錄 triage 事件時。

它不取代 `.agent/roles/engineer.md`；它是在 Engineer 角色之上，加上一層「是否要記錄到 pending-review-notes」的判斷與執行規格。

## 使用前先讀

1. `.agent/roles/engineer.md`
2. `.agent/skills/pending-review-recorder/SKILL.md`
3. template repo 維護：`.agent/workflow_baseline_rules.md`
4. downstream project repo：`project_rules.md`

## Engineer 專屬可自動記錄事件

- 同一類失敗重複出現，且已阻斷實作
- 為了繼續工作必須採用 workaround
- 同模組反覆出現環境或依賴問題，短時間內無法排除
- user 明確要求把某個實作問題留下 triage 記錄

## Engineer 專屬跳過條件

- 開發中預期會出現的紅燈
- 剛改到一半的編譯或測試失敗
- 一次性 typo、立即修掉的 lint / type issue
- 還沒形成具體症狀摘要、只有零散 console 噪音

## 預設欄位建議

- `recorded_by_role: engineer`
- `workflow_phase: implementation`
- `detection_mode: auto` 或 `manual`
- `event_class`: `blocker` / `workaround` / `user-requested-record`
- `next_owner: engineer`

若核心問題其實是規格歧義而非實作問題：

- `next_owner` 應改為 `planner`

## 執行步驟

1. 判斷事件是否命中 Engineer allow-list
2. 套用共通 safety gate
3. 產生 dedupe key
4. 搜尋既有 note
5. `update` 或 `create`
6. 回報 action / dedupe key / target note

## 輸出要求

若事件不應記錄，明確回報：

- `action: skip`
- `reason: expected in-progress implementation failure`

若事件應記錄，明確回報：

- `action: create` 或 `update`
- `target_note`
- `next_owner`

## 硬限制

- 不要把工程中間態雜訊大量寫入 triage note
- 不要把正式實作結論直接寫成 pending-review note
- 不要覆蓋既有 note 的原始 evidence 摘要，只增補新 evidence
