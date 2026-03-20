# SESSION-HANDOFF

## Current goal

Scheme A 的 release 與 follow-up cleanup 已經在主 repo 完成。這一輪進一步把 `core + overlay + git subtree` 的 delivery contract 往前推了一段：manifest/export drift 已修正、projection/bootstrap 已從純 stub 擴成可 materialize staged export tree、sync apply/verify 已支援獨立 downstream repo 的 staged-root lane。現在真正剩下的，不再是 contract 沒定義，而是把這批新變更整理成下一個正式 commit / release candidate，並決定是否要再往真正的 git subtree remote lane 繼續收斂。

## Current branch

main

## Active container mode

- Standard Dockerfile / GHCR accelerated
- Debian GNU/Linux 12 dev container

## Files touched

- `.agent/runtime/scripts/workflow_core_contracts.py`
- `.agent/runtime/scripts/workflow_core_export_landing_checklist.py`
- `.agent/runtime/scripts/workflow_core_export_materialize.py`
- `.agent/runtime/scripts/workflow_core_manifest.py`
- `.agent/runtime/scripts/workflow_core_projection.py`
- `.agent/runtime/scripts/workflow_core_release_create.py`
- `.agent/runtime/scripts/workflow_core_release_precheck.py`
- `.agent/runtime/scripts/workflow_core_release_publish_notes.py`
- `.agent/runtime/scripts/workflow_core_sync_apply.py`
- `.agent/runtime/scripts/workflow_core_sync_precheck.py`
- `.agent/runtime/scripts/workflow_core_sync_verify.py`
- `.agent/runtime/scripts/portable_smoke/workflow_core_smoke.py`
- `.agent/runtime/tools/vscode_terminal_pty/codex_pty_bridge.py`
- `.agent/runtime/tools/vscode_terminal_pty/extension.js`
- `.agent/skills/__init__.py`
- `.agent/skills/_shared/__init__.py`
- `.agent/skills/INDEX.md`
- `.agent/skills/github-explorer/scripts/github_explorer.py`
- `.agent/skills/skill-converter/scripts/skill_converter.py`
- `.agent/PORTABLE_WORKFLOW.md`
- `.agent/PR_PREPARATION.md`
- `.agent/workflows/**`
- `core_ownership_manifest.yml`
- `README.md`
- `doc/AGENT_WORKFLOW_TEMPLATE_UPSTREAM.md`
- `doc/ENVIRONMENT_RECOVERY.md`
- `doc/HOME_OFFICE_SWITCH_SOP.md`
- `doc/NEW_MACHINE_SETUP.md`
- `doc/TOOL_USAGE.md`
- `maintainers/chat/2026-03-19-core-ownership-manifest-v1.md`
- `maintainers/chat/2026-03-19-subtree-mutable-path-split-checklist.md`
- `maintainers/release_artifacts/**`
- `tests/test_copilot_composer_gate_regression.py`
- `tests/test_workflow_core_delivery_contract.py`
- `tests/test_external_skill_package_regression.py`
- `tests/test_pty_bridge_launch_regression.py`
- `tests/test_workflow_core_export_materialize.py`
- `tests/test_workflow_core_sync_precheck.py`
- `tests/test_workflow_core_wrapper_commands.py`

## What has been confirmed

