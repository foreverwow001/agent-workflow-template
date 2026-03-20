# SESSION-HANDOFF

## Current goal

本輪真正剩下的事情已縮成 release formalization：remote staged-sync phase-2 transport 已實作為 `workflow_core_sync_stage.py`，獨立 downstream remote-stage e2e 也已固化成 versioned maintainer artifact，full test suite 目前為 `57 passed, 17 subtests passed`。接下來要做的是：1. 把這批未提交變更整理成正式 commit；2. 以該最終 code HEAD 建立 `core-v20260320-2`；3. 跑新的 release chain，將 metadata / notes artifacts 納入版本控制並 push。

## Current branch

main

## Active container mode

- Standard Dockerfile / GHCR accelerated
- Debian GNU/Linux 12 dev container

## Files touched

- `.agent/runtime/scripts/workflow_core_contracts.py`
- `.agent/runtime/scripts/workflow_core_manifest.py`
- `.agent/runtime/scripts/workflow_core_sync_apply.py`
- `.agent/runtime/scripts/workflow_core_sync_stage.py`
- `core_ownership_manifest.yml`
- `doc/AGENT_WORKFLOW_TEMPLATE_UPSTREAM.md`
- `maintainers/chat/handoff/core-overlay/cli-spec.md`
- `maintainers/chat/handoff/core-overlay/README.md`
- `maintainers/chat/handoff/core-overlay/remote-stage-e2e-core-v20260320-2.md`
- `maintainers/chat/handoff/core-overlay/remote-stage-e2e-core-v20260320-2.json`
- `maintainers/chat/handoff/core-overlay/daily-sync-sop.md`
- `maintainers/chat/handoff/core-overlay/sync-checklist.md`
- `tests/test_workflow_core_wrapper_commands.py`

## What has been confirmed

- Scheme A mutable split phase 1 已落 code：canonical manifest 改到 `.agent/state/skills/skill_manifest.json`、whitelist 改到 `.agent/config/skills/skill_whitelist.json`、audit log 改到 `.agent/state/skills/audit.log`；舊 `.agent/skills/_shared/*.json` / `audit.log` 只保留 read fallback。
- Scheme A mutable split phase 2/3 已落 code：external/local skills 安裝到 `.agent/skills_local/**`，builtin core index 固定為 `.agent/skills/INDEX.md`，local additions 改寫到 `.agent/state/skills/INDEX.local.md`。
- `core_ownership_manifest.yml` 已成為 release/sync automation 的共同 machine-readable source of truth，並已擴充 `export_profiles.curated-core-v1`。
- `core_ownership_manifest.yml` 的 export/managed contract drift 已補齊：`root_path_contract.projection_script` 現已指向實際 artifact path，`managed_paths` 也已補上 `.agent/skills/__init__.py` 與 `.agent/skills/INDEX.md`，使 `curated-core-v1` export profile 與 managed ownership 對齊。
- `workflow_core_manifest.py` 已修正 `split_required.recommended_target` 的 compound-target 判讀，不再把仍屬 managed core 的 `.agent/skills/INDEX.md` 誤判為 state-only target。
- `workflow_core_projection.py`、`workflow_core_sync_precheck.py`、`workflow_core_sync_apply.py`、`workflow_core_sync_verify.py`、`workflow_core_export_materialize.py`、`workflow_core_export_landing_checklist.py` 與 `portable_smoke/workflow_core_smoke.py` 都已在 repo 中 materialize。
- `workflow_core_projection.py` 已不再只是 live-path 檢查 stub；它現在可從 staged/export tree 複製 managed paths 回 downstream root live paths，並在缺少 `doc/implementation_plan_index.md` 時 bootstrap 最小 placeholder。
- `workflow_core_sync_apply.py` 目前已同時支援兩種 downstream lane：既有 `--staging-root` apply，以及新的 remote-stage chain 所需 warning gate。只要 `sync precheck` 的 warning 完全限制在 staging root，且沒有 `core_divergence_paths` / `state_only_paths`，就允許 apply 繼續，不再誤拒 `overlay_only_paths` 類型的 staging warning。
- `workflow_core_sync_verify.py` 已支援 `--staging-root` lane，可在 downstream apply 後直接拿 worktree 與 staged export tree 比對，而不要求先存在可 fetch 的 release ref。
- `workflow_core_sync_stage.py` 已新增並可作為 phase-2 remote transport wrapper：它能 fetch `--source-remote` / `--source-ref`，從來源 ref 讀取 canonical manifest，依 `curated-core-v1` materialize export tree 到 `.workflow-core/staging/<release-ref>/`，並輸出 `workflow-core-stage-metadata.json`。
- `workflow_core_manifest.py` 已新增 `load_manifest_text(...)`，讓 manifest 可以直接從 fetched source ref blob 解析；`workflow_core_contracts.py` 也已補上 `safe_ref_label`、`fetch_ref`、`read_bytes_at_ref`、`read_text_at_ref` 供 remote-stage transport 使用。
- `workflow_core_release_precheck.py` 已升級成真正執行 portable smoke，不只是檢查 smoke suite path 存在。
- `workflow_core_release_create.py` 的 metadata 命名已修成 `workflow-core-release-<ref>.metadata.json`，避免與 `publish-notes` sidecar `.json` collision。
- 正式 release source commit 已建立：`a9a4f0f feat: finalize workflow-core scheme A release source`。
- 主 repo 上的正式 release chain 已跑完，並建立新 tag：`core-v20260320-1`。
- release artifacts 已改為預設落在 `maintainers/release_artifacts/`，且本次 `core-v20260320-1` 的 metadata / notes / sidecar JSON 都已納入版本控制。
- workflow docs / governance cleanup 已完成並提交：`657a103 docs: align workflow governance contracts`。
- legacy terminal tooling retirement 已完成並提交：`2c720fe chore: retire legacy terminal tooling`。
- environment / workspace polish 已完成並提交：`3e7ee92 chore: polish workspace environment docs`。
- maintainers archive / governance history 已完成並提交：`5105d56 docs: add maintainer archive and governance history`。
- internal PR preparation guide 已更新並提交：`59f104d docs: refresh internal release preparation guide`。
- 舊的已合併遠端分支 `chore/sync-dev-team-Idx-019` 與 `feature/v1.1.0-sendtext-bridge` 已自 GitHub 刪除；遠端目前只剩 `origin/main`。
- `workflow_core_export_landing_checklist.py --source-ref HEAD` 目前已在本地 current worktree 上回到 `pass`。
- 新增 focused regression 已補上 remote-stage 與 warning-gate coverage：`tests/test_workflow_core_wrapper_commands.py` 現在覆蓋 `sync stage` remote fetch/materialize flow 與 overlay-only staging warning allowlist；focused 結果為 `13 passed`。
- 已用隔離 `upstream/` + `downstream/` temp repos 做過一輪真正的 remote-stage downstream e2e 驗證：
	- `workflow_core_sync_stage.py --source-remote workflow-core-upstream --source-ref core-v20260320-2-e2e-source`: `pass`
	- `workflow_core_sync_precheck.py`: `warn`，且 warning 僅限 `.workflow-core/staging/core-v20260320-2/**`
	- `workflow_core_sync_apply.py --staging-root .workflow-core/staging/core-v20260320-2`: `pass`
	- `workflow_core_sync_verify.py --staging-root .workflow-core/staging/core-v20260320-2`: `pass`
	- probe file `.agent/workflows/dev-team.md` 已由 `older downstream content` 變成 `upstream managed content`
