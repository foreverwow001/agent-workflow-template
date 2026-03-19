# IvyHouse Terminal PTY

第一版的 **dual-backend pseudo-TTY 主路徑 extension**。

它的目標不是立刻取代全部 legacy tool，而是先把已驗證成功的 Codex PTY prototype 收斂成一個可持續擴充的新主工具，並把 Copilot 接進同一份 runtime core。

目前的 monitor / capture active truth 以本 README 為主；maintainer 導航入口見：

- `maintainers/chat/2026-03-19-terminal-tooling-source-map.md`

## 目前範圍

- 支援 `codex` 與 `copilot` 兩個 backend profile
- 使用 VS Code extension terminal + Python PTY bridge
- 提供共用 command pipeline：start / restart / send / submit / verify / smoke
- 持續落地 backend-aware live transcript 與 debug jsonl
- 內建最小 recovery state 與 fallback prompt 介面

## 命令面

### 相容層

- `ivyhouseTerminalPty.start`
- `ivyhouseTerminalPty.restart`
- `ivyhouseTerminalPty.send`
- `ivyhouseTerminalPty.submit`
- `ivyhouseTerminalPty.verify`
- `ivyhouseTerminalPty.smokeTest`
- `ivyhouseTerminalPty.showRecoveryStatus`
- `ivyhouseTerminalPty.retryLastAction`
- `ivyhouseTerminalPty.rebuildSession`
- `ivyhouseTerminalPty.enableFallback`
- `ivyhouseTerminalPty.declineFallback`
- `ivyhouseTerminalPty.resetSessionState`

### 雙 backend 命令

- `ivyhouseTerminalPty.startCodex`
- `ivyhouseTerminalPty.startCopilot`
- `ivyhouseTerminalPty.restartCodex`
- `ivyhouseTerminalPty.restartCopilot`
- `ivyhouseTerminalPty.sendToCodex`
- `ivyhouseTerminalPty.sendToCopilot`
- `ivyhouseTerminalPty.submitCodex`
- `ivyhouseTerminalPty.submitCopilot`
- `ivyhouseTerminalPty.verifyCodex`
- `ivyhouseTerminalPty.verifyCopilot`
- `ivyhouseTerminalPty.smokeTestCodex`
- `ivyhouseTerminalPty.smokeTestCopilot`

## 安裝與啟用

1. 在 workspace / dev container 內執行：

```bash
bash .agent/runtime/scripts/vscode/install_terminal_tooling.sh
```

前置條件：當前環境必須能直接執行 `codex` 與 `copilot`，或在 VS Code 設定中把 `ivyhouseTerminalPty.codexCommand`、`ivyhouseTerminalPty.copilotCommand` 改成實際可用的執行檔名稱。

2. 在 VS Code 執行：`Developer: Reload Window`

> 這支安裝腳本目前會以 PTY primary、fallback secondary 的順序安裝 tooling，不會替你安裝 `codex` / `copilot` CLI 本體。

## Artifact Contract

預設寫到 `.service/terminal_capture/`：

- `codex_pty_live.txt`
- `codex_pty_debug.jsonl`
- `copilot_pty_live.txt`
- `copilot_pty_debug.jsonl`

每個 backend 現在都採 **current + rotated history** 模型：

- 固定檔名保留給 current view，供 workflow / preflight / operator 直接判讀
- `ivyhouseTerminalPty.start*` 與 `ivyhouseTerminalPty.restart*` 會先 rotate 舊的 current files，再開始新一輪 session evidence
- `ivyhouseTerminalPty.rotateArtifacts` 可在新 workflow 任務開始前主動 rotate current files；workflow bootstrap 建議固定帶 `reason="new-workflow"`
- rotated 檔命名為 `<artifact>.<timestamp>.<ext>`，例如 `codex_pty_debug.20260318T101530Z.jsonl`
- 每種 artifact 只保留最近 `ivyhouseTerminalPty.rotationMaxHistory` 組 rotation

### 主判讀面

- `codex_pty_debug.jsonl`
- `copilot_pty_debug.jsonl`

這兩份 structured debug jsonl 才是 PTY 主路徑的 authoritative evidence。

workflow 之後若要判定 `start / send / submit / verify / smoke / close / recovery` 是否成功，應優先讀這兩份檔，而不是舊的 `monitor_debug.jsonl`、`codex_last.txt`，或只靠 transcript 肉眼判斷。

