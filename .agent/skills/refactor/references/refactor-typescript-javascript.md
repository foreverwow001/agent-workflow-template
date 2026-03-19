# Refactor TypeScript / JavaScript

## 優先修法

- 將過胖 component 拆成 render layer + hook / helper
- 用 guard clauses 取代多層條件巢狀
- 以 type / interface 清楚定義邊界，逐步消滅 `any`
- 抽出重複的 API response parsing、validation、mapping 邏輯
- 將魔法字串與旗標狀態改成具名常數或 enum-like 型別

## React / Node 注意事項

- 重構 state 更新時不得引入 mutation
- 抽 hook 時要確認副作用邊界與依賴陣列仍正確
- 拆 API handler 時，先把 validation、service、response mapping 分開
- 若 refactor 會影響 public props / response shape，這已不是單純 behavior-preserving refactor
