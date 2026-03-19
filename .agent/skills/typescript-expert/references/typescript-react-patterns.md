# TypeScript React Patterns

## 元件結構

- component 保持薄，盡量只做 render orchestration
- 複雜邏輯移到 hook 或 helper
- props 要有清楚型別與合理預設

## State 更新

- 對依賴前值的 state 更新使用 functional update
- 避免 stale closure 問題
- 不要在狀態更新流程中直接 mutate 既有資料

## 條件渲染

- 優先清楚的 guard / `&&` rendering
- 避免多層 ternary 造成可讀性崩壞

## Hooks

- hook 名稱使用 `useXxx`
- hook 專注處理一種狀態或一條 side-effect boundary
- 對回傳值提供明確型別與穩定 shape
