# PTY Monitor / Capture 契約

> 建立日期：2026-03-13
> 狀態：Archived - superseded by `maintainers/chat/2026-03-19-terminal-tooling-source-map.md` and `.agent/runtime/tools/vscode_terminal_pty/README.md`
> 用途：定義 `.agent/runtime/tools/vscode_terminal_pty` 目前已可作為 workflow 主觀測面的 artifact、stable event、成功/失敗判定規則，以及 legacy monitor 在主路徑轉移後仍保留的責任。
>
> 這份文件只處理 **PTY monitor / capture contract**，不是 merged fallback tool 的完整需求文。
> 若本文件與舊的 monitor / injector / orchestrator 描述衝突，凡屬 PTY 主路徑觀測契約者，以本文件為準。

> 2026-03-19 補註：active PTY contract 已回收到 `.agent/runtime/tools/vscode_terminal_pty/README.md`。本文件自此只保留歷史決策脈絡，不再作為現行 workflow / runtime 的 authoritative baseline。

---

## 1. 這份契約目前保證什麼

目前 `.agent/runtime/tools/vscode_terminal_pty` 已能穩定落地兩類 artifact：

- 給人讀的 live transcript
- 給 workflow / 自動化判讀的 structured debug event

從現有實作看，之後 workflow 若要判定 `start / send / submit / verify / smoke / close / recovery` 是否成功，**主判讀面應改讀 PTY debug jsonl，而不是 legacy monitor 的 `monitor_debug.jsonl` 或 `codex_last.txt`**。

但這份契約也明確保留幾個邊界：

- fallback backend 目前只有狀態與詢問介面，尚未真正接上 merged legacy fallback tool
- fallback backend 現在已能由 PTY recovery flow 在 user 同意後真正啟動 bridge / terminal，但 verify / smoke 等高階流程仍未完整自動承接
- reload reconnect 仍未保證
- 長 prompt、多行、非 ASCII、interrupt、paste-heavy 場景仍未列為正式保證
- 下列 low-level debug event 可保留做除錯，但**不應**被當成 workflow 的唯一 authoritative success signal

---

## 2. Authoritative Artifact

預設 artifact 都落在 `.service/terminal_capture/`。

### A. PTY 主路徑正式 artifact

| backend | human-readable transcript | structured debug evidence |
|---|---|---|
| Codex | `codex_pty_live.txt` | `codex_pty_debug.jsonl` |
| Copilot | `copilot_pty_live.txt` | `copilot_pty_debug.jsonl` |

### A-2. current 與 rotated history

- 固定檔名的 `*_pty_live.txt` / `*_pty_debug.jsonl` 是 current files，供 workflow / preflight / operator 做主判讀。
- `start` / `restart` 與顯式 `ivyhouseTerminalPty.rotateArtifacts` 會把上一輪 current files rotate 成帶 timestamp 的歷史檔，再開新的 current files。
- rotated 檔只保留最近幾輪 session evidence，供人工回溯；它們不是 workflow / preflight 的預設主判讀面。

### B. Artifact 角色分工

`*_pty_debug.jsonl`：

- workflow 自動判讀的主依據
- 用來判定 startup ready、send、submit、verify、smoke、close、recovery、fallback prompt
- 應優先依賴 stable logical event，而不是逐段解析 transcript

`*_pty_live.txt`：

- 給人類肉眼追 transcript
- 用來輔助確認 prompt echo、實際回應、UI 狀態與失敗前後文
- 不建議單獨作為 workflow pass/fail 的唯一依據

`ivyhouseTerminalPty.showRecoveryStatus` 的 output：

- 屬於 operator convenience surface
- 可快速看到 recovery state、lastError、artifact path
- 不是 durable artifact，不應取代 `*_pty_debug.jsonl`

---

## 3. Stable Event Contract

### A. JSONL 基本格式

`*_pty_debug.jsonl` 每行都是一個 JSON object，至少包含：

- `ts`
- `kind`
- `type`

只要事件和某一個 session 綁定，預期還會帶：

- `sessionId`

之後 workflow 若要做主判讀，應以 `type + kind + sessionId` 為主鍵，而不是只看單一字串片段。

### B. 可視為 stable 的 logical event 類別

下列事件可以視為目前契約的一部分：

#### Session / lifecycle

- `terminal_created`
- `pty.session.closed`
- `pty.close.wait.started`
- `pty.close.wait.succeeded`
- `pty.close.wait.failed`
- `pty.process_exit.expected`

#### Startup readiness

- `pty.keyboard_protocol.changed`
- `pty.startup.signals`
- `pty.startup.semantic_ready`
- `pty.startup.ready`

#### Send / submit

- `pty.submit.settle_wait`
- `send_text_result`
- `send_submit_result`

#### Verify / smoke

- `pty.verify.started`
- `pty.verify.succeeded`
- `pty.verify.failed`
- `pty.smoke.step.started`
- `pty.smoke.step.succeeded`
- `pty.smoke.step.failed`
- `pty.smoke.iteration.started`
- `pty.smoke.iteration.succeeded`
- `pty.smoke.iteration.failed`

