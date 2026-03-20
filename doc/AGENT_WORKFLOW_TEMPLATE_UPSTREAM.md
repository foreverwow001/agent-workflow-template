# Workflow-Core Upstream / Downstream Guide

本文件目的：把目前 template repo 已落地的 `workflow-core` export / projection / sync lane，整理成 upstream 維護者與 downstream 使用者都能直接照跑的最短操作說明。

這份文件處理的是「現在 repo 真正可執行的流程」，不是早期手動挑檔、`cp -r`、`rsync` 的過渡做法。

---

## 1. 目前已定型的實際模型

目前 repo 的 workflow-core 交付模型如下：

- machine-readable source of truth：`./core_ownership_manifest.yml`
- active export profile：`curated-core-v1`
- export analysis：`.agent/runtime/scripts/workflow_core_export_landing_checklist.py`
- export materialization：`.agent/runtime/scripts/workflow_core_export_materialize.py`
- projection / bootstrap artifact：`.agent/runtime/scripts/workflow_core_projection.py`
- downstream sync wrappers：
  - `.agent/runtime/scripts/workflow_core_sync_precheck.py`
  - `.agent/runtime/scripts/workflow_core_sync_apply.py`
  - `.agent/runtime/scripts/workflow_core_sync_verify.py`
- shared portable verification：`.agent/runtime/scripts/portable_smoke/workflow_core_smoke.py`

重點是：

1. upstream 不再靠人工挑檔決定 export surface，而是以 manifest + export profile 決定。
2. downstream 不再靠人工覆蓋 root live paths，而是以 `sync apply` + projection/bootstrap materialize。
3. portable smoke 已是 core-managed runtime artifact，不是外部另裝的 optional 模組。

---

## 2. 現在推薦的 upstream scope

`curated-core-v1` 目前涵蓋的核心面向：

### A. Workflow contract

- `.agent/workflows/**`
- `.agent/workflows/references/**`
- `.agent/roles/coordinator.md`
- `.agent/roles/planner.md`
- `.agent/roles/engineer.md`
- `.agent/roles/qa.md`
- `.agent/roles/security.md`

### B. Runtime / sync / projection toolchain

- `.agent/runtime/**`
- `.agent/VScode_system/**`
- `.agent/templates/handoff_template.md`
- `core_ownership_manifest.yml`

### C. Curated builtin skills

- `.agent/skills/__init__.py`
- `.agent/skills/INDEX.md`
- `.agent/skills/_shared/__init__.py`
- `.agent/skills/schemas/**`
- curated builtin package dirs listed in `core_ownership_manifest.yml`

### D. Shared plan/log templates

- `doc/plans/Idx-000_plan.template.md`
- `doc/logs/Idx-000_log.template.md`

---

## 3. 明確不屬於 workflow-core export 的內容

這些仍屬 overlay / maintainer / environment surface，不應進 `curated-core-v1`：

- `project_rules.md`
- `doc/implementation_plan_index.md`
- active `doc/plans/Idx-*_plan.md`
- active `doc/logs/Idx-*_log.md`
- `maintainers/**`
- `.agent/workflow_baseline_rules.md`
- `.agent/PORTABLE_WORKFLOW.md`
- `.agent/PR_PREPARATION.md`
- `.agent/scripts/setup_workflow.sh`
- `.agent/scripts/run_codex_template.sh`
- `.devcontainer/**`
- `tests/**`
- `.agent/state/**`
- `.agent/config/**`
- `.agent/skills_local/**`

---

## 4. Upstream Release / Export Flow

### Step 1. 確認 export profile 在來源 ref 可落地

```bash
/workspaces/agent-workflow-template/.venv/bin/python \
  .agent/runtime/scripts/workflow_core_export_landing_checklist.py \
  --repo-root . \
  --source-ref HEAD
```

判讀原則：

- `pass`：目前來源 ref 已可直接 materialize export tree
- `warn`：仍有 `worktree-only` 或 `missing` include patterns
- `fail`：manifest / export contract 自己不一致

### Step 2. 先跑 release precheck

```bash
/workspaces/agent-workflow-template/.venv/bin/python \
  .agent/runtime/scripts/workflow_core_release_precheck.py \
  --repo-root .
```

