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

## Historical uncommitted batch in original draft

以下內容描述的是這份 handoff 最初起草當下，當時仍未提交的那一批 Obsidian / triage / reviewed-sync 工作。

這一整批後續已提交並 push 為 `0f9bef3 feat: add obsidian triage and reviewed sync tooling`；保留這段的目的，是讓接手者知道原始 draft 當時觀察到的工作範圍。

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

## Historical file snapshot in original draft

以下檔案清單同樣是 handoff 原始 draft 起草時的工作樹快照，不代表目前 repo 仍處於未提交狀態。

### Modified tracked files in original draft

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

### Untracked new files in original draft

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
- handoff 原始 draft 起草當時，這批 Obsidian / triage / reviewed-sync 變更尚未 commit；該狀態後續已被 `0f9bef3` 取代，不再是目前狀態。
- `pending-review-recorder.py`、`reviewed_sync_manager.py` 與對應測試檔在原始 draft 驗證階段 editor diagnostics 為乾淨。
- 原始 draft 階段的 focused tests 已通過：
  - `./.venv/bin/python -m unittest tests.test_pending_review_recorder_skill tests.test_reviewed_sync_manager_skill tests.test_dev_entry_workflow_contract`
  - 結果：`Ran 14 tests in 0.109s` / `OK`
- 目前功能批次已在 `origin/main`：`0f9bef3 feat: add obsidian triage and reviewed sync tooling`
- 目前 handoff 補充已另有兩個本地 docs commit：`62dab22 docs: update obsidian sync handoff follow-up` 與 `1ce95e1 docs: finalize obsidian sync handoff resolution`

## Current stage

- 公司端 VS Code 目前已無 dirty state / Source Control 異常；先前那批混合 staged/unstaged 狀態已確認是本地 index/worktree 問題，且已收斂
- 功能批次已完成提交並位於 `origin/main`：`0f9bef3 feat: add obsidian triage and reviewed sync tooling`
- dirty state / index 問題已完成診斷與收斂，結論已寫入本 handoff
- 這份 handoff 後續補充與 Obsidian Explorer follow-up 已再提交並推上 `main`：`9d0740f docs: refresh obsidian sync handoff final state`、`3f94286 feat: auto-link obsidian vault in devcontainer`、`2f3cd5d docs: add obsidian vault mount handoff note`
- template repo 的 maintainer-local single-root Explorer exposure 已正式產品化：`post_create.sh` 會在 mount 存在時自動建立 `obsidian-vault -> /obsidian/vault`
- 目前本地 `main` 與 `origin/main` 已再次對齊；handoff 中先前提到的 ahead 2 狀態已成歷史

## Obsidian vault mount verification at company

先前一度懷疑公司端打開 Dev Container 後沒有如預期自動掛載 Obsidian vault；後續現場複查後，已確認「mount 本身是正常的」，真正造成誤判的是 Explorer 不會自動顯示不在目前 workspace root 之下的路徑。

### 現場驗證結果

- repo 內目前打開的 Container Configuration File 就是 `.devcontainer/devcontainer.json`
- container 內 `/obsidian/vault` 實際存在，而且 mount 已生效
- `/proc/self/mountinfo` 顯示來源路徑就是公司主機上的 `C:\Users\forev\OneDrive\4-管理專用\Jonas\AI生成\程式\ObsidianVault`
- `ls /obsidian/vault` 已可直接看到 `00-indexes/`、`10-inbox/`、`20-reviewed/`、`30-archives/` 與 `.obsidian/`

### 真正的問題點

- 左側 Explorer 預設只顯示目前 workspace root，也就是 `/workspaces/agent-workflow-template`
- Obsidian vault 是另一個已掛載但不在 repo 目錄樹下的路徑：`/obsidian/vault`
- 因此「Explorer 沒看到 vault」不等於「vault 沒有 mount」

### 已採取動作

