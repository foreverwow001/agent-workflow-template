# 環境回復指南（agent-workflow-template）

此指南處理的是：容器壞掉、切錯模式、GHCR pull 失敗、post-create 沒跑完，或換機後無法順利重新進入開發環境。

## 1. 先判斷你現在在哪一種狀態

### A. 主入口設定有問題

症狀：

- `Dev Containers: Reopen in Container` 直接失敗
- `.devcontainer/devcontainer.json` 被改成錯的模式或內容

建議：

1. 先確認 `.devcontainer/devcontainer.json` 是否仍為 Dockerfile 標準模式
2. 若只是想快速回到可重建基線，先恢復到標準模式
3. 再執行 `Dev Containers: Rebuild and Reopen in Container`

### B. Dockerfile build 失敗

症狀：

- build log 顯示 apt 安裝或 Dockerfile 語法錯誤

建議：

1. 在失敗對話中選 `Open Folder Locally` 或 `Reopen in Recovery Container`
2. 修正 `.devcontainer/Dockerfile`
3. 再執行 `Dev Containers: Rebuild Container`

### C. GHCR 模式失敗

症狀：

- pull image 失敗
- digest 找不到
- 權限不足

建議：

1. 若是權限問題，先 `docker login ghcr.io`
2. 若只是要快速恢復工作，直接切回 Dockerfile 標準模式
3. GHCR 模式是加速變體，不應阻斷你回到可工作的基線

### D. post-create 沒有完成

症狀：

- `.venv` 沒建立
- terminal tooling 沒裝好
- 容器進去了，但工具缺一半

建議：

在容器內重跑：

```bash
bash .agent/runtime/scripts/devcontainer/post_create.sh
```

## 2. 標準回復流程

1. 確認 Docker daemon 正常
2. 確認 VS Code 可打開 repo
3. 先回到 `.devcontainer/devcontainer.json` 的 Dockerfile 標準模式
4. 執行 `Dev Containers: Rebuild and Reopen in Container`
5. 進容器後若需要，手動補跑：

```bash
bash .agent/runtime/scripts/devcontainer/post_create.sh
bash .agent/runtime/scripts/vscode/install_terminal_tooling.sh
```

6. 最後執行 `Developer: Reload Window`

7. 若要確認 PTY 主路徑至少已進入可用狀態，再執行：

```bash
python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-pty --allow-pty-cold-start --json
```

8. 若這輪需要 fallback runtime，也補跑：

```bash
python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-fallback --json
```

fallback 模式現在不要求 `proposed_api_true` 一定恢復成 true；若 shell integration attachment、bridge healthz、token 與 artifact compatibility 都正常，aggregate 仍可 pass。

## 3. 兩種模式的回復原則

- **標準模式失敗**：修 Dockerfile 或主入口設定，因為這是 template 的基線
- **GHCR 模式失敗**：優先退回標準模式，不要讓加速變體阻塞維護工作

## 4. 常見排查點

### Docker 沒起來

- Windows / macOS：先確認 Docker Desktop 已啟動
- Linux：確認 Docker daemon 正常運作

### VS Code 找不到 Dev Container 設定

- 確認 repo 內存在 `.devcontainer/devcontainer.json`
- 確認你開的是 repo 根目錄，不是子資料夾

### Python interpreter 路徑不對

- 本 repo 預設 interpreter 指向 `/workspaces/${localWorkspaceFolderBasename}/.venv/bin/python`
- 若 `.venv` 不存在，重跑 `bash .agent/runtime/scripts/devcontainer/post_create.sh`

### terminal tooling 沒生效

1. 在容器內執行：

```bash
bash .agent/runtime/scripts/vscode/install_terminal_tooling.sh
```

2. 執行 `Developer: Reload Window`

3. 若 PTY 仍然不可用，再檢查：

```bash
python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-pty --allow-pty-cold-start --json
```

若你準備切 fallback runtime，則改補：

```bash
python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-fallback --json
```

## 5. 換機時的維護上下文

若這次環境回復同時伴隨維護工作切換，請不要依賴 chat 視窗記憶。

GitHub Copilot Chat 目前不應假設可以在另一台電腦原生接續同一段 session；跨機接續請改走 export + handoff。

請使用：

- `maintainers/chat/handoff/` 保存可提交摘要
- `maintainers/chat/*.json` 保存原始匯出（本機 / OneDrive，不提交）

## 6. 核心原則

- `implementation_plan_index.md` 留給 template 使用者，不拿來記錄 template 自己的維護任務
- template 自己的環境 / 容器 / chat 維護資訊集中在 `maintainers/`
- Dockerfile 標準模式永遠是最後可回退的基線
