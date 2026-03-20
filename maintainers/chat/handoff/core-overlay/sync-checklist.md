# Core + Overlay Sync Command / Release Checklist

> 建立日期：2026-03-19
> 狀態：Active Supporting Doc
> 用途：把 core + overlay + git subtree 的日常同步流程，收斂成 phase-1 `workflow-core` wrapper family 對齊的 command contract 與 release checklist。

---

## 0. 這份文件的定位

這份文件不是逐行定義最終 shell 或 Python 實作，而是固定目前 phase-1 script / wrapper 應承擔的責任、輸入、輸出與失敗條件。

目標是避免後續擴充或搬到其他 downstream repo 時，又各自發明不同的 sync 手法。

目前 repo 已有對應的 wrapper scripts、projection/bootstrap artifact 與 focused tests；這份文件保留的價值是把操作順序、hard gate 與 machine-readable contract 用 maintainer 可審閱的方式固定下來。

若要看更正式的 command 介面定義，請接著看：

- `cli-spec.md`

這份文件預設搭配下列文件一起看：

- `daily-sync-sop.md`
- repo root `core_ownership_manifest.yml`
- `remote-stage-e2e-core-v20260320-2.md`

---

## 1. script contract 先固定什麼，不固定什麼

### 先固定

- upstream release 前必跑哪些檢查
- downstream sync 前必跑哪些檢查
- 每一步應輸出哪些 machine-readable metadata
- 哪些情況必須 hard fail
- 哪些情況可進入 manual review / override
- canonical manifest、projection/bootstrap artifact、portable smoke suite 各自的固定路徑

### 先不要固定

- 實際 shell 寫法
- 實際 Python entrypoint 名稱
- 最終用 `git subtree`、`git worktree`、或 export branch wrapper 的內部細節
- CI/CD 平台綁定

### 先固定的路徑 contract

- canonical machine-readable source of truth: `./core_ownership_manifest.yml`
- projection/bootstrap artifact: `.agent/runtime/scripts/workflow_core_projection.py`
- portable smoke suite: `.agent/runtime/scripts/portable_smoke/workflow_core_smoke.py`

這三個路徑一旦定型，後續 wrapper command 應讀 manifest，再由 manifest 指向 projection/bootstrap 與 smoke suite，而不是各 command 各自 hardcode 一套 prefix 或 path。

---

## 2. 建議 command family

未來建議至少收斂成以下六個 wrapper command。名字可再調整，但責任面最好固定。

### A. upstream release lane

#### `workflow-core release precheck`

用途：在 upstream 發版前，驗證這次變更是否仍符合 core contract。

最低責任：

1. 確認變更未違反 managed/excluded path 邊界
2. 確認 root live path contract 未被破壞
3. 確認 `.agent/skills` mutable/state 沒重新回流進 core tree
4. 以 `./core_ownership_manifest.yml` 為唯一 machine-readable source of truth 讀取 ownership 與 verification contract
5. 產出 machine-readable precheck 結果

最低輸出：

```json
{
  "status": "pass|fail",
  "release_candidate_ref": "<git ref>",
  "managed_path_violations": [],
  "live_path_contract_ok": true,
  "skills_mutable_split_ok": true,
  "notes": []
}
```

#### `workflow-core release create`

用途：建立可供 downstream 同步的 release ref。

最低責任：

1. 只在 `release precheck` 通過後執行
2. 建立 tag、release branch，或固定 export ref
3. 輸出 downstream 可引用的唯一 ref

最低輸出：

```json
{
  "status": "pass|fail",
  "release_ref": "<tag|branch|sha>",
  "created_artifacts": [],
  "notes": []
}
```

#### `workflow-core release publish-notes`

用途：為 downstream 維護者生成最小同步說明。

最低責任：

1. 列出本次 release ref
2. 列出是否需要 projection/bootstrap
3. 列出是否有 downstream manual action
4. 列出 manifest path 與 portable smoke suite path
5. 列出 blocking changes 或 migration note

最低輸出：

- markdown release note
- json metadata sidecar

### B. downstream sync lane

