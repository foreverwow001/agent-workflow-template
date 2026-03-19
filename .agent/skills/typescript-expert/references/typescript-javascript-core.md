# TypeScript / JavaScript Core

## 代碼品質原則

- Readability first：先讓人看得懂，再談聰明抽象
- KISS：優先最簡單可工作的方案
- DRY：抽共用邏輯，但不要為了抽象而抽象
- YAGNI：沒有當前需求就不要預建複雜延伸點

## 核心標準

### 命名

- 變數名稱要描述意圖，例如 `marketSearchQuery`、`isUserAuthenticated`
- 函式優先使用動詞-名詞結構，例如 `fetchMarketData`、`calculateSimilarity`
- 避免單字母、過度縮寫與語意不明的旗標名

### 不可變性

- 更新 object / array 時優先使用 spread、map、filter
- 不要直接 mutate React state 或共享資料結構

### 錯誤處理

- `async` 函式要處理失敗路徑，不要假設 API 一定成功
- 對外錯誤訊息要穩定，不要把底層 exception 直接暴露成產品介面

### Async / Await

- 可獨立並行的操作優先 `Promise.all`
- 避免不必要的 sequential await
- 對 cancellation / timeout / loading state 要有明確策略

### 型別安全

- 優先定義 interface / type 描述資料邊界
- 避免 `any`；必要時優先 `unknown` + narrowing
- 對 public API、component props、hook return value 提供明確型別
