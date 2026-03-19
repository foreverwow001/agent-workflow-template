---
name: python-expert
description: "Python implementation guidance for Engineer. Use when writing, refactoring, or reviewing .py files, adding type hints, improving correctness, tightening error handling, making code more Pythonic, or documenting public APIs."
---

# Python Expert

提供 Engineer 在 Python 任務中的優先級明確指南：先確保 correctness，再補 type safety、performance、style 與 documentation。

## 何時使用

當任務符合任一條件時，Engineer 應載入本 skill：

- 新增或修改 `.py`
- 撰寫 Python script、module、service、CLI、資料處理邏輯
- 重構現有 Python 程式碼
- 需要補型別、docstring、錯誤處理或 Pythonic 寫法

## 核心要求

- Correctness 優先於 style；先避免 bug，再談漂亮
- 公開函式與核心資料結構應有清楚型別
- 不要用 bare `except:`，例外處理要具體
- 先用標準函式庫與簡單資料結構，不要過早複雜化
- Docstring 應描述目的、參數、回傳值與必要的錯誤情境

## Engineer 工作流

1. 先讀 [references/python-correctness.md](./references/python-correctness.md) 掌握 bug 與邊界風險。
2. 再讀 [references/python-type-safety.md](./references/python-type-safety.md) 與 [references/python-performance.md](./references/python-performance.md) 中與任務相符的部分。
3. 撰寫 public API 或共享模組時，再讀 [references/python-style-and-documentation.md](./references/python-style-and-documentation.md)。
4. 在寫 code 前先決定資料結構、函式介面與邊界條件。
5. 寫實作時同步補 type hints，而不是最後才補。
6. 對錯誤、資源管理與邊界輸入做顯式處理。
7. 對簡單轉換優先用 Pythonic 寫法，但不要為了炫技犧牲可讀性。
8. 完成後用 checklist 回看 correctness、type safety、performance、style、testing。

## 參考資料

- [references/python-correctness.md](./references/python-correctness.md)
- [references/python-type-safety.md](./references/python-type-safety.md)
- [references/python-performance.md](./references/python-performance.md)
- [references/python-style-and-documentation.md](./references/python-style-and-documentation.md)
