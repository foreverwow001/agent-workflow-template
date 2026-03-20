# Changelog

## 2026-03-13 — Terminal PTY primary + fallback migration

### Highlights

- terminal workflow 主路徑正式收斂到 PTY；README、workflow docs、bootstrap/recovery 已對齊。
- 新增 PTY-primary 安裝入口 [.agent/runtime/scripts/vscode/install_terminal_tooling.sh](.agent/runtime/scripts/vscode/install_terminal_tooling.sh)；舊 [.agent/runtime/scripts/vscode/install_terminal_orchestrator.sh](.agent/runtime/scripts/vscode/install_terminal_orchestrator.sh) 降級為 shim。
- fallback bridge client 降級成 fallback-only compatibility helper。
- `/workflow/start` 與 `/workflow/status` 正式退休，不再列為 fallback roadmap。
- Injector / Monitor 的直接 runtime 依賴已切斷，legacy 套件改以歷史/抽取來源定位保留。

### What changed

- PTY 主路徑與 fallback 文檔：
  - [README.md](README.md)
  - [.agent/workflows/AGENT_ENTRY.md](.agent/workflows/AGENT_ENTRY.md)
  - [.agent/workflows/dev-team.md](.agent/workflows/dev-team.md)
  - [.agent/roles/coordinator.md](.agent/roles/coordinator.md)
  - [doc/plans/Idx-000_plan.template.md](doc/plans/Idx-000_plan.template.md)

- installer / bootstrap / recovery：
  - [.agent/runtime/scripts/vscode/install_terminal_tooling.sh](.agent/runtime/scripts/vscode/install_terminal_tooling.sh)
  - [.agent/runtime/scripts/vscode/install_terminal_orchestrator.sh](.agent/runtime/scripts/vscode/install_terminal_orchestrator.sh)
  - [.agent/runtime/scripts/devcontainer/post_create.sh](.agent/runtime/scripts/devcontainer/post_create.sh)
  - [doc/NEW_MACHINE_SETUP.md](doc/NEW_MACHINE_SETUP.md)
  - [doc/ENVIRONMENT_RECOVERY.md](doc/ENVIRONMENT_RECOVERY.md)
  - [doc/HOME_OFFICE_SWITCH_SOP.md](doc/HOME_OFFICE_SWITCH_SOP.md)

- preflight / fallback compatibility：
  - [.agent/runtime/scripts/vscode/workflow_preflight_check.py](.agent/runtime/scripts/vscode/workflow_preflight_check.py)
  - [.agent/runtime/scripts/vscode/workflow_preflight_fallback.py](.agent/runtime/scripts/vscode/workflow_preflight_fallback.py)
  - [.agent/runtime/scripts/sendtext_bridge_client.py](.agent/runtime/scripts/sendtext_bridge_client.py)
  - [.vscode/settings.json](.vscode/settings.json)

### Notes / Risks

- legacy package source 與 README 仍保留在 repo，因為它們還是能力抽取與 migration 對照的參考資產；但它們不再代表 workflow 推薦路徑。
- orchestrator extension 內部仍保有 retired `/workflow/*` handler 與 workflow loop 歷史實作，但對外 helper surface 與 maintainer 文檔已不再把它們視為現行能力。

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

- VS Code 終端工具（local extensions，歷史記錄）：
  - legacy injector / monitor / orchestrator 三件式，已於 2026-03-13 cleanup 移除

- 安裝與 preflight：
  - [.agent/runtime/scripts/vscode/install_terminal_orchestrator.sh](.agent/runtime/scripts/vscode/install_terminal_orchestrator.sh)（歷史上曾作為舊安裝入口，現已降級為 shim）
  - [.agent/runtime/scripts/vscode/workflow_preflight_check.py](.agent/runtime/scripts/vscode/workflow_preflight_check.py)

- 環境/新機文件：
  - [doc/NEW_MACHINE_SETUP.md](doc/NEW_MACHINE_SETUP.md)
  - [doc/ENVIRONMENT_RECOVERY.md](doc/ENVIRONMENT_RECOVERY.md)

### Quick start (Dev Container / VS Code Server)

1) 安裝 local extensions（歷史記錄，現請改用 PTY primary installer）：

```bash
bash .agent/runtime/scripts/vscode/install_terminal_orchestrator.sh
```

2) VS Code 執行：`Developer: Reload Window`

3) Engineer 注入前 preflight（預設不要求 bridge）：

```bash
python .agent/runtime/scripts/vscode/workflow_preflight_check.py --json
```

若此輪要用 HTTP SendText Bridge（僅在需要時啟用）：

```bash
python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-bridge --json
```

### Notes / Risks

- 本 repo 內含多個 `.vsix`（local extension 封包），利於離線/換機安裝，但會增加 repo 體積；若你希望 template 更精簡，可在後續改為只保留 source，或改用 Release assets 存放。
- Workflow 預設政策為「命令注入固定走 Injector extension 的 sendText；監測優先 Proposed API，必要時才啟用 Monitor fallback；HTTP bridge 非預設路徑」。
