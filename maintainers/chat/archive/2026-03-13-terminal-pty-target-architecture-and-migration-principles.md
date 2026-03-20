# Terminal PTY 目標架構與遷移原則

> 建立日期：2026-03-13
> 狀態：Archived - superseded by `maintainers/chat/2026-03-19-terminal-tooling-source-map.md` and `.agent/runtime/tools/vscode_terminal_pty/README.md`
> 用途：把 terminal tooling 的主目標、fallback 定位、啟動時機與遷移邊界正式定成單一基準，避免後續實作繼續受舊文件的暫時性假設干擾。

> 2026-03-19 補註：本文件保留 terminal-tooling 架構收斂時的歷史脈絡，但不再承擔 active 規則來源角色。現在要看現行 maintainer 入口，請讀 `maintainers/chat/2026-03-19-terminal-tooling-source-map.md`；要看 PTY / fallback 的 live contract，請直接讀 runtime README。

---

## 1. 這份文件的地位

這份文件處理的不是單次 debug 結果，而是之後所有 terminal tooling 相關實作都要遵守的**目標架構**。

從這一刻開始，若文件之間出現衝突，terminal tooling 的主從關係、fallback 邊界、啟動時機與 migration 方向，應以本文件為準。

### 本文件明確取代的舊假設

- 不再把 `injector / monitor / orchestrator` 視為未來長期並存的三件式主工具。
- 不再把「PTY 先做、legacy 三件式先各自保留」視為長期目標；那只是一段過渡狀態。
- 不再把「是否移除 Copilot extension-side fallback」當成目前最重要的結尾決策；這只是現行 runtime safety net 的設定問題，不是架構主問題。

---

## 2. 一句話結論

未來 workflow 中的 `send prompt + submit enter + monitor/capture + workflow automation glue`，目標都應由 `.agent/runtime/tools/vscode_terminal_pty` 承接為**唯一主路徑**；目前的 `injector / monitor / orchestrator` 則應被收斂成一個**單一 fallback tool**，只在 PTY 不可用時，經使用者明確同意後才按需啟動。

---

## 3. 目標架構

### A. 主路徑：Terminal PTY

`.agent/runtime/tools/vscode_terminal_pty` 是未來 workflow 的正式主工具。

它最終要承接的能力包括：

- 啟動與維護 `codex` / `copilot` PTY session
- 對 PTY session 送 prompt
- 以 PTY-native 方式送 submit / enter
- 落地 transcript、debug event、verify 與 smoke evidence
- 提供 workflow 所需的 monitor / capture 契約
- 提供 recovery / retry / rebuild / fallback prompt 的前端協調點

### B. 備援路徑：合併後的單一 fallback tool

目前的 `injector / monitor / orchestrator` 不會作為三個長期獨立產品保留。

它們的未來定位是：

- 把仍有保留價值的 legacy 能力收斂到**一個** fallback tool
- 這個工具只作為 PTY 主路徑失效時的替代方案
- 它不是新的主架構，也不是平行主路徑

### C. 不接受的最終狀態

下面這些都不是目標：

- PTY 與 Injector/Monitor/Orchestrator 長期四件並存
- runtime 正常情況下仍預設走 sendText / Proposed API / bridge
- 發生 PTY 失敗時自動 silent fallback 到 legacy backend
- 保留三套各自獨立維護的 legacy 文檔與操作心智模型

---

## 4. fallback 工具的定位與啟動原則

### A. fallback 不是主工具

合併後的單一 fallback tool 只在以下條件成立時才有介入資格：

- PTY 無法啟動
- PTY 已啟動但無法完成必要的 send / submit / monitor 行為
- PTY recovery / rebuild 後仍無法回到可工作的狀態

### B. fallback 不預先常駐

合併後的單一 fallback tool 不應：

- 在 VS Code 開啟 workspace 時自動啟動
- 在 session 建立時自動啟動
- 在 reload window / restart window 時自動啟動
- 只是因為「可能之後會用到」就先起來待命

它應該是**按需啟動**的工具，而不是背景常駐基礎設施。

### C. fallback 必須先詢問使用者

當 PTY 不可用時，agent 應：

1. 說明 PTY 失敗在哪一層
2. 說明目前可改用 merged fallback tool
3. 詢問使用者是否要改走 fallback

只有在使用者明確同意後，fallback tool 才能啟動並接手該次工作。

若使用者拒絕：