- 上述 e2e 結果已被固化成 versioned maintainer artifact：`maintainers/chat/handoff/core-overlay/remote-stage-e2e-core-v20260320-2.md` 與 `.json`。
- `doc/AGENT_WORKFLOW_TEMPLATE_UPSTREAM.md` 已改寫成以 `workflow_core_sync_stage.py` 作為優先 transport，而不是手動 `cp -r` / `rsync`。
- core-overlay maintainer docs 已補齊 `sync stage` lane：`cli-spec.md`、`sync-checklist.md`、`daily-sync-sop.md` 與 `README.md` 現已對齊 `sync stage -> precheck -> apply -> verify` 的實際順序與 contract。
- `core_ownership_manifest.yml` 的 automation contract 已將 `workflow-core sync stage` 納入 `commands_must_read_manifest`。
- full `pytest` 已在這一輪 remote-stage 變更上跑完並通過：`57 passed, 17 subtests passed`。
- 目前 `HEAD` 仍是 `bb63a4e999dafd188d50863f7eb1c2c644b1790a`；本輪 remote-stage 相關變更尚未 commit，worktree 不乾淨，release tag 尚未建立。

## Current stage

- `bb63a4e` 仍是當前已提交基線，但本輪又在其上新增了 remote-stage wrapper、warning gate 修正、docs 對齊與 versioned e2e artifact；這批變更目前停留在 working tree。
- 最新正式 workflow-core release tag 仍是 `core-v20260320-1`；新的 `core-v20260320-2` 尚未建立，因此 downstream 若只追 tag，仍看不到本輪 remote-stage delivery。
- 本輪工程上的未完成項目其實只剩 release formalization：把目前工作樹變更提交、建立 `core-v20260320-2`、跑 release chain、將新的 metadata / notes artifacts commit 並 push。

## What was rejected

- 不把新 tag 指到舊 `HEAD`；正式 release 最終是建立在 `a9a4f0f` 這個新 release-source commit，而不是 `5036f74`。
- 不把 release artifacts 留在 repo root；最終改為 `maintainers/release_artifacts/`，並連同 wrapper tests 一起修正。
- 不為了整理 release 而用 destructive git 操作清工作樹；所有後續 cleanup 都拆成獨立 follow-up commits。
- 不對已被 `main` 吃進去的遠端分支再做無意義 merge；最後直接刪除遠端 stale branches。
- 不把新的 downstream staged sync lane 做成另一路與 manifest 脫鉤的例外流程；目前 apply/verify 仍維持 manifest-backed contract，只是新增 `--staging-root` 這條獨立 downstream lane。
- 不把 full `pytest` collection failure 當成外部環境噪音忽略；實際上它揭露了 `tests` absolute-import 契約，最後以最小 `tests/__init__.py` 修正。

