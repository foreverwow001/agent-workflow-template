# 新專案啟動 SOP（Scheme A: core + overlay）

> 建立日期：2026-03-20
> 狀態：Active Maintainer SOP
> 用途：提供 maintainer 一份最短、可照跑的新專案導入流程，使用目前已落地的 Scheme A：curated workflow core + downstream overlay。

---

## 0. 先講結論

目前 Scheme A 可以視為已完整落地。

已落地的理由是：

- mutable path split 已完成
- `core_ownership_manifest.yml` 已成為單一 machine-readable truth
- projection/bootstrap 已落成 runtime artifact
- portable smoke 已成為 release / sync 共用驗證入口
- `workflow-core sync stage -> precheck -> apply -> verify` 已有實作、文件與 e2e 驗證
- `core-v20260320-2` 已是正式 release tag，並有 versioned release artifacts

但有一個操作面要先分清楚：

- 第一次建立新專案：先做一次 bootstrap，把 curated core 放進新 repo
- 後續吃 upstream 更新：走 `workflow-core` release / sync lane，不再整包複製 template repo

這份 SOP 寫的是 maintainer 角度的「怎麼開一個新的 downstream repo」。

---

## 1. 你最後會得到什麼

做完這份 SOP 後，新專案 repo 應具備：

- root live paths 已存在，例如 `.agent/**` 與 `doc/**`
- curated workflow core 已落到 repo root
- 專案自己的 overlay 檔已建立，例如 `project_rules.md`
- `project_maintainers/chat/` skeleton 已存在，可直接寫入 project-local handoff
- `project_maintainers/improvement_candidates/` skeleton 已存在，可直接記錄候選 reusable 經驗
- 後續可再追 `workflow-core` release tag 更新

---

## 2. 前置條件

你需要有兩個本地目錄：

1. 一份目前這個 template repo 的工作副本
2. 一份新的 downstream repo 工作副本

以下示意：

- template repo：`/workspaces/agent-workflow-template`
- new repo：`/workspaces/my-new-project`

本文預設使用的正式 release 是：

- `core-v20260320-2`

新專案最小建議依賴如下：

- `git`
- `python` 或 `python3`，且要能執行 `python -m venv`
- `node`
- `npm`
- `codex`
- `copilot`
- `bwrap`（Linux / Dev Container 建議安裝）

如果你是從目前這份 curated core 啟動新 repo，建議把依賴檢查寫成固定第一步，而不是等 PTY 報錯才補救。

---

## 3. 第一次建立新專案

### Step 0. 先檢查並安裝最小依賴

第一次 bootstrap 前，先在新 repo 執行：

```bash
bash .agent/runtime/scripts/install_workflow_prereqs.sh
```

這支腳本會先檢查新專案最小依賴；若缺少而且環境允許，就會自動安裝。當前自動安裝策略如下：

- `git`、`python3`、`python3-venv`、`python-is-python3`、`nodejs`、`npm`、`bubblewrap`
  - 透過 `apt-get` 安裝
- `@openai/codex`、`@github/copilot`
  - 透過 `npm install -g` 安裝

若你只想先看缺什麼，不想自動安裝：

```bash
bash .agent/runtime/scripts/install_workflow_prereqs.sh --check-only
```

### Step 1. 建立空的 downstream repo

先建立遠端 repo，再在本機 clone：

```bash
git clone https://github.com/YOUR_ORG/YOUR_NEW_REPO.git /workspaces/my-new-project
cd /workspaces/my-new-project
```

這個 repo 一開始可以是空的，或只有最小 README / `.gitignore`。

### Step 2. 從正式 release materialize curated core

第一次 bootstrap，建議直接用 template repo 內的 export tool 從正式 release tag materialize 一份乾淨 export tree。

在 template repo 執行：

```bash
cd /workspaces/agent-workflow-template

./.venv/bin/python .agent/runtime/scripts/workflow_core_export_materialize.py \
  --repo-root . \
  --source-ref core-v20260320-2 \
  --output /tmp/workflow-core-bootstrap-core-v20260320-2
```

成功後，你會得到：

- `/tmp/workflow-core-bootstrap-core-v20260320-2/`：curated core tree
- `/tmp/workflow-core-bootstrap-core-v20260320-2/workflow-core-export-curated-core-v1.json`：export metadata

### Step 3. 把 curated core 放進新 repo root

把 export tree 同步到新 repo root：

```bash
rsync -a /tmp/workflow-core-bootstrap-core-v20260320-2/ /workspaces/my-new-project/
```

這一步是第一次 bootstrap，目的只是把 release 內容落進空 repo；它不是日後更新 lane 的替代品。

### Step 4. 建立 downstream overlay 檔案

進到新 repo，補齊專案自己的 overlay：

```bash
cd /workspaces/my-new-project
```

至少建立或確認以下檔案：

1. `project_rules.md`
2. `doc/implementation_plan_index.md`
3. `.agent/roles/domain_expert.md`

另外，`project_maintainers/chat/` 與 `project_maintainers/improvement_candidates/` skeleton 會隨 curated core 一起帶入新 repo；它們是新專案自己的 supporting handoff / candidate surface，不是 template repo `maintainers/` 的延伸。

最小建議內容：

#### `project_rules.md`

```md
# Project Rules

## 1. 專案背景
- 專案名稱：<your project>
- 技術棧：<python / typescript / etc.>

## 2. 開發限制
- 語言：繁體中文 / English
- 禁止直接修改 production secrets

## 3. 專案特有規則
- <your repo specific rules>
```

