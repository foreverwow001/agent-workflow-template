# Legacy Terminal Tooling 刪除前清單

> 建立日期：2026-03-13
> 狀態：Archived - historical blocker snapshot
> 用途：在真正刪除 `tools/vscode_terminal_injector`、`tools/vscode_terminal_monitor`、`tools/vscode_terminal_orchestrator` 之前，明確列出尚未完成的遷移項、受影響檔案，以及建議拆分的 migration patch。

---

## 1. 先回答核心問題

### 結論

**目前還不能刪。**

而且不只是因為 fallback 還沒搬完，更因為 **template workflow 本身還沒有正式把 `.agent/runtime/tools/vscode_terminal_pty` 升成主要的 send prompt + submit enter + monitor/capture 工具**。

### 這件事是否也應寫進刪除前清單？

**是，必須寫，而且應該列為刪除前的 0 號 blocker。**

如果 PTY 還沒成為 template workflow 的正式主路徑，就直接刪 legacy 三件式，等於把目前文件、安裝腳本、Coordinator 規則與 preflight 心智模型一起打壞。

---

## 2. 現況判定：PTY 是否已搬入 template workflow 主路徑？

### 判定

**還沒有。**

### 直接證據

1. Template README 仍把 legacy 三件式寫成目前主路徑。
   - `README.md`
   - 目前文字仍是「主路徑是兩個 local VS Code extensions：Injector + Monitor，Orchestrator 保留為 legacy 相容」。

2. Workflow 入口文件原本把 send/monitor 規則綁在 Injector/Monitor。
   - `.agent/workflows/AGENT_ENTRY.md`
   - `.agent/workflows/dev-team.md`
   - 目前仍要求 `extension-sendtext-required` 與 `proposed-primary-with-extension-fallback`。

3. Coordinator 角色規則原本明寫「所有 Codex/OpenCode 操作必須透過 Injector extension sendText」。
   - `.agent/roles/coordinator.md`

4. 安裝與 bootstrap 原本仍以 legacy 安裝腳本為中心。
   - `.agent/runtime/scripts/vscode/install_terminal_orchestrator.sh`
   - `.agent/runtime/scripts/devcontainer/post_create.sh`
   - `doc/NEW_MACHINE_SETUP.md`
   - `doc/ENVIRONMENT_RECOVERY.md`
   - `doc/HOME_OFFICE_SWITCH_SOP.md`

5. workspace settings 原本仍殘留 legacy 設定鍵。
   - `.vscode/settings.json`
   - 目前仍有 `ivyhouseTerminalOrchestrator.sendtextBridgeEnabled` 與 `ivyhouseTerminalInjector.autoStartCodexPtyPrototype`。

6. fallback README 原本自己也明寫 workflow loop / `/workflow/start` / `/workflow/status` 還沒搬完。
   - `.agent/runtime/tools/vscode_terminal_fallback/README.md`

### implication

這些判定反映的是建立此 checklist 當下的狀態；之後 Patch A/B/C/E/F 已陸續落地，下面的 blocker 狀態應以本文件更新後的註記為準。

所以「刪 legacy 三件式」之前，先把 PTY 升格為 template workflow 主路徑，是硬性前置作業。

---

## 3. 刪除前 blockers 總表

### Blocker 0. 把 PTY 正式升成 template workflow 主路徑

狀態：**已完成**

這是刪除 legacy 三件式之前的首要條件。

需要完成：

- workflow 文件不再要求 `ivyhouseTerminalInjector.*`
- workflow 文件不再把 monitor fallback 當主監測面
- README / onboarding / recovery 都以 `ivyhouseTerminalPty.*` 為主要操作面
- 安裝腳本不再以 legacy 三件式為中心命名與敘事
- preflight / fallback 語意與 README 對齊

### Blocker 1. fallback 尚未承接 orchestrator 的剩餘能力邊界

狀態：**已部分完成**

目前已正式退休：

- `POST /workflow/start`
- `GET /workflow/status`

目前不再保留：

- workflow loop / orchestration state machine
- legacy QA PASS cleanup prompt

這代表 orchestrator 仍有歷史實作可供參考，但上述能力已不再是 fallback roadmap。