#### `workflow-core sync precheck`

用途：在 downstream pull subtree 前，先檢查是否可安全同步。

最低責任：

1. 檢查 working tree 是否乾淨，或至少區分類型
2. 檢查是否存在 core managed path 的 local divergence
3. 檢查 overlay/state path 的變更是否只屬於 local scope
4. 從 `./core_ownership_manifest.yml` 讀取 managed / overlay / state contract，而不是各自 hardcode prefix
5. 輸出 sync 風險分類

最低輸出：

```json
{
  "status": "pass|warn|fail",
  "release_ref": "<target ref>",
  "core_divergence_paths": [],
  "overlay_only_paths": [],
  "state_only_paths": [],
  "manual_review_required": false,
  "notes": []
}
```

#### `workflow-core sync apply`

用途：在 downstream 實際套用 upstream core 更新。

最低責任：

1. 用固定 wrapper 執行 sync apply，不手打 ad hoc subtree / checkout / copy 指令
2. 若 delivery mode 需要 projection/bootstrap，則自動接續執行
3. 保留 sync 前後 ref 與變更摘要
4. projection/bootstrap 由 core-managed artifact `.agent/runtime/scripts/workflow_core_projection.py` 交付，而不是 downstream 額外預裝 wrapper
5. 支援獨立 downstream repo 的 staged-root lane，讓 managed paths 可直接從 staged/export tree materialize 回 root live path
6. 同步失敗時回報明確失敗階段

最低輸出：

```json
{
  "status": "pass|fail",
  "release_ref": "<target ref>",
  "sync_mode": "direct-root|staging-plus-projection",
  "projection_ran": true,
  "changed_managed_paths": [],
  "failed_stage": null,
  "notes": []
}
```

#### `workflow-core sync stage`

用途：把 upstream release ref 的 curated export tree stage 到 downstream repo 內，作為後續 apply / verify 的固定輸入。

最低責任：

1. 用固定 wrapper 執行 remote/export-tree staging，不手打 ad hoc `cp -r`、`rsync`、或零散 git plumbing
2. 若指定 upstream remote，先 fetch 指定 ref，再從 fetched ref 讀 manifest 與 export profile
3. 預設輸出到 `.workflow-core/staging/<release-ref>/`
4. 產出 stage metadata，讓後續 apply / verify 能追蹤 source remote/ref 與 selected paths
5. 失敗時明確指出是 fetch、manifest、還是 export selection 問題

最低輸出：

```json
{
  "status": "pass|fail",
  "release_ref": "<target ref>",
  "source_ref": "<source ref>",
  "resolved_source_ref": "<sha>",
  "source_remote": "origin",
  "profile_name": "curated-core-v1",
  "staging_root": "/abs/path/.workflow-core/staging/<release-ref>",
  "metadata_path": "/abs/path/.workflow-core/staging/<release-ref>/workflow-core-stage-metadata.json",
  "selected_path_count": 0,
  "selected_paths": [],
  "notes": []
}
```

#### `workflow-core sync verify`

用途：在 downstream 套用後立刻做最小驗證。

最低責任：

1. 檢查 root live path 是否存在
2. 檢查 `AGENT_ENTRY.md` 依賴的入口檔仍可用
3. 跑最小 preflight
4. 跑 shared portable smoke suite `.agent/runtime/scripts/portable_smoke/workflow_core_smoke.py`
5. 檢查 `.agent/skills` split contract 未被回破壞
6. 若指定 staged-root lane，直接比對 worktree 與 staged/export tree 的 managed paths 是否已對齊

最低輸出：

```json
{
  "status": "pass|fail",
  "live_paths_ok": true,
  "agent_entry_contract_ok": true,
  "preflight_ok": true,
  "skills_split_ok": true,
  "notes": []
}
```

---

## 3. upstream 發版 checklist

### Release gate

在 upstream 準備發版前，至少逐項確認：

