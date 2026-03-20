# Preflight 遷移方案：PTY-aware + Fallback-aware 兩層

> 建立日期：2026-03-13
> 狀態：Archived - superseded by `maintainers/chat/2026-03-19-terminal-tooling-source-map.md`, `.agent/runtime/scripts/vscode/workflow_preflight_check.py`, and `.agent/runtime/scripts/vscode/workflow_preflight_fallback.py`
> 用途：把現有 `.agent/runtime/scripts/vscode/workflow_preflight_check.py` 的單層 legacy 檢查模型，整理成未來的兩層 preflight 架構：PTY-aware primary layer + fallback-aware compatibility layer。

> 2026-03-19 補註：preflight 的 active truth 已回到 aggregator 與 fallback layer script。本文件保留遷移背景與當時的收斂判斷，不再作為現行 preflight 規格來源。

> 2026-03-13 更新：第一輪 aggregator 重構與 clean-container 驗證已完成。`workflow_preflight_check.py` 已接上 `workflow_preflight_pty.py` 與 `workflow_preflight_fallback.py`，CLI 已支援 `--require-pty`、`--allow-pty-cold-start`、`--require-fallback`、`--pty-backends`，`--require-bridge` 也已降級為 alias warning。fallback layer 目前不再要求 Proposed API 一定為 true；只要 shell integration attachment、bridge healthz、token 與 artifact compatibility 成立，即可視為 fallback-ready。

## 0. 目前落地狀態

### 已完成

- `.agent/runtime/scripts/vscode/workflow_preflight_pty.py` 已存在並可輸出 backend-level PTY summary。
- `.agent/runtime/scripts/vscode/workflow_preflight_fallback.py` 已存在並可輸出 fallback layer summary。
- `.agent/runtime/scripts/vscode/workflow_preflight_check.py` 已完成 aggregator 化，會輸出 layer-separated JSON 與 aggregate status。
- `--require-bridge` 已只作 `--require-fallback` alias，不再主導整體 preflight 語意。
- clean-container 驗證已跑過：`post_create.sh`、`install_terminal_tooling.sh`、PTY-primary preflight 與 fallback-required preflight 都已實際驗證。
- fallback-ready 的實際判定已補成「Proposed API 或 shell integration attachment 其一可用，再加上 bridge/token/artifact 正常」。

### 尚未完成

- `proposed_api_true` 對 `.agent/runtime/tools/vscode_terminal_fallback` 仍可能是 `false`；這看起來更像 client/runtime allowlist 問題，而不是 repo 內 preflight 邏輯缺口。
- 是否要把 fallback layer 的 monitor backend status 拆成更明確的 `proposed-api` / `shell-integration` 子狀態，仍可再精煉。

---

## 1. 為什麼要拆成兩層

現在的 `workflow_preflight_check.py` 只檢查兩件事：

1. `monitor_debug.jsonl` 裡是否有 `proposed_api=true`
2. SendText Bridge 的 `healthz` 與 token 是否正常

這套模型在 legacy workflow 時合理，但在目前架構下有明顯問題：

- 它完全不知道 PTY 主路徑的 artifact 與 stable event
- 它會把 legacy bridge / monitor 的健康狀態誤當成「整體 terminal workflow ready」
- 它缺少「主路徑先判、fallback 只作次級 readiness」的層次

所以遷移方向不應是「直接在原腳本裡再多加幾個 if」，而是把 preflight 本身分成兩層。

---

## 2. 目標架構

### Layer 1: PTY-aware preflight

這是未來 workflow 的 primary readiness check。

它回答的問題是：

- PTY 主路徑是否已具備可觀測的 artifact / event 基礎
- PTY 主路徑最近是否留下可用的 authoritative evidence
- 若 PTY 目前沒有 evidence，是「尚未啟動」還是「有失敗跡象」

### Layer 2: fallback-aware preflight

這是 compatibility / backup readiness check。

它回答的問題是：

- 若 PTY 失敗，legacy fallback 所需的 monitor / bridge 能否接手
- Proposed API / shell integration / bridge 基礎是否可用

### Aggregator layer

現有 `workflow_preflight_check.py` 未來應變成 aggregator：

- 先跑 PTY-aware layer
- 再跑 fallback-aware layer
- 最後輸出一個分層結果，而不是一個混在一起的 pass/fail

---

## 3. 現有腳本的問題點

### A. 檔名與檢查內容都偏 legacy

目前核心函式：

