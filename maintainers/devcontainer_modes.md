# Dev Container 模式說明

> 本 repo 採雙軌 Dev Container 結構：`Dockerfile` 是標準模式，`GHCR` 是加速模式。

## 模式定位

### 1. 標準模式（預設）

- 入口：`.devcontainer/devcontainer.json`
- 建置來源：`.devcontainer/Dockerfile`
- 適用情境：
  - template 要提供給其他人使用
  - 新電腦 / 新環境首次開工
  - 需要可重建、可理解的開發環境

### 2. 加速模式（選用）

- 入口來源：`.devcontainer/devcontainer.ghcr.json`
- 建置來源：預建 GHCR image
- 適用情境：
  - 維護者自己常用的快速開工流程
  - 已知 GHCR image 可用且要減少 build 時間

## 共同初始化邏輯

兩種模式都會呼叫：

- `.agent/runtime/scripts/devcontainer/post_create.sh`

這支腳本負責：

- 建立 `.venv`（若尚未存在）
- 安裝固定版 `uv`
- 若 repo 內有依賴清單則安裝依賴
- 安裝 local terminal extensions

> 若 repo 尚未有 `pyproject.toml` / `uv.lock` / `requirements*.txt`，腳本會安全略過依賴安裝，不會因缺檔失敗。

## 如何切換模式

### 方法 A：維持 repo 乾淨的本機 override（建議）

使用 VS Code 的 `Dev Containers: Repository Configuration Paths` 設定，在本機外部建立 repo 專用設定覆寫。

做法：

1. 在本機設定一個 repo configuration 根目錄
2. 依 `git remote -v` 的 repo 路徑建立對應資料夾
3. 把 `.devcontainer/devcontainer.ghcr.json` 的內容存成該外部覆寫位置的 `.devcontainer/devcontainer.json`
4. 重新執行 `Dev Containers: Rebuild and Reopen in Container`

優點：

- 不會把 repo 內的 `.devcontainer/devcontainer.json` 改髒
- 公司與家裡電腦可以各自用不同模式

### 方法 B：直接切換 repo 內主入口（簡單，但會產生 diff）

若只是暫時要切到 GHCR 模式，可把 `.devcontainer/devcontainer.ghcr.json` 複製覆蓋到 `.devcontainer/devcontainer.json`，重建容器後使用。

完成後請記得恢復回標準模式，避免把加速變體誤當成 template 主入口提交。

## 維護原則

- `devcontainer.json` 永遠保留為 Dockerfile 標準模式
- `devcontainer.ghcr.json` 永遠視為選用加速變體
- 若兩種模式都需要 post-create 初始化，統一走共用腳本，避免行為漂移
- 若之後要發佈預建 image，優先由 Dockerfile 產生，而不是手工維護兩套獨立環境