- 已在公司端確認：若只維持 repo 這個單一 workspace，Explorer 不會自動顯示 `/obsidian/vault` 這種 workspace root 之外的掛載路徑
- 為了讓目前這個 repo workspace 的左側 Explorer 直接看得到 vault，已在 repo root 建立本機 symlink：`obsidian-vault -> /obsidian/vault`
- 這個 symlink 只用來暴露已掛載的 vault 給目前 Explorer 使用，不是正式 workflow 契約，也不是要提交的 repo 內容
- 該 symlink 已加入本機 `.git/info/exclude`，避免污染 git status
- 後續已由 `3f94286 feat: auto-link obsidian vault in devcontainer` 把這個 single-root Explorer exposure 正式落成 `post_create.sh` 自動化；目前不再依賴每台機器手動建立 symlink

### 後續真正要處理的事

- 目前 full-vault mount 雖可用，但設定仍是 maintainer-local 的硬編碼 host path：`source=${localEnv:USERPROFILE}/OneDrive/4-管理專用/Jonas/AI生成/程式/ObsidianVault,target=/obsidian/vault,type=bind`
- 這個設計對單一 maintainer 可用，但跨機可攜性仍差；若後續要正式收斂，仍建議改成由本機環境變數或本機 override 提供 host path，而不是直接硬編碼在 repo 內

## Follow-up issue discovered after this handoff draft

在這份 handoff 草稿完成後，後續實際已經把當時那批 Obsidian / triage / reviewed-sync / gate 變更提交並 push 到 `main`：

- commit: `0f9bef3 feat: add obsidian triage and reviewed sync tooling`
- 已確認當時本地 `HEAD` 與 `origin/main` 一致

但之後在公司電腦重新 rebuild Dev Container 並重新打開 workspace 時，又出現「看起來還有很多尚未 commit 的檔案」的異常狀態。

### 異常現象

- git dirty state 是真的，不是單純 VS Code UI 沒刷新
- 當時觀察到 local `HEAD` 與 `origin/main` 都是 `0f9bef3`
- 但 working tree 同時出現 staged 與 unstaged 兩層變更
- 狀態型態包含：`MM`、staged `D`、以及對應檔案重新以 `??` 或 unstaged modified 形式出現

### Dirty state 結構

當時拆開看，髒狀態不是單一層，而是兩層混在一起：

1. staged changes
   - 幾乎是在把剛剛 commit 的 Obsidian / pending-review / reviewed-sync 相關檔案整批移除
   - 規模大約是 29 個檔案、約 4013 deletions、4 insertions
2. unstaged changes
   - 又把其中一部分內容重新加回來或局部修改
   - 規模大約是 16 個檔案、114 insertions、4 deletions

這代表問題比較像「本地 index / worktree 疊出異常狀態」，不是單純又新增了一批正常開發中的修改。

### 已做過的排查

已檢查以下 rebuild 路徑：

- `.agent/runtime/scripts/devcontainer/post_create.sh`
- `.devcontainer/devcontainer.json`
- `.devcontainer/devcontainer.ghcr.json`

目前確認：

- 這些 devcontainer rebuild / post-create 路徑本身沒有 `git add`、`git reset`、`git restore`、`git checkout`、`git clean`、`git stash`、`git commit` 之類會直接改 git 狀態的命令
- 因此「單純 rebuild 本身直接把 repo 改髒」這個假說，目前沒有直接證據支持

但另外有找到 repo 內其他 script 含 git 清理邏輯：

- `.agent/scripts/run_codex_template.sh`
  - `git reset --hard "$PRE_HEAD" 2>/dev/null || true`
  - `git restore --worktree --staged -- . 2>/dev/null || true`

這不代表它就是本次直接根因，但若公司端有跑到這條腳本，必須列入排查。

### 目前最合理判斷

- 比較像是公司電腦上的 workspace / index 原本就殘留過一份 dirty state
- rebuild 之後只是重新掛載或重新看見那份本地狀態
- 目前沒有證據顯示 devcontainer 的標準 rebuild 流程本身會直接產生這批 git 變更

### 公司端接手時的第一優先工作

到公司後，不要直接在這個 dirty tree 上繼續做功能延伸。先做以下診斷：

