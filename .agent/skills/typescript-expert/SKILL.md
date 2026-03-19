---
name: typescript-expert
description: "TypeScript and JavaScript implementation guidance for Engineer. Use when writing or refactoring .ts, .tsx, .js, or .jsx files, building React or Node code, defining API boundaries, improving async handling, or tightening type safety."
---

# TypeScript Expert

提供 Engineer 在 TypeScript / JavaScript 任務中的實作標準與決策框架，重點是可維護、可驗證、型別清楚的程式碼。

## 何時使用

當任務符合任一條件時，Engineer 應載入本 skill：

- 新增或修改 `.ts`、`.tsx`、`.js`、`.jsx`
- 實作 React / Node.js / API handler / 前端狀態邏輯
- 需要補強型別、安全的 async 寫法或前端/後端結構一致性
- User 要求用 TypeScript/JavaScript 撰寫或重構程式碼

## 核心要求

- 命名必須清楚，避免單字母與語意模糊縮寫
- 優先不可變資料更新，避免直接 mutate state / shared object
- Async 邏輯要明確處理錯誤；可並行就不要不必要地序列 await
- TypeScript 優先使用明確型別；避免 `any`，必要時要有理由
- React component、hook、API handler 都要維持單一責任與清楚邊界
- 輸入資料要在邊界驗證，不要把未驗證資料一路傳進核心邏輯

## Engineer 工作流

1. 先讀 [references/typescript-javascript-core.md](./references/typescript-javascript-core.md) 掌握命名、不可變性、錯誤處理、async 與型別安全。
2. 若是 React 任務，再讀 [references/typescript-react-patterns.md](./references/typescript-react-patterns.md)。
3. 若是 API / Node / service 任務，再讀 [references/typescript-api-and-testing.md](./references/typescript-api-and-testing.md)。
4. 確認 repo 現有 TS/JS 結構、命名與測試風格，不要硬套外部框架慣例。
5. 先把資料模型、props、API input/output 型別定清楚，再寫邏輯。
6. 對非同步、狀態更新與輸入驗證做顯式處理。
7. 若是 React，優先讓 component 保持薄，邏輯進 hook / helper。
8. 完成後再回頭檢查 code smell、測試與文件。

## 參考資料

- [references/typescript-javascript-core.md](./references/typescript-javascript-core.md)
- [references/typescript-react-patterns.md](./references/typescript-react-patterns.md)
- [references/typescript-api-and-testing.md](./references/typescript-api-and-testing.md)
