# workflow-core CLI Spec v1

> 建立日期：2026-03-19
> 狀態：Active Maintainer Spec
> 用途：把 `workflow-core` 六個 wrapper commands 收斂成統一的 CLI 契約，先固定參數形狀、exit code、stdout/stderr 規格與 machine-readable 輸出。

---

## 0. 範圍

這份 spec 定義的是 command contract，不是內部實作細節。

它要先固定三件事：

1. 操作者與腳本之間的介面
2. upstream release lane 與 downstream sync lane 的共同 exit code / I/O 行為
3. 哪些狀態算 pass、manual review、blocking fail、runtime error

這份 spec 不限定最終一定要用 shell、Python、或 CI job 實作；但所有實作都應服從同一份 CLI contract。

---

## 1. Command Family

第一版先固定以下六個 commands：

1. `workflow-core release precheck`
2. `workflow-core release create`
3. `workflow-core release publish-notes`
4. `workflow-core sync precheck`
5. `workflow-core sync apply`
6. `workflow-core sync verify`

目前 repo 已落第一版 Python entrypoint 與支援 artifact：

- `workflow-core release precheck`
  - `.agent/runtime/scripts/workflow_core_release_precheck.py`
- `workflow-core release create`
  - `.agent/runtime/scripts/workflow_core_release_create.py`
- `workflow-core release publish-notes`
  - `.agent/runtime/scripts/workflow_core_release_publish_notes.py`
- `workflow-core sync precheck`
  - `.agent/runtime/scripts/workflow_core_sync_precheck.py`
- `workflow-core sync apply`
  - `.agent/runtime/scripts/workflow_core_sync_apply.py`
- `workflow-core sync verify`
  - `.agent/runtime/scripts/workflow_core_sync_verify.py`
- projection/bootstrap artifact
  - `.agent/runtime/scripts/workflow_core_projection.py`
- shared manifest/contract helpers
  - `.agent/runtime/scripts/workflow_core_manifest.py`
  - `.agent/runtime/scripts/workflow_core_contracts.py`
- curated export materializer
  - `.agent/runtime/scripts/workflow_core_export_materialize.py`
- export landing checklist generator
  - `.agent/runtime/scripts/workflow_core_export_landing_checklist.py`
- first-wave export profile
  - `core_ownership_manifest.yml > export_profiles > curated-core-v1`

目前這組 phase-1 wrapper family 已有 focused tests 覆蓋主要 contract；本文件仍作為 CLI 介面與輸出契約的 maintainer 參照。

補充：`workflow_core_export_materialize.py` 與 `workflow_core_export_landing_checklist.py` 都不是第 1 版 wrapper family 的第七個 release/sync command；前者負責把 canonical manifest 中已經決定的 export profile materialize 成可審查 export tree，後者負責把同一個 profile 轉成可重跑的 landing checklist，區分 source ref 已具備、只存在 working tree、以及仍缺失的項目，用來正式開始 curated core / overlay 落地。

---

## 2. Common CLI Conventions

### 2.1 Common argument rules

- `--repo-root PATH`
  - optional
  - default: current working directory
  - meaning: repo 根目錄
- `--manifest PATH`
  - optional
  - default: `./core_ownership_manifest.yml`
  - meaning: 所有 release / sync commands 應共讀的 canonical machine-readable source of truth
- `--json`
  - optional flag
  - default: text mode
  - meaning: stdout 只輸出 machine-readable JSON

### 2.2 Output rules

- `stdout`
  - 只輸出 primary report
  - text mode 時輸出單一可讀報告
  - `--json` mode 時輸出單一 JSON object
- `stderr`
  - 只用於 usage error、runtime error、或 hard fail 補充訊息
  - `--json` mode 下若是 runtime error，stderr 應輸出單一 JSON error object
- 不應把 progress chatter 混進 stdout JSON
- projection/bootstrap 與 shared smoke suite 的 path 應從 manifest 衍生，不應由 individual command 各自 hardcode

### 2.3 Exit code contract

所有 `workflow-core` commands 第一版共用以下 exit code：

