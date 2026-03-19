# TypeScript API And Testing

## API / Node 邊界

### REST 約定

- 路徑、方法、狀態碼要一致
- response 結構要穩定，成功與錯誤都要可預測

### 輸入驗證

- 在 request 邊界驗證 body / query / params
- 不要把未驗證輸入直接丟進 service / DB / template / shell

## 檔案組織

- components、hooks、lib、types、api client 分層清楚
- 檔案名稱遵守既有專案慣例；沒有既有慣例時，component 用 PascalCase、utility 用 camelCase

## 測試標準

- 測試名稱要描述行為與情境，不要用 `works`
- 優先 AAA 結構：Arrange / Act / Assert
- 對 edge case、error path、fallback path 要有覆蓋

## 常見 Code Smell

- 長函式
- 深層巢狀
- 魔法數字 / 字串
- 無型別或 `any` 蔓延
- component 過胖
- 直接 mutate state