### Blocker 2. legacy extension 之間仍有直接程式依賴

狀態：**已完成**

原本存在：

- `tools/vscode_terminal_monitor/extension.js` 直接呼叫 `ivyhouseTerminalInjector.sendLiteralToCodex`
- `tools/vscode_terminal_monitor/extension.js` 直接呼叫 `ivyhouseTerminalInjector.restartCodex`
- `tools/vscode_terminal_injector/extension.js` 仍會等 `ivyhouseTerminalMonitor.ping`

這些直接呼叫已在 Patch F 切斷；現在三件式的剩餘問題以歷史文件與刪除順序為主，不再是直接 runtime 耦合。

### Blocker 3. 安裝與維運路徑仍明確要求安裝 legacy 三件式

狀態：**已完成**

目前已完成：

- `.agent/runtime/scripts/vscode/install_terminal_tooling.sh` 成為 PTY-primary 主入口
- `.agent/runtime/scripts/vscode/install_terminal_orchestrator.sh` 已降級為 shim
- recovery / new machine / home-office SOP 已切換到新 installer

說明：active installer、devcontainer、workspace recommendations 與換機/recovery 流程都已切到 PTY + fallback；legacy 套件不再屬於預設安裝面。

### Blocker 4. settings / docs / changelog 仍殘留 legacy 為主的操作心智

狀態：**已完成**

說明：active settings、README、workflow docs、recovery docs 與 bridge client 都已改成 PTY primary / fallback by consent；殘留的 legacy 引用只存在於歷史 maintainer 文檔、changelog 與待刪除資料夾本身。

### Patch G readiness

狀態：**ready**

目前已完成：

- PTY 已成為 template workflow 唯一主路徑
- fallback 邊界已明確收斂，`/workflow/start` 與 `/workflow/status` 已正式退休
- legacy extension 直接 runtime 依賴已切斷
- installer / devcontainer / workspace recommendations 不再預設安裝 legacy 三件式
- 全 repo 掃描結果顯示，剩餘 legacy 提及僅屬歷史/存檔用途

結論：就 repo 的 active behavior 而言，已達到可安全刪除 `tools/vscode_terminal_injector`、`tools/vscode_terminal_monitor`、`tools/vscode_terminal_orchestrator` 的狀態。

---

## 4. 建議拆分的 migration patch

以下 patch 是「刪除前作業」建議切法，不是一次大爆改。

### Patch A. Workflow 主路徑切換到 PTY

目標：把 template workflow 的正式規則從 `Injector + Monitor` 改成 `Terminal PTY primary + fallback by consent`。

建議一起改的檔案：

- `README.md`
- `.agent/workflows/AGENT_ENTRY.md`
- `.agent/workflows/dev-team.md`
- `.agent/roles/coordinator.md`
- `.agent/VScode_system/Ivy_Coordinator.md`
- `.agent/VScode_system/tool_sets.md`
- `.agent/VScode_system/chat_instructions_ivy_house_rules.md`
- 任何仍明寫 `IvyHouse Injector` / `IvyHouse Monitor` 為主路徑的 `.agent/**` 文件

這個 patch 完成後，repo 才能說「PTY 已搬入這個 template 的 workflow 中，成為主要的送 prompt + enter + monitor 工具」。

### Patch B. Installer / Bootstrap 切換

目標：把安裝與 bootstrap 從「legacy 三件式」改成「PTY + Fallback」。

建議一起改的檔案：

- `.agent/runtime/scripts/vscode/install_terminal_orchestrator.sh`
  - 可選策略 1：直接改內容但保留舊檔名一段時間
  - 可選策略 2：新增新檔名（例如 `install_terminal_tooling.sh`），舊檔保留 shim
- `.agent/runtime/scripts/devcontainer/post_create.sh`
- `doc/NEW_MACHINE_SETUP.md`
- `doc/ENVIRONMENT_RECOVERY.md`
- `doc/HOME_OFFICE_SWITCH_SOP.md`

建議這個 patch 同時決定：

- 是否保留舊安裝腳本作為 shim
- PTY 與 fallback 是否都要在 bootstrap 時安裝
- fallback 是否只安裝、不自動啟動

