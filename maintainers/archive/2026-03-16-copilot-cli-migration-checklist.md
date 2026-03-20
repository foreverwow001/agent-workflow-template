# Copilot CLI Migration Checklist

> 建立日期：2026-03-16
> 狀態：Archived - completed migration record
> 用途：保留 `OpenCode -> Copilot CLI` 一次到位遷移的實作清單與驗證證據。active truth 已回到 runtime source、workflow docs 與 maintainer 規格文件，本檔不再作為現行規格來源。

## 1. 決策摘要

本次 migration 採以下固定契約：

- workflow 合約名稱：`copilot-cli`
- CLI binary：`copilot`
- 第二個 backend kind：`copilot`
- PTY command surface：`startCopilot` / `restartCopilot` / `sendToCopilot` / `submitCopilot` / `verifyCopilot` / `smokeTestCopilot`
- fallback command surface：`startCopilot` / `restartCopilot` / `sendToCopilot` / `sendLiteralToCopilot`
- settings keys：`copilotCommand` / `copilotTerminalName` / `autoStartCopilot`
- terminal names：`Copilot PTY` / `Copilot CLI`
- artifact names：`copilot_pty_debug.jsonl` / `copilot_pty_live.txt` / `copilot_live.txt`
- Copilot PTY text transport：`direct-text`
- Copilot PTY submit transport：`carriage-return`
- Copilot fresh-session gate：focused composer probe gate（`terminal.show(false)` + probe echo）
- Copilot fresh prompt delay：`1500ms`

固定不採用的做法：

- 不保留 active source 中的 `opencode` naming surface 作為長期 alias
- 不把 `GitHub Copilot Chat` 與 `copilot-cli` 混寫成同一個角色
- 不為了字面一致去重寫 archive / handoff / changelog 的歷史證據

## 2. Copilot PTY 基線證據

這次 migration 先補了受控的 Copilot PTY 行為基線，因此後續 runtime patch 不再屬於盲改。

### 已確認的事實

1. `copilot` binary 已安裝，且 `copilot --version` / `copilot --help` 可正常執行。
2. Copilot CLI 可在 raw PTY 中啟動，啟動後 process 持續存活，沒有一啟動就退出。
3. steady-state startup 會出現以下可判讀信號：
   - `GitHub Copilot`
   - `Loading environment`
   - `Visual Studio Code - Insiders connected`
   - prompt marker `❯`
4. 首次啟動會跳出 terminal multi-line input setup 對話，會要求 user 決定是否新增 key binding。
5. Copilot 的 submit semantics 不能沿用 OpenCode 的假設；`Ctrl+S` 會進入 Copilot command surface，`csi-u-enter` 也沒有成為穩定 submit 路徑。
6. 已直接驗證可用的 Copilot PTY 契約為：`direct-text` 送 prompt，`carriage-return` 做 submit。
7. fresh rebuilt Copilot session 的真正風險不只是 timing，而是 composer 可能尚未進入可見且可輸入狀態；穩定基線需要 focused composer probe gate，只有 probe echo 成功才送 smoke prompt。
8. 目前穩定 baseline 已直接驗證通過：`freshPromptDelayMs: 1500`、composer gate 預設 `attempts: 4`、`timeoutMs: 1800`、`retryDelayMs: 500`，且前端 `startCopilot -> verifyCopilot -> smokeTestCopilot` 可成功。
9. 針對上述 baseline 已補回歸測試 `tests/test_copilot_composer_gate_regression.py`，全量 `pytest` 亦已通過。

### 對 migration 的直接結論

- 風險已從「未知相容性」降成「已知行為差異」。
- 最大 runtime 差異不在啟動命令，而在 submit semantics 與 startup-ready gating。
- migration 不能只做 rename；PTY / fallback runtime 必須加入 Copilot-specific startup、focused composer gate 與 submit 邏輯。

## 3. 實作前硬性約束

1. `GitHub Copilot Chat` 仍固定是 Coordinator，不是 executor。
2. workflow 文件裡的 executor / qa tool 名稱一律寫 `copilot-cli`，不直接寫 `copilot`。
3. active 文件全面切換到 Copilot 命名後，archive / handoff / changelog 保持原文，只在必要的 active 文件說明「OpenCode slot 已被 Copilot CLI 取代」。
4. `.service/terminal_capture/**` 與測試 capture artifact 不做手工 rename；應由 migration 後的新 smoke / preflight 重新生成。

## 4. 必改檔案清單

下列清單只列 active truth 與會參與實作/驗證的 source、config、test、maintainer docs。

### A. Runtime 核心

