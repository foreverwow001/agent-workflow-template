# Chat Archive 規則

> 用途：定義 `maintainers/chat/archive/` 的收錄條件、命名規則、合併原則與刪除門檻。
> 這份文件只處理 maintainer chat 文檔的 archive 治理，不處理下游專案文件。

## 1. archive 的角色

`archive/` 只保留**歷史脈絡**，不承擔 active 規則來源角色。

放進 archive 的文件，預設表示：

- 它已不再是目前工作的 authoritative baseline
- 它仍有回溯設計決策或 handoff 演進鏈的價值
- 後續可被閱讀，但不應再直接拿來驅動新實作

## 2. 哪些文件應進 archive

符合任一條件即可進 archive：

1. **已被新文件完整取代的規格草稿**
   - 例如 requirements、design、implementation checklist 都已被單一 active spec 吸收。
2. **已完成階段任務的狀態摘要**
   - 例如某一輪 blocker snapshot、runtime summary、收尾分析。
3. **里程碑型 handoff**
   - 對應某次明確轉折、收斂或驗證結果，且保留後仍有歷史價值。
4. **歷史分析文**
   - 仍有治理或設計脈絡價值，但其中的 active 假設已失效。

## 3. 哪些文件不應放進 archive

以下內容不要丟進 archive：

1. **目前仍是規則來源的 active 文件**
2. **可重複使用的模板**
   - 例如 `handoff/SESSION-HANDOFF.template.md`
3. **原始 chat export JSON**
   - 原始 JSON 留在 `maintainers/chat/*.json` 的本機/OneDrive 流程，不進 git archive。
4. **只是舊，但沒有歷史價值的重複草稿**
   - 這類應優先合併摘要後刪除，不是直接累積進 archive。

## 4. 檔案狀態標記

archive 內文件應在開頭明確標示狀態，建議只使用下列幾種：

- `Archived`
- `Archived - historical blocker snapshot`
- `Archived - superseded by <active doc>`
- `Archived - lineage summary`

若文件仍需保留補充說明，應直接在開頭寫清楚 successor，而不是讓讀者自行猜。

## 5. 命名規則

archive 檔名沿用 maintainer chat 的日期前綴：

- `YYYY-MM-DD-<topic>.md`

若是合併摘要，名稱應明示其職責，例如：

- `YYYY-MM-DD-<topic>-draft-lineage.md`
- `YYYY-MM-DD-<topic>-historical-summary.md`

不要使用 `final`, `new`, `latest`, `v2-final` 這類會快速失效的命名。

## 6. handoff 收斂規則

handoff 不因日期相同就自動合併。

只有在以下條件同時成立時，才應把多份 handoff 收斂成一份摘要或移轉到 archive：

1. 它們服務的是**同一輪工作目標**
2. 其中沒有獨立的里程碑證據
3. 後續閱讀時保留多份只會增加重複成本

若 handoff 各自代表不同里程碑，例如：

- pre-rebuild
- workflow-readiness
- structure-analysis

則應分段保留，不視為重複。

## 7. draft 收斂規則

對 requirements / design / checklist 類文件，優先採以下順序：

1. 先確認是否已有單一 active spec 完整吸收決策
2. 若已吸收：
   - 建立一份 lineage / summary 檔
   - 在 summary 內列出被吸收的舊檔名與原因
   - 刪除平行 draft 檔，不讓 archive 無限制堆疊
3. 若尚未吸收：
   - draft 可暫留 active 區
   - 不要太早丟進 archive 假裝已結案

## 8. 刪除門檻

archive 內文件可以刪，但必須同時滿足：

1. 已有更高密度、可追溯的替代摘要
2. 刪掉後不會失去關鍵決策脈絡
3. `maintainers/chat/README.md` 或相關 index 已同步更新

如果刪除會讓讀者看不出「為什麼當初這樣決定」，那就先不要刪。

## 9. 每次收斂時的最小同步項

當你新增、合併、移轉或刪除 archive 文件時，至少同步檢查：

1. `maintainers/chat/README.md`
2. `maintainers/index.md`
3. 被取代文件的本地引用是否仍存在

必要時補一行狀態摘要，讓後續維護者知道這次 archive 收斂做了什麼。

## 10. 實務判斷原則

優先順序永遠是：

1. 讓 active 區清楚
2. 讓 archive 可追溯
3. 避免 archive 變成第二個 active 區

如果一份歷史文件還需要大量 cross-reference 才能理解，通常代表它該被收斂，而不是繼續原樣堆著。
