---
name: reviewed-sync-manager
description: "Workflow-template-only tool for writing reviewed-sync candidates to Obsidian and promoting approved candidates into 20-reviewed with frontmatter normalization, index updates, and dedupe."
---

# Reviewed Sync Manager

## 用途

這是一個 **只允許在 workflow template repo 使用** 的 maintainer-local 工具，用來處理 Obsidian 的兩段式 reviewed sync 流程：

1. `write-candidate`
   - 把候選整理稿寫進 `10-inbox/reviewed-sync-candidates/`
2. `promote-candidate`
   - 把已確認 candidate promotion 到 `20-reviewed/`
   - 補齊 reviewed frontmatter
   - 更新 index
   - 套用 dedupe

## 硬邊界

- 這個工具 **只能在 workflow template repo 中使用**
- downstream project repo **不得**使用這個工具
- downstream repo 仍維持 restricted consumer / pending-review intake 模式
- 這個工具不負責處理 `pending-review-notes`
- 這個工具不會把 raw log / secret / token / 敏感 payload 直接寫進 reviewed knowledge

## Canonical 結構

- entry doc: `.agent/skills/reviewed-sync-manager/SKILL.md`
- canonical script: `.agent/skills/reviewed-sync-manager/scripts/reviewed_sync_manager.py`

## 支援的輸入來源

`write-candidate` 支援三種來源：

- repo 檔案
- 手動摘要
- 結構化 JSON payload

## JSON Payload Contract

JSON mode 已收斂成固定欄位、固定版本的 contract。

- `schema_version` 必須固定為 `reviewed-sync-candidate.v1`
- 不接受未列在 contract 內的額外欄位
- list 欄位必須是 JSON array，不接受字串與隱含轉型

### 必填欄位

- `schema_version`: string
- `title`: string
- `source_repo`: string
- `source_path`: string
- `source_type`: string
- `summary_text`: string
- `target_reviewed_dir`: string

### 選填欄位

- `index_targets`: string[]
- `why_in_inbox`: string[]
- `reusability_check`: string[]
- `next_review_action`: string[]
- `source_notes`: string[]
- `source_excerpt`: string
- `tags`: string[]
- `related_topics`: string[]
- `related_projects`: string[]
- `candidate_source_mode`: string
- `candidate_key`: string
- `reviewed_key`: string
- `synced_on`: string

### Canonical JSON 範例

```json
{
  "schema_version": "reviewed-sync-candidate.v1",
  "title": "reviewed sync policy summary",
  "source_repo": "agent-workflow-template",
  "source_path": "maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md",
  "source_type": "maintainer-policy",
  "summary_text": "整理 reviewed-sync policy 的核心結論。",
  "target_reviewed_dir": "agent-workflow-template/workflow-knowledge",
  "index_targets": ["workflows.md"],
  "why_in_inbox": ["需要人工確認是否值得沉澱成長期知識"],
  "reusability_check": ["可跨 session 重用"],
  "next_review_action": ["人工 review 後決定 promotion"],
  "source_notes": ["repo file: maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md"],
  "source_excerpt": "# reviewed-sync policy\n...",
  "tags": ["inbox", "candidate", "reviewed-sync"],
  "related_topics": ["obsidian", "reviewed-sync"],
  "related_projects": ["agent-workflow-template"],
  "candidate_source_mode": "repo-file",
  "candidate_key": "agent-workflow-template|maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md|maintainer-policy|agent-workflow-template/workflow-knowledge|reviewed sync policy summary",
  "reviewed_key": "agent-workflow-template|maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md|agent-workflow-template/workflow-knowledge|reviewed sync policy summary",
  "synced_on": "2026-03-21"
}
```

### 自動補值規則

- repo file / manual summary mode 仍可省略部分欄位，由 script 產出 canonical payload
- JSON mode 不允許 contract 外欄位，避免 writer / promotion 介面漂移
- candidate 與 reviewed frontmatter 會保留 `payload_schema_version`

## Writer 階段

### 使用方式

```bash
python .agent/skills/reviewed-sync-manager/scripts/reviewed_sync_manager.py write-candidate \
  --vault-root /obsidian/vault \
  --source-file maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md \
  --title "reviewed sync policy summary" \
  --target-reviewed-dir agent-workflow-template/workflow-knowledge
```

```bash
python .agent/skills/reviewed-sync-manager/scripts/reviewed_sync_manager.py write-candidate \
  --vault-root /obsidian/vault \
  --summary-text "整理這輪 Obsidian mount 與 reviewed-sync 邊界的結論" \
  --title "obsidian mount governance summary" \
  --target-reviewed-dir agent-workflow-template/maintainer-sops
```

```bash
python .agent/skills/reviewed-sync-manager/scripts/reviewed_sync_manager.py write-candidate \
  --vault-root /obsidian/vault \
  --payload-file /tmp/reviewed_sync_payload.json
```

### Writer 規格

- 寫入位置固定為 `10-inbox/reviewed-sync-candidates/`
- 會建立 `reviewed-sync-candidate` 類型 frontmatter
- 會產生穩定的 `candidate_key` / `reviewed_key`
- 若同一 candidate 已存在，優先 update，不重複新增
- 會為 promotion 階段預先保存：
  - `target_reviewed_dir`
  - `index_targets`
  - `related_topics`
  - `related_projects`

## Promotion 階段

### 使用方式

```bash
python .agent/skills/reviewed-sync-manager/scripts/reviewed_sync_manager.py promote-candidate \
  --vault-root /obsidian/vault \
  --candidate-file /obsidian/vault/10-inbox/reviewed-sync-candidates/2026-03-21-candidate-reviewed-sync-policy-summary.md \
  --reviewed-by human
```

### Promotion 規格

- 讀取 candidate frontmatter，決定目標 `20-reviewed/<target_reviewed_dir>`
- promotion 時會：
  - 補齊 reviewed frontmatter
  - 將 `review_status` 改為 `approved`
  - 將 `promotion_status` 改為 `reviewed`
  - 記錄 `reviewed_by`
  - 依 `reviewed_key` 搜尋既有 reviewed note
  - 若命中既有 reviewed note，執行 merge / dedupe
  - 若未命中，建立新的 reviewed note
  - 更新 `00-indexes/*.md`
- 若 promotion 命中既有 reviewed note，原 candidate 會移到 `30-archives/superseded/`

## Index 更新規則

- index target 由 writer 階段決定，也可由 JSON payload 明確指定
- promotion 時若 index 檔不存在，會建立最小 index note
- 若 index 已存在相同 wiki link，不重複新增

## Template Repo 守門規則

script 會在執行前檢查這是不是 workflow template repo。

若不是，直接回傳錯誤，不做任何寫入。

## 輸出契約

### `write-candidate`

- `action`: `create` / `update`
- `target_note`
- `candidate_key`
- `reviewed_key`

### `promote-candidate`

- `action`: `promote` / `merge`
- `target_note`
- `archived_candidate`（若有）
- `updated_indexes`
- `reviewed_key`

## 不屬於本工具的範圍

- downstream repo 的 Obsidian intake
- `pending-review-notes` triage 記錄
- 自動決定是否通過人工 review
- 未經確認內容直接升格為 reviewed knowledge