### Patch C. Workspace Settings / Preflight 對齊

目標：把 workspace 設定與 preflight 敘事切到 PTY primary。

建議一起改的檔案：

- `.vscode/settings.json`
- `.agent/runtime/scripts/vscode/workflow_preflight_check.py`
- `.agent/runtime/scripts/sendtext_bridge_client.py`

這個 patch 要處理的不是只有程式碼，還包含語意：

- PTY 是 authoritative 主路徑
- fallback 是條件式、需經使用者同意
- `/workflow/start` 與 `/workflow/status` 若未保留，client 與文件都要降級說明

### Patch D. Legacy Docs 降級與 retirement 標記

目標：把 legacy 三件式從「主工具」降級成「過渡期 fallback 能力來源」。

建議一起改的檔案：

- `tools/vscode_terminal_injector/README.md`
- `tools/vscode_terminal_monitor/README.md`
- `tools/vscode_terminal_orchestrator/README.md`
- `doc/AGENT_WORKFLOW_TEMPLATE_UPSTREAM.md`
- `CHANGELOG.md`
- `maintainers/chat/archive/2026-03-13-merged-fallback-tool-draft-lineage.md`

### Patch E. Fallback 能力補齊或正式宣告不保留

目標：決定 orchestrator 剩餘能力哪些要搬、哪些正式退休。

至少要明確決議：

- `/workflow/start`
- `/workflow/status`
- workflow loop
- legacy cleanup prompt

若決議不保留，也必須同步修改：

- `.agent/runtime/scripts/sendtext_bridge_client.py`
- 相關 README / maintainer docs

### Patch F. Legacy 互相依賴切斷

目標：讓 monitor / injector / orchestrator 變成真正可刪，而不是彼此 still-linked。

建議一起改的檔案：

- `tools/vscode_terminal_monitor/extension.js`
- `tools/vscode_terminal_injector/extension.js`
- 任何仍直接 `executeCommand("ivyhouseTerminalInjector...`)` 或 `executeCommand("ivyhouseTerminalMonitor...`)` 的 runtime

完成這個 patch 之前，不能安全刪其中任何一個資料夾。

### Patch G. 真正刪除 legacy 三件式

只有在 A-F 全部完成，且做過至少一輪 reload + preflight + fallback 驗證後，才進到這個 patch。

建議動作：

- 刪除 `tools/vscode_terminal_injector`
- 刪除 `tools/vscode_terminal_monitor`
- 刪除 `tools/vscode_terminal_orchestrator`
- 移除所有殘留命令名、設定鍵、安裝步驟、文件連結

---

## 5. 建議的提交順序

建議不要直接做一個「砍三個資料夾」的大 commit。

比較合理的提交順序：

1. `docs/workflow`: 把 PTY 升成 template workflow 主路徑
2. `bootstrap/install`: 切換安裝腳本與環境回復流程
3. `settings/preflight`: 清掉 legacy 為主的設定與操作心智
4. `fallback-boundary`: 補齊或正式退休 orchestrator 剩餘能力
5. `legacy-decouple`: 切斷 injector/monitor/orchestrator 互相依賴
6. `remove-legacy-terminal-tools`: 真正刪資料夾

---

## 6. 這份清單對目前決策的直接含義

### 是否可以立刻開始做所有刪除前作業？

**現在不應直接整批開做。**

因為目前最前面的 blocker 是：

> PTY 還沒正式搬進 template workflow，成為主要的送 prompt + enter + monitor 工具。

在這件事完成之前，後面所有刪除前作業都只能算是「局部整理」，不能進到真正 retirement 階段。

### 所以這件事是不是應該寫進刪除前清單？

**是，而且已經列成 Blocker 0。**

---

## 7. 最短結論

要刪 `injector / monitor / orchestrator` 之前，先完成兩件事：

1. 讓 PTY 真正成為 template workflow 的正式主路徑。
2. 讓 fallback 與剩餘 legacy 能力邊界被正式收斂或正式退休。

在這之前，legacy 三件式最多只能降級，不能直接刪除。