- `_load_latest_proposed_api`
- `_check_bridge_healthz`
- `_check_bridge_token`

對 PTY 來說，這三件事都不是 primary readiness。

### B. `require_bridge` 的語意過強

現在只要 `--require-bridge`，整個 preflight 就把 bridge healthz / token 當成 fail gate。

在新架構下應改成：

- bridge readiness 只屬於 fallback-aware layer
- 除非 workflow 明確要求 fallback mode，否則不應升格為 primary failure

### C. 缺少 PTY 狀態分類

PTY-aware layer 至少要能分出：

- `ready`
- `cold`（尚未啟動或尚無 evidence）
- `degraded`
- `failed`

而不是只有布林值。

---

## 4. 建議的檔案拆分

### A. 保留 aggregator 入口

保留：

- `.agent/runtime/scripts/vscode/workflow_preflight_check.py`

但讓它只負責：

- parse args
- 呼叫兩層 preflight
- 組合結果
- 決定 CLI exit code

### B. 新增 PTY-aware layer

建議新增：

- `.agent/runtime/scripts/vscode/workflow_preflight_pty.py`

責任：

- 讀 `.service/terminal_capture/codex_pty_debug.jsonl`
- 讀 `.service/terminal_capture/copilot_pty_debug.jsonl`
- 解析 stable logical event
- 產出 PTY readiness summary

### C. 新增 fallback-aware layer

建議新增：

- `.agent/runtime/scripts/vscode/workflow_preflight_fallback.py`

責任：

- 延續現有 `monitor_debug.jsonl` proposed API 檢查
- 檢查 sendtext bridge `healthz`
- 檢查 token
- 必要時補上 fallback artifact existence checks

---

## 5. PTY-aware layer 應檢查什麼

### A. Primary artifact existence

至少檢查：

- `.service/terminal_capture/codex_pty_debug.jsonl`
- `.service/terminal_capture/copilot_pty_debug.jsonl`

但這裡的缺檔不應一律是 fail。

建議語意：

- 缺檔：`cold` 或 `unknown`
- 有檔但完全沒有 stable event：`degraded`
- 有檔且有 recent stable event：`ready`

### B. Stable event readiness

PTY-aware layer 優先讀這些 stable event：

- `terminal_created`
- `pty.keyboard_protocol.changed`
- `pty.startup.ready`
- `pty.command.succeeded`
- `pty.command.failed`
- `pty.state.changed`
- `pty.fallback.prompted`
- `pty.fallback.declined`

### C. backend-level summary

對每個 backend 分別輸出：

- `artifact_exists`
- `latest_startup_ready_ts`
- `latest_command_succeeded_ts`
- `latest_command_failed_ts`
- `latest_recovery_state`
- `status`

其中 `status` 建議為：

- `ready`
- `cold`
- `degraded`
- `failed`

### D. PTY layer 不應做的事

- 不直接要求 bridge healthz
- 不要求 `monitor_debug.jsonl` 出現 proposed_api true
- 不要求 fallback artifact 一定存在

---

## 6. fallback-aware layer 應檢查什麼

### A. Proposed API / monitor layer

保留目前邏輯：

- `monitor_debug.jsonl` 中是否有 `type=proposed_api`
- `onDidWriteTerminalData` 是否為 true

但在實際 fallback-ready 判定上，現在不再要求 Proposed API 必須是唯一可用監測後端；若 shell integration 已成功掛上，也可視為 monitor backend ready。

建議補檢：

- `shell_execution_start(hasRead=true)` 是否存在
- 是否已有 terminal attach evidence

### B. bridge layer

保留目前邏輯：

- `GET /healthz`
- `.service/sendtext_bridge/token`

### C. artifact compatibility

可選擇補檢：

- `monitor_debug.jsonl`
- `codex_live.txt`
- `copilot_live.txt`
- `codex_last.txt`

這些檢查不必全部升格為 fail，可作 warning / info。

### D. fallback layer 的 status 建議

建議輸出：

- `ready`
- `degraded`
- `unavailable`

---

## 7. Aggregator 輸出格式建議

現有輸出是單層：

- `status`
- `checks`
- `failures`
- `warnings`

未來建議改成：

```json
{
  "status": "pass|warn|fail",
  "mode": "pty-primary|fallback-required|compat-only",
  "pty": {
    "status": "ready|cold|degraded|failed",
    "checks": { ... }
  },
  "fallback": {
    "status": "ready|degraded|unavailable",
    "checks": { ... }
  },
  "failures": [...],
  "warnings": [...],
  "next_steps": [...]
}
```

