# Merged Fallback Tool V1 Spec

> 建立日期：2026-03-13
> 狀態：Archived - superseded by `maintainers/chat/2026-03-19-terminal-tooling-source-map.md` and `.agent/runtime/tools/vscode_terminal_fallback/README.md`
> 用途：作為 `.agent/runtime/tools/vscode_terminal_fallback` 的正式規格文件，整合先前的 requirements、design 與 implementation checklist。
>
> 若本文件與較早的 fallback draft 衝突，以本文件為準。

> 2026-03-19 補註：active fallback scope 與 operator-facing contract 已回收到 `.agent/runtime/tools/vscode_terminal_fallback/README.md`。本文件自此只保留歷史規格脈絡，不再承擔 active spec 角色。

---

## 1. 角色定位

`.agent/runtime/tools/vscode_terminal_fallback` 是 PTY 主路徑失效時的單一 legacy fallback adapter。

它的角色只有三個：

- 在 PTY 不可用時重建 legacy terminal
- 對 legacy terminal 提供最小的 programmatic send / submit 能力
- 提供最小 capture、legacy verify 與 localhost bridge 相容面

它不是第二套 terminal 平台，也不是新的 combined workflow runtime。

---

## 2. 固定前提

以下前提已視為固定，不再在後續文件中重新討論：

1. `.agent/runtime/tools/vscode_terminal_pty` 是唯一主路徑。
2. fallback 不是平行主路徑。
3. fallback 不會在 VS Code 啟動、workspace 開啟、reload、restart window 時自動常駐。
4. PTY 失敗時，agent 必須先詢問使用者是否同意 fallback；不可 silent fallback。
5. `/workflow/start` 與 `/workflow/status` 已正式退休，不屬於 fallback roadmap。
6. combined workflow loop、QA PASS cleanup 自動化與治理 log 流程不進 v1。

---

## 3. Package 與 Namespace

### A. Package identity

- 目錄：`.agent/runtime/tools/vscode_terminal_fallback/`
- npm `name`：`ivyhouse-terminal-fallback`
- `displayName`：`IvyHouse Terminal Fallback`
- `publisher`：`ivyhouse-local`

### B. VS Code namespace

- command namespace：`ivyhouseTerminalFallback.*`
- configuration namespace：`ivyhouseTerminalFallback.*`

不再引入或延續：

- `ivyhouseTerminalInjector.*`
- `ivyhouseTerminalMonitor.*`
- `ivyhouseTerminalOrchestrator.*`

---

## 4. V1 Scope

### A. 必保留能力

#### 1. Terminal lifecycle

- `startCodex`
- `restartCodex`
- `startCopilot`
- `restartCopilot`
- 可選 `startAll`
- `resetSessionState`

#### 2. Programmatic send surface

- `sendToCodex`
- `sendToCopilot`
- `sendLiteralToCodex({ text, submit })`
- `sendLiteralToCopilot({ text, submit })`
- 內部統一層：`sendLiteral({ terminalKind, text, submit })`

#### 3. Legacy capture / verify surface

- `captureCodexOutput`
- `autoCaptureCodexStatus`
- `restartAndCaptureCodexStatus`
- `verifyCodexStatusInjection`
- `showDiagnostics`

#### 4. Bridge compatibility

- `GET /healthz`
- `POST /send`
- token auth
- localhost-only bind
- rate limit
- payload / request size guard
- audit log

### B. 明確不納入 v1 的能力

- combined workflow loop / orchestration state machine
- `POST /workflow/start`
- `GET /workflow/status`
- QA PASS cleanup prompt
- 新的 governance automation
- PTY 主路徑本身的 retry / recovery / reconnect 問題

---

## 5. Artifact 與相容面

### A. V1 保留的 legacy artifact 路徑

- `.service/terminal_capture/monitor_debug.jsonl`
- `.service/terminal_capture/codex_live.txt`
- `.service/terminal_capture/copilot_live.txt`
- `.service/terminal_capture/codex_last.txt`
- `.service/terminal_capture/sendtext_bridge_events.jsonl`
- `.service/sendtext_bridge/token`

### B. Artifact 語意

這些路徑只屬於 fallback / legacy compatibility surface。

它們不是 PTY 主路徑的 authoritative artifact。

PTY 主路徑仍以：

- `codex_pty_debug.jsonl`
- `copilot_pty_debug.jsonl`
- `codex_pty_live.txt`
- `copilot_pty_live.txt`

作為正式觀測面。

### C. Legacy verify 邏輯

v1 保留既有 `/status` 驗證心智：

- `hasStatusEcho`
- `hasContextLeft`
- `hasCodexSignal`
- `hasPastedOverlay`

也就是說，`analyzeCodexStatusCapture` 這類 legacy one-shot capture 判讀仍屬 fallback v1 一部分。

---

## 6. 啟動與同意契約

### A. 啟動條件

fallback 只在下列條件成立時才可介入：

1. PTY 無法啟動
2. PTY 已啟動但無法完成必要的 send / submit / monitor 行為
3. PTY recovery / rebuild 後仍無法回到可工作狀態

### B. 使用者同意流程

當 PTY 失敗時，agent 必須：

1. 說明 PTY 失敗在哪一層
2. 說明可改用 fallback，但 fallback 只提供 legacy send / capture / verify 能力
3. 詢問使用者是否同意啟動 fallback

若使用者拒絕：

- fallback 不啟動
- workflow 停在 `manual-action-required` 或同等可解釋狀態

若使用者同意：

- PTY side 應真正觸發 fallback handoff，而不是只記錄 accepted 狀態
- 至少要完成 fallback terminal / bridge 就位
- 若最後一步是安全可重放的 `send` / `submit`，可直接由 fallback runtime 接手
- 若最後一步不適合自動重放，則應明確停在 manual continuation，而不是假裝 fallback 已完整完成原本的 PTY verify / smoke

---

## 7. 與歷史三件式的關係

舊的 injector / monitor / orchestrator 已刪除。

它們留下的保留價值，現在只應被理解成歷史能力來源：

- Injector：legacy terminal lifecycle + sendLiteral pattern
- Monitor：legacy capture + `/status` verify pattern
- Orchestrator：bridge auth / rate limit / audit log pattern

後續若需要追設計脈絡，應看 archive 文檔，而不是重新恢復三件式命名空間。

---

## 8. 實作與驗收基準

fallback v1 至少應滿足：

1. 使用者在 PTY failure 後明確同意，fallback 才會啟動。
2. 可重建 Codex / Copilot legacy terminal。
3. 可對 Codex / Copilot 送出 programmatic text + submit。
4. 可做 legacy capture。
5. 可做 legacy `/status` 驗證。
6. `GET /healthz` 與 `POST /send` 可用。
7. 現有 bridge client 不需再恢復 `/workflow/*` 才能工作。
8. README 與 maintainer 文檔不再把 fallback 寫成第二主架構。

---

## 9. 文件連動

目前與本規格直接相關的 authoritative 文檔：

1. `maintainers/chat/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md`
2. `maintainers/chat/2026-03-13-pty-monitor-and-capture-contract.md`
3. `maintainers/chat/2026-03-13-preflight-migration-plan.md`

較早的 requirements、design、implementation checklist 草稿已完成整併，應移至 archive 作為歷史參考。
