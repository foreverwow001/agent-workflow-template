# SESSION-HANDOFF

## 目前目標

不要再把這輪工作主線放在 PTY runtime bug 修補；目前真正的下一步，是把 `.agent/runtime/tools/vscode_terminal_pty` 從「已驗證可行的 runtime」往「正式主路徑契約」推進。今晚最建議直接接的工作，是先定義 `PTY monitor / capture` 正式契約，讓後續 workflow 能以 PTY artifact / event 作為主觀測面，再往 merged fallback tool 需求整理前進。

## 目前分支

main

## 目前容器模式

- Standard Dockerfile / GHCR accelerated
- Debian GNU/Linux 12 dev container

## 本輪涉及檔案

- maintainers/chat/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md
- maintainers/chat/2026-03-13-pty-status-summary-and-next-steps.md
- maintainers/chat/handoff/2026-03-12-dual-pty-followup-handoff.md
- maintainers/chat/handoff/2026-03-13-terminal-pty-next-step-handoff.md
- maintainers/index.md

## 已確認事項

- `maintainers/chat/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md` 仍是目前 terminal tooling 的權威基準；本次建立 handoff 前已重新讀過最新內容。
- 當前架構方向已固定成兩層：`.agent/runtime/tools/vscode_terminal_pty` 是唯一未來主路徑；`injector / monitor / orchestrator` 只應收斂成單一 fallback tool。
- fallback tool 的原則已定：不能在 session 開啟、reload、restart window 時自動啟動；只有在 PTY 不可用時，且 agent 先詢問使用者同意後才可啟動。
- OpenCode submit parity、close barrier、orphan leakage、以及 extension-side fallback delay 是否保留，現在都不是主問題；除非有新的 post-fix evidence，否則不要重開。
- `maintainers/chat/2026-03-13-pty-status-summary-and-next-steps.md` 已把下一階段主線收斂成四塊：PTY monitor/capture 契約、workflow glue 主體轉移、merged fallback tool 邊界、agent fallback 問答流程。
- 若今晚要只做一件最有價值的事，優先順序應是先補 `PTY monitor / capture` 正式契約，再談 fallback tool 需求整理。
- handoff 目錄目前可直接銜接的最新文件，已改成這份 2026-03-13 handoff；maintainer index 也已同步指向它。
- repo 目前仍有不少與本工作無關的 unstaged 變更；接續時不要順手整理其他檔，除非任務真的需要。

## 已明確排除的判讀

- 不要再把 PTY 與 injector / monitor / orchestrator 視為長期平行主路徑。
- 不要把單一 safety-net 參數調整，誤當成 terminal 架構是否可繼續前進的前提。
- 不要在沒有新 runtime 證據的情況下，重新追 OpenCode submit parity、close barrier 或 orphan 問題。
- 不要讓 fallback tool 變成 silent fallback 或背景常駐補丁。
- 不要忽略目前工作樹裡其他人或其他流程留下的未提交修改；這輪若只做 maintainer docs，就維持這個邊界。

## 下一個可直接使用的 prompt

請以 `maintainers/chat/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md` 與 `maintainers/chat/2026-03-13-pty-status-summary-and-next-steps.md` 為準，直接處理下一步主線：起草一份新的 maintainer 文檔，檔名建議為 `maintainers/chat/2026-03-13-pty-monitor-and-capture-contract.md`。先讀 `.agent/runtime/tools/vscode_terminal_pty/extension.js`、`.agent/runtime/tools/vscode_terminal_pty/README.md`，必要時再對照 fallback README 與 git history，盤點目前 PTY 已落地的 artifact / debug event / verify / smoke 判讀點，以及歷史 legacy capture 曾承擔的觀測責任。然後輸出一份正式契約，至少要回答：1. workflow 之後應以哪些 PTY artifact / event 作為 authoritative evidence；2. send、submit、verify、smoke 各自的成功與失敗判定規則；3. 哪些舊 monitor 能力已可由 PTY 取代、哪些仍屬 fallback；4. 需要連動修訂哪些 maintainer docs 或 README。除非讀 code 時發現新的 post-fix evidence，否則不要重開 OpenCode submit parity、close barrier、orphan leakage、或 fallback delay 的討論。

## 風險

- `PTY monitor / capture` 契約還沒正式落文件，現在最容易發生的風險不是 runtime 壞掉，而是後續文件或實作又被舊 monitor / orchestrator 心智模型拉回去。
- repo 內仍有一些對外 README 或 legacy 說明沒有完全收斂到新架構；寫契約文件時需要區分「歷史描述」與「新的 authoritative 規則」。
- 目前工作樹有其他未提交變更，若今晚擴大成整 repo 清理，容易誤碰不相干的修改。
- 目標架構文今天已出現過後續編輯；正式下筆前，仍應再讀一次最新內容，不要直接依賴舊摘要記憶。

## 驗證狀態

- 已驗證：重新讀過最新的目標架構文與 PTY summary；確認 handoff 目錄與 maintainer index 現在都可指向這份新交接。
- 尚未驗證：這一輪沒有再執行新的 PTY runtime 命令，也沒有新增任何 code-path 測試；本 handoff 只處理文件交接與下一步收斂。