1. 再次確認 `git status --short --branch` 與 `git rev-parse --short HEAD && git rev-parse --short origin/main`
2. 分開看 `git diff --cached --stat` 與 `git diff --stat`
3. 判斷這批 staged 刪除 / unstaged 回填是否有任何內容其實要保留
4. 搜尋是否真的有流程會執行 `.agent/scripts/run_codex_template.sh` 或其他會改 index/worktree 的 wrapper
5. 若確認這批變更都不是要保留的工作成果，再決定是否清理回 `origin/main`

## Resolution at company

後續在公司端實際收尾時，最後證實這不是「上一輪功能變更沒有 commit/push 完」的問題，而是 index 與 worktree 疊出來的混合狀態。

### 實際處理方式

實際採用的收斂步驟如下：

1. 先重新確認 focused tests 仍可通過：
  - `./.venv/bin/python -m unittest tests.test_pending_review_recorder_skill tests.test_reviewed_sync_manager_skill tests.test_dev_entry_workflow_contract`
2. 對整個目前 worktree 重新做一次整體 stage：
  - `git add -A`
3. 再看真正的 staged diff：
  - `git diff --cached --stat`

### 結果

- 重新 stage 之後，原本混在一起的 staged 整批刪除與 unstaged 回填直接收斂掉
- staged diff 最後只剩這份 handoff 的 follow-up 補充，不再有 Obsidian / pending-review / reviewed-sync 那批功能檔案的實質差異
- 這代表先前看到的 `MM`、staged `D`、`??` 混合狀態，核心問題確實是 index/worktree 疊出的本地異常狀態，不是遠端缺 commit
- 公司端後續重新打開 VS Code / Source Control 時，已不再出現那批假的混合 dirty state

### 被證實與未被證實的假說

已被證實：

- `0f9bef3 feat: add obsidian triage and reviewed sync tooling` 這批功能變更早已在 `origin/main`
- devcontainer rebuild 路徑本身沒有直接改 git state 的命令
- 問題可以透過重新 stage 目前 worktree，把假的兩層差異收斂回真實差異面

尚未被直接證實：

- `.agent/scripts/run_codex_template.sh` 是否真的在公司端被執行並造成這次異常
- VS Code Source Control 或其他本地 wrapper 是否曾在更早階段動過 index

### 最後收尾動作

在重新 stage 後，唯一剩下的真實變更是 handoff follow-up 本身，因此後續實際分成兩次 docs 提交完成收尾：

- `62dab22 docs: update obsidian sync handoff follow-up`
- `1ce95e1 docs: finalize obsidian sync handoff resolution`

後續又補了兩個與 handoff / vault visibility 直接相關的 commit，且目前都已在 `origin/main`：

- `9d0740f docs: refresh obsidian sync handoff final state`
- `2f3cd5d docs: add obsidian vault mount handoff note`

另外，`3f94286 feat: auto-link obsidian vault in devcontainer` 已把 template repo 的 single-root Explorer exposure 正式產品化；因此目前已不再存在「本地 docs commit 尚未 push、branch ahead 2」這個狀態。

## What was rejected or intentionally constrained

- 不把 `reviewed-sync-manager` 匯出給 downstream repo；它維持 workflow-template-only maintainer tool。
- 不把 downstream 啟動知識 intake 退化成整包掃描 vault；只允許 `00-indexes/` + 最小必要 `20-reviewed/`。
- 不把 `pending-review-notes/` 當成啟動前置知識面；它只保留 capture / triage 用途。
- 不把 downstream repo 預設改成 full-vault mount；full-vault mount 只屬於 workflow template repo 的 maintainer-local 模式。

## Immediate next work after this commit

若到公司後要延續這條線，建議優先順序如下：

1. 若要讓 downstream 操作面更一致，優先在 active docs / SOP / onboarding 範例統一使用 `--setup-obsidian-restricted-access`，不要同時教兩套旗標名稱
2. 若未來還要再往上收斂 operator surface，應做更高層 wrapper command，而不是回頭把 `.devcontainer/**` 變成 export-managed surface
3. 持續維持 downstream 的 Obsidian access surface 為 single-root repo-local shape，避免任何文件或新工具把使用者帶回 full-vault / multi-root 心智模型
4. 視需要再補更正式的 regression：
   - downstream restricted mount contract
   - pending-review-recorder CLI payload edge cases
   - reviewed-sync-manager promotion / archive edge cases

