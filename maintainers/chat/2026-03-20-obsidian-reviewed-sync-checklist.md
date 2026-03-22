# Obsidian Reviewed Sync Checklist

> 建立日期：2026-03-20
> 性質：Active supporting doc
> 用途：提供 Obsidian 已安裝但尚未正式設定時的前置作業清單，確保後續串接維持 repo-first 與 reviewed-sync 原則。

## 1. 使用時機

這份 checklist 用在以下時機：

- Obsidian 已安裝，但 vault 與同步規則尚未建立
- 準備開始把 repo 內高訊號 markdown 導入 Obsidian
- 想先把治理邊界定清楚，再決定是否做更進一步的檢索或自動化

## 2. 先確認的原則

開始前先確認以下四點：

1. repo 仍是 canonical source of truth
2. Obsidian 只承接經 review 的內容
3. 不做 repo <-> vault 雙向編輯
4. 不把 raw capture、runtime state、未審核候選資料直接塞進 vault
5. 若 agent 在 Dev Container 中需要直接讀取 Obsidian，優先使用受控 mount，不靠臨時複製

## 3. Vault 前置結構

正式設定前，先決定 vault 至少要有哪幾種區域：

- inbox
  - 暫放待 review 的候選同步內容
- reviewed
  - 放已通過 review、可保留的知識筆記
- indexes
  - 放主題索引、入口頁、MOC 類整理頁
- project-mirrors
  - 放來自各 repo 的已核准同步材料

重點不是資料夾名字一定要完全一致，而是要先把「待 review」與「已核准」分開。

## 3.1 Dev Container mount 邊界

若後續要讓 agent 在 Dev Container workflow 中直接讀取 Obsidian，建議先定義 mount 邊界：

- read-only mount
  - `00-indexes/`
  - `20-reviewed/`
  - 必要時才包含特定 `30-project-mirrors/<repo>/`
- default writable mount
  - `10-inbox/pending-review-notes/`
- optional extra writable mount
  - `10-inbox/reviewed-sync-candidates/`
- default no-mount
  - `30-archives/`
  - 私人草稿、原始捕捉資料、敏感資料區

原則是：讀取預設放在 read-only mount；downstream default 的寫入只集中到 `10-inbox/pending-review-notes/` 這個單一 writable inbox zone。

補充：目前這個 workflow template repo 的 Dev Container 實作，已為 maintainer-local 環境直接提供 full-vault mount 到 `/obsidian/vault`。因此這份邊界定義應理解為治理建議與 downstream 預設，不是說 template repo 目前仍停留在 restricted mount 模式。

## 4. 同步來源白名單

真正開始同步前，先列出允許來源。

目前推薦白名單：

- 高品質 handoff 摘要
- 經整理後的 decision record
- 穩定的 maintainer SOP / checklist / analysis
- 已完成初步 reusable assessment 的 improvement candidate 摘要
- 已完成任務後整理出的 lessons learned

## 5. 不同步黑名單

正式設定前，也要先列出明確黑名單：

- `doc/plans/*.md`
- `doc/logs/*.md`
- `.agent/workflow_baseline_rules.md`
- `project_rules.md`
- runtime state
- terminal capture
- raw chat export JSON
- 未完成 review 的 handoff / candidate
- 含敏感資訊、專案私有整合細節、一次性 workaround 的內容

## 6. Note metadata 最小欄位

若之後要在 Obsidian 內做可追溯整理，建議每份同步筆記至少帶這些欄位：

- `source_repo`
- `source_path`
- `source_type`
- `review_status`
- `synced_on`
- `promotion_status`

其中：

- `review_status` 建議至少區分 `pending`、`approved`、`rejected`
- `promotion_status` 建議至少區分 `local-only`、`reviewed`、`promotion-candidate`

## 7. 第一次手動同步流程

第一次不要做自動化，先手動跑完整流程：

1. 從 repo 挑一份已完成且高訊號的 markdown
2. 依白名單 / 黑名單檢查它是否適合同步
3. 在 vault 建立對應 note 或整理摘要
4. 記錄 `source_repo` 與 `source_path`
5. 標記 `review_status=approved`
6. 確認 vault 內沒有把它改寫成新的 authoritative version
7. 若要給 agent 讀取，再確認它位於預期的 read-only mount 區域

只要第一次手動流程還不穩，就不要進入腳本化或自動同步。

## 8. 設定完成前不要做的事

