# IvyHouse Terminal Fallback

最小可用版的 **legacy fallback adapter**。

它不是 PTY 主路徑，也不是新的 combined terminal platform。它的定位只有一個：

- 當 `.agent/runtime/tools/vscode_terminal_pty` 主路徑不可用，且使用者明確同意後，提供 legacy terminal 的 send / capture / verify / bridge 最小能力。

## 目前狀態

這個資料夾目前已完成第二輪最小能力：

- `package.json` 已定義 command namespace、config keys 與 activation strategy
- `extension.js` 已接上 terminal lifecycle、sendLiteral、capture、`/status` verify、on-demand bridge
- 明確不保留 workflow loop、`/workflow/start`、`/workflow/status`、legacy cleanup prompt

### 已可用的第二輪能力

- start Codex fallback terminal
- restart Codex fallback terminal
- start Copilot fallback terminal
- restart Copilot fallback terminal
- `startAll`
- `sendLiteralToCodex({ text, submit })`
- `sendLiteralToCopilot({ text, submit })`
- user-facing `sendToCodex` / `sendToCopilot`
- rolling live capture: `codex_live.txt` / `copilot_live.txt`
- one-shot capture: `codex_last.txt`
- structured diagnostics: `monitor_debug.jsonl`
- `captureCodexOutput`
- `autoCaptureCodexStatus`
- `restartAndCaptureCodexStatus`
- `verifyCodexStatusInjection`
- on-demand bridge server
	- `GET /healthz`
	- `POST /send`
	- bearer / `x-ivy-token` auth
	- token auto-create to `.service/sendtext_bridge/token` when bridge starts
	- localhost-only bind
	- in-memory token-bucket rate limit
	- audit log: `sendtext_bridge_events.jsonl`
- `showDiagnostics`
- `resetSessionState`
- PTY consented handoff
	- 當 `.agent/runtime/tools/vscode_terminal_pty` 的 recovery flow 收到 user 同意後，可由 PTY side 真正啟動 fallback terminal / bridge
	- 對 `send` / `submit` 這類安全可重放的最後一步，現在可直接由 fallback runtime 接手
	- 若最後一步不適合自動重放，fallback runtime 仍會先完成 bridge / terminal 就位，再交給 operator 繼續

### 已明確退休的能力

- workflow loop / orchestration state machine
- `POST /workflow/start`
- `GET /workflow/status`
- legacy QA PASS cleanup prompt

## 命令面

目前已預留的 user-facing commands：

- `ivyhouseTerminalFallback.startCodex`
- `ivyhouseTerminalFallback.restartCodex`
- `ivyhouseTerminalFallback.startCopilot`
- `ivyhouseTerminalFallback.restartCopilot`
- `ivyhouseTerminalFallback.startAll`
- `ivyhouseTerminalFallback.sendToCodex`
- `ivyhouseTerminalFallback.sendToCopilot`
- `ivyhouseTerminalFallback.captureCodexOutput`
- `ivyhouseTerminalFallback.autoCaptureCodexStatus`
- `ivyhouseTerminalFallback.restartAndCaptureCodexStatus`
- `ivyhouseTerminalFallback.verifyCodexStatusInjection`
- `ivyhouseTerminalFallback.showDiagnostics`
- `ivyhouseTerminalFallback.resetSessionState`

## 內部 API

已接上但不 expose 到 Command Palette 的 internal commands：

- `ivyhouseTerminalFallback.sendLiteral`
- `ivyhouseTerminalFallback.sendLiteralToCodex`
- `ivyhouseTerminalFallback.sendLiteralToCopilot`
- `ivyhouseTerminalFallback.startBridge`
- `ivyhouseTerminalFallback.stopBridge`

## Artifact 相容面

fallback 目前刻意沿用 legacy artifact 名稱，目的是先把 monitor / bridge 依賴往下壓，而不是同時再改 artifact contract：

- `.service/terminal_capture/monitor_debug.jsonl`
- `.service/terminal_capture/codex_live.txt`
- `.service/terminal_capture/copilot_live.txt`
- `.service/terminal_capture/codex_last.txt`
- `.service/terminal_capture/sendtext_bridge_events.jsonl`

這代表現有 preflight、維運腳本與人工作業可以先沿用舊檔名，不需要等 merged fallback tool v1 才切換。

## Bridge 行為

- bridge 不會在 extension activation 時自動啟動
- 只有 internal command `ivyhouseTerminalFallback.startBridge` 被呼叫時才會 listen
- PTY consented handoff 也可以在接手流程中觸發 `startBridge`
- listen 位址固定是 `127.0.0.1`
- 啟動 bridge 時，若沒有 `IVY_SENDTEXT_BRIDGE_TOKEN` 且 token file 不存在，會自動建立 `.service/sendtext_bridge/token`
- `POST /send` 目前只承接最小 send adapter，不負責 workflow loop

## Capture 與 Verify

- fallback capture 主路徑優先用 Proposed API `onDidWriteTerminalData`
- 若 Proposed API 不可用，會嘗試沿用 shell integration `execution.read()` fallback stream
- `/status` verify 仍沿用 legacy Codex capture 判讀：`/status` echo + `context left` 或 `OpenAI Codex/Tip:`，且不能命中 pasted overlay
- preflight / operator 心智模型現在應理解為：只要 Proposed API 或 shell integration 其一可用，再加上 bridge / token / artifact compatibility 正常，即可視為 fallback-ready

## Activation 原則

- 不在 VS Code 啟動時自動常駐
- 不在 workspace 開啟時自動常駐
- 只有在執行 fallback command 時才 activation
- bridge 不因 extension activation 自動啟動

## 打包

在此資料夾執行：

```bash
npm -s exec --yes @vscode/vsce package -- --allow-missing-repository --skip-license
```