| 檔案 | 修改面向 |
|------|----------|
| `.agent/runtime/tools/vscode_terminal_pty/extension.js` | backend kind `opencode -> copilot`、profile 命名、startup pattern、`direct-text + carriage-return` submit semantics、focused composer probe gate、artifact prefix、UX 文案、command registration |
| `.agent/runtime/tools/vscode_terminal_pty/package.json` | command ids/title、settings keys、預設 terminal name、verify config key、autoStart key、extension description |
| `.agent/runtime/tools/vscode_terminal_pty/README.md` | backend 說明、命令示例、前置條件、artifact 名稱、Copilot-specific 注意事項 |
| `.agent/runtime/tools/vscode_terminal_fallback/extension.js` | backend kind、command ids、terminal names、command/settings key、capture file names、send literal target |
| `.agent/runtime/tools/vscode_terminal_fallback/package.json` | command ids/title、settings keys、alwaysCapture key、extension description |
| `.agent/runtime/tools/vscode_terminal_fallback/README.md` | command surface、terminal names、capture files、Copilot fallback 說明 |
| `.agent/runtime/scripts/vscode/workflow_preflight_pty.py` | backend 預設、settings key 解析、summary key 名稱 |
| `.agent/runtime/scripts/vscode/workflow_preflight_check.py` | `--pty-backends` 預設與 help 文字 |
| `.agent/runtime/scripts/vscode/workflow_preflight_fallback.py` | artifact compatibility 中的 `opencode_live.txt` 改為 `copilot_live.txt` |
| `.agent/runtime/scripts/sendtext_bridge_client.py` | `terminal-kind` choices 從 `codex|opencode` 改成 `codex|copilot` |
| `.agent/runtime/scripts/vscode/install_terminal_tooling.sh` | 缺少 CLI 提示與設定 key 從 OpenCode 改成 Copilot CLI |

### B. Workflow 合約與模板

| 檔案 | 修改面向 |
|------|----------|
| `.agent/workflows/AGENT_ENTRY.md` | tool options `codex-cli|copilot-cli`、PTY command 面、fallback 命令名稱 |
| `.agent/workflows/dev-team.md` | OpenCode 敘事改為 Copilot CLI、PTY/fallback command 面、executor/qa 名稱 |
| `.agent/roles/coordinator.md` | Codex/OpenCode 雙 backend 改為 Codex/Copilot CLI、命令面、禁止事項 wording |
| `.agent/roles/qa.md` | Cross-QA tool 名稱、skills-evaluator 敘事與 reviewer 文案 |
| `.agent/VScode_system/Ivy_Coordinator.md` | Coordinator 操作對象、executor naming、禁止向 Copilot terminal 注入 git |
| `.agent/VScode_system/tool_sets.md` | tool inventory、terminal naming、任務分工文案 |
| `.agent/VScode_system/chat_instructions_ivy_house_rules.md` | Chat 規則內的工具與 terminal 命名 |
| `doc/plans/Idx-000_plan.template.md` | `executor_tool` / `qa_tool` / `last_change_tool` naming、Copilot Chat vs `copilot-cli` 角色區分、QA 建議矩陣 |
| `README.md` | 安裝前置條件、PTY command surface、CLI 命名、missing-command 診斷 |

### C. Setup 與 workspace config

| 檔案 | 修改面向 |
|------|----------|
| `.vscode/settings.json` | `autoStartOpenCode`、`opencodeCommand` 等 workspace overrides 改成 Copilot 對應鍵 |
| `.vscode/extensions.json` | 移除 OpenCode extension recommendation；若有需要，改成 Copilot 相關 recommendation 或單純刪除 |
| `.devcontainer/devcontainer.json` | 移除/替換 `sst-dev.opencode` 類依賴與說明 |
| `.devcontainer/devcontainer.ghcr.json` | 同上 |
| `.idx/dev.nix` | 移除/替換 OpenCode extension / package 參考 |

### D. 測試與 active maintainer docs

| 檔案 | 修改面向 |
|------|----------|
| `tests/test_copilot_composer_gate_regression.py` | Copilot submit/gate active truth regression coverage |
| `tests/test_workflow_preflight_pty.py` | settings key、backend name、command path、預期 summary key |
| `maintainers/chat/2026-03-13-merged-fallback-tool-spec.md` | active 設計文中的 backend / command / artifact naming truth |
| `maintainers/chat/2026-03-13-preflight-migration-plan.md` | active preflight truth、artifact 與 backend naming |
| `maintainers/chat/2026-03-13-pty-monitor-and-capture-contract.md` | PTY artifact contract 從 OpenCode 改成 Copilot |
| `maintainers/chat/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md` | active architecture truth 中的第二 backend 命名與責任 |

## 5. 只更新 active truth，不碰歷史內容

