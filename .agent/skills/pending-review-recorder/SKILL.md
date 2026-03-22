---
name: pending-review-recorder
description: "Use when deciding whether a work incident should be recorded to pending-review-notes, deduplicating against existing notes, and creating or updating a structured triage note for engineer, QA, or security reviewer workflows."
---

# Pending Review Recorder

## 用途

把工作過程中值得保留、但尚未形成正式結論的事件，穩定地寫入 `pending-review-notes`，並避免 agent 因重複記錄而產生大量相似 note。

這個 skill 的定位是：

- triage intake，不是正式知識發佈器
- dedupe / update 決策器，不是 raw log dump 工具
- role-shared capability，可被 engineer、QA、security reviewer 共用

## 邊界

這個 skill 只能處理：

- `pending-review-notes` 類型事件
- 尚未定案但值得留痕的工作問題、風險、觀察與 workaround

這個 skill 不能直接做：

- 自動升格為 reviewed note
- 自動升格為 reviewed-sync candidate
- 自動把內容寫成正式 decision / SOP / policy
- 寫入 raw log、stack trace dump、secret、token、個資或敏感 payload

## Canonical 結構

- canonical script: `.agent/skills/pending-review-recorder/scripts/pending_review_recorder.py`
- role overlays:
  - `.agent/roles/engineer_pending_review_recorder.md`
  - `.agent/roles/qa_pending_review_recorder.md`
  - `.agent/roles/security_pending_review_recorder.md`

## 何時使用

當符合以下任一情況時，可使用本 skill：

- engineer、QA、security reviewer 命中自己的 auto-record trigger
- user 明確要求把某個事件寫入 `pending-review-notes`
- 需要先判斷某事件應該 `create`、`update` 還是 `skip`

## 使用方式

```bash
python .agent/skills/pending-review-recorder/scripts/pending_review_recorder.py \
  --notes-dir /path/to/pending-review-notes \
  --payload-file /path/to/event.json
```

若未提供 `--payload-file`，則改從 stdin 讀取 JSON payload。

## 使用前必查

1. 已讀 active rule source
   - template repo 維護：`.agent/workflow_baseline_rules.md`
   - downstream project repo：`project_rules.md`
2. 已讀對應角色 base role
   - engineer：`.agent/roles/engineer.md`
   - QA：`.agent/roles/qa.md`
   - security reviewer：`.agent/roles/security.md`
3. 已確認工作區是否真的具備 `pending-review-notes` 可寫入能力
4. 已確認本次事件不含敏感資料

若 `pending-review-notes` 不可寫，或 vault / note sink 根本不存在：

- 不要自行改寫其他區域
- 回報 `skip` 並說明缺少 writable sink

## 共通 allow-list

只有命中以下事件類型時，才允許自動寫入：

- 重複失敗或持續 blocker
- 已可重現但未定級的 QA 問題
- 需要後續 triage 的安全訊號
- 為了繼續工作採用 workaround
- user 明確要求留痕的事件

其他事件預設 `skip`。

## 共通 safety gate

命中以下任一條件時，必須 `skip`，不可自動寫入：

- 含 secret、token、個資、敏感 payload
- 只有整包 raw log / stack trace，沒有可摘要的事件訊號
- 只是一次性低價值錯誤
- 正在走到正式結論、正式 decision 或 reviewed knowledge
- 事件其實只是正常開發中間態紅燈

## 標準流程

1. 確認角色：`engineer`、`qa`、`security-reviewer`
2. 套用該角色 trigger 規則
3. 套用共通 safety gate
4. 產生 dedupe key
5. 搜尋既有 note
6. 決定 `create`、`update` 或 `skip`
7. 若寫入，使用標準欄位與模板
8. 回報本次動作摘要

## Dedupe Key 規則

dedupe key 必須至少由以下欄位組成：

- `project_scope`
- `recorded_by_role`
- `event_class`
- `module_area`
- `symptom_signature`

`symptom_signature` 必須：

- 去敏
- 穩定
- 短字串
- 可跨多次重複事件保持一致

例如：

- `pytest-login-seeded-admin-failure`
- `npm-build-missing-env-schema`
- `authz-admin-endpoint-missing-check`

## Update 優先規則

- dedupe key 相同：優先 update 既有 note
- dedupe key 相同且只是多一筆 evidence：update 同一份 note
- dedupe key 相同但事件狀態變化：更新 `current_status`，不另開新 note
- dedupe key 不同：才建立新 note

## 檔名規則

新 note 預設使用以下檔名規則：

- `<occurred_on>-<recorded_by_role>-<event_class>-<symptom_signature>.md`

例如：

