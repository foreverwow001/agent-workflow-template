# SESSION-HANDOFF

## 目前目標

在已完成的 dual-backend PTY runtime evidence 基礎上，正式把後續目標收斂成：`terminal pty` 取代現行 workflow 主路徑，而 `injector / monitor / orchestrator` 未來則整併成單一、按需啟動、需經使用者同意的 fallback tool。

## 目前分支

main

## 目前容器模式

- Standard Dockerfile / GHCR accelerated
- Debian GNU/Linux 12 dev container

## 本輪涉及檔案

- maintainers/chat/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md
- maintainers/chat/2026-03-13-pty-status-summary-and-next-steps.md
- maintainers/chat/handoff/2026-03-12-dual-pty-followup-handoff.md

## 已確認事項

- 前端 command surface 已可同時操作兩個 backend：`startCodex`、`startOpenCode`、`smokeTestCodex`、`smokeTestOpenCode` 都已成功執行。
- Codex 與 OpenCode 可同時存活於各自獨立的前端 terminal。
- 兩個 backend 的並行前端 smoke 已成功；可參考 `.service/terminal_capture/pty_smoke_frontend_summary.txt`。
- 在 OpenCode PTY 存活期間，Codex PTY 仍可接受手動 prompt 與 submit。
- 前端 command surface 已將手動 prompt `reply with exactly pong` 分別送到兩個 PTY。
- Codex 已在 `.service/terminal_capture/codex_pty_live.txt` 中明確輸出 `pong`。
- OpenCode 已在 `.service/terminal_capture/opencode_pty_live.txt` 中明確輸出 `pong`。
- OpenCode 的 startup gating 現在已改由 profile-specific semantic-ready detection 成功通過，不再走先前的 timeout 路徑。
- 2026-03-13 這輪 appended-log soak 中，Codex `restart` 與 3 輪 `smokeTest` 再次成功，且 iteration 邊界只看到 expected-close 後重建 session，沒有新的 close-timeout 噪音。
- 2026-03-13 這輪 appended-log soak 中，Codex smoke 明確走 `csi-u-text` + `csi-u-enter`，並在送出前記錄 `pty.submit.settle_wait(delayMs=140)`。
- 2026-03-13 這輪 appended-log soak 中，OpenCode `restart` 與 3 輪 `smokeTest` 雖成功完成，但補查 debug startup 後，已確認前端其實收到了 `ESC[>5u`；先前看到的 `direct-text` + `carriage-return` 是 extension 只接受 `ESC[>7u` 的偵測缺口，不是最終產品結論。
- `.service/terminal_capture/real_opencode_csi_u_acceptance.json` 仍記錄一次 `csi-u-text + csi-u-enter` 成功命中 `pong`；現在可和 `ESC[>5u` startup 證據一起判讀為「OpenCode 具備 CSI-u 路徑，但前端漏判」。
- post-reload rerun 已確認：OpenCode `restart` 成功，startup 會記錄 `pty.keyboard_protocol.changed(enabled=true, modeValue=5)`，且 3 輪 `smokeTest` 的 `send_text_result` / `send_submit_result` 已全部轉成 `csi-u-text` + `csi-u-enter`。
- 同一輪 rerun 中沒有再出現新 session 建立後 prompt 寫回舊 sessionId 的情況；先前 stale-session desync 已被修正。
- reload 後再補跑一次 OpenCode `restart` 與 `smokeTest`，已確認 close barrier 也正常收斂：每輪 iteration close 邊界都記錄 `pty_close_force_kill`，接著落到 `process_exit(signal="SIGKILL")`、`pty.session.closed`、`pty.close.wait.succeeded`，沒有新的 `pty.close.wait.failed(timeout)`。
- 之後再優化 `.agent/runtime/tools/vscode_terminal_pty/codex_pty_bridge.py` 的 staged shutdown 後，新的 OpenCode session 已改成直接走 `process_exit(signal=null)`、`pty.session.closed`、`pty.close.wait.succeeded`，不再出現新的 `pty_close_force_kill`；先前殘留的 4 個歷史 orphaned `opencode` process 也已清理，清理後再跑 3 組 `restart + smokeTest` 與最後一個補充 `restart`，orphan 計數仍維持 0。
- 進一步評估 extension 端 fallback 後，`.agent/runtime/tools/vscode_terminal_pty/extension.js` 已把 OpenCode 的 `pty_close_force_kill` 延後到 `1500ms`，Codex 仍維持 `500ms`。根據最近 appended log，新的 OpenCode close 在約 `204ms` 到 `307ms` 完成，所以這次調整是把 fallback 降級成更後面的 safety net，而不是更早介入。
- 之後又做了一次受控驗證：暫時把 workspace 的 `ivyhouseTerminalPty.opencodeCloseForceKillDelayMs` 設成 `0` 後再跑 `restart + smokeTest`，新增區段仍只看到 `process_exit(signal=null)`、`pty.session.closed`、`pty.close.wait.succeeded`，沒有新的 `pty_close_force_kill`、`pty.close.wait.failed`，orphan 計數也維持 0。驗證完成後，workspace override 已移除。
- `.agent/runtime/tools/vscode_terminal_pty/extension.js` 已在本輪修正三件事：1. CSI-u enable 改為接受 `ESC[>Nu`，不再只接受 `ESC[>7u`；2. OpenCode startup ready 改為等待 CSI-u；3. create/new-session 路徑會先清 stale state，並阻止 stale session 繼續接管 output / write。
- OpenCode profile 的 provisional `140ms` settle delay 已移除；若修正後 rerun 仍證明需要，再以 OpenCode 自身證據單獨回補。
- 架構決策已正式收斂：未來 workflow 中的 send prompt / enter / monitor / automation glue 都以 `.agent/runtime/tools/vscode_terminal_pty` 為主路徑；現行 `injector / monitor / orchestrator` 不再作為長期三件並存工具，而是待整併成單一 fallback tool。
- merged fallback tool 的啟動原則也已定清楚：它不會在開 session、reload window、restart window 時自動啟動，只會在 PTY 不可用時，由 agent 先詢問使用者是否同意後才按需啟動。

