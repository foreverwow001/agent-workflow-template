# SESSION-HANDOFF

## Current goal

自 `maintainers/chat/handoff/2026-03-20-scheme-a-implementation-handoff.md` 之後，到目前為止有兩段工作已經明確分開：

1. 上一份 handoff 當時尚未完成的 bootstrap / dependency hardening，後續已完成 commit、測試並推上 `main`
2. 目前工作樹中則累積了一批新的 Obsidian / pending-review triage / reviewed-sync / downstream intake gate 變更，目標是把 repo-first + reviewed-sync + downstream restricted consumer profile 落成明確工具與 workflow 契約

這份 handoff 的用途，是把「自上一份 handoff 後已完成了什麼」和「目前這批準備帶去公司繼續接手的變更」一次講清楚。

## Current branch

main

## Active container mode

- Standard Dockerfile / GHCR accelerated
- Debian GNU/Linux 12 dev container

## Since previous handoff: completed and already on `main`

上一份 handoff 裡最後一條未完成事項是：把 bootstrap / dependency hardening 變更提交並 push。

這件事後續已完成，而且又往前推進了 4 個 commit：

- `f268b73 chore: bootstrap workflow prerequisites`
  - 新增 `.agent/runtime/scripts/install_workflow_prereqs.sh`
  - `post_create.sh` 改為先做最小依賴檢查
  - `install_terminal_tooling.sh` 改成可自動補 CLI 條件
  - `.agent/PORTABLE_WORKFLOW.md`、`doc/NEW_MACHINE_SETUP.md`、`maintainers/new-project-core-overlay-sop.md` 已同步補 bootstrap / prereq 文件
- `a90a4f2 test: cover bootstrap hardening scripts`
  - 新增 `tests/test_bootstrap_hardening_regression.py`
- `bd5d2d1 feat: add downstream project handoff skeleton`
  - downstream repo 現在隨 curated core 帶出 `project_maintainers/README.md`
  - 新增 `project_maintainers/chat/README.md`
  - 新增 `project_maintainers/chat/archive/README.md`
  - 新增 `project_maintainers/chat/handoff/SESSION-HANDOFF.template.md`
- `5ccf352 feat: add improvement candidate promotion flow`
  - downstream repo 現在隨 curated core 帶出 `project_maintainers/improvement_candidates/README.md`
  - 新增 `IMPROVEMENT-CANDIDATE.template.md`
  - 新增 `PROMOTION-GUIDE.md`

也就是說，上一份 handoff 當時掛著的 bootstrap / dependency hardening follow-up，現在已不再是待辦；它已經被提交、測試，且目前 `origin/main` 與本地 `main` 一致。

## Current uncommitted batch

目前真正還沒提交的是一批新的 Obsidian / triage / reviewed-sync 工作，範圍如下：

### 1. Obsidian mount and governance

- `.devcontainer/devcontainer.json`
- `.devcontainer/devcontainer.ghcr.json`
- `.gitignore`
- `maintainers/chat/README.md`
- `maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md`
- `maintainers/chat/2026-03-20-obsidian-reviewed-sync-checklist.md`
- `maintainers/chat/2026-03-20-obsidian-vault-structure-and-frontmatter.md`

這批變更已把 workflow template repo 的 maintainer-local full-vault mount 寫入 Dev Container：

- `OBSIDIAN_VAULT_ROOT=/obsidian/vault`
- bind mount 指到 maintainer 本機 vault

同時也把政策邊界寫清楚：

- workflow template repo = full curator profile（maintainer-local）
- downstream repo = restricted consumer profile
- downstream 啟動讀取面應為 `00-indexes/` + 最小必要 `20-reviewed/`
- `pending-review-notes/` 不是啟動前置閱讀，只在 capture / triage 路徑下按需 read / write

### 2. Pending review triage recorder