### 輔助 transcript

- `codex_pty_live.txt`
- `copilot_pty_live.txt`

這兩份檔主要給人類追 transcript、看 prompt echo 與失敗前後文，不建議單獨拿來當 workflow pass/fail 的唯一依據。

### 快速狀態面

- `ivyhouseTerminalPty.showRecoveryStatus`

這個 command 可以快速顯示 recovery state、lastError 與 artifact path，但它不是 durable artifact，不能取代 `*_pty_debug.jsonl`。

### rotated history

- rotated debug/live 檔只保留最近幾輪 session evidence，方便回溯上一輪 start/restart 前的狀態
- workflow 與 preflight 的預設主判讀面仍是固定檔名的 current files，不應直接改讀 rotated history

## Stable Event 類別

目前可視為 PTY monitor / capture 契約一部分的 logical event 類型包括：

- session / lifecycle：`terminal_created`、`pty.session.closed`、`pty.close.wait.started`、`pty.close.wait.succeeded`、`pty.close.wait.failed`、`pty.process_exit.expected`
- startup readiness：`pty.keyboard_protocol.changed`、`pty.startup.signals`、`pty.startup.semantic_ready`、`pty.startup.ready`
- send / submit：`pty.submit.settle_wait`、`send_text_result`、`send_submit_result`
- verify / smoke：`pty.verify.started`、`pty.verify.succeeded`、`pty.verify.failed`、`pty.smoke.step.*`、`pty.smoke.iteration.*`
- command / recovery / fallback：`pty.command.started`、`pty.command.succeeded`、`pty.command.failed`、`pty.state.changed`、`pty.retry.*`、`pty.rebuild.*`、`pty.fallback.*`、`pty.manualActionRequired`

相對地，`stdout_data`、`stderr_data`、`write_input`、`process_exit` 這類 low-level trace 目前仍有用，但更適合當 debug signal，不建議 workflow 直接把它們當唯一成功條件。

## 實作不變條件

下面這些規則不能被破壞：

- 不要混用 `raw text + CSI u Enter`
- 不要把 raw `\r` 當成 Codex 在 `CSI u` 模式下的正式 submit 契約
- 不要把 `terminal.sendText` / active terminal / `sendSequence` 帶回新工具主路徑

## 目前的 backend profile 假設

- `codex` 與 `copilot` 共用同一份 smoke spec：`pong` 與 `smoke-ok`
- `codex` 仍維持 `csi-u-text + csi-u-enter` 主路徑；`copilot` 的正式契約則是 `direct-text + carriage-return + focused composer probe gate`
- 若未來兩者在 startup-ready marker、submit transport 或 recovery policy 上繼續分化，差異應限制在 profile 層調整，不回滾共用 runtime 結構

## 目前尚未完成

- fallback backend 已能在使用者同意後被 PTY recovery flow 真正啟動，但 verify / smoke 等較高階流程仍未完整自動接手
- recovery state machine 還是最小版本，尚未涵蓋所有 workflow case
- 尚未處理真正的 reload reconnect
- 尚未保證長 prompt、多行、非 ASCII、interrupt、paste-heavy 場景

## 啟動 ready 判定

新工具現在不會只因為 PTY stdin 可寫就立刻送第一個 prompt。

目前第一輪 prompt 會等到這些條件都成立才放行：

1. backend 已啟用 `CSI u` keyboard protocol
2. 已從啟動畫面看到語意化 ready marker：header、已解析完成的 model 行，以及 prompt/status UI（例如 `context left`）
3. 在上述 marker 出現後，再額外 debounce `ivyhouseTerminalPty.startupReadyDebounceMs` 毫秒

這是為了避免第一個 prompt 在 UI 還沒真正起來前就先被送進去，同時降低只靠「靜默時間」判定帶來的 race。

就 monitor / capture 契約而言，**只有 `pty.startup.ready` 才代表 session 已進入可安全送第一個 prompt 的狀態**。

## 主路徑判定摘要

### Start

- 不應只因 terminal 建起來或 stdin 可寫就算成功
- 至少要走到 `pty.startup.ready`

### Send

- 以 `send_text_result.ok === true` + `pty.command.succeeded(command="send")` 為準

### Submit

