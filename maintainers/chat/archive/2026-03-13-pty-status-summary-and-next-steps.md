# PTY 現況總結與後續待辦排序

> 建立日期：2026-03-13
> 用途：保留 PTY runtime 的已驗證事實與下一步實作排序。
> 搭配文件：`maintainers/chat/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md`
>
> 2026-03-13 更新：terminal tooling 的主目標、fallback 定位與合併方向，現在以「目標架構與遷移原則」文件為準；本文件專注在 runtime evidence 與依此衍生的近期待辦。

---

## 1. 一句話結論

`.agent/runtime/tools/vscode_terminal_pty` 已完成雙 backend 第一輪 runtime 驗證，足以作為未來 workflow 的主路徑基礎；接下來最重要的不是再追既有 submit / close bug，而是把 `send prompt + submit enter + monitor/capture + workflow glue` 正式收斂到 PTY 主路徑，並把現行 `injector / monitor / orchestrator` 整併成單一、按需啟動、需經使用者同意的 fallback tool。

---

## 2. 已站穩的 runtime 事實

下面這些可視為目前已驗證成立，不需要再回頭重做根因討論：

- `.agent/runtime/tools/vscode_terminal_pty` 已是新的 PTY 核心實作位置。
- Codex 主路徑的 startup gating、verify、smoke、close barrier、submit settle-delay 已有直接 runtime 證據。
- Codex 仍明確走 `csi-u-text` + `csi-u-enter`，且程式化 submit 前保留 `pty.submit.settle_wait(delayMs=140)`。
- OpenCode startup 已可正確辨識 `ESC[>5u`，不再被誤判成只能走 `direct-text` + `carriage-return`。
- OpenCode post-reload rerun 已穩定走 `csi-u-text` + `csi-u-enter`。
- OpenCode stale-session desync 已修正，不再把新 session 的 prompt 寫回舊 sessionId。
- bridge staged shutdown 上線後，新 OpenCode session 的 close 已可直接走 `process_exit(signal=null) -> pty.session.closed -> pty.close.wait.succeeded`。
- 清掉歷史 orphaned `opencode` process 後，較長 soak 沒再產生新的 orphan leakage。
- OpenCode extension-side close fallback 已被證明不是功能性必要條件，但目前設定維持現狀，這不構成主架構阻塞。

---

## 3. 不應再被當成主問題的事項

以下題目在目前證據下，已不應再作為下一輪實作主線：

- 重新追 OpenCode submit parity
- 重新追 OpenCode close barrier timeout
- 重新討論 OpenCode 是否需要沿用 Codex 的 `140ms` settle delay
- 把單一 runtime safety-net 設定變動，誤判成整體 terminal architecture 的核心決策

若未來要重開，必須有新的 post-fix evidence，而不是單靠舊的 provisional 記錄。

---

## 4. 依新架構推導出的目前缺口

既然主目標已改成「PTY 作為唯一主路徑、legacy 三件式合併成單一 fallback tool」，那目前真正還缺的是下面四塊：

### A. PTY monitor / capture 正式契約

目前 PTY 已有 transcript 與 debug event，但還缺清楚的產品化契約，例如：

- workflow 要讀哪一份 artifact 才算正式 evidence
- monitor/capture 對外暴露哪些欄位才足以替代舊 monitor
- `/status` 類 verify 與 smoke 是否完全改走 PTY artifact 判讀

### B. workflow automation glue 的主體轉移

現在 runtime 已能跑，但 workflow automation 的心智模型仍帶有舊 orchestrator 殘留：

- 誰負責發命令
- 誰負責判讀完成
- 誰負責 workflow loop / status / recovery glue

這些都要改成以 PTY 為主體，而不是預設仍從舊 bridge 思維出發。

### C. merged fallback tool 的功能邊界

接下來要整理的不是「保留哪三個工具」，而是：

- 哪些 legacy 能力在 PTY 失敗時仍有價值
- 這些能力如何收斂成一個 fallback tool
- 哪些功能可以完全退休，哪些功能要保留到 fallback tool

### D. agent 的 fallback 問答流程

依新架構，fallback 必須：

- 不在 session 開啟 / reload / restart window 時自動啟動
- 只在 PTY 不可用時才按需啟動
- 啟動前由 agent 明確詢問使用者是否同意

這代表 recovery 狀態機與文件描述都要配合這個互動邊界。

---

## 5. 現在最合理的階段判讀

目前位置應這樣描述：

1. Codex PTY prototype 可行性驗證：已完成。
2. Codex runtime 穩定化與 close/submit 關鍵修正：已完成。
3. 雙 backend PTY core 重構：第一輪已完成。
4. OpenCode submit parity、close barrier 收斂與 orphan 控制：已完成到足夠支撐架構前進的程度。
5. PTY 主路徑產品化 + merged fallback tool 收斂：現在才是主線。

因此，現在不是「繼續補單點 bug」階段，而是「把已驗證的 PTY runtime 轉成正式主架構」階段。

---

## 6. 後續待辦排序

### 第一優先：把 PTY 主路徑缺的契約補齊

先做：

1. 定義 PTY monitor / capture 的正式契約。
2. 明確 workflow 該讀哪些 PTY artifact / event 才能判定 send、submit、verify、smoke 成功。
3. 讓後續文件不再把舊 monitor 當成預設主觀測面。

### 第二優先：盤點 merged fallback tool 的需求

再做：

1. 盤點 injector / monitor / orchestrator 還有哪些能力值得保留。
2. 決定這些能力如何合併成單一 fallback tool。
3. 明確寫出 fallback tool 的啟動條件、使用者同意流程與拒絕後的停止狀態。

### 第三優先：才回頭整理舊入口與舊文檔

只有在主路徑與 fallback 邊界都站穩後，才應再做：

1. legacy tool 入口降級或移除。
2. 舊 monitor / orchestrator 專屬文檔退場。
3. 舊三件式相關 README、handoff、索引統一改寫。

---

## 7. 決策邊界

接下來做事時，應遵守以下邊界：

- 不要再把 PTY 與三件式視為長期平行主路徑。
- 不要讓 fallback tool 在 session 開啟、reload 或 restart window 時自動啟動。
- 不要讓 agent 在 PTY 失敗時 silent fallback。
- 不要把現行單一 safety-net 參數設定，誤當成架構是否前進的前提條件。
- 不要在 monitor / workflow glue 尚未搬進 PTY 主路徑前，就宣告 legacy 已可直接刪除。

---

## 8. 建議的下一個工作提示

如果下一輪要直接接著做，建議 prompt 可以收斂成：

> 以 `maintainers/chat/2026-03-13-terminal-pty-target-architecture-and-migration-principles.md` 為主架構基準，延續目前已完成的 PTY runtime evidence。不要再把 OpenCode submit parity、close barrier 或 orphan leakage 當成主問題。下一步請集中處理：1. PTY 主路徑的 monitor / capture 正式契約；2. injector / monitor / orchestrator 應如何合併成單一 fallback tool；3. fallback tool 只能按需啟動，且在 PTY 不可用時由 agent 先詢問使用者是否同意使用。