1. 這次改動確實屬於共通 core 能力，不是 project-local overlay 需求
2. 沒有把 runtime state、local install、generated output 放回 core
3. 沒有破壞 root live path continuity
4. 沒有新增未登記的 managed path 或 excluded path 例外
5. 若有 contract 變更，對應文件已同步更新
6. `./core_ownership_manifest.yml` 已同步反映本次 release contract

### Release-ready validation

在開始真正的 curated export 前，建議先跑一次 export landing checklist，避免把 `HEAD` 尚未包含、但 working tree 已經存在的路徑誤判成真正缺失：

```bash
python .agent/runtime/scripts/workflow_core_export_landing_checklist.py --profile curated-core-v1 --output maintainers/chat/handoff/core-overlay
```

判讀原則：

- `Ready In Source Ref`：可直接進入下一輪 release candidate
- `Present Only In Working Tree`：代表已經在本地落地，但還沒進入來源 ref，應先整理進下一個 release candidate
- `Still Missing`：代表第一波 scope 仍有真實缺口，需先補齊或調整 profile

若要直接進入目前已驗證的最小補集，不必重新人工收斂；可直接採用：

- `maintainers/chat/handoff/core-overlay/curated-core-v1-release-candidate-batch.md`
- `maintainers/chat/handoff/core-overlay/curated-core-v1-release-candidate-batch.json`

這兩份 artifact 已固定目前 17 個 `worktree-only` include patterns 對應的最小 release-candidate 批次，並記錄在隔離驗證中把 `curated-core-v1` 從 `warn` 推進到 `pass` 的結果。

至少驗證：

1. `AGENT_ENTRY.md` 依賴的入口路徑仍成立
2. preflight / bootstrap 路徑仍成立
3. `.agent/skills` canonical core tree 不會因正常操作產生 runtime-written diff
4. portable smoke suite 可從 core-managed path 直接執行
5. 下游需要知道的 migration action 已被寫清楚

### Release artifact

每次 release 至少應產出：

1. 唯一 release ref
2. 一份 release metadata json
3. 一份簡短 downstream sync note
4. 一份指向 `./core_ownership_manifest.yml` 的 manifest metadata

建議 release metadata 欄位：

```json
{
  "release_ref": "core-vYYYYMMDD-N",
  "source_commit": "<sha>",
  "requires_projection": true,
  "requires_manual_followup": false,
  "breaking_contracts": [],
  "migration_notes": []
}
```

---

## 4. downstream 同步 checklist

### Sync stage

同步前若 upstream release 需要先進 staging root，至少確認：

1. 目標 release ref 已明確
2. 若走 remote lane，upstream remote 名稱與可 fetch ref 已確認
3. staging root 預設落在 `.workflow-core/staging/<release-ref>/`
4. stage wrapper 會輸出 metadata，而不是只留下不帶來源資訊的檔案副本
5. 後續 apply / verify 要直接消費同一個 staging root，不另外手動改路徑

### Sync precheck

同步前至少確認：

1. 目標 release ref 已明確
2. 本地 overlay 與 state 變更已被識別
3. 本地沒有未處理的 core managed path divergence
4. `./core_ownership_manifest.yml` 存在且可被 wrapper commands 共同讀取
5. projection/bootstrap 所需條件已存在
6. 若 staging root 位於 repo 內，需接受 `.workflow-core/staging/**` 被分類為 manual-review warning，而不是誤判成 core divergence

### Sync apply

同步時至少保證：

1. 一律走固定 wrapper command，不手打 ad hoc subtree 指令
2. 若需要 projection/bootstrap，必須自動串接，不可依賴操作者記憶
3. projection/bootstrap artifact 應隨 core 交付，不要求 downstream 先安裝外部 wrapper
4. 若以獨立 downstream staged-root lane 同步，應由 wrapper 從 staged/export tree 讀入 managed paths，而不是要求操作者自行手動複製回 root
5. 發生衝突時，要能指出是 core divergence、delivery contract，還是 split contract 問題

### Sync verify

同步後至少驗證：