#### Command / recovery / fallback

- `pty.command.started`
- `pty.command.succeeded`
- `pty.command.failed`
- `pty.artifacts.rotated`
- `pty.state.changed`
- `pty.retry.scheduled`
- `pty.retry.exhausted`
- `pty.rebuild.started`
- `pty.rebuild.succeeded`
- `pty.rebuild.failed`
- `pty.fallback.prompted`
- `pty.fallback.accepted`
- `pty.fallback.declined`
- `pty.manualActionRequired`

### C. 只建議當診斷訊號的 low-level event

下面這些事件目前有價值，但更接近 runtime trace，不建議 workflow 直接把它們當唯一成功條件：

- `pty_open`
- `spawn_failure`
- `write_input`
- `stdout_data`
- `stderr_data`
- `process_error`
- `process_exit`
- `pty_close_requested`
- `pty_close_force_kill`
- `handle_input`
- `set_dimensions`
- `set_dimensions_forward_error`
- `terminal_closed_by_vscode`

原因很簡單：這些事件偏內部實作細節，後續重構時最容易變動。

---

## 4. 成功與失敗判定規則

### A. Start 成功

workflow 不應只因 terminal 建起來或 stdin 可寫，就判定 session ready。

目前正式規則是：

1. 看到 `terminal_created`
2. 看到 `pty.keyboard_protocol.changed(enabled=true, protocol="csi-u")`
3. 看到 `pty.startup.signals`
4. 看到 `pty.startup.semantic_ready`
5. 最後看到 `pty.startup.ready`

只有 `pty.startup.ready` 才代表這個 session 已進入可安全送第一個 prompt 的狀態。

### B. Send 成功

若是單純 `send` 而不含 submit，主判定規則是：

1. `pty.command.started(command="send")`
2. `send_text_result.ok === true`
3. `pty.command.succeeded(command="send")`

若 `pty.command.failed(command="send")` 出現，應直接視為失敗，不需要再從 transcript 猜。

### C. Submit 成功

submit 的正式成功訊號是：

1. `send_submit_result.ok === true`
2. 後續沒有同 request 的 `pty.command.failed`

另外，依目前 PTY 主路徑設計，**submit transport 必須依 backend 判讀**。

因此目前建議 workflow 做這樣的判讀：

- `codex`：`send_text_result.mode === "csi-u-text"`、`send_submit_result.mode === "csi-u-enter"` 視為正常主路徑
- `copilot`：`send_text_result.mode === "direct-text"`、`send_submit_result.mode === "carriage-return"` 視為正常主路徑
- `copilot` fresh session：在 verify/smoke 前應優先看到 `pty.startup.composer_input_probe.succeeded`

例外：

- 非 printable 字元時，`direct-text-fallback` 仍可能是暫時容許的送字路徑
- close / rebuild 前後的低階診斷區段，不應用這個規則誤判

### D. Verify 成功

verify 的正式成功條件是：

1. `pty.verify.started`
2. 對應 prompt 的 `send_text_result.ok === true`
3. 對應 submit 的 `send_submit_result.ok === true`
4. `pty.verify.succeeded`
5. 外層有 `pty.command.succeeded(command="verify")`

verify 的正式失敗條件是：

- `pty.verify.failed`
- 或外層 `pty.command.failed(command="verify")`

目前 wait 規則不是固定秒數硬超時，而是：

- `verifyTimeoutMs` 是 idle timeout
- 若等待期間持續看到 meaningful progress output，timer 會延長
- `verifyMaxTimeoutMs` 是整體硬上限

因此 workflow 若要模擬 PTY 的判斷，必須理解這是「progress-aware timeout」，不是單純 `N 秒沒回就 fail`。

### E. Smoke 成功

smoke 現在是 fresh-session based contract，不是沿用舊 session。

每一輪 smoke iteration 都必須：

1. 重建 fresh PTY session
2. 再次走到 `pty.startup.ready`
3. 跑 `reply with exactly pong`
4. 跑 `reply with exactly smoke-ok`
5. 每一步都出現對應的 `pty.smoke.step.succeeded`
6. 該輪最後出現 `pty.smoke.iteration.succeeded`

整體 smoke 成功的正式條件是：

- 所有 iteration 都有 `pty.smoke.iteration.succeeded`
- 沒有任何 `pty.smoke.iteration.failed`
- 外層出現 `pty.command.succeeded(command="smokeTest")`

### F. Close 成功

close 不應只看 terminal 面板消失，而應看 barrier 是否真正收斂。

正式成功訊號：

1. `pty.close.wait.started`
2. `pty.session.closed`
3. `pty.close.wait.succeeded`

正式失敗訊號：

- `pty.close.wait.failed`

`pty_close_force_kill` 可以視為 safety-net 介入證據，但不是成功條件本身。

### G. Recovery / fallback 狀態判讀

目前 recovery state 是正式 contract 的一部分，可出現在：

