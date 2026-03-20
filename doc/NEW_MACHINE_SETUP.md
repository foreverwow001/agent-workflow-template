# 新電腦開工指南（agent-workflow-template）

目標：在公司電腦、家裡電腦或新機上，用同一份 repo 快速重建一致的 VS Code + Dev Container 開發環境。

## 1. 一次性準備

1. 安裝 VS Code 或 VS Code Insiders
2. 安裝 Docker Desktop（Windows / macOS）或 Docker Engine（Linux）
3. 安裝 Dev Containers extension（Microsoft）
4. 用 Git clone 這個 repo

## 2. 預設開工方式：Dockerfile 標準模式

1. 在 VS Code 打開 repo
2. 執行 `Dev Containers: Reopen in Container`
3. VS Code 會讀取 `.devcontainer/devcontainer.json`
4. 這個主入口會以 `.devcontainer/Dockerfile` 建立容器
5. 容器建立後會自動執行 `.agent/runtime/scripts/devcontainer/post_create.sh`

`post_create.sh` 會處理：

- 先呼叫 `.agent/runtime/scripts/install_workflow_prereqs.sh`，檢查 workflow 最小依賴
- 建立 `.venv`
- 安裝固定版 `uv`
- 若 repo 內存在依賴清單，則安裝依賴
- 安裝本 repo 內建的 local terminal tooling（PTY primary、fallback secondary，legacy 相容套件暫時保留）
- 檢查 `codex` / `copilot` CLI 是否存在；若缺少且環境允許，會自動用 npm 全域安裝

> 這個 template 本身不強制依賴 `uv.lock` 或 `requirements*.txt`。若你之後把 template 套用到自己的專案，再把自己的依賴清單加入版控即可。

## 3. 可選加速方式：GHCR 預建 image

若你是維護者本人，想縮短容器 build 時間，可改用 GHCR 加速模式。

加速模式設定檔：

- `.devcontainer/devcontainer.ghcr.json`

建議做法：

- 優先使用本機 repo override 方式，不要直接把 repo 內主入口改髒
- 切換方式與注意事項請看：`maintainers/devcontainer_modes.md`

## 4. 容器建立後建議檢查

1. 確認 VS Code 左下角已進入 Dev Container
2. 在容器內執行：

```bash
bash .agent/runtime/scripts/vscode/install_terminal_tooling.sh
```

這支腳本現在會先檢查：

- `git`
- `python` / `python3 + venv`
- `node`
- `codex`
- `copilot`

另外在 Linux / Dev Container 會一併檢查：

- `bwrap`

若其中任一缺失，而且環境具備 `npm` 與可寫的 global prefix，或具備 passwordless `sudo`，會自動安裝：

```bash
sudo apt-get install -y git python3 python3-venv python-is-python3 nodejs npm bubblewrap
sudo npm install -g @openai/codex
sudo npm install -g @github/copilot
```

若自動安裝條件不成立，腳本會保留警告訊息，不會靜默跳過。

3. 執行 `Developer: Reload Window`

4. 建議再跑一次 PTY-primary preflight：

```bash
python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-pty --allow-pty-cold-start --json
```

若這台機器之後需要承接 fallback runtime，也建議再跑：

```bash
python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-fallback --json
```

PTY 主路徑本身**不要求**你額外設定 runtime `argv.json`。

fallback-ready 現在不要求 Proposed API 一定是唯一可用路徑；若 shell integration fallback stream 已掛上，加上 bridge healthz、token 與 artifact compatibility 正常，preflight 仍可回 ready。

只有在你想讓 fallback runtime 優先使用 Proposed API capture，而不是 shell integration fallback stream 時，才需要在本機 VS Code 的 `argv.json` 加入：

```json
{
  "enable-proposed-api": [
    "ivyhouse-local.ivyhouse-terminal-fallback"
  ]
}
```

儲存後完整關閉並重新開啟 VS Code。

## 5. 換機時不要拿來同步的內容

以下內容不應當成環境還原來源：

- `.venv/`
- `.pytest_cache/`
- `.service/`
- 任何本機 token / secrets

應同步的是：

- repo 內容
- `.devcontainer/` 設定
- VS Code Settings Sync
- 必要時的 maintainer handoff 摘要

補充：

- VS Code Settings Sync 主要同步的是編輯器偏好，不是把同一段 GitHub Copilot Chat session 原生搬到另一台電腦。
- Remote / Dev Container 視窗內的狀態仍要在每台機器各自建立，因此換機後還是要重新 `Reopen in Container`，必要時重跑 `post_create.sh` 與 terminal tooling 安裝。

## 6. 若你同時維護 chat 交接

- GitHub Copilot Chat 目前不應假設能在公司與家裡兩台電腦間無縫續聊同一段 session。
- 可提交摘要：`maintainers/chat/handoff/`
- 原始 export JSON：`maintainers/chat/*.json`（本機 / OneDrive 保存，不提交）

詳情請看：`maintainers/chat/README.md` 與 `doc/HOME_OFFICE_SWITCH_SOP.md`
