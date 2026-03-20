# SESSION-HANDOFF

## Current goal

延續 2026-03-19 啟動的 Scheme A 實作，把 `core + overlay + git subtree` 的 skills mutable split 與 delivery contract 收尾，並在公司機器上把這批已完成變更整理成真正的 upstream release source。

## Current branch

main

## Active container mode

- Standard Dockerfile / GHCR accelerated
- Debian GNU/Linux 12 dev container

## Files touched

- `.agent/skills/_shared/__init__.py`
- `.agent/skills/__init__.py`
- `.agent/skills/github-explorer/scripts/github_explorer.py`
- `.agent/skills/skill-converter/scripts/skill_converter.py`
- `.agent/scripts/setup_workflow.sh`
- `.agent/skills/INDEX.md`
- `.agent/skills/RESTRUCTURE_BLUEPRINT.md`
- `.agent/PORTABLE_WORKFLOW.md`
- `doc/AGENT_WORKFLOW_TEMPLATE_UPSTREAM.md`
- `README.md`
- `core_ownership_manifest.yml`
- `maintainers/chat/2026-03-19-subtree-mutable-path-split-checklist.md`
- `.agent/runtime/scripts/workflow_core_release_precheck.py`
- `.agent/runtime/scripts/workflow_core_release_create.py`
- `.agent/runtime/tools/vscode_terminal_pty/codex_pty_bridge.py`
- `.agent/runtime/tools/vscode_terminal_pty/extension.js`
- `.agent/runtime/scripts/devcontainer/post_create.sh`
- `.devcontainer/Dockerfile`
- `tests/test_external_skill_package_regression.py`
- `tests/test_workflow_core_wrapper_commands.py`
- `tests/test_pty_bridge_launch_regression.py`
- `tests/test_copilot_composer_gate_regression.py`
- `maintainers/chat/handoff/2026-03-20-scheme-a-implementation-handoff.md`

## What has been confirmed

- Scheme A 的 mutable split phase 1 已落 code：canonical manifest 改到 `.agent/state/skills/skill_manifest.json`、whitelist 改到 `.agent/config/skills/skill_whitelist.json`、audit log 改到 `.agent/state/skills/audit.log`；舊 `.agent/skills/_shared/*.json` / `audit.log` 只保留 read fallback。
- mutable split phase 2/3 也已落 code：external/local skills 現在安裝到 `.agent/skills_local/**`，builtin core index 固定為 `.agent/skills/INDEX.md`，local additions 改寫到 `.agent/state/skills/INDEX.local.md`。
- `github-explorer`、`skill-converter`、`manifest-updater` 的 machine-readable ownership 已回收進 `core_ownership_manifest.yml` 的 `curated-core-v1` export profile；legacy fallback files 仍維持 excluded/deferred。
- bootstrap / operator docs / active checklist 都已同步到新 contract，不再把 external/local installs 寫成 `.agent/skills/**`、也不再把 core `INDEX.md` 當成 local append surface。
- `workflow_core_release_precheck.py` 已升級成真正執行 portable smoke，不只是檢查 smoke suite 路徑存在。
- `workflow_core_release_create.py` 的 metadata 命名已修成 `workflow-core-release-<ref>.metadata.json`，避免被 `publish-notes` 的 sidecar `.json` 覆寫。
- Copilot PTY reload/startup failure 的 root cause 已定位並修正：不是 binary 缺失，而是 PTY bridge 在 reload 當下直接執行 VS Code Copilot wrapper script，偶發撞到 extension 正在重寫該檔，stderr 會出現 `OSError: [Errno 26] Text file busy`。bridge 現已在啟動 shebang wrapper 時先解析 interpreter，再透過 interpreter 啟動 wrapper，避免 `ETXTBSY`。
- Copilot PTY 的另一條 startup 誤判也已修正：近期 artifact 已證明 Copilot 可在 `direct-text + carriage-return` 路徑下正常進入 prompt，但 session 不一定會送出 CSI-U enable signal；Copilot profile 的 startup gate 現已取消 `requireCsiU`，避免把已可輸入的 fresh session 誤判成 timeout。
- 缺少 `/usr/bin/bwrap` 的 Codex 警告已確認是 container/system dependency，而不是 repo runtime bug；目前 container 已安裝 `bubblewrap`，且 devcontainer Dockerfile 與 post-create 都已補上顯式安裝路徑，之後重建 container 應不再缺這個 binary。
- focused regression 已通過：
  - `tests/test_external_skill_package_regression.py`
  - `tests/test_workflow_core_sync_precheck.py`
  - `tests/test_workflow_core_export_materialize.py`
  - `tests/test_workflow_core_wrapper_commands.py`
- 針對本輪 PTY / environment 修正的 focused regression 也已通過：
  - `tests/test_copilot_composer_gate_regression.py`
  - `tests/test_pty_bridge_launch_regression.py`
  - `tests/test_workflow_preflight_pty.py`