關鍵點：

- `status` 是 aggregate 結果
- `pty` 與 `fallback` 必須各自有獨立狀態
- 使用者與 workflow 才知道是主路徑有問題，還是只有 fallback 有問題

---

## 8. CLI 參數遷移建議

### A. 保留舊參數

保留：

- `--repo-root`
- `--json`

### B. 調整舊 bridge 參數語意

現有：

- `--require-bridge`

建議未來改成：

- `--require-fallback`

若要保留舊參數，應只做 alias，不再把 `bridge == preflight 主體` 當作核心語意。

### C. 新增參數

建議新增：

- `--require-pty`
- `--allow-pty-cold-start`
- `--require-fallback`
- `--pty-backends codex,copilot`

這樣 workflow 才能區分：

- 我只是要檢查 PTY 主路徑是否已有 evidence
- 還是我要強制 fallback 也 ready

---

## 9. 遷移步驟

### Phase 1: 文檔與輸出模型先行

- [x] 先確定兩層 preflight 的 status model
- [x] 先確定 aggregate JSON schema

### Phase 2: 抽出 fallback-aware layer

- [x] 把現有 `_load_latest_proposed_api`
- [x] `_check_bridge_healthz`
- [x] `_check_bridge_token`
- [x] 移到 `workflow_preflight_fallback.py`

### Phase 3: 建 PTY-aware layer

- [x] 新增讀 `codex_pty_debug.jsonl` / `copilot_pty_debug.jsonl` 的函式
- [x] 新增 stable event parser
- [x] 新增 backend-level readiness summary

### Phase 4: aggregator 改寫

- [x] `workflow_preflight_check.py` 只剩 orchestration 與輸出整合
- [x] 舊 `require_bridge` 改為 alias 或 warning

### Phase 5: workflow 文檔收斂

- [x] README / maintainer 文檔改成「PTY primary, fallback secondary」
- [ ] 後續再評估是否真的需要保留 bridge-required gate 作為強制條件
- [x] workflow 治理文件是否要正式接受 fallback-ready = shell integration + bridge，而不是只盯 `proposed_api_true`

---

## 10. 摘要結論

`workflow_preflight_check.py` 未來不應再是「legacy bridge health check script」，而應該變成：

- 一個 aggregator
- 內含 PTY-aware primary layer
- 內含 fallback-aware compatibility layer

而最重要的遷移原則只有一句話：

> 先判 PTY 主路徑，再判 fallback 是否可接手；不要再把 fallback readiness 誤當成整體 workflow readiness。

## 11. 具體實作變更清單

### A. `.agent/runtime/scripts/vscode/workflow_preflight_pty.py` 預計新增的函式

建議第一版至少有：

- `load_jsonl_events(debug_file: Path) -> list[dict[str, Any]]`
- `extract_latest_event(events: list[dict[str, Any]], event_type: str) -> dict[str, Any] | None`
- `extract_latest_recovery_state(events: list[dict[str, Any]]) -> str | None`
- `summarize_backend_pty(repo_root: Path, backend: str) -> dict[str, Any]`
- `run_pty_preflight(repo_root: Path, backends: list[str], allow_cold_start: bool) -> dict[str, Any]`

這裡的 `summarize_backend_pty(...)` 應直接輸出單 backend summary，而 `run_pty_preflight(...)` 再負責組 backend-level aggregate。

### B. `.agent/runtime/scripts/vscode/workflow_preflight_fallback.py` 預計新增的函式

建議第一版至少有：

- `load_latest_monitor_proposed_api(debug_file: Path) -> dict[str, Any]`
- `inspect_shell_integration_attachment(debug_file: Path) -> dict[str, Any]`
- `check_bridge_healthz(healthz_url: str, timeout_sec: float) -> dict[str, Any]`
- `check_bridge_token(token_file: Path) -> dict[str, Any]`
- `inspect_fallback_artifacts(repo_root: Path) -> dict[str, Any]`
- `run_fallback_preflight(repo_root: Path, require_fallback: bool, healthz_url: str, timeout_sec: float) -> dict[str, Any]`

這基本上就是把現有 `workflow_preflight_check.py` 的 legacy 檢查邏輯抽出去，外加最小 artifact summary 與 shell integration fallback evidence。