- workflow 應停在可解釋的 recovery / manual-action-required 狀態
- 不可偷偷換 backend 繼續做

---

## 5. 遷移原則

### 原則 1：先把主路徑做完整，再收斂 fallback

PTY 不只要能「送進去」，還要能完整承接：

- send prompt
- submit enter
- monitor / capture
- verify / smoke
- workflow automation glue

只有當這些能力已轉進 PTY 主路徑，legacy 才能真正退到 fallback。

### 原則 2：legacy 能力以功能收斂，不以套件數量保留

之後要保留的是能力，不是套件數量。

因此 migration 的方向不是：

- 保留 Injector
- 保留 Monitor
- 保留 Orchestrator

而是：

- 盤點三者哪些能力在 PTY 主路徑成熟前仍有保留價值
- 把這些能力收進同一個 fallback tool
- 讓使用者與 agent 只需要理解「PTY 主路徑 + 單一 fallback tool」兩層結構

### 原則 3：不以自動啟動換取表面穩定

fallback tool 若在開 session、reload 或 restart 時就自動啟動，會模糊主/備援邊界，讓後續很難判讀到底是哪條路徑真的在工作。

因此寧可要求 agent 在失敗時明確詢問，也不要把 fallback 做成背景常駐補丁。

### 原則 4：文件與實作必須使用同一套主從關係

文件不能再持續描述：

- Injector 是主注入工具
- Monitor 是主監測工具
- Orchestrator 是 workflow glue 主體

這些描述若還出現在後續維護文檔裡，只能作為歷史分析，不應再作為新實作的依據。

---

## 6. 對目前實作階段的直接含義

### 已經成立的事

- `.agent/runtime/tools/vscode_terminal_pty` 已是新的主架構起點
- Codex / Copilot 的雙 backend PTY runtime 已有直接 evidence
- Copilot-specific submit/gating 已收斂到 `direct-text + carriage-return + focused composer probe gate`，不再是當前主阻塞

### 還沒完成，但下一步必須對準的事

- 把已落地的 PTY monitor / capture 契約繼續往 workflow / operator 文件收斂
- 把 workflow automation glue 從舊 orchestrator 思維轉成 PTY 主路徑思維
- 定義 merged fallback tool 的最小功能面
- 決定哪些 legacy code 只是過渡資產，哪些要真的搬進 fallback tool

### 不再作為主問題追的事

- 是否立即移除某個單一 runtime safety net 設定
- 是否暫時仍保留某個 Copilot close fallback delay
- 是否再把已關帳的 submit parity / close timeout 問題重開

這些屬於 operational tuning，不是目標架構本身。

---

## 7. 對現有文檔的處理原則

依本文件，`maintainers/chat` 下的文檔應分成三類：

### A. 保留並修正

- 保留那些仍有證據價值、handoff 價值、或治理分析價值的文件
- 但若它們還沿用舊的 terminal tooling 主從關係，就要加註或改寫

### B. 保留但視為歷史分析

- 例如 workflow / 治理分析文件
- 可以保留，但必須避免再被誤用為 terminal tooling 的最新架構基準

### C. 刪除

- 若文件的主要用途已被本文件與較新的 summary / handoff 完整取代
- 且它的核心前提仍停留在 Codex-only 或三件式過渡邊界
- 則應直接刪除，避免未來維護時被舊前提誤導

---

## 8. 下一階段的實作排序

1. 先以 PTY 主路徑為中心，把已存在的 monitor / capture 契約繼續收斂進 workflow glue 與 operator 文件。
2. 再盤點 injector / monitor / orchestrator 的遺留能力，整理成 merged fallback tool 的需求清單。
3. 明確定義 agent 在 PTY 失敗時的詢問流程、接受 fallback 後的行為，以及拒絕 fallback 後的停止狀態。
4. 等 PTY 主路徑與 merged fallback tool 都定型後，再回頭刪除或降級舊三件式的剩餘文檔與入口。

---

## 9. 摘要結論

這份文件把後續實作的方向收斂成兩句話：

- `.agent/runtime/tools/vscode_terminal_pty` 是未來 workflow 的唯一主路徑。
- `injector / monitor / orchestrator` 的未來不是繼續三件並存，而是收斂成一個按需啟動、需經使用者同意的 fallback tool。

之後若有新的文檔、handoff、implementation note 與這兩句話衝突，應優先修正文件，而不是繼續沿用舊假設。
