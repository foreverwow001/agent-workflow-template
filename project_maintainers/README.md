# Project Maintainers Surface

這個目錄是給 downstream / 新專案本身使用的 supporting maintainer surface。

用途：

- 保存新專案自己的 chat handoff 與跨 session 摘要
- 保存可能值得回 upstream 的 improvement candidates
- 明確區分 template repo 的 `maintainers/` 與 downstream 專案自己的維護面
- 讓第一次 bootstrap 後，新專案不必再手動建立 chat handoff skeleton

治理原則：

- 這裡不是 workflow authoritative rule source
- authoritative project docs 仍以 `project_rules.md`、`doc/implementation_plan_index.md`、`doc/plans/*`、`doc/logs/*` 為主
- upstream 只提供這個 skeleton 與 template；新專案後續產生的 dated handoff / archive / improvement candidate 內容屬於 downstream local overlay

目前建議結構：

- `chat/`：session handoff 與 archive
- `improvement_candidates/`：待驗證、待 promotion 的 reusable candidate 區

## Optional Obsidian Access

若 downstream / 新專案需要在 Dev Container 中受控讀取 Obsidian，推薦使用 restricted consumer profile，而不是直接掛 full vault。

若 downstream 只想記一個同步入口，現在優先使用：

```bash
python .agent/runtime/scripts/workflow_core_sync_update.py \
	--repo-root . \
	--release-ref <release-ref> \
	--source-remote workflow-core-upstream \
	--setup-obsidian-restricted-access
```

這個 wrapper 會依序處理 `sync stage -> sync apply -> sync verify`，並在使用預設 staging root 時自動覆蓋舊的 generated staging tree，避免每次手動清理 `.workflow-core/staging/<release-ref>/`。

目前 core 已內建 generator artifact，可在 downstream repo 執行：

```bash
python .agent/runtime/scripts/workflow_core_obsidian_restricted_mount.py --repo-root .
```

若你只需要單獨產生 Obsidian restricted access sample，而不是跑完整個 one-click sync lane，也可改用以下入口：

```bash
python .agent/runtime/scripts/workflow_core_projection.py --repo-root . --bootstrap-overlay-index --setup-obsidian-restricted-access
python .agent/runtime/scripts/workflow_core_sync_apply.py --repo-root . --release-ref <release-ref> --setup-obsidian-restricted-access
```

若你需要自訂輸出目錄或強制覆蓋既有 sample，仍可搭配低階參數 `--obsidian-mount-output-dir` 與 `--force-obsidian-mount-sample`。

這會產生：

- `.devcontainer/devcontainer.obsidian-restricted.jsonc`
- `.devcontainer/OBSIDIAN_RESTRICTED_MOUNT.md`

預設 contract 為：

- single-root workspace，不使用 multi-root workspace
- repo 內 access surface 固定落在 `obsidian-knowledge/`
- 預設 read-only 面為 `obsidian-knowledge/00-indexes/` 與 `obsidian-knowledge/20-reviewed/`
- `obsidian-knowledge/10-inbox/pending-review-notes/` 是 default writable mount，但只在 capture / triage 命中時 on-demand read
- downstream 不提供 `10-inbox/reviewed-sync-candidates/` 的 read 或 write，也不預設 mount `30-archives/` 或 full vault