- `normal`
- `retryable`
- `rebuildable`
- `prompting-fallback`
- `fallback-declined`

實務判讀：

- `retryable`：還可以先嘗試 retry
- `rebuildable`：應優先走 rebuild，而不是繼續沿用舊 session
- `prompting-fallback`：PTY 主路徑已不足，需要先問使用者要不要 fallback
- `fallback-declined`：應停在 manual-action-required，而不是 silent fallback

---

## 5. 目前 workflow 應怎麼讀 PTY evidence

### A. 建議的主判讀順序

1. 先看對應 backend 的 `*_pty_debug.jsonl`
2. 再依 `requestId + sessionId + type` 還原當次操作
3. 只有需要人工確認內容時，才回頭看 `*_pty_live.txt`

### B. 不建議再沿用的舊判讀方式

下面這些不應再是 PTY 主路徑的主要成功判讀方式：

- 只看 `monitor_debug.jsonl` 的 `proposed_api=true`
- 只看 `codex_last.txt` 是否抓到 `/status`
- 只看 terminal transcript 肉眼似乎有送出 prompt
- 只看 terminal 還活著，就認定 session 可繼續使用

---

## 6. Legacy Capture 責任現在如何理解

舊 monitor extension 已移除；下面這些責任現在應被理解成「歷史上由 legacy monitor 承擔，之後只屬 fallback / 歷史能力來源」。

| 能力 | PTY 是否已承接主路徑 | legacy monitor 目前定位 |
|---|---|---|
| backend-aware rolling transcript | 是 | 不再是 PTY 主路徑必要元件 |
| structured runtime event | 是 | 不再是 PTY 主路徑必要元件 |
| startup ready 判定 | 是 | 不再是 PTY 主路徑必要元件 |
| send / submit 成功判定 | 是 | 不再是 PTY 主路徑必要元件 |
| verify / smoke evidence | 是 | 不再是 PTY 主路徑必要元件 |
| Proposed API availability 檢查 | 否 | 保留給 legacy terminal workflow |
| shell integration fallback capture | 否 | 保留給 legacy terminal workflow |
| `codex_last.txt` 單次 capture | 否 | 保留給 legacy `/status` 類 one-shot capture |
| `analyzeCodexStatusCapture` | 否 | 仍是 legacy Codex CLI `/status` 驗證邏輯 |

換句話說，這些 legacy capture 能力最像是：

- 給舊 `Codex CLI` / `Copilot CLI` terminal workflow 的 capture extension
- 給 Proposed API / shell integration fallback 的觀測面
- 給 merged fallback tool 未來可能吸收的一部分能力來源

但它**不應再被描述成 PTY workflow 的預設主監測工具**。

---

## 7. 這份契約目前不保證的事

為了避免後續誤用，下面這些先明確排除：

- 不保證 `*_pty_live.txt` 可直接機械判讀為 pass/fail
- 不保證所有 low-level debug event 名稱都長期不變
- 不保證 reload 後沿用舊 sessionId reconnect
- 不保證 fallback backend 現在已可實際接手
- 不保證多行 / 大段 paste / 非 ASCII prompt 現在就等同正式產品契約

---

## 8. 需要連動修訂的文件

這份契約落下後，下一輪至少應連動處理：

1. `.agent/runtime/tools/vscode_terminal_pty/README.md`
   - 補上這份契約的連結
   - 把「目前輸出檔案」提升成 artifact contract 摘要

2. `.agent/runtime/tools/vscode_terminal_fallback/README.md`
   - 明確說明 fallback 的 capture / verify 邊界
   - 避免再引回已刪除的 legacy monitor 心智模型

3. `maintainers/chat/2026-03-13-merged-fallback-tool-spec.md`
   - 與 fallback 正式規格對齊 capture / verify / bridge 邊界

4. `.agent/runtime/scripts/vscode/workflow_preflight_check.py` 與相關治理文檔
   - PTY-aware + fallback-aware 的第一輪 preflight 已落地
   - 下一步是讓 workflow / governance 文件全面接受新的 aggregate output，而不是繼續沿用舊的 bridge-centric gate 心智模型

## 8.5. fallback-active 狀態補充

PTY recovery state 現在除了 `prompting-fallback`、`fallback-declined` 之外，還可能看到：

- `fallback-active`

它代表：

- user 已明確同意 fallback
- PTY side 已真正觸發 fallback handoff
- fallback bridge / terminal 已就位

但這不保證最後一步一定已被完整自動重放。

- 對 `send` / `submit` 這類安全可重放的最後一步，runtime 可以直接交給 fallback adapter 接手
- 對 verify / smoke 的局部步驟，仍可能停在 manual continuation

---

## 9. 摘要結論

從現在開始，PTY 主路徑的觀測契約應簡化成三句話：

1. workflow 的 authoritative evidence 先讀 `*_pty_debug.jsonl`
2. transcript `*_pty_live.txt` 主要給人讀，不是主判決面
3. legacy monitor 保留給舊 terminal workflow 與未來 fallback tool，不再是 PTY 主路徑預設 monitor
