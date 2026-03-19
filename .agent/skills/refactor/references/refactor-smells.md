# Refactor Smells

## 常見 Code Smell 與優先修法

### 1. Long Function

- 先抽出純計算邏輯
- 再抽出 I/O 或副作用區塊
- 抽完後讓主流程只保留高階敘事

### 2. Duplicated Logic

- 先確認重複區塊真的語意相同
- 抽成 helper / utility / shared service
- 避免為了 DRY 過度抽象

### 3. God Module / Large Class

- 依責任拆成數個明確模組
- 讓每個模組只負責一個邊界清楚的能力
- 先拆讀取/轉換/寫入，再拆 domain / infra

### 4. Long Parameter List

- 合併成 parameter object / typed config
- 對外公開 API 優先用明確命名欄位，不要靠參數順序記憶

### 5. Deep Nesting

- 優先改為 guard clauses / early returns
- 若驗證流程複雜，拆成 `validate_*` helper

### 6. Magic Values

- 抽成具名常數或 enum-like 結構
- 讓商業規則名稱進入程式碼，而不是只留下數字或字串

### 7. Weak Type Boundaries

- 為 public API、核心資料結構、跨模組介面補型別
- 讓錯誤在邊界被攔下，而不是在深層 runtime 才爆開
