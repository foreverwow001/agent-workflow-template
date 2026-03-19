# Code Review Checklist

## 用途

這份 checklist 用來補齊 `code_reviewer.py` 無法完全自動判斷的 review 面向。

## 建議順序

1. 先閱讀 `code_reviewer.py` 的 JSON 輸出。
2. 先處理 `fail` 類問題，再看下面 checklist。
3. 最後把自動 findings 與人工判斷整合成 review comment。

## Checklist

### Correctness

- 變更是否真的符合需求？
- 有沒有明顯的 branch / null / empty input 邊界情況漏掉？
- 回傳值、例外與 side effects 是否一致？

### Security

- 有沒有把輸入直接帶進 shell / SQL / 動態執行？
- 有沒有新增 hardcoded secret、token、測試帳密？
- 權限、路徑、檔案刪除操作是否過於寬鬆？

### Maintainability

- 函式是否過長或責任混雜？
- 命名是否清楚、是否需要拆分 helper？
- 註解是否只解釋「做什麼」，而沒有補充「為什麼」？

### Error Handling

- 例外處理是否過寬（例如 bare except）？
- 發生失敗時，訊息是否足夠讓人定位問題？
- 有沒有吞掉錯誤卻不留下任何觀測資訊？

### Tests

- 若變更牽涉業務邏輯，是否有對應測試？
- 新增邏輯是否至少有 happy path + edge case coverage？
- 如果這次沒補測試，review comment 是否有明確指出缺口？