1. root 下 `./.agent/**`、`./doc/**` live path 仍可用
2. `AGENT_ENTRY.md` 所需檔案仍可直接讀取
3. 最小 preflight 可過
4. shared portable smoke suite 可過
5. `.agent/skills` split 後的 state/config/local install 沒被拉回 core managed tree
6. 若 apply 走 staged-root lane，verify 也要能直接以 staged/export tree 作為對齊基準

### Sync record

每次 sync 後至少記錄：

1. sync 日期
2. upstream release ref
3. sync operator
4. 是否執行 projection/bootstrap
5. 是否存在 temporary divergence

建議 sync record 欄位：

```json
{
  "synced_at": "2026-03-19T00:00:00Z",
  "release_ref": "core-vYYYYMMDD-N",
  "operator": "<name>",
  "projection_ran": true,
  "temporary_divergence": [],
  "verification": {
    "live_paths_ok": true,
    "preflight_ok": true,
    "skills_split_ok": true
  }
}
```

---

## 5. 哪些情況要 hard fail

下列情況不應只給 warning，而應直接 fail：

1. `AGENT_ENTRY.md` 依賴的 root live path 缺失
2. 準備 release 時發現 `.agent/skills` mutable state 被重新寫回 core
3. downstream sync 前發現 core managed path 有未分類 local divergence
4. 需要 projection/bootstrap，但執行條件或腳本不存在
5. canonical `./core_ownership_manifest.yml` 缺失、失效、或不同 commands 讀的是不同 manifest path
6. verify 階段 preflight 或 portable smoke suite 失敗

---

## 6. 哪些情況可進 manual review

下列情況可先停在 manual review，而不是立刻 fail：

1. downstream 有 overlay-only 變更，但不影響 core managed path
2. release note 中有 manual migration step，需要操作者確認是否已完成
3. temporary divergence 已存在，但有明確對應 upstream follow-up，且這次 sync 不碰該路徑
4. `.workflow-core/staging/**` staged input 位於 downstream repo 內，`sync precheck` 因此回 `warn`；只要 warning 可被確認來自 staged export tree 本身，而不是 root live path 下的 core divergence，即可進入 apply

manual review 的重點是讓腳本明確說出「為什麼停」，不是把判斷責任全部丟回人腦。

---

## 7. 最小落地順序紀錄

這組 phase-1 wrapper family 已依下列優先序完成最小落地；後續若要擴充，仍建議沿用同一個優先順序：

1. 先做 `workflow-core sync stage`
2. 再做 `workflow-core sync precheck`
3. 再做 `workflow-core sync apply`
4. 再做 `workflow-core sync verify`
5. 然後補 `workflow-core release precheck`
6. 最後再補 `release create` 與 `publish-notes`

原因很簡單：先把 remote/export-tree transport 收斂成固定 wrapper，再把 downstream 消費端的風險擋住，接著才 materialize 回 root live path，最後驗證落地結果，會比先包裝 upstream 發版更重要。

---

## 8. 已驗證的 downstream staged sync lane

截至 2026-03-20，下面這條最小 lane 已有獨立 downstream temp repo 的實際驗證：

1. upstream release ref 先經 `workflow-core sync stage` materialize 到 downstream `.workflow-core/staging/<label>/`
2. `workflow-core sync precheck` 回 `warn`
3. warning 原因僅來自 `.workflow-core/staging/**` staged input
4. `workflow-core sync apply --staging-root ...` 回 `pass`
5. `workflow-core sync verify --staging-root ...` 回 `pass`
6. portable smoke during verify 回 `pass`
7. downstream 先前故意偏離的 managed workflow file 已成功恢復成 staged export 內容

這代表目前 phase-1 已不只是在維護 command contract；`export -> stage -> apply -> verify` 這條 lane 已有實際可重跑的 downstream 落地模型。

---

## 9. 最短結論

這份文件真正要固定的，不是某一條 shell 指令，而是兩件事：

1. upstream release 與 downstream sync 必須有一致的 machine-readable contract
2. live path continuity 與 `.agent/skills` split contract 必須成為每次發版與同步的 hard gate

只要這兩件事先固定，後續不論 wrapper 最後用 shell、Python，或 CI job 實作，都不容易漂成一堆 repo-specific 手工流程。
