# 公司與家裡切換 SOP

目標：讓你在公司電腦與家裡電腦之間切換時，快速恢復相同工作狀態，並避免誤以為 GitHub Copilot Chat 會原生跨機續聊。

## 核心原則

- 專案內容用 GitHub repo 同步。
- 原始 chat export JSON 放本機或 OneDrive，不提交。
- handoff 摘要放 repo，可提交。
- VS Code Settings Sync 用來同步設定，不用來同步同一段 Copilot Chat session。
- 換機後一律把 Dev Container 與 terminal tooling 視為要在該機器重新就位。

## 離開目前電腦前

1. 確認目前變更已經 commit，或至少 push 到遠端與 OneDrive 備份。
2. 在 VS Code 執行 `Chat: Export Chat...`。
3. 把 JSON 存到 `maintainers/chat/`，但不要提交。
4. 依 `maintainers/chat/handoff/SESSION-HANDOFF.template.md` 更新或新增 handoff 摘要。
5. 提交 handoff 摘要與必要文件變更。
6. 若這輪有 container 或工具特殊狀態，把模式與風險寫進 handoff。

## 到另一台電腦後

1. 開啟同一個 repo，先 pull 最新變更。
2. 確認 VS Code Settings Sync 已登入並同步完成。
3. 用 Dockerfile 標準模式開工：`Dev Containers: Reopen in Container`。
4. 若容器已開但工具不完整，在容器內執行 `bash .agent/runtime/scripts/devcontainer/post_create.sh`。
5. 再執行 `bash .agent/runtime/scripts/vscode/install_terminal_tooling.sh`。
6. 在 VS Code 執行 `Developer: Reload Window`。
7. 建議跑一次 `python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-pty --allow-pty-cold-start --json`。
8. 先讀最新 handoff 摘要，再視需要打開本機或 OneDrive 上的 chat export JSON。
9. 用 handoff 內的 next prompt 開新 chat 接續，不要預期會直接回到原本那一段 session。

## 若今天只想快速恢復工作

1. Pull repo。
2. Reopen in Container。
3. 重跑 post-create 與 terminal tooling 安裝。
4. 跑 PTY-primary preflight。
5. 讀 handoff。
6. 開新 chat，貼上 next prompt。

## 常見誤區

- 誤區：VS Code Settings Sync 會把 Copilot Chat 對話一起同步。
  - 正解：不應這樣假設；chat 接續請靠 export + handoff。
- 誤區：另一台機器只要 clone repo 就會自動有同樣的 Dev Container 狀態。
  - 正解：container 與 remote extension 狀態仍需在該機器重建。
- 誤區：原始 chat JSON 也應提交到 repo。
  - 正解：原始 JSON 留在本機或 OneDrive，repo 只提交 handoff 摘要。

## 相關文件

- `doc/NEW_MACHINE_SETUP.md`
- `doc/ENVIRONMENT_RECOVERY.md`
- `maintainers/chat/README.md`
- `maintainers/chat/handoff/SESSION-HANDOFF.template.md`
