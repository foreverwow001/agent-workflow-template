# SESSION-HANDOFF

> 建立日期：2026-03-13
> 狀態：Archived - milestone handoff

## Current goal

這份 handoff 原本建立於 rebuild 前；目前已補記 rebuild 後的實際驗證結果。重點是：preflight aggregator 已落地、clean-container 驗證已完成，而且 fallback layer 現在可透過 shell integration attachment + bridge/token/artifact 健康度達到 ready，不再被單一 `proposed_api_true` 綁死。

## Current branch

main

## Active container mode

- 目前已完成 rebuild 後驗證
- 已確認為 Standard Dockerfile mode
- Debian GNU/Linux 12 dev container

## Files touched

- .devcontainer/devcontainer.json
- .devcontainer/Dockerfile
- .agent/runtime/scripts/devcontainer/post_create.sh
- .agent/runtime/scripts/vscode/install_terminal_tooling.sh
- .agent/runtime/scripts/vscode/workflow_preflight_pty.py
- .agent/runtime/scripts/vscode/workflow_preflight_fallback.py
- maintainers/chat/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md
- maintainers/chat/2026-03-13-pty-monitor-and-capture-contract.md
- maintainers/chat/2026-03-13-merged-fallback-tool-spec.md
- maintainers/chat/2026-03-13-preflight-migration-plan.md
- .agent/runtime/tools/vscode_terminal_pty/README.md
- .agent/runtime/tools/vscode_terminal_fallback/README.md
- .agent/runtime/tools/vscode_terminal_fallback/extension.js
- .agent/runtime/tools/vscode_terminal_fallback/package.json
- .agent/runtime/scripts/vscode/workflow_preflight_check.py

## What has been confirmed

- terminal tooling 的 authoritative 架構已定：.agent/runtime/tools/vscode_terminal_pty 是唯一主路徑，legacy injector / monitor / orchestrator 的未來只剩單一 fallback tool。
- silent fallback 已被明確排除；PTY 失敗後必須先由 agent 解釋失敗層級並詢問使用者是否同意啟動 fallback。
- PTY monitor / capture 契約已落成 active maintainer doc，authoritative evidence 已收斂到 .service/terminal_capture/*_pty_debug.jsonl，*_pty_live.txt 只作 transcript 輔助。
- merged fallback tool v1 的 scope 已落成 authoritative spec，/workflow/start、/workflow/status、combined workflow loop、QA PASS cleanup prompt 都已正式排除在 v1 外。
- fallback package scaffold 已存在：.agent/runtime/tools/vscode_terminal_fallback/package.json、.agent/runtime/tools/vscode_terminal_fallback/extension.js、.agent/runtime/tools/vscode_terminal_fallback/README.md 都已建立，命名空間固定為 ivyhouseTerminalFallback.*。
- dev container 主入口已切到 Dockerfile 標準模式；post-create 會建立 .venv、安裝 uv，並優先走 .agent/runtime/scripts/vscode/install_terminal_tooling.sh 安裝 PTY primary + fallback tooling。
- `workflow_preflight_check.py` 的 aggregator 已完成整合：已接上 PTY layer 與 fallback layer，CLI 已支援 `--require-pty`、`--allow-pty-cold-start`、`--require-fallback`、`--pty-backends`，且 `--require-bridge` 已降級為 alias warning。
- rebuild 後已實際重跑 `post_create.sh`、`install_terminal_tooling.sh`、以及 `workflow_preflight_check.py` 的 PTY-primary / fallback-required 驗證。
- fallback bridge 已可由 `ivyhouseTerminalFallback.startBridge` 實際 listen，`/healthz` 已驗證返回 `status=ok`。
- fallback diagnostics 已證明 shell integration attachment 可成立；因此 fallback-ready 現在接受「shell integration + bridge + token + artifact compatibility」這條路徑，不再要求 `proposed_api_true` 一定恢復成 `true`。
- HOME_OFFICE / recovery / maintainer docs 已改成 rebuild 後應重跑 post-create、install_terminal_tooling、Reload Window，再執行 PTY-primary preflight 的心智模型。
- 目前工作樹仍有大量本輪變更；這份 handoff 的目的就是讓 rebuild 後不要靠記憶重新拼上下文。

## What was rejected

- 不再把 OpenCode submit parity、close barrier、orphan leakage、或單一 fallback delay 視為這輪主線；除非有新的 post-fix evidence，否則不要重開這些 runtime bug 討論。
- 不再把 legacy monitor / bridge health 視為整體 workflow ready 的唯一代表；preflight 必須改成 PTY-aware primary + fallback-aware secondary。
- 不再把 fallback tool 當第二主架構或背景常駐服務；它只能是 PTY failure 後按需啟動的 legacy adapter。
- 不再延續 ivyhouseTerminalInjector.*、ivyhouseTerminalMonitor.*、ivyhouseTerminalOrchestrator.* 作為新 public surface。

## Next exact prompt

請先讀這份 handoff，再讀 active 文檔中的 preflight migration plan。重點不要再放在「aggregator 能不能跑」，而要放在收尾：1. 重新檢查 workflow / governance / README 類文檔，哪些地方還停留在舊的 bridge-centric preflight 心智模型；2. 決定是否要把 `proposed_api_true=false` 但 shell integration 可用的 fallback-ready 判定，正式寫進更多 operator 文件；3. 若仍想追 `proposed_api_true` 本身恢復成 true，則改從 VS Code 客戶端 runtime allowlist / Proposed API 設定角度調查，而不是繼續改 repo 內 preflight 程式碼。

## Risks

- 現在最大的風險不再是 clean-container 未驗證，而是文件落後於已落地行為：很多地方仍可能默認 fallback-ready 取決於 `proposed_api_true`，但實際上 shell integration attachment 已能構成有效 monitor backend。
- `.agent/runtime/tools/vscode_terminal_fallback` 的 `proposed_api_true` 仍可能維持 false；這看起來比較像 VS Code 客戶端 runtime allowlist 或 Proposed API 啟用條件，而不是 repo 內 preflight 缺陷。
- repo 仍有其他未提交修改；rebuild 後若要繼續實作，避免順手整理與 preflight / handoff 無關的檔案。

## Verification status

- 已驗證：authoritative 文檔鏈已形成；PTY 主架構、fallback v1 scope、monitor/capture 契約、以及 preflight 遷移方案都已有 active docs；fallback package 與 PTY/fallback installer 骨架也已落檔；rebuild 後的 `.agent/runtime/scripts/devcontainer/post_create.sh`、`.agent/runtime/scripts/vscode/install_terminal_tooling.sh`、`.agent/runtime/scripts/vscode/workflow_preflight_check.py --require-pty --allow-pty-cold-start --json`、`.agent/runtime/scripts/vscode/workflow_preflight_check.py --require-fallback --json` 都已實際驗證通過。
- 已驗證：fallback bridge 已由 `ivyhouseTerminalFallback.startBridge` 啟動並通過 `/healthz`；fallback diagnostics 也已證明 shell integration attachment 可成立。
- 尚未驗證：`.agent/runtime/tools/vscode_terminal_fallback` 的 `proposed_api_true` 為何在目前這個環境中維持 false，尚未從 VS Code 客戶端 runtime allowlist 角度做獨立調查。