- `.agent/skills/pending-review-recorder/SKILL.md`
- `.agent/skills/pending-review-recorder/scripts/pending_review_recorder.py`
- `.agent/roles/engineer_pending_review_recorder.md`
- `.agent/roles/qa_pending_review_recorder.md`
- `.agent/roles/security_pending_review_recorder.md`
- `.agent/roles/engineer.md`
- `.agent/roles/qa.md`
- `.agent/roles/security.md`
- `.agent/skills/INDEX.md`
- `.agent/skills/_shared/__init__.py`
- `.agent/scripts/setup_workflow.sh`
- `.agent/PORTABLE_WORKFLOW.md`
- `core_ownership_manifest.yml`
- `tests/test_pending_review_recorder_skill.py`

這批變更已經把 `pending-review-recorder` 落成可用 skill / script：

- 處理 `pending-review-notes` 的 `create / update / skip`
- 依 dedupe key 去重與更新
- 角色 trigger 分流為 engineer / QA / security reviewer 三個薄 overlay
- 補齊導出面，讓 downstream curated core 可以攜帶這個 triage 能力

### 3. Reviewed sync manager

- `.agent/skills/reviewed-sync-manager/SKILL.md`
- `.agent/skills/reviewed-sync-manager/scripts/reviewed_sync_manager.py`
- `tests/test_reviewed_sync_manager_skill.py`

這個工具已經落成 writer + promotion 兩段式流程，但有明確硬邊界：

- 只能在 workflow template repo 使用
- downstream repo 不得使用

功能包括：

- `write-candidate`
  - 支援 repo file / manual summary / structured JSON payload
- `promote-candidate`
  - promotion 到 `20-reviewed/`
  - 補齊 reviewed frontmatter
  - 更新 `00-indexes/`
  - reviewed dedupe / merge
  - duplicate candidate archive

### 4. Workflow contract hardening for downstream Obsidian intake

- `.agent/workflows/AGENT_ENTRY.md`
- `.agent/workflows/dev-team.md`
- `.agent/roles/coordinator.md`
- `tests/test_dev_entry_workflow_contract.py`

這批變更已把 downstream / 新專案工作區的 Obsidian intake gate 收斂成正式入口契約：

- 先檢閱 `00-indexes/`
- 再依索引只讀最小必要 `20-reviewed/`
- 啟動階段不得掃 `10-inbox/reviewed-sync-candidates/`、`30-archives/` 與其他未 allow-list 的 vault 路徑
- `10-inbox/pending-review-notes/` 不屬於啟動前置閱讀，只在 capture / triage 命中時才後續 read / write

## Files currently changed but not yet committed

### Modified tracked files

- `.agent/PORTABLE_WORKFLOW.md`
- `.agent/roles/coordinator.md`
- `.agent/roles/engineer.md`
- `.agent/roles/qa.md`
- `.agent/roles/security.md`
- `.agent/scripts/setup_workflow.sh`
- `.agent/skills/INDEX.md`
- `.agent/skills/_shared/__init__.py`
- `.agent/workflows/AGENT_ENTRY.md`
- `.agent/workflows/dev-team.md`
- `.devcontainer/devcontainer.ghcr.json`
- `.devcontainer/devcontainer.json`
- `.gitignore`
- `core_ownership_manifest.yml`
- `maintainers/chat/README.md`
- `tests/test_dev_entry_workflow_contract.py`

### Untracked new files

- `.agent/roles/engineer_pending_review_recorder.md`
- `.agent/roles/qa_pending_review_recorder.md`
- `.agent/roles/security_pending_review_recorder.md`
- `.agent/skills/pending-review-recorder/SKILL.md`
- `.agent/skills/pending-review-recorder/scripts/pending_review_recorder.py`
- `.agent/skills/reviewed-sync-manager/SKILL.md`
- `.agent/skills/reviewed-sync-manager/scripts/reviewed_sync_manager.py`
- `maintainers/chat/2026-03-20-obsidian-reviewed-sync-checklist.md`
- `maintainers/chat/2026-03-20-obsidian-vault-structure-and-frontmatter.md`
- `maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md`
- `tests/test_pending_review_recorder_skill.py`
- `tests/test_reviewed_sync_manager_skill.py`

## What has been confirmed