## 已明確排除的判讀

- 不把先前 apply_patch 造成的 delete/recreate UI 視為真正的 git delete；那只是工具層級的整檔替換痕跡，不代表有意移除 `.agent/runtime/tools/vscode_terminal_pty/extension.js`。
- 不再把 OpenCode 前端 `direct-text` + `carriage-return` 視為功能邊界；現已找到 root cause 是 CSI-u enable 偵測只接受 `>7u`。
- 不再把 OpenCode provisional `140ms` settle-delay 視為待定共用常數；在沒有 OpenCode 自身證據前，它不應繼續沿用 Codex 理由。
- 不再把 OpenCode repeated `pty.close.wait.failed(timeout)` 視為單純 soak 風險；timeout 後 stale-session write 代表 lifecycle correctness 問題。
- 不再把 `injector / monitor / orchestrator` 視為長期要三件並存的主工具；它們之後只應以 merged fallback tool 的形式存在。
- 不接受 silent fallback；PTY 不可用時必須先問使用者，而不是直接切到 legacy path。

## 下一個可直接使用的 prompt

從 `maintainers/chat/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md` 與 `maintainers/chat/2026-03-13-pty-status-summary-and-next-steps.md` 接續。不要再把 OpenCode submit parity、close barrier、orphan leakage、或單一 fallback delay 參數當成主問題。下一步請集中處理：1. PTY 主路徑的 monitor / capture 正式契約；2. 現行 injector / monitor / orchestrator 要如何整併成單一 fallback tool；3. fallback tool 必須按需啟動，且只有在 PTY 不可用時由 agent 先詢問使用者是否同意使用。

## 風險

- OpenCode submit parity 已由 post-reload rerun 關帳；目前沒有證據需要為它恢復 `140ms` settle delay。
- OpenCode close lifecycle 已被 bridge staged shutdown 與較長 soak 驗證；若之後要再優化，方向應是評估 extension 端 force-kill fallback 是否仍有必要，而不是重新追 barrier resolve bug。
- OpenCode 已不再保留 provisional `140ms` settle delay；若 rerun 後真的出現 Enter suppression，再以 OpenCode 專屬證據回補。
- TUI 工具的 real-CLI transcript artifact 噪音偏高；若沒有仔細區分 prompt echo 與實際回應，容易產生錯誤信心。
- 真正還沒完成的是 PTY 主路徑的產品化契約與 merged fallback tool 的能力邊界，而不是單一 runtime bug。

## 驗證狀態

- 已驗證：兩個 backend 的前端 `start` 與 `smokeTest`、獨立 terminal 建立、backend-aware 日誌分流、對兩個 PTY 的明確手動 prompt send/submit、兩邊都明確輸出 `pong`，以及 Codex clean expected-close 路徑。另已補到 OpenCode `ESC[>5u` startup 證據與一次 real-CLI `csi-u-text + csi-u-enter` 命中 `pong` 的 artifact。
- 尚未完成：PTY monitor / capture 正式契約、workflow automation glue 向 PTY 主路徑轉移，以及 merged fallback tool 的最小功能面與使用者同意流程。
