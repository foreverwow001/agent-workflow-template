# [專案名稱] - 系統開發核心守則

> ⚠️ **請將此檔案客製化為你的專案規則**
> 
> 此檔案是 AGENT_ENTRY.md 的必讀檔案之一，所有 Agent 都必須遵守這些規則。

---

## 1. 核心溝通與行為規範

- **語言規範：** [繁體中文 / English / 其他]
  - 所有對話、程式碼註解、文檔說明，使用指定語言
- **確認機制：** 在執行任何程式碼撰寫或架構變更前，**必須先複述一次需求**，並詢問使用者確認
- **遇到困難時的應對：**
  - 若連續 2 次修正錯誤失敗，**禁止**盲目嘗試
  - **必須**使用搜尋工具，搜尋「截至目前最新的解決方案」或相關 GitHub Issue
  - 回報時請說：「我嘗試修復但失敗了，根據最新的網路資訊，問題可能出在...，建議我們改用...方法。」

---

## 2. 系統架構策略

- **架構模式：** [請選擇並填入]
  - [ ] Monorepo (單一儲存庫)
  - [ ] Multi-repo (多儲存庫)
  - [ ] Monolith (單體架構)
  - [ ] Microservices (微服務)

- **主要技術棧：**
  - **Backend:** [Python / Node.js / Go / Java / ...]
  - **Frontend:** [React / Vue / Streamlit / Next.js / ...]
  - **Database:** [PostgreSQL / MongoDB / MySQL / Redis / ...]
  - **Deployment:** [Cloud Run / AWS / Azure / Vercel / ...]

- **資料庫策略：** [請描述資料庫設計原則]

---

## 3. 開發流程與部署

- **Git Flow：**
  1. **Local Dev:** 本地修改代碼
  2. **Local Test:** **必須**在本地測試無誤
  3. **Confirmation:** 確認功能正常後，才可執行 Push
  4. **Deployment:** [描述部署流程]

- **分支策略：**
  - `main` - 生產環境
  - `develop` - 開發環境
  - `feature/*` - 功能分支
  - `hotfix/*` - 緊急修復

- **Commit 訊息規範：** 遵循 Conventional Commits
  - `feat: 新增功能`
  - `fix: 修復問題`
  - `refactor: 重構`
  - `docs: 文件更新`
  - `test: 測試相關`
  - `chore: 雜項`

---

## 4. 開發技術規範

### 檔案長度規範（分級制）

| 檔案類型 | 建議上限 | 嚴禁超過 |
|---------|---------|---------|
| **主程式** (app.py, main.py) | ≤ 600 行 | 800 行 |
| **UI 模組** (ui/*.py) | ≤ 500 行 | 600 行 |
| **業務邏輯** (core/*.py, scripts/*.py) | ≤ 400 行 | 500 行 |
| **工具模組** (utils/*.py) | ≤ 300 行 | 400 行 |
| **測試檔案** (tests/*.py) | ≤ 500 行 | 1000 行 |

### 程式碼規範

- **檔案註釋：** 每個檔案第一行必須說明該檔案用途、職責
- **模組化路由：** 程式碼須按功能拆分（如 `/modules/parsers/`, `/modules/core/`）
- **命名規範：** 
  - Python: `snake_case`
  - JavaScript: `camelCase`
  - 類別: `PascalCase`
  - 常數: `UPPER_CASE`

### 前端規範（如適用）

- **視覺風格：** [描述品牌色系、設計規範]
- **操作回饋：** 所有耗時操作必須有 Loading 動畫與 Toast 提示

---

## 5. 資安與敏感資料

- **絕對禁止：** 嚴禁將 API Key、密碼、Token 直接寫入源碼（這是天條！）
- **強制規範：** 所有敏感資料必須透過 `.env` 環境變數讀取
- **Mock Data：** 本地開發一律使用模擬數據，確保無 Key 也能運行測試

### `.env` 範例

```bash
# API Keys
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...

# Feature Flags
ENABLE_DEBUG=false
```

---

## 6. Agent 自動化規範

為確保跨 Session 開發的連續性，避免重複開啟終端機：

### 連線持久化 (Session Persistence)

- ✅ **強制紀錄**：啟動長效型程序（如 `codex`, `npm run dev`, `streamlit`）時，Agent 必須將其 `Command ID` 與 `Process Name` 寫入 `.agent/active_sessions.json`
- ✅ **優先重用**：在執行指令前，先檢查 `.agent/active_sessions.json`，若有可用的 `Command ID` 則優先使用

### QA 自動化標準

- 雖然可以重用終端，但 QA 驗證邏輯仍須封裝為獨立腳本（如 `tests/verify_xxx.py`），以確保測試的可重複性與非互動式執行

---

## 7. 專案特定規範

> 請在此補充專案特有的規則、限制或最佳實踐

### [自訂章節 1]
- [規則內容]

### [自訂章節 2]
- [規則內容]

---

## 📝 修訂歷史

| 日期 | 版本 | 修訂內容 | 修訂者 |
|------|------|---------|--------|
| YYYY-MM-DD | 1.0 | 初版建立 | - |

---

**⚠️ 客製化完成後，請刪除所有 `[請填入...]` 提示訊息**