### Step 3. materialize curated export tree

```bash
/workspaces/agent-workflow-template/.venv/bin/python \
  .agent/runtime/scripts/workflow_core_export_materialize.py \
  --repo-root . \
  --source-ref HEAD \
  --output /tmp/curated-core-v1
```

輸出目錄會包含：

- curated workflow-core files
- `workflow-core-export-curated-core-v1.json` metadata

---

## 5. Downstream Sync Flow

目前推薦的 downstream 操作方式，是把 upstream export tree 先放到 repo 內的 staging 位置，再用 wrapper commands 完成 apply / verify。

建議 staging 路徑：

- `.workflow-core/staging/<release-ref-or-label>/`

### Step 1. 將 export tree 放進 downstream staging root

範例：

```bash
mkdir -p .workflow-core/staging/core-v20260320-1
cp -R /tmp/curated-core-v1/. .workflow-core/staging/core-v20260320-1/
```

### Step 2. 先跑 sync precheck

```bash
/path/to/python .agent/runtime/scripts/workflow_core_sync_precheck.py \
  --repo-root . \
  --release-ref core-v20260320-1
```

若 staging root 位於 repo 內，`sync precheck` 會因 `.workflow-core/staging/**` 出現在 working tree 而回 `warn`。這是預期行為，不代表 core managed path 已經有 local divergence。

### Step 3. 套用 staged export tree

```bash
/path/to/python .agent/runtime/scripts/workflow_core_sync_apply.py \
  --repo-root . \
  --release-ref core-v20260320-1 \
  --staging-root .workflow-core/staging/core-v20260320-1
```

目前 `sync apply` 的行為：

1. 先跑 manifest-backed `sync precheck`
2. 若 warning 只來自 staging tree 本身，允許繼續
3. 載入 staged export tree 的 managed paths
4. 呼叫 `workflow_core_projection.py` materialize root live paths
5. 若 `doc/implementation_plan_index.md` 缺失，bootstrap 最小 placeholder

### Step 4. 套用後立刻 verify

```bash
/path/to/python .agent/runtime/scripts/workflow_core_sync_verify.py \
  --repo-root . \
  --release-ref core-v20260320-1 \
  --staging-root .workflow-core/staging/core-v20260320-1
```

目前 `sync verify` 會檢查：

1. required live path anchors
2. `AGENT_ENTRY.md` 入口 contract
3. post-apply managed changes是否已和 staged export tree 對齊
4. portable smoke suite
5. skills mutable split contract

---

## 6. 2026-03-20 實際驗證結果

目前這套流程已用「current worktree snapshot -> curated export tree -> 獨立 downstream temp repo」實際驗證過一輪。

驗證結果：

- export landing checklist on current worktree snapshot: `pass`
- export materialize from snapshot `HEAD`: `pass`
- downstream `sync precheck`: `warn`
  - 原因：repo 內 `.workflow-core/staging/**` 屬 staged input，需 manual review
- downstream `sync apply --staging-root ...`: `pass`
- downstream `sync verify --staging-root ...`: `pass`
- mutated downstream managed file successfully restored to exported content
- portable smoke during verify: `pass`

換句話說，現在已經不是只有 contract / stub 存在，而是 `export -> stage -> apply -> verify` 這條最小 downstream lane 已能跑通。

---

## 7. 維護注意事項

1. 只要 `curated-core-v1` includes 改了，就必須同步更新 `managed_paths`，避免 export landing checklist 再次出現 contract drift。
2. `split_required.recommended_target` 若是 compound target，不能把仍屬 managed core 的 path 誤當成 state-only pattern。
3. 若 staging root 放在 downstream repo 內，`sync precheck` 回 `warn` 是預期；真正的 blocking 條件仍是 core managed path divergence。
4. `workflow_core_projection.py` 現在已能 materialize staged managed files，但 `doc/implementation_plan_index.md` 仍屬 overlay artifact，bootstrap 的 placeholder 只保證入口 contract，不代表 upstream 接管該檔 ownership。
5. 若未來改成 fetched release ref / subtree remote lane，`sync apply` / `sync verify` 仍應保留 `--staging-root` 路徑，因為這是目前已驗證過的獨立 downstream fallback lane。