## Next exact prompt

請先讀 `maintainers/chat/handoff/2026-03-20-scheme-a-implementation-handoff.md`，再對照 `core_ownership_manifest.yml`、`.agent/runtime/scripts/workflow_core_sync_stage.py`、`.agent/runtime/scripts/workflow_core_manifest.py`、`.agent/runtime/scripts/workflow_core_contracts.py`、`.agent/runtime/scripts/workflow_core_sync_apply.py`、`doc/AGENT_WORKFLOW_TEMPLATE_UPSTREAM.md`、`maintainers/chat/handoff/core-overlay/cli-spec.md`、`maintainers/chat/handoff/core-overlay/sync-checklist.md`、`maintainers/chat/handoff/core-overlay/daily-sync-sop.md` 與 `maintainers/chat/handoff/core-overlay/remote-stage-e2e-core-v20260320-2.md`。目前 remote-stage transport 與 versioned e2e artifact 都已落地，full `pytest` 為 `57 passed, 17 subtests passed`，但這批變更仍未 commit，正式 release tag 仍停在 `core-v20260320-1`。下一步請直接完成 release formalization：1. 把當前工作樹整理成正式 commit；2. 以該 commit 建立 `core-v20260320-2`；3. 執行 `workflow_core_release_create.py` 與 `workflow_core_release_publish_notes.py`，將新的 artifacts 納入版本控制並 push。

## Risks

- 目前 remote-stage wrapper 尚未正式 commit / tag；若現在中斷，repo 內只有 working tree 變更，downstream 仍無法透過正式 release tag 取得這批 transport 改動。
- 新的 `workflow_core_sync_stage.py` 目前採用「fetch remote ref -> 讀 source-ref manifest -> materialize curated export tree 到 staging root」模型；這已滿足 phase-2 remote transport，但若未來要與真正 `git subtree` 原生命令完全對齊，仍可能需要再定義額外的 transport owner / ref naming governance。
- release artifacts 目前只存在 `core-v20260320-1`；完成 `core-v20260320-2` 前，release history 仍落後最新已驗證 contract。
- `core_ownership_manifest.yml` 的 curated package 清單已比 2026-03-19 初稿更前進；後續若 skills tree 再變動，仍要防止 `builtin_core_packages`、`review_required_package_dirs` 與 `export_profiles.curated-core-v1` 漂移。
- release artifacts 現在已 versioned；未來每次 release chain 都應保持 artifact 產出位置、檔名規則與 git-tracked 歷史一致。
- `maintainers/chat/2026-03-19-core-ownership-manifest-v1.md` 與 `2026-03-19-subtree-mutable-path-split-checklist.md` 仍是 2026-03-19 基線文件；它們的 framing 仍有效，但內容已落後目前 manifest curated scope 與已完成項目，後續若持續沿用，最好補一份 archive / delta note。

## Verification status

- 已驗證：主 repo 上的 `workflow_core_release_precheck.py`、`workflow_core_release_create.py`、`workflow_core_release_publish_notes.py` 已完成正式 release chain，並建立 `core-v20260320-1`。
- 已驗證：release artifacts 預設輸出位置已切到 `maintainers/release_artifacts/`，相關 wrapper tests 修正後通過。
- 已驗證：focused regressions 通過，包括 external skill package、sync precheck、export materialize、wrapper commands、Copilot PTY gate / launch、PTY preflight。
- 已驗證：本輪新增 focused workflow-core regressions 通過：`13 passed`（wrapper commands，含 remote-stage 與 staging-warning gate coverage）。
- 已驗證：`workflow_core_export_landing_checklist.py --source-ref HEAD` 在 current worktree 上為 `pass`。
- 已驗證：獨立 downstream temp repo 的 remote-stage sync lane 已完整跑通：`stage pass -> precheck warn -> apply pass -> verify pass`，且 managed probe file 已被 upstream staged export 內容覆蓋。
- 已驗證：core-overlay maintainer docs 已對齊 `sync stage -> precheck -> apply -> verify` 與 verified downstream flow。
- 已驗證：versioned maintainer artifact 已入 repo：`remote-stage-e2e-core-v20260320-2.md` / `.json`。
- 已驗證：後續 full `pytest` 為綠燈，最新整體結果為 `57 passed, 17 subtests passed`。
- 已驗證：`bb63a4e` 仍是目前已提交基線；本輪 remote-stage 變更尚未 commit、尚未推送、尚未建立新 release tag。
- 已驗證：遠端 stale branches 已清除。
- 尚未完成：將本輪 remote-stage 變更整理成正式 commit、建立 `core-v20260320-2`、執行新的 release chain、提交 artifacts 並 push。