- 最新驗證結果：
  - 18 passed, 3 subtests passed（skills split + manifest/export/sync contract）
  - 8 passed（wrapper command focused tests）
  - 7 passed（Copilot PTY gate / PTY bridge launch / PTY preflight focused tests）
- 主 repo 現況可通過正式 release precheck：`workflow-core release precheck: pass`，且 `portable_smoke_ok: True`、`skills_mutable_split_ok: True`。
- 已在隔離 temp snapshot repo 完整跑過 release chain，成功建立 temp tag `core-v20260319-2-temp`，並產出三個 artifacts：
  - `workflow-core-release-core-v20260319-2-temp.metadata.json`
  - `workflow-core-release-core-v20260319-2-temp.md`
  - `workflow-core-release-core-v20260319-2-temp.json`
- 目前 container 內已直接驗證 `bwrap` 在 PATH 上可用：`/usr/bin/bwrap`，版本 `0.8.0`。

## Current stage

- 程式、文件、manifest 與 focused validation 都已達到「可發布」狀態。
- 這輪另外插入的 PTY / environment 修正也已落 code 並通過 focused validation；它們不改變 Scheme A 的 release 主線，但應視為同一次 worktree 內已完成的 supporting fix，而不是待解 blocker。
- 目前唯一還沒在主 repo 落下的，是新的正式 release ref / tag。
- 原因不是 code 未完成，而是主 repo 的 `HEAD` 仍停在舊 commit `5036f74e3ec13d9ca4424b7fe684832329931982`，這批 Scheme A 實作仍在 working tree，尚未整理成新的 commit。
- 現有正式 tag 仍只有 `core-v20260319-1`；它對應的是舊 release，不包含這輪 mutable split phase 2/3、release precheck smoke、以及 release metadata collision fix。

## What was rejected

- 不在主 repo 直接建立新的 release tag 指向舊 `HEAD`。原因：那會把新 tag 指到不含本輪實作的舊內容，發布語意錯誤。
- 不為了做 release 而重置或清掉目前其他未提交變更。原因：repo 內本來就有其他 dirty state，這輪只應整理和 Scheme A 相關的變更，不應用 destructive git 操作硬清工作樹。
- 不把隔離 temp repo 的 `core-v20260319-2-temp` 當成正式 release source。原因：它只用來驗證 current worktree 內容能跑完整 release chain，不是主 repo 的正式交付 ref。

## Next exact prompt

請先讀 `maintainers/chat/handoff/2026-03-20-scheme-a-implementation-handoff.md`。這輪 Scheme A implementation 已完成 code/doc/manifest/validation，現在只差把主 repo 的這批變更整理成正式 release source。先做三件事：1. 檢查並只 stage 本輪 Scheme A / workflow-core 相關檔案；2. 建立一個新的 commit，內容至少包含 skills mutable split phase 2/3、docs/manifest 同步、release precheck smoke、以及 release metadata collision fix；3. 在主 repo 上依序執行 `workflow_core_release_precheck.py`、`workflow_core_release_create.py`、`workflow_core_release_publish_notes.py`，建立新的正式 release ref（不要重用 `core-v20260319-1`）。若過程中發現工作樹還混有不想一起發版的 unrelated changes，先做範圍收斂，不要把新 tag 指到舊 HEAD，也不要用 destructive git 指令硬清整個 repo。

## Risks

- 主 repo 目前仍是 dirty worktree；到公司後若直接在主 repo 建 tag，最容易犯的錯是把 tag 指到舊 HEAD，而不是這輪已驗證過的 current content。
- 這輪已修改 `core_ownership_manifest.yml` 的 export profile；若後續又有其他人改同檔，release 前要先重新確認 `curated-core-v1` includes/excludes/deferred_paths 沒被回退。
- temp release 驗證是成功的，但 temp tag `core-v20260319-2-temp` 只存在 `/tmp/workflow-core-release-*` 隔離 repo，不能當主 repo 正式追蹤依據。
- 雖然 Copilot PTY 的 `ETXTBSY` 與 false-timeout root cause 都已修正，這輪尚未在真實 VS Code reload 後重新做一次完整 interactive smoke；目前依據是 artifact 診斷、runtime checks 與 focused regression，而不是新的 end-to-end reload transcript。

## Verification status

- 已驗證：skills split regression、sync precheck、export materialize、wrapper command tests 都已通過；主 repo release precheck 也已通過。
- 已驗證：isolated temp snapshot 上可完整跑完 `release create -> publish-notes`，且 release metadata 與 notes sidecar 不再 collision。
- 已驗證：Copilot wrapper command 目前可正常解析為 interpreter 啟動；Copilot PTY profile 已取消 `requireCsiU`；`bwrap` 已在目前 container 安裝完成，且 Dockerfile / post-create 已補上持久化修正。
- 尚未驗證：主 repo 上的新正式 release commit / tag / publish-notes 尚未建立，因為這批變更還沒先落成 commit。