- Scheme A mutable split phase 1 已落 code：canonical manifest 改到 `.agent/state/skills/skill_manifest.json`、whitelist 改到 `.agent/config/skills/skill_whitelist.json`、audit log 改到 `.agent/state/skills/audit.log`；舊 `.agent/skills/_shared/*.json` / `audit.log` 只保留 read fallback。
- Scheme A mutable split phase 2/3 已落 code：external/local skills 安裝到 `.agent/skills_local/**`，builtin core index 固定為 `.agent/skills/INDEX.md`，local additions 改寫到 `.agent/state/skills/INDEX.local.md`。
- `core_ownership_manifest.yml` 已成為 release/sync automation 的共同 machine-readable source of truth，並已擴充 `export_profiles.curated-core-v1`。
- `core_ownership_manifest.yml` 的 export/managed contract drift 已補齊：`root_path_contract.projection_script` 現已指向實際 artifact path，`managed_paths` 也已補上 `.agent/skills/__init__.py` 與 `.agent/skills/INDEX.md`，使 `curated-core-v1` export profile 與 managed ownership 對齊。
- `workflow_core_manifest.py` 已修正 `split_required.recommended_target` 的 compound-target 判讀，不再把仍屬 managed core 的 `.agent/skills/INDEX.md` 誤判為 state-only target。
- `workflow_core_projection.py`、`workflow_core_sync_precheck.py`、`workflow_core_sync_apply.py`、`workflow_core_sync_verify.py`、`workflow_core_export_materialize.py`、`workflow_core_export_landing_checklist.py` 與 `portable_smoke/workflow_core_smoke.py` 都已在 repo 中 materialize。
- `workflow_core_projection.py` 已不再只是 live-path 檢查 stub；它現在可從 staged/export tree 複製 managed paths 回 downstream root live paths，並在缺少 `doc/implementation_plan_index.md` 時 bootstrap 最小 placeholder。
- `workflow_core_sync_apply.py` 已支援 `--staging-root` lane，可在獨立 downstream repo 中直接從 staged export tree 載入 managed paths，再串 projection/bootstrap；不再只支援「同 repo 以 git ref checkout managed paths」。
- `workflow_core_sync_verify.py` 已支援 `--staging-root` lane，可在 downstream apply 後直接拿 worktree 與 staged export tree 比對，而不要求先存在可 fetch 的 release ref。
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
- 新增的 focused regressions 已通過：
	- `tests/test_workflow_core_export_materialize.py`
	- `tests/test_workflow_core_delivery_contract.py`
	- `tests/test_workflow_core_wrapper_commands.py`
	- 最新結果：`18 passed`
- 已用 current worktree snapshot 做過一輪真正獨立 downstream repo 的 end-to-end staged sync 驗證：
	- snapshot export materialize: `pass`
	- downstream sync precheck: `warn`（只因 `.workflow-core/staging/**` 屬 staged input）
	- downstream sync apply `--staging-root`: `pass`
	- downstream sync verify `--staging-root`: `pass`
	- portable smoke during verify: `pass`
	- downstream mutated managed workflow file 已成功回復成 staged export 內容
- `doc/AGENT_WORKFLOW_TEMPLATE_UPSTREAM.md` 已改寫成現在真正可跑的 upstream export + downstream staged sync flow，不再建議以手動 `cp -r` / `rsync` 作為主要模型。
- 目前 worktree 不再乾淨；這一輪新增的 core/overlay follow-up 改動尚未 commit。

## Current stage

- 這一輪的 release 主線已完成；不再存在「新的正式 release ref / tag 尚未建立」這個 blocker。
- 目前最新正式 workflow-core release tag 是 `core-v20260320-1`，其 release artifacts 已隨 repo history 追蹤。
- repo 目前公開分支仍位於 `59f104d docs: refresh internal release preparation guide`，但 working tree 另有一批未提交的 core/overlay follow-up 變更：manifest、projection/apply/verify、upstream guide、handoff 與 focused tests。
- 這批未提交變更已把先前 handoff 中列出的三個 gap 實際往前推進：
	- projection/bootstrap 不再只是 stub
	- sync apply 不再只支援同 repo checkout model
	- 獨立 downstream repo e2e staged sync 已有實際驗證紀錄
- 下一步應聚焦在：1. 把這批變更整理成 commit；2. 決定是否需要新的 release candidate / tag；3. 視需要把 staged-root lane 再推進到真正的 git subtree remote lane。

## What was rejected

