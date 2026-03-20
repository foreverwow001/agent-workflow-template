# Workflow Core Remote Stage E2E Validation

> 建立日期：2026-03-20
> release_ref：`core-v20260320-2`
> 狀態：Validated Maintainer Record
> 用途：固定 `workflow-core sync stage -> sync precheck -> sync apply -> sync verify` 在隔離 upstream/downstream temp repos 上的完整驗證結果，作為 phase-2 remote transport 的可追溯證據。

---

## Summary

- validation_type: `isolated-remote-stage-downstream-sync-e2e`
- release_ref: `core-v20260320-2`
- source_ref: `core-v20260320-2-e2e-source`
- source_remote_name: `workflow-core-upstream`
- profile_name: `curated-core-v1`
- selected_path_count: `101`
- stage_status: `pass`
- precheck_status: `warn`
- precheck_reason: `overlay-dirty limited to staging tree`
- apply_status: `pass`
- verify_status: `pass`
- managed_file_probe: `.agent/workflows/dev-team.md`
- managed_file_result: `downstream probe content was replaced by upstream managed content`

## Validation Setup

- 建立兩個隔離 temp repos：`upstream/` 與 `downstream/`
- 將當前主 repo snapshot 複製到兩邊後各自初始化 git commit
- 在 `upstream/` 修改 managed file `.agent/workflows/dev-team.md` 為 `upstream managed content`
- 在 `downstream/` 將同一 managed file 改成 `older downstream content`
- 在 `upstream/` 建立 tag `core-v20260320-2-e2e-source`
- 在 `downstream/` 新增 remote `workflow-core-upstream -> ../upstream`

## Command Flow

1. `workflow_core_sync_stage.py --source-remote workflow-core-upstream --source-ref core-v20260320-2-e2e-source --release-ref core-v20260320-2 --json`
2. `workflow_core_sync_precheck.py --release-ref core-v20260320-2 --json`
3. `workflow_core_sync_apply.py --release-ref core-v20260320-2 --staging-root .workflow-core/staging/core-v20260320-2 --json`
4. `workflow_core_sync_verify.py --release-ref core-v20260320-2 --staging-root .workflow-core/staging/core-v20260320-2 --json`

## Observed Results

### Stage

- `status = pass`
- `resolved_source_ref = 6e9d83f632b5029d11b3de9c4b4d15772d0f152a`
- `selected_path_count = 101`
- metadata file emitted to staging root: `workflow-core-stage-metadata.json`
- notes:
  - `materialized workflow-core export tree into staging root`
  - `fetched source ref from remote before staging export tree`

### Precheck

- `status = warn`
- `core_divergence_paths = []`
- `state_only_paths = []`
- `unclassified_paths = []`
- `manual_review_required = true`
- `manual_review_reasons = ["overlay-dirty"]`
- 所有 warning path 都位於 `.workflow-core/staging/core-v20260320-2/**`

### Apply

- `status = pass`
- `sync_mode = staging-plus-projection`
- `projection_ran = true`
- notes:
  - `loaded managed paths from staged export tree`
  - `sync precheck warning was limited to the staged export tree and was ignored for apply`
  - `projection/bootstrap materialized managed live paths and validated required anchors`

### Verify

- `status = pass`
- `live_paths_ok = true`
- `agent_entry_contract_ok = true`
- `preflight_ok = true`
- `portable_smoke_ok = true`
- `skills_split_ok = true`

## Contract Implications

- `workflow-core sync stage` 已經提供 phase-2 remote transport 的可執行 wrapper，不再依賴手動 `cp -R` staging。
- `workflow-core sync precheck` 對 staging tree 產生的 `overlay-dirty` warning 屬於預期訊號；只要 warning 僅限 staging root，`workflow-core sync apply` 應允許繼續。
- `workflow-core sync apply` 與 `workflow-core sync verify` 在此 lane 下可成功將 downstream managed live paths 對齊到 remote source ref 所代表的 curated export tree。

## Conclusion

本次隔離驗證證明：對 `curated-core-v1`，目前的 `workflow-core sync stage -> precheck -> apply -> verify` 鏈條已可支援 remote source ref 的 downstream staged sync，並能正確覆蓋既有 managed path 差異，同時保留 staging-root warning 作為人工審核訊號。