- 以 `send_submit_result.ok === true` 為準
- `codex` 的正常主路徑應優先看到 `csi-u-text + csi-u-enter`
- `copilot` 的正常主路徑應優先看到 `direct-text + carriage-return`，且 fresh session 應先通過 `composer_input_probe.succeeded`

### Verify

- 以 `pty.verify.succeeded` + `pty.command.succeeded(command="verify")` 為準
- timeout 是 progress-aware，不是固定秒數硬超時

### Smoke

- 每一輪都要 fresh session
- 每一輪都要重新走到 `pty.startup.ready`
- 每一輪都要通過 `pong` 與 `smoke-ok`

### Close

- 以 `pty.close.wait.started -> pty.session.closed -> pty.close.wait.succeeded` 為準
- `pty_close_force_kill` 只是 safety-net 介入證據，不是成功條件

## 目前可跑的 smoke 路徑

目前已補上可直接呼叫的 smoke test command：

- `ivyhouseTerminalPty.smokeTest`
- `ivyhouseTerminalPty.smokeTestCodex`
- `ivyhouseTerminalPty.smokeTestCopilot`

它現在預設會連跑 `ivyhouseTerminalPty.smokeIterationCount` 次，而且每一輪都會重建 fresh PTY session，因此每輪都會重新經過 startup gating。單輪會依序執行：

1. 重建 PTY session，並重新等待 startup-ready
2. 送出 `reply with exactly pong` 並等待 `pong`
3. 送出 `reply with exactly smoke-ok` 並等待 `smoke-ok`

等待 `pong` / `smoke-ok` 的 timeout 現在不是單純固定秒數就直接失敗。

- `ivyhouseTerminalPty.verifyTimeoutMs` 現在代表 idle timeout：如果 Codex 在等待期間持續輸出有意義的 progress（例如 `Working` 狀態與後續內容刷新），waiter 會延長，不會因為固定 12 秒到點就過早 timeout
- `ivyhouseTerminalPty.verifyMaxTimeoutMs` 是整體上限：即使 progress 一直存在，超過這個總時間仍會失敗，避免無限等待

另外，`ivyhouseTerminalPty.send` / `ivyhouseTerminalPty.sendToCodex` / `ivyhouseTerminalPty.sendToCopilot` 都支援程式化參數 `{ text, submit }`，因此可以明確跑 `start -> send -> submit -> verify` 這條主路徑，而不是只停在骨架命令存在。

## Recovery 狀態

目前實作了最小狀態機：

- `normal`
- `retryable`
- `rebuildable`
- `prompting-fallback`
- `fallback-active`
- `fallback-declined`

可用 `ivyhouseTerminalPty.showRecoveryStatus` 查看兩個 backend 各自的 session、最後錯誤與 artifact 路徑。

這些狀態目前也屬於 monitor / capture 契約的一部分：

- `retryable`：可先 retry
- `rebuildable`：應優先 rebuild，不應繼續沿用舊 session
- `prompting-fallback`：PTY 已不足，應先問使用者是否同意 fallback
- `fallback-active`：user 已同意，且 fallback terminal / bridge 已被接手流程啟動
- `fallback-declined`：必須停在 manual-action-required，而不是 silent fallback

### consented fallback handoff

目前 `ivyhouseTerminalPty.enableFallback` 與 rebuild failure prompt 不再只是記錄 accepted 狀態。

- PTY side 會真正啟動 fallback runtime 與 bridge
- 若最後一步是安全可重放的 `send` / `submit`，會直接交由 fallback runtime 接手
- 若最後一步不適合自動重放（例如 verify / smoke 的局部步驟），則會把 fallback runtime 準備完成，並留在 manual continuation 狀態

相關 PTY debug event 會以 `pty.fallback.*` 類型落到 `*_pty_debug.jsonl`，其中 handoff 完成後的 recovery state 會轉成 `fallback-active`。

## 與 Legacy Capture 的關係

舊 monitor extension 已在 migration cleanup 中移除。

目前應這樣理解：

- PTY：主路徑的 send / submit / monitor / capture / verify / smoke evidence
- fallback：主路徑不可用時，承接 legacy-style send / capture / verify 的最小能力

## 打包

在此資料夾執行：

```bash
npm -s exec --yes @vscode/vsce package -- --allow-missing-repository --skip-license
```