- 上一份 handoff 中列為未完成的 bootstrap / dependency hardening，後續已完成 commit、測試與 push；它不是目前待辦。
- `main` 自上一份 handoff 後新增 4 個已提交 commit：`f268b73`、`a90a4f2`、`bd5d2d1`、`5ccf352`。
- 目前 working tree 沒有 staged changes；所有這批 Obsidian / triage / reviewed-sync 變更都尚未 commit。
- `pending-review-recorder.py`、`reviewed_sync_manager.py` 與對應測試檔目前 editor diagnostics 為乾淨。
- focused tests 已通過：
  - `./.venv/bin/python -m unittest tests.test_pending_review_recorder_skill tests.test_reviewed_sync_manager_skill tests.test_dev_entry_workflow_contract`
  - 結果：`Ran 14 tests in 0.109s` / `OK`

## Current stage

- 已完成狀態分析與 focused 驗證
- 目前這批未提交工作已具備可提交狀態
- 下一個立即動作應是：
  1. 建立本 handoff
  2. 將目前 Obsidian / triage / reviewed-sync / gate 變更 commit
  3. push 到 `origin/main`

## What was rejected or intentionally constrained

- 不把 `reviewed-sync-manager` 匯出給 downstream repo；它維持 workflow-template-only maintainer tool。
- 不把 downstream 啟動知識 intake 退化成整包掃描 vault；只允許 `00-indexes/` + 最小必要 `20-reviewed/`。
- 不把 `pending-review-notes/` 當成啟動前置知識面；它只保留 capture / triage 用途。
- 不把 downstream repo 預設改成 full-vault mount；full-vault mount 只屬於 workflow template repo 的 maintainer-local 模式。

## Immediate next work after this commit

若到公司後要延續這條線，建議優先順序如下：

1. 先決定 downstream 專用 Obsidian mount 方案要不要落成更正式的 Dev Container / generator contract
2. 若要讓 downstream bootstrap automation 支援 Obsidian access，優先做 restricted partial-vault profile，而不是 export full-vault config
3. 視需要再補更正式的 regression：
   - downstream restricted mount contract
   - pending-review-recorder CLI payload edge cases
   - reviewed-sync-manager promotion / archive edge cases

## Next exact prompt

請先讀 `maintainers/chat/handoff/2026-03-22-obsidian-sync-and-triage-handoff.md`，再確認 `maintainers/chat/2026-03-20-project-maintainers-obsidian-sync-policy.md`、`maintainers/chat/2026-03-20-obsidian-reviewed-sync-checklist.md`、`maintainers/chat/2026-03-20-obsidian-vault-structure-and-frontmatter.md`、`.agent/skills/pending-review-recorder/`、`.agent/skills/reviewed-sync-manager/`、`.agent/workflows/AGENT_ENTRY.md` 與 `tests/test_pending_review_recorder_skill.py`、`tests/test_reviewed_sync_manager_skill.py`、`tests/test_dev_entry_workflow_contract.py`。若下一步要延伸工作，優先做 downstream restricted Obsidian mount contract / generator 設計，或補這批 recorder / reviewed-sync / intake gate 的 regression coverage。

## Risks

- `reviewed-sync-manager` 目前是 template-only tool，若未來要把某部分能力下放 downstream，必須先重新切清 writer / promotion 邊界，而不是直接 export 整包。
- template repo 目前 full-vault mount 使用的是 maintainer-local 路徑假設；這不具 downstream 可攜性。
- downstream restricted mount 的設計方向已清楚，但尚未實作成正式 bootstrap / generator contract。
- `pending-review-recorder` 雖已有 focused tests，但若未來擴大自動寫入事件類型，仍需防止 note 爆量與 dedupe 漂移。
- 目前 workflow 契約已限制 downstream 啟動讀取面；若後續 docs / role prompts 再變更，需維持 `AGENT_ENTRY.md`、`dev-team.md`、`coordinator.md` 與 contract test 同步。

## Verification status

- 已驗證：上一份 handoff 之後新增的 4 個 commit 已在 `main`，且 `origin/main` 與本地對齊。
- 已驗證：目前未提交的 Obsidian / triage / reviewed-sync / gate 變更 focused tests 通過，結果為 `14 tests OK`。
- 已驗證：目前關鍵新 script 與測試檔無 editor diagnostics。
- 尚未完成：把目前這批未提交檔案正式 commit 並 push。