- `0`
  - `pass`
  - command 成功，且沒有 blocking issue，也不需要 manual review
- `10`
  - `warn`
  - command 已完成，但需要 manual review / operator attention
- `20`
  - `fail`
  - command 執行成功，但命中 blocking contract violation 或 hard gate
- `30`
  - `error`
  - command 本身發生 runtime/infrastructure error，例如 git 無法執行、repo 無效、必要腳本不存在
- `2`
  - 保留給 `argparse`/usage error

### 2.4 Status vocabulary

所有 JSON 輸出中的 `status` 第一版固定只用：

- `pass`
- `warn`
- `fail`
- `error`

`warn` 代表可繼續，但不應靜默跳過人審；`fail` 代表不應往下一步自動推進。

---

## 3. Command Specs

### 3.1 `workflow-core release precheck`

#### Required arguments

- 無

#### Optional arguments

- `--repo-root PATH`
- `--release-candidate-ref REF`
- `--manifest PATH`
- `--json`

#### Behavior

- 驗證 release candidate 是否仍符合 core ownership boundary
- 驗證 root live path contract 未被破壞
- 驗證 `.agent/skills` mutable/state 未回流進 core
- 以 `./core_ownership_manifest.yml` 為預設唯一 machine-readable source of truth

#### stdout JSON contract

```json
{
  "status": "pass|fail|error",
  "repo_root": "/abs/path",
  "manifest_path": "/abs/path",
  "release_candidate_ref": "<ref-or-null>",
  "managed_path_violations": [],
  "live_path_contract_ok": true,
  "skills_mutable_split_ok": true,
  "notes": []
}
```

#### stderr contract

- `usage` 或 `runtime error` 時輸出錯誤說明

#### Exit code

- `0`, `20`, `30`, `2`

### 3.2 `workflow-core release create`

#### Required arguments

- `--release-ref REF`

#### Optional arguments

- `--repo-root PATH`
- `--manifest PATH`
- `--source-ref REF`
- `--output PATH`
- `--json`

#### Behavior

- 僅在 release precheck 通過後建立 downstream 可引用的 release ref

#### stdout JSON contract

```json
{
  "status": "pass|fail|error",
  "repo_root": "/abs/path",
  "manifest_path": "/abs/path",
  "release_ref": "<ref>",
  "source_ref": "<ref-or-null>",
  "created_artifacts": [],
  "notes": []
}
```

#### stderr contract

- `usage` 或 `runtime error` 時輸出錯誤說明

#### Exit code

- `0`, `20`, `30`, `2`

### 3.3 `workflow-core release publish-notes`

#### Required arguments

- `--release-ref REF`

#### Optional arguments

- `--repo-root PATH`
- `--manifest PATH`
- `--metadata PATH`
- `--output PATH`
- `--json`

#### Behavior

- 生成 downstream 維護者可直接使用的最小 release note

#### stdout JSON contract

```json
{
  "status": "pass|fail|error",
  "repo_root": "/abs/path",
  "manifest_path": "/abs/path",
  "release_ref": "<ref>",
  "output_path": "/abs/path/or-null",
  "requires_projection": true,
  "requires_manual_followup": false,
  "notes": []
}
```

#### stderr contract

- `usage` 或 `runtime error` 時輸出錯誤說明

#### Exit code

- `0`, `10`, `20`, `30`, `2`

### 3.4 `workflow-core sync precheck`

#### Required arguments

- `--release-ref REF`

#### Optional arguments

- `--repo-root PATH`
- `--manifest PATH`
- `--managed-prefix PREFIX`
  - repeatable
  - phase-1 override only; target state is manifest-driven classification
- `--overlay-prefix PREFIX`
  - repeatable
  - phase-1 override only; target state is manifest-driven classification
- `--state-prefix PREFIX`
  - repeatable
  - phase-1 override only; target state is manifest-driven classification
- `--strict-clean`
  - 若有任何 dirty path，直接升級為 `fail`
- `--json`

#### Behavior