## Next exact prompt

請先讀 `maintainers/chat/handoff/2026-03-22-obsidian-sync-and-triage-handoff.md`，特別是 `Resolution at company`、`Current stage` 與 `Immediate next work after this commit`。目前 handoff follow-up、vault visibility 補充、single-root Explorer exposure、downstream restricted mount generator，以及 opt-in bootstrap / sync apply integration 都已在 `origin/main`；因此不要再回頭處理舊的 ahead 2 歷史狀態，也不要再把 `.devcontainer/**` 當成 export-managed surface。若要延續這條線，優先做 active docs / onboarding 的操作面收斂，統一使用 `--setup-obsidian-restricted-access` 當作 operator-facing 入口。若未來再次看到 staged 刪除加 unstaged 回填的混合狀態，先用 `git add -A` 重新收斂目前 worktree，再判斷真實 diff 面。

## Risks

- `reviewed-sync-manager` 目前是 template-only tool，若未來要把某部分能力下放 downstream，必須先重新切清 writer / promotion 邊界，而不是直接 export 整包。
- template repo 目前 full-vault mount 使用的是 maintainer-local 路徑假設；這不具 downstream 可攜性。
- downstream restricted mount contract 與 opt-in bootstrap / sync apply integration 已落地；後續風險改為文件與 onboarding 操作面若不統一，容易讓使用者記成舊旗標名稱。
- `pending-review-recorder` 雖已有 focused tests，但若未來擴大自動寫入事件類型，仍需防止 note 爆量與 dedupe 漂移。
- 目前 workflow 契約已限制 downstream 啟動讀取面；若後續 docs / role prompts 再變更，需維持 `AGENT_ENTRY.md`、`dev-team.md`、`coordinator.md` 與 contract test 同步。
- 公司端這次 dirty state 雖已排除，但它暴露出一個實務風險：若直接看見 staged 刪除與 unstaged 回填混在一起，就貿然修改或 commit，容易把假的 index 狀態誤判成新的功能變更。
- `.agent/scripts/run_codex_template.sh` 仍含 git reset/restore 清理邏輯；雖未證實是這次根因，但未來若再出現相同型態異常，仍應優先納入排查。

## Verification status

- 已驗證：上一份 handoff 之後新增的 4 個 commit 已在 `main`，且 `origin/main` 與本地對齊。
- 已驗證：原始 draft 階段，當時未提交的 Obsidian / triage / reviewed-sync / gate 變更 focused tests 通過，結果為 `14 tests OK`。
- 已驗證：原始 draft 階段，當時關鍵新 script 與測試檔無 editor diagnostics。
- 後續另已驗證過一次：Obsidian / triage / reviewed-sync 那批變更曾成功 commit / push 為 `0f9bef3 feat: add obsidian triage and reviewed sync tooling`，而且當時本地 `HEAD` 與 `origin/main` 相同。
- 後續另已驗證過一次：devcontainer rebuild 路徑本身沒有直接修改 git state 的命令；dirty tree 較像是公司端本地 workspace / index 殘留狀態重新浮現。
- 已驗證：重新執行 `git add -A` 後，混合的 staged deletion / unstaged 回填已收斂，只剩 handoff follow-up 本身是真實差異。
- 已完成：handoff follow-up 已提交為 `62dab22 docs: update obsidian sync handoff follow-up`。
- 已完成：handoff 最終收斂版已提交為 `1ce95e1 docs: finalize obsidian sync handoff resolution`。
- 已完成：handoff 遠端狀態已再刷新為 `9d0740f docs: refresh obsidian sync handoff final state`。
- 已完成：template repo 的 single-root Explorer exposure 已提交為 `3f94286 feat: auto-link obsidian vault in devcontainer`，且 focused bootstrap regression 通過。
- 已完成：vault visibility 補充已提交為 `2f3cd5d docs: add obsidian vault mount handoff note`。
- 目前狀態：本地 `main` 與 `origin/main` 已對齊；後續若再看到 repo 差異，應先區分是不是這份 handoff 自身的新補寫，或是新的 downstream restricted mount 產品化工作。