### C. `.agent/runtime/scripts/vscode/workflow_preflight_check.py` 預計新增或保留的函式

建議 aggregator 最後只保留這組函式：

- `parse_args() -> argparse.Namespace`
- `run_preflight(repo_root: Path, require_pty: bool, allow_pty_cold_start: bool, require_fallback: bool, pty_backends: list[str], healthz_url: str, timeout_sec: float) -> dict[str, Any]`
- `aggregate_preflight_status(pty_result: dict[str, Any], fallback_result: dict[str, Any], require_pty: bool, require_fallback: bool, allow_pty_cold_start: bool) -> dict[str, Any]`
- `format_text_report(result: dict[str, Any]) -> str`
- `main() -> int`

建議把現有：

- `_load_latest_proposed_api`
- `_check_bridge_healthz`
- `_check_bridge_token`

全部搬出 aggregator，讓 aggregator 不再直接讀 legacy artifact。

---

## 12. 輸出 schema 具體規格

建議 `workflow_preflight_check.py --json` 的 aggregate 輸出固定至少包含：

```json
{
  "status": "pass|warn|fail",
  "mode": "pty-primary|fallback-required|compat-only",
  "repo_root": "...",
  "pty": {
    "status": "ready|cold|degraded|failed",
    "backends": {
      "codex": {
        "artifact_exists": true,
        "latest_startup_ready_ts": "...",
        "latest_command_succeeded_ts": "...",
        "latest_command_failed_ts": null,
        "latest_recovery_state": "normal",
        "status": "ready"
      },
      "copilot": {
        "artifact_exists": false,
        "latest_startup_ready_ts": null,
        "latest_command_succeeded_ts": null,
        "latest_command_failed_ts": null,
        "latest_recovery_state": null,
        "status": "cold"
      }
    },
    "checks": {}
  },
  "fallback": {
    "status": "ready|degraded|unavailable",
    "checks": {
      "proposed_api_true": {"ok": true},
      "shell_integration_attached": {"ok": true},
      "sendtext_bridge_healthz": {"ok": true},
      "sendtext_bridge_token": {"ok": true},
      "artifact_compatibility": {"ok": true}
    }
  },
  "failures": [],
  "warnings": [],
  "next_steps": []
}
```

### schema 設計原則

- `pty.backends` 必須保留 backend-level summary
- `fallback.checks` 保留 legacy-style check map，方便延續現有 operator 心智模型
- `status` 只代表 aggregate 結果，不取代 layer-level 狀態

---

## 13. CLI flags 具體規格

### 建議保留

- `--repo-root`
- `--json`
- `--healthz-url`
- `--timeout-sec`

### 建議新增

- `--require-pty`
  - 語意：PTY layer 若非 `ready`，視為 aggregate fail

- `--allow-pty-cold-start`
  - 語意：若 PTY layer 是 `cold`，可降級為 warning 而非 fail

- `--require-fallback`
  - 語意：fallback layer 若非 `ready`，視為 aggregate fail

- `--pty-backends codex,copilot`
  - 語意：指定 PTY layer 要檢查哪些 backend

### 建議保留為 alias 的舊參數

- `--require-bridge`
  - 行為：等同 `--require-fallback`
  - 額外：輸出 warning，提示名稱已改語意

---

## 14. exit code 規格

建議 exit code 先維持簡單：

- `0`：aggregate `status == pass`
- `1`：aggregate `status == fail`

若 aggregate `status == warn`，建議仍先回 `0`，讓現有 shell workflow 不會因冷啟動或 fallback warning 被硬中斷。

這點很重要，因為 PTY-aware layer 新增後，`cold` 將變成正常狀態之一；不應把它直接等同錯誤。

---

## 15. 何時可以開始實作

對 preflight 這條線來說，文檔只要做到下面這個程度，就適合開始實作：

1. layer 邊界明確
2. 函式責任明確
3. JSON schema 明確
4. CLI flags 明確
5. exit code policy 明確

以現在這份計畫來說，**第一輪骨架拆分與 clean-container 驗證已完成**。下一步不再是「能不能開始實作」，而是收尾與文件收斂，尤其是：

- workflow / governance 文件如何接受新的 aggregate output
- `proposed_api_true=false` 但 shell integration 可用時，operator 文件如何描述這是「fallback-ready」而不是故障
- 是否仍要保留 `bridge-required` 作為特定操作模式的強制 gate

不需要再回頭重做骨架，除非你要改變 public JSON schema 或 CLI flags。