- 讀取 git working tree 狀態
- 讀取 `--manifest` 指向的 canonical ownership contract
- 將 dirty paths 分成 `core divergence`、`overlay-only`、`state-only`、`unclassified`
- 若命中 core divergence，直接 `fail`
- 若只有 overlay/state/unclassified，回 `warn` 並要求 manual review

#### stdout JSON contract

```json
{
  "status": "pass|warn|fail|error",
  "repo_root": "/abs/path",
  "manifest_path": "/abs/path",
  "release_ref": "<ref>",
  "clean_worktree": false,
  "strict_clean": false,
  "core_divergence_paths": [],
  "overlay_only_paths": [],
  "state_only_paths": [],
  "unclassified_paths": [],
  "manual_review_required": false,
  "manual_review_reasons": [],
  "dirty_entries": [],
  "notes": []
}
```

#### stderr contract

- `usage` 或 `runtime error` 時輸出錯誤說明

#### Exit code

- `0`, `10`, `20`, `30`, `2`

### 3.5 `workflow-core sync apply`

#### Required arguments

- `--release-ref REF`

#### Optional arguments

- `--repo-root PATH`
- `--manifest PATH`
- `--sync-mode MODE`
  - `direct-root|staging-plus-projection`
- `--projection-script PATH`
- `--json`

#### Behavior

- 執行固定 wrapper 的 sync apply
- 若需要 projection/bootstrap，必須在同一 command 中自動串接
- projection/bootstrap 的預設 artifact path 應由 manifest 提供，而非各 command 自己定義

#### stdout JSON contract

```json
{
  "status": "pass|fail|error",
  "repo_root": "/abs/path",
  "manifest_path": "/abs/path",
  "release_ref": "<ref>",
  "sync_mode": "direct-root|staging-plus-projection",
  "projection_ran": true,
  "changed_managed_paths": [],
  "failed_stage": null,
  "notes": []
}
```

#### stderr contract

- `usage` 或 `runtime error` 時輸出錯誤說明

#### Exit code

- `0`, `20`, `30`, `2`

### 3.6 `workflow-core sync verify`

#### Required arguments

- `--release-ref REF`

#### Optional arguments

- `--repo-root PATH`
- `--manifest PATH`
- `--require-live-path PATH`
  - repeatable
- `--preflight-command CMD`
- `--smoke-command CMD`
- `--json`

#### Behavior

- 驗證 sync 後 root live path、入口契約、portable smoke suite 與最小 preflight 是否仍成立

#### stdout JSON contract

```json
{
  "status": "pass|fail|error",
  "repo_root": "/abs/path",
  "manifest_path": "/abs/path",
  "release_ref": "<ref>",
  "live_paths_ok": true,
  "agent_entry_contract_ok": true,
  "preflight_ok": true,
  "portable_smoke_ok": true,
  "skills_split_ok": true,
  "notes": []
}
```

#### stderr contract

- `usage` 或 `runtime error` 時輸出錯誤說明

#### Exit code

- `0`, `20`, `30`, `2`

---

## 4. Hard-Gate Rules

下列情況第一版應直接 `fail`，不降級為 `warn`：

1. `AGENT_ENTRY.md` 依賴的 root live path 缺失
2. `.agent/skills` mutable state 被重新寫回 core managed tree
3. downstream sync 前發現未分類的 core managed path divergence
4. 需要 projection/bootstrap，但必要條件不存在
5. `--manifest` 指向的 canonical `core_ownership_manifest.yml` 缺失或無法解析
6. verify 階段 preflight 或 portable smoke suite 失敗

---

## 5. Manual Review Rules

下列情況可先回 `warn`，但不得默默當 `pass`：

1. 只有 overlay-only path 變更
2. 只有 state-only path 變更
3. 有 unclassified path，需要操作者判斷 ownership
4. release note 指出有 manual migration step

---

## 6. 最短結論

這份 CLI spec 的核心，不是把六個 commands 的名字列出來而已，而是先把整條 release/sync pipeline 的 I/O contract 固定住。

一旦 exit code、stdout/stderr、status vocabulary 與 JSON shape 先穩定，後續就能用同一份 contract 去驅動 shell wrapper、Python script、甚至 CI automation，而不會每個 repo 各自長出不同同步流程。