#### `doc/implementation_plan_index.md`

```md
# Implementation Plan Index

| Task ID | 名稱 | 狀態 | 建立日期 | 完成日期 |
|---------|------|------|---------|---------|
| Idx-001 | Bootstrap project workflow | Planning | 2026-03-20 | - |
```

#### `.agent/roles/domain_expert.md`

把它改成你的專案領域角色，例如：

- API Expert
- E-commerce Expert
- Data Platform Expert
- Ads Analytics Expert

### Step 5. 確認 root live path 已成立

新 repo 至少應看得到：

- `.agent/workflows/AGENT_ENTRY.md`
- `.agent/workflows/dev-team.md`
- `.agent/runtime/scripts/workflow_core_projection.py`
- `.agent/runtime/scripts/portable_smoke/workflow_core_smoke.py`
- `core_ownership_manifest.yml`
- `doc/plans/Idx-000_plan.template.md`
- `doc/logs/Idx-000_log.template.md`

### Step 6. 做第一次 bootstrap commit

建議在 downstream repo 先做一次乾淨初始提交：

```bash
cd /workspaces/my-new-project
git add .
git commit -m "chore: bootstrap workflow core from core-v20260320-2"
git push origin main
```

---

## 4. 新專案開工前要做什麼

第一次 bootstrap 完成後，開工前建議照這個順序看：

1. `.agent/workflows/AGENT_ENTRY.md`
2. `.agent/workflows/dev-team.md`
3. `project_rules.md`
4. `doc/implementation_plan_index.md`

若你要在新機 / Dev Container 開工，機器層的環境文件仍看 template repo 本身的 maintainer docs；它們不是 curated core export 的一部分。

---

## 5. 之後怎麼吃 upstream 更新

第一次 bootstrap 完後，之後不要再整包複製 template repo。

後續更新請改走 release / sync lane：

### Step 1. 在 downstream repo 內 stage 新 release

如果你的 downstream repo 已經有上一版 workflow core，可以直接用 template repo 內的 wrapper 對 downstream repo 執行 remote stage。

先在 downstream repo 加一個專門追 workflow core 的 upstream remote：

```bash
cd /workspaces/my-new-project
git remote add workflow-core-upstream https://github.com/foreverwow001/agent-workflow-template.git
git fetch workflow-core-upstream --tags
```

在 template repo 執行：

```bash
cd /workspaces/agent-workflow-template

./.venv/bin/python .agent/runtime/scripts/workflow_core_sync_stage.py \
  --repo-root /workspaces/my-new-project \
  --release-ref core-v20260320-2 \
  --source-remote workflow-core-upstream \
  --source-ref core-v20260320-2
```

重點：

- script 是從 template repo 執行
- `--repo-root` 指向 downstream repo
- `--source-remote` 是 downstream repo 內指向 workflow-core upstream 的 remote，不要直接假設是 `origin`
- downstream repo 內會出現 `.workflow-core/staging/core-v20260320-2/`

### Step 2. 在 downstream repo apply / verify

等 downstream repo 已經帶有 workflow core script 後，就可以在 downstream 自己執行：

```bash
cd /workspaces/my-new-project

python .agent/runtime/scripts/workflow_core_sync_precheck.py \
  --repo-root . \
  --release-ref core-v20260320-2

python .agent/runtime/scripts/workflow_core_sync_apply.py \
  --repo-root . \
  --release-ref core-v20260320-2 \
  --staging-root .workflow-core/staging/core-v20260320-2

python .agent/runtime/scripts/workflow_core_sync_verify.py \
  --repo-root . \
  --release-ref core-v20260320-2 \
  --staging-root .workflow-core/staging/core-v20260320-2
```

如果 `sync precheck` 因 `.workflow-core/staging/**` 回 `warn`，這在目前模型下是預期訊號；真正 blocking 的是 core managed path divergence。

---

## 6. 什麼不要做

以下做法現在都不推薦：

1. 用 GitHub `Use this template` 複製整包 repo
2. 把 `maintainers/**` 一起帶進 downstream 當 canonical surface
3. 讓 downstream 直接長期修改 core managed paths
4. 用手打 ad hoc `cp -r` / `rsync` 當日常更新 lane
5. 把 `.agent/state/**`、`.agent/config/**`、`.agent/skills_local/**` 當成 upstream managed core

---

## 7. 最短版本

如果你只想記最短步驟，照這個做：

1. 建立空 repo
2. 用 template repo 的 `workflow_core_export_materialize.py --source-ref core-v20260320-2` 匯出 curated core
3. 把匯出樹同步到新 repo root
4. 建 `project_rules.md`、`doc/implementation_plan_index.md`、客製 `domain_expert.md`
5. commit 成新專案的 bootstrap baseline
6. 之後所有 upstream 更新只走 `workflow-core sync stage / precheck / apply / verify`

---

## 8. 參考文件

- `core_ownership_manifest.yml`
- `doc/AGENT_WORKFLOW_TEMPLATE_UPSTREAM.md`
- `maintainers/chat/handoff/core-overlay/daily-sync-sop.md`
- `maintainers/chat/handoff/core-overlay/sync-checklist.md`
- `maintainers/chat/handoff/core-overlay/cli-spec.md`
- `maintainers/release_artifacts/workflow-core-release-core-v20260320-2.md`