- 不要直接把整個 repo 掛進 vault 當主要寫入面
- downstream project repo 不要把整個 vault 以可寫方式掛進 container
- 不要建立自動 ingest 全部 markdown 的流程
- 不要讓 agent 從 Obsidian 直接回寫 authoritative docs
- 不要把 `project_maintainers/` 整包鏡像進 vault
- 不要在 review 規則尚未固定前設計 automation

補充：workflow template repo 若由 maintainer 在本機 Dev Container 明確 opt-in，則可例外採用 full-vault writable mount；但仍應保留 reviewed-sync 與 staged promotion 的治理規則。

## 8.1 Canonical writer / promotion 工具

現在 workflow template repo 已提供 maintainer-local canonical tool：

- `.agent/skills/reviewed-sync-manager/scripts/reviewed_sync_manager.py`

用途分成兩段：

1. `write-candidate`
  - 將 repo file / manual summary / JSON payload 寫入 `10-inbox/reviewed-sync-candidates/`
2. `promote-candidate`
  - 將 candidate promotion 到 `20-reviewed/`
  - 同步補 frontmatter、更新 `00-indexes/`、處理 dedupe

限制：

- 這個工具只允許在 workflow template repo 使用
- downstream project repo 不得使用這個工具

## 9. Full-Vault Mode 最小容器驗證

若目前採用的是 workflow template repo 的 maintainer-local full-vault mount，可在 container 內追加跑一輪最小驗證，確認 `00-indexes/`、`10-inbox/`、`20-reviewed/` 真的可見且可操作。

### 9.1 最小容器驗證清單

先確認 mount 根目錄存在：

```bash
echo "$OBSIDIAN_VAULT_ROOT"
ls -la /obsidian/vault
```

預期結果：

- 能看到 `/obsidian/vault`
- 能列出 `00-indexes`、`10-inbox`、`20-reviewed`

再確認三層都可讀：

```bash
ls -la /obsidian/vault/00-indexes
ls -la /obsidian/vault/10-inbox
ls -la /obsidian/vault/20-reviewed
```

預期結果：

- 三個目錄都能正常列出內容
- 不出現 `No such file or directory` 或 `Permission denied`

若目前 workspace 內有 `obsidian-vault -> /obsidian/vault` 的 symlink，也可順手確認 Explorer 對應路徑正常：

```bash
ls -la /workspaces/agent-workflow-template/obsidian-vault
ls -la /workspaces/agent-workflow-template/obsidian-vault/00-indexes
```

再確認三層目前在 full-vault mount 下都可寫：

```bash
touch /obsidian/vault/00-indexes/.container-write-check && rm /obsidian/vault/00-indexes/.container-write-check
touch /obsidian/vault/10-inbox/.container-write-check && rm /obsidian/vault/10-inbox/.container-write-check
touch /obsidian/vault/20-reviewed/.container-write-check && rm /obsidian/vault/20-reviewed/.container-write-check
```

預期結果：

- 三條命令都成功
- 不出現 `Permission denied`
- 驗證檔建立後立即清掉，不留下測試垃圾

若要一次跑完，可使用這組最小 smoke check：

```bash
set -e
for dir in /obsidian/vault/00-indexes /obsidian/vault/10-inbox /obsidian/vault/20-reviewed; do
  test -d "$dir"
  test -r "$dir"
  test -w "$dir"
  touch "$dir/.container-write-check"
  rm "$dir/.container-write-check"
  echo "OK: $dir"
done
```

若這組檢查全部通過，代表目前 container 內對這三層的 mount、讀取與基本寫入能力都正常。

## 10. 完成前置作業的判準

以下條件都成立，才算完成前置作業：

1. 已明確區分 repo 與 Obsidian 的角色
2. 已定義同步白名單與黑名單
3. 已決定 vault 內的 reviewed / pending 結構
4. 已定義 Dev Container 的 read-only / writable mount 邊界
5. 已定義最小 metadata 欄位
6. 已完成至少一次手動 reviewed-sync 演練

## 11. 與相關文件的關係

- 原則與治理邊界：`2026-03-20-project-maintainers-obsidian-sync-policy.md`
- vault 結構與欄位範本：`2026-03-20-obsidian-vault-structure-and-frontmatter.md`
- downstream 候選晉升判準：`../../project_maintainers/improvement_candidates/PROMOTION-GUIDE.md`

這份 checklist 是操作層補充，不取代政策文件。
