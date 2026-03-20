# Workflow Core Release Artifacts

> 用途：集中保存 template maintainer 在主 repo 上產生並決定納入版本歷史的正式 workflow-core release artifacts。

## 為什麼放這裡

- 這些檔案屬於 maintainer / release governance artifact，不屬於 `.agent/**` runtime surface。
- downstream workflow 不需要把這些 release note 與 metadata 當成 live contract 直接讀取。
- 把它們放在 `maintainers/` 下，能和 handoff、archive、SOP、release history 一起維護。

## 收錄內容

- `workflow-core-release-<release-ref>.metadata.json`
- `workflow-core-release-<release-ref>.md`
- `workflow-core-release-<release-ref>.json`

## 規則

- 正式 release chain 產出的 artifacts 應預設寫入此資料夾。
- 若該 release 需要保留可追溯紀錄，應直接納入 git。
- temp / isolated snapshot repo 產出的驗證 artifacts 不應混入此目錄，除非它們被明確升格成正式 maintainer record。