下列檔案不做全文 rename，只保留原文作為歷史證據：

| 檔案 | 處理策略 |
|------|----------|
| `.agent/CHANGELOG_v1.2.0.md` | 保持原文 |
| `maintainers/chat/archive/2026-03-11-template-workflow-analysis.md` | 保持原文 |
| `maintainers/chat/archive/2026-03-12-dual-pty-followup-handoff.md` | 保持原文 |
| `maintainers/chat/archive/2026-03-13-legacy-terminal-pre-delete-checklist.md` | 保持原文 |
| `maintainers/chat/archive/2026-03-13-pty-status-summary-and-next-steps.md` | 保持原文 |
| `maintainers/chat/archive/2026-03-13-terminal-pty-next-step-handoff.md` | 保持原文 |
| `maintainers/chat/archive/2026-03-13-pre-rebuild-handoff.md` | 保持原文 |
| `maintainers/chat/archive/2026-03-13-pty-workflow-readiness-handoff.md` | 保持原文 |

必要時只在 active 文件補一句：`OpenCode slot 後續已被 Copilot CLI 取代。`

## 6. 實作策略

雖然這次是一次到位 migration，但實作順序仍要固定，避免 patch 中途處於不可驗證狀態。

1. 先改 runtime 核心與 package.json command/config surface。
2. 再改 preflight / bridge client / install tooling。
3. 再改 workflow 合約、template、README。
4. 再改 setup/config 與 active maintainer docs。
5. 最後更新 tests、重跑 smoke、重生 artifact。

## 7. 實作後的驗證清單

### A. PTY 核心驗證

- `ivyhouseTerminalPty.startCodex`
- `ivyhouseTerminalPty.startCopilot`
- `ivyhouseTerminalPty.verifyCodex`
- `ivyhouseTerminalPty.verifyCopilot`
- `ivyhouseTerminalPty.smokeTestCodex`
- `ivyhouseTerminalPty.smokeTestCopilot`

必看 evidence：

- `codex_pty_debug.jsonl`
- `copilot_pty_debug.jsonl`
- `codex_pty_live.txt`
- `copilot_pty_live.txt`

驗證點：

- Copilot verify 仍使用 `direct-text + carriage-return`
- fresh smoke session 先看到 `composer_input_probe.succeeded`
- 之後 `smoke-ping -> pong` 與 `smoke-ok -> smoke-ok` 都成功

### B. Fallback 驗證

- `ivyhouseTerminalFallback.startBridge`
- `ivyhouseTerminalFallback.startCodex`
- `ivyhouseTerminalFallback.startCopilot`
- `ivyhouseTerminalFallback.sendToCopilot`
- `python .agent/runtime/scripts/sendtext_bridge_client.py healthz`

### C. Preflight 驗證

- `python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-pty --allow-pty-cold-start --json`
- `python .agent/runtime/scripts/vscode/workflow_preflight_check.py --require-fallback --json`

驗證點：

- backend summary key 已從 `opencode` 改成 `copilot`
- command path 指向 `copilot`
- fallback artifact compatibility 已對齊 `copilot_live.txt`

### D. Template / workflow 合約驗證

- 檢查 `Idx-000_plan.template.md` 的 `executor_tool` / `qa_tool` / `last_change_tool` 是否已統一為 `codex-cli|copilot-cli`
- 檢查 `AGENT_ENTRY.md`、`dev-team.md`、`coordinator.md` 是否仍清楚區分 `Copilot Chat` 與 `copilot-cli`
- 重新跑一次 `/dev` smoke walkthrough，確認 READ_BACK_REPORT、Role Selection、Cross-QA naming 都不再提 `opencode`

### E. 測試驗證

- `python -m pytest -q`
- `python -m pytest tests/test_copilot_composer_gate_regression.py -q`
- 聚焦測試：`python -m pytest tests/test_workflow_preflight_pty.py -q`

### F. Source hygiene 驗證

- active source/config/test/doc 中不再出現 `opencode` / `OpenCode`
- archive / handoff / changelog 保留原文，不納入 hygiene fail
- `.service/terminal_capture/**` 由新 smoke 重生，不手工追字面 rename

## 8. 完成定義

當以下條件同時成立，可視為 migration 完成：

1. active truth 檔案已全部切到 `copilot-cli` / `copilot` 命名契約。
2. PTY 與 fallback 對 Copilot CLI 的 startup / submit / verify / smoke 路徑已有直接 evidence。
3. preflight、template、tests、README 與 maintainer active docs 已全部對齊。
4. active source/config/test/doc 中不再殘留 `opencode` surface。
5. 歷史文件仍保留原文，沒有為追求字面一致而破壞審計證據。
