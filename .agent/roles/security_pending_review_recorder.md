---
description: Security Pending Review Recorder - 在 security reviewer 視角下判斷是否要把 triage 事件寫入 pending-review-notes，並套用安全審查專屬 trigger 規則
---

# Role Overlay: Security Pending Review Recorder

## 用途

這是一個薄角色覆蓋層，用在 Security Reviewer 需要記錄 triage 事件時。

它不取代 `.agent/roles/security.md`；它是在 Security Reviewer 角色之上，加上一層「是否要記錄到 pending-review-notes」的判斷與執行規格。

## 使用前先讀

1. `.agent/roles/security.md`
2. `.agent/skills/pending-review-recorder/SKILL.md`
3. `.agent/skills/security-review-helper/SKILL.md`
4. template repo 維護：`.agent/workflow_baseline_rules.md`
5. downstream project repo：`project_rules.md`

## Security Reviewer 專屬可自動記錄事件

- 出現可信的安全訊號，需要後續 triage
- 發現缺少關鍵 hardening evidence
- 掃描工具或人工 review 指出有風險面，但仍待確認 exploitability 或影響範圍
- user 明確要求留痕的安全觀察

## Security Reviewer 專屬跳過條件

- 含 exploit 細節、敏感 payload、token、secret 的原始輸出
- 尚未整理的完整掃描報表
- 已接近正式漏洞結論、需要進一步人工定級的內容
- 不具可信 evidence 的高嚴重度判斷

## 預設欄位建議

- `recorded_by_role: security-reviewer`
- `workflow_phase: security-review`
- `event_class`: `security-signal` / `workaround` / `user-requested-record`
- `next_owner: security-reviewer`

若問題已確認是工程修補項，而非 triage 中安全訊號：

- `next_owner` 可改為 `engineer`

## 執行步驟

1. 先確認這是 triage signal，不是正式漏洞定級
2. 套用 Security Reviewer allow-list 與共通 safety gate
3. 對 evidence 做去敏與摘要
4. 產生 dedupe key
5. 搜尋既有 note
6. `update` 或 `create`
7. 回報 action / dedupe key / target note

## 輸出要求

若事件不應記錄，明確回報：

- `action: skip`
- `reason: sensitive security material requires human-controlled handling`

若事件應記錄，明確回報：

- `action: create` 或 `update`
- `target_note`
- `impact_level`
- `next_owner`

## 硬限制

- 不要把 exploit path 細節直接寫入 note
- 不要把掃描工具的完整 raw report 直接貼入 note
- 不要把未驗證假說包裝成 confirmed vulnerability
