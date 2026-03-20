# SESSION-HANDOFF

> 建立日期：2026-03-16
> 狀態：Archived - milestone handoff

## Current goal

這輪 submit semantics 驗證已完成。最終目標已從「比較 `csi-u-enter` / `Ctrl+S`」收斂為固定 Copilot PTY 的穩定契約，並確認目前工作樹中的 `startCopilot -> verifyCopilot -> smokeTestCopilot` 可穩定通過。

## Current branch

main

## Active container mode

- Standard Dockerfile / GHCR accelerated
- Debian GNU/Linux 12 dev container

## Files touched

- .agent/runtime/tools/vscode_terminal_pty/extension.js
- tests/test_copilot_composer_gate_regression.py
- .service/terminal_capture/copilot_pty_debug.jsonl
- .service/terminal_capture/copilot_pty_live.txt

## What has been confirmed

- Copilot PTY 已切到獨立 backend surface，workspace settings 內的 `ivyhouseTerminalPty.copilotCommand` 已固定為絕對路徑：`/home/vscode/.vscode-server-insiders/data/User/globalStorage/github.copilot-chat/copilotCli/copilot`，不再依賴 extension host 的 PATH。
- `waitForOutputMatch` 的 waiter bug 已修正：`lastProgressAt` 不再沿用舊 session 的 `lastOutputAt`，而是從本次 request 的 `startedAt` 開始計時；先前那種送出 submit 後 10ms 級別就 `PTY_VERIFY_TIMEOUT` 的假 timeout 已被定位成 runtime bug，而不是 Copilot 回應問題。
- Copilot fresh session 的穩定基線為：`freshPromptDelayMs: 1500`，之後再進 focused composer probe gate；不再依賴純 delay 猜 timing。
- Copilot smoke spec 已從原本的 reverse/devowel prompt 改成和其他 backend 一致的 exact-match 題型：`reply with exactly pong` / `reply with exactly smoke-ok`。
- Copilot 的最終送字/submit 契約已固定為：`textMode: "direct-text"` + `submitMode: "carriage-return"`。
- 在 `Ctrl+S` submit 配置下，前端實測雖然 `startCopilot` 與 `verifyCopilot` 可成功，但 `smokeTestCopilot` 會失敗；原因不是 session 起不來，而是 Copilot CLI 內 `Ctrl+S` 會進入 command surface。
- 使用者已明確確認：Copilot CLI 中的 `Ctrl+S` 會顯示 command 選項，不是 Enter action，因此 `Ctrl+S` 已被判定為錯誤 submit semantics。
- `csi-u-enter` 也已被排除為最終 submit 方案；它沒有成為穩定的 Copilot composer submit path。
- 真正的 fresh-session 問題不在 binary 啟動，而在 Copilot composer 還沒進入可見且可輸入狀態時，prompt 可能被 UI 狀態吞掉或變成 hidden input。
- 目前 `.agent/runtime/tools/vscode_terminal_pty/extension.js` 內的 Copilot profile 狀態為：`submitMode: "carriage-return"`、smoke spec 為 `pong/smoke-ok`、`freshPromptDelayMs: 1500`，且 `composerInputGate` 預設為 `attempts: 4`、`timeoutMs: 1800`、`retryDelayMs: 500`。
- focused composer probe gate 的關鍵行為已驗證：在 fresh rebuilt Copilot session 中，先 `terminal.show(false)` 把 Copilot PTY 帶到前景，再送 probe；只有 probe echo 成功才放行真正 smoke prompt。
- 最新前端驗證已確認：`startCopilot` 成功、`verifyCopilot` 成功、`smokeTestCopilot` 成功；debug evidence 已看到 `composer_input_probe.succeeded`、`pong`、`smoke-ok`。
- 回歸測試已補上：`tests/test_copilot_composer_gate_regression.py` 驗證 Copilot profile 仍保留 `direct-text + carriage-return`、`freshPromptDelayMs: 1500`，以及 focused probe-echo gate wiring。
- 全量 `pytest` 已通過，作為這輪 submit/gate 修正後的回歸檢查。

## What was rejected

- 不再把 `Ctrl+S` 當 Copilot CLI 的 submit。原因：實測 transcript 與使用者手動確認都指出它會打開 Copilot CLI command 選項，而不是執行 Enter submit。
- 不再把 `csi-u-enter` 當 Copilot CLI 的 submit。原因：這條路沒有形成穩定的 Copilot composer submit 行為，最終可驗證成功的是 `carriage-return`。
- 不再把原本 Copilot smoke prompt 的 reverse/devowel 題型視為必要驗證。原因：它們增加了 prompt 相容性雜訊，不能有效隔離 submit path 問題。
- 不再把 verify 的瞬間 timeout 當成 Copilot 本身不回應。原因：那是 PTY waiter 的起始時間邏輯錯誤，已在 runtime 修正。
- 不再假設 `copilot` binary 會自動出現在 extension host PATH。原因：前面已遇過 start 失敗，且絕對路徑配置已證明是較穩定的做法。
- 不再只靠增大 fresh-session delay 修 Copilot。原因：delay-only 不能穩定保證 composer 真正接受輸入；真正有效的是 focused probe-echo gate。
- 不再把 hidden-input 假說當成可接受工作模式。原因：即使 `direct-text` 已寫入 PTY，如果 composer 沒進入可輸入狀態，手動 Enter 也不會穩定執行 smoke prompt。

## Next exact prompt

請先讀這份 handoff，不要重做前面的 `Ctrl+S` / `csi-u-enter` submit 分析。現在把 Copilot PTY 的 active truth 視為已定版：`direct-text + carriage-return + focused composer probe gate + freshPromptDelayMs: 1500`。後續如果要繼續 migration，重點應放在 active docs/config/source hygiene 同步；只有在新的回歸出現時，才重新打開 submit semantics 分析。

## Risks

- 目前工作樹是 dirty 的，而且有大量與本任務無關的 `.agent/skills/**`、docs、tests 變更；不要為了這輪 Copilot PTY 測試去 reset 或整理那些檔案。
- `.service/terminal_capture/copilot_pty_debug.jsonl` 與 `.service/terminal_capture/copilot_pty_live.txt` 已累積多輪測試內容；讀 artifact 時必須只看最新尾段，不能混入舊 run。
- Copilot CLI 的 submit 路徑現在雖已穩定，但仍依賴 focused composer probe gate；如果未來有人改動 `terminal.show(false)`、probe echo matcher 或 gate 參數，前端 smoke 可能再度退化。
- live transcript 對 Copilot composer 狀態的保真度低，真正的判讀應以最新 `copilot_pty_debug.jsonl` 為主。

## Verification status

- 已驗證：`copilotCommand` 絕對路徑設定已在 workspace 生效；Copilot waiter timing bug 已修；Copilot smoke prompt 已簡化；`Ctrl+S` 與 `csi-u-enter` 都不是最終 submit semantics。
- 已驗證：目前 source code 中 Copilot profile 使用 `direct-text + carriage-return`，並保留 `freshPromptDelayMs: 1500`。
- 已驗證：focused composer probe gate 已接入 fresh smoke session，且預設收斂為 `attempts: 4`、`timeoutMs: 1800`、`retryDelayMs: 500`。
- 已驗證：前端 `startCopilot -> verifyCopilot -> smokeTestCopilot` 可通過，最新 debug evidence 已看到 `composer_input_probe.succeeded`、`pong`、`smoke-ok` 與 `pty.command.succeeded(command="smokeTest")`。
- 已驗證：`tests/test_copilot_composer_gate_regression.py` 通過，且全量 `pytest` 通過。