- `2026-03-21-qa-qa-defect-pytest-login-seeded-admin-failure.md`
- `2026-03-21-engineer-blocker-npm-build-missing-env-schema.md`

補充規則：

- `symptom_signature` 必須先 slugify，再寫入檔名
- 若同名檔案已存在，但 dedupe key 不同，尾碼改為 `-2`、`-3` 依序遞增
- 一旦 note 建立完成，後續 update 不應重新命名

## 實際搜尋 / 更新流程

canonical script 的搜尋更新流程應固定如下：

1. 遞迴掃描 `pending-review-notes` 內所有 `*.md`
2. 只納入 `note_kind: pending-review-note` 的檔案
3. 從 frontmatter 計算 dedupe key
4. 與本次 payload 的 dedupe key 做 exact match
5. 若找到多份 match：
  - 優先更新 `last_seen_on` 最新的那一份
  - 其餘列為 duplicate candidates，供後續人工清理
6. 若完全找不到 match，才建立新 note

update 時的實作規則：

- 更新 `last_seen_on`
- 遞增 `occurrence_count`
- merge `evidence_refs`
- 取較高的 `impact_level`
- append 一筆 `Update History`
- 保留既有檔名

### 建議更新欄位

若命中既有 note，優先更新：

- `last_seen_on`
- `occurrence_count`
- `evidence_refs`
- `impact_level`
- `current_status`
- `workaround_applied`
- `next_owner`

### 建議 split 條件

以下情況應新開 note，而不是硬併：

- 同模組但不同 root cause
- 同表象但角色上下文完全不同
- 同問題已從 triage observation 變成正式 defect / decision / reviewed item

## 標準欄位契約

最小欄位：

- `title`
- `note_kind`
- `source_repo`
- `project_scope`
- `recorded_by_role`
- `detection_mode`
- `event_class`
- `workflow_phase`
- `current_status`
- `impact_level`
- `reproducibility`
- `module_area`
- `symptom_signature`
- `occurred_on`
- `last_seen_on`
- `occurrence_count`
- `evidence_refs`
- `workaround_applied`
- `next_owner`
- `tags`

固定值：

- `note_kind: pending-review-note`
- `current_status: pending-triage` 作為自動建立的預設值

## 標準模板

```yaml
---
title: concise issue summary
note_kind: pending-review-note
source_repo: <repo-name>
project_scope: <repo-name>
recorded_by_role: engineer
detection_mode: auto
event_class: blocker
workflow_phase: implementation
current_status: pending-triage
impact_level: medium
reproducibility: reproducible
module_area: path/or/module
symptom_signature: stable-short-signature
occurred_on: 2026-03-21
last_seen_on: 2026-03-21
occurrence_count: 1
evidence_refs:
  - command or test reference
workaround_applied: false
next_owner: engineer
tags:
  - pending-review
  - triage
---
```

```markdown
# Symptom Summary

一句話描述問題。

# What Happened

- 發生情境
- 觀察到的行為
- 是否可重現

# Impact

- 影響誰
- 阻斷哪個流程

# Evidence Summary

- 測試名稱 / command / 檔案路徑 / CI run id
- 不貼整包 raw output

# Workaround

- 是否已有暫時解法
- 代價與風險

# Next Action

- 下一步要誰接手
- 需要補什麼資訊
```

## 輸出契約

skill 執行完成後，應清楚回報：

- `action`: `create` / `update` / `skip`
- `reason`: 為什麼採用這個動作
- `role`: `engineer` / `qa` / `security-reviewer`
- `dedupe_key`: 本次比對使用的 key
- `target_note`: 若有 create / update，回報 note 路徑或標識

建議回報骨架：

```markdown
PENDING_REVIEW_ACTION: update
ROLE: qa
DEDUPE_KEY: <project_scope>|<role>|<event_class>|<module_area>|<symptom_signature>
TARGET_NOTE: <path-or-note-id>
REASON: repeated reproducible QA defect matched existing note
```

## Role Adapter 契約

本 skill 不直接取代角色本身；角色差異應由薄 overlay role 負責。

- engineer overlay：偏 implementation blocker / workaround / dependency issue
- QA overlay：偏 reproducible defect / flaky behavior / acceptance gap
- security reviewer overlay：偏 security signal / missing hardening evidence / suspicious attack surface

角色 overlay 的責任是：

- 套用角色 trigger matrix
- 決定預設 `workflow_phase`
- 決定預設 `next_owner`
- 決定哪些事件要 `skip`

skill 本身只負責：

- allow-list / safety gate
- dedupe / update
- 欄位與模板
- create / update / skip 決策骨架
