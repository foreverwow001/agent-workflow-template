# Changelog

## 2026-02-19 — Workflow contract sync + VS Code terminal tooling

### Highlights

- `/dev` workflow 合約更新（Coordinator/Role Selection Gate/Preflight Gate/Cross-QA 規則整合）。
- 終端注入與監測能力落地為三件式 local VS Code extensions：Injector / Monitor / Orchestrator。
- 新增一鍵 preflight 腳本，Engineer 注入前先檢查 Proposed API 與（選用）Bridge 健康度。
- 補齊可攜式環境骨架（Dev Container 與 IDX），並更新 extension recommendations。

### What changed

- Workflow 文件同步至最新治理版本：
  - [.agent/workflows/AGENT_ENTRY.md](.agent/workflows/AGENT_ENTRY.md)
  - [.agent/workflows/dev-team.md](.agent/workflows/dev-team.md)
  - [.agent/roles/coordinator.md](.agent/roles/coordinator.md)
  - [doc/plans/Idx-000_plan.template.md](doc/plans/Idx-000_plan.template.md)

- VS Code 終端工具（local extensions）：
  - [tools/vscode_terminal_injector](tools/vscode_terminal_injector)
  - [tools/vscode_terminal_monitor](tools/vscode_terminal_monitor)
  - [tools/vscode_terminal_orchestrator](tools/vscode_terminal_orchestrator)

- 安裝與 preflight：
  - [scripts/vscode/install_terminal_orchestrator.sh](scripts/vscode/install_terminal_orchestrator.sh)（會一次安裝 Injector/Monitor/Orchestrator）
  - [scripts/vscode/workflow_preflight_check.py](scripts/vscode/workflow_preflight_check.py)

- 環境/新機文件：
  - [doc/NEW_MACHINE_SETUP.md](doc/NEW_MACHINE_SETUP.md)
  - [doc/ENVIRONMENT_RECOVERY.md](doc/ENVIRONMENT_RECOVERY.md)

### Quick start (Dev Container / VS Code Server)

1) 安裝 local extensions：

```bash
bash scripts/vscode/install_terminal_orchestrator.sh
```

2) VS Code 執行：`Developer: Reload Window`

3) Engineer 注入前 preflight（預設不要求 bridge）：

```bash
python scripts/vscode/workflow_preflight_check.py --json
```

若此輪要用 HTTP SendText Bridge（僅在需要時啟用）：

```bash
python scripts/vscode/workflow_preflight_check.py --require-bridge --json
```

### Notes / Risks

- 本 repo 內含多個 `.vsix`（local extension 封包），利於離線/換機安裝，但會增加 repo 體積；若你希望 template 更精簡，可在後續改為只保留 source，或改用 Release assets 存放。
- Workflow 預設政策為「命令注入固定走 Injector extension 的 sendText；監測優先 Proposed API，必要時才啟用 Monitor fallback；HTTP bridge 非預設路徑」。