- 不把新 tag 指到舊 `HEAD`；正式 release 最終是建立在 `a9a4f0f` 這個新 release-source commit，而不是 `5036f74`。
- 不把 release artifacts 留在 repo root；最終改為 `maintainers/release_artifacts/`，並連同 wrapper tests 一起修正。
- 不為了整理 release 而用 destructive git 操作清工作樹；所有後續 cleanup 都拆成獨立 follow-up commits。
- 不對已被 `main` 吃進去的遠端分支再做無意義 merge；最後直接刪除遠端 stale branches。
- 不把新的 downstream staged sync lane 做成另一路與 manifest 脫鉤的例外流程；目前 apply/verify 仍維持 manifest-backed contract，只是新增 `--staging-root` 這條獨立 downstream lane。

## Next exact prompt

請先讀 `maintainers/chat/handoff/2026-03-20-scheme-a-implementation-handoff.md`，再對照 `core_ownership_manifest.yml`、`maintainers/chat/2026-03-19-core-ownership-manifest-v1.md`、`maintainers/chat/2026-03-19-subtree-mutable-path-split-checklist.md`、`.agent/runtime/scripts/workflow_core_manifest.py`、`.agent/runtime/scripts/workflow_core_projection.py`、`.agent/runtime/scripts/workflow_core_sync_apply.py`、`.agent/runtime/scripts/workflow_core_sync_verify.py`、`.agent/runtime/scripts/workflow_core_export_materialize.py` 與 `doc/AGENT_WORKFLOW_TEMPLATE_UPSTREAM.md`。這批 core/overlay follow-up 變更目前還在 working tree，但 focused tests 與獨立 downstream e2e staged sync 已經通過。下一步請做三件事：1. 先收斂並提交這一批 manifest/projection/sync/docs/tests 變更；2. 判斷這批是否值得建立新的 workflow-core release candidate/tag；3. 再分析 staged-root lane 之後，是否還需要真正的 git subtree remote transport implementation，還是目前已足夠作為 phase-2 交付模型。

## Risks

- 這批新增變更目前仍未 commit；若要把它當成新的正式交付，需要先整理成 commit，否則 downstream lane 的新能力只存在 working tree。
- `workflow_core_sync_apply.py` / `workflow_core_sync_verify.py` 現已支援 staged-root lane，但這仍不是直接操作 remote subtree 的 transport implementation；若未來要和真正的 subtree remote flow 合流，還需要決定 transport owner 與 remote/ref model。
- current worktree snapshot 的 downstream e2e 驗證已通過，但它目前是 temp snapshot repo 留痕，而不是 repo 內 versioned artifact；若要長期追蹤，可能還需新增 maintainer log / SOP 留痕。
- `core_ownership_manifest.yml` 的 curated package 清單已比 2026-03-19 初稿更前進；後續若 skills tree 再變動，仍要防止 `builtin_core_packages`、`review_required_package_dirs` 與 `export_profiles.curated-core-v1` 漂移。
- release artifacts 現在已 versioned；未來每次 release chain 都應保持 artifact 產出位置、檔名規則與 git-tracked 歷史一致。

## Verification status

- 已驗證：主 repo 上的 `workflow_core_release_precheck.py`、`workflow_core_release_create.py`、`workflow_core_release_publish_notes.py` 已完成正式 release chain，並建立 `core-v20260320-1`。
- 已驗證：release artifacts 預設輸出位置已切到 `maintainers/release_artifacts/`，相關 wrapper tests 修正後通過。
- 已驗證：focused regressions 通過，包括 external skill package、sync precheck、export materialize、wrapper commands、Copilot PTY gate / launch、PTY preflight。
- 已驗證：本輪新增 focused workflow-core regressions 通過：`18 passed`（export materialize + delivery contract + wrapper commands）。
- 已驗證：`workflow_core_export_landing_checklist.py --source-ref HEAD` 在 current worktree 上為 `pass`。
- 已驗證：獨立 downstream temp repo 的 staged sync lane 已完整跑通：`precheck warn -> apply pass -> verify pass`。
- 已驗證：後續多輪 full `pytest` 為綠燈，最新整體結果為 `52 passed`。
- 已驗證：遠端 stale branches 已清除。
- 尚未驗證：這批新的 core/overlay follow-up 變更尚未完成 full `pytest`、正式 commit、以及新的 release candidate / tag。
