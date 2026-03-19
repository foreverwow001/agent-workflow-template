---
name: security-review-helper
description: "Use when performing a Security Review, deterministic security intake, attack-surface mapping, exploit-path validation, or writing structured security findings."
---

# Security Review Helper

> 用途：降低 Security Review 執行摩擦。
> 這不是新的 gate 規格來源，也不負責決定是否觸發 Security Review；觸發條件與欄位契約仍以 `.agent/workflows/AGENT_ENTRY.md` 第 3 節為唯一來源。

## 何時使用

當任務已命中 Security Review trigger，或 user / Coordinator 明確要求安全審查時，Security Reviewer 可先依本 helper 完成 intake，再開始寫正式審查結果。

## 與 code-reviewer 的分工

- `code-reviewer`：做 Python 檔案 / 目錄 / diff 的自動 pre-scan，幫你先抓語法、明顯 secret、危險 API 使用、基本 maintainability 與部分 security smell。
- `security-review-helper`：做 exploitability 導向的深度審查，回答「這條路徑能不能真的被打？impact 是什麼？要不要擋 QA？」

結論：`code-reviewer` 不能取代 Security Review；它只能降低人工審查成本。

## 使用前先確認

1. 已讀 `.agent/roles/security.md`
2. 已確認 Plan / `EXECUTION_BLOCK` 已存在以下欄位：
   - `security_review_required`
   - `security_review_trigger_source`
   - `security_review_trigger_matches`
   - `security_review_conclusion`
3. 已確認這次審查的變更檔案、Goal、SPEC、檔案變更表可讀

若 trigger 已命中但 Plan 尚未回填上述欄位：

- 先要求 Coordinator 回填
- 不要直接跳進 finding 撰寫

## 快速流程

1. 先確認 trigger source / matches 與審查範圍。
2. 用 `code-reviewer` 做 pre-scan。
3. 用攻擊面與 trust boundary 視角收斂真正可利用的漏洞。
4. 將 confirmed / rejected / uncertain 明確分流。
5. 輸出 Security Review 決策，供 Coordinator 回填。

## 建議前置動作

在開始寫 finding 前，先跑一次 `code-reviewer` 當 pre-scan：

```bash
# 單檔
python .agent/skills/code-reviewer/scripts/code_reviewer.py path/to/file.py

# 目錄
python .agent/skills/code-reviewer/scripts/code_reviewer.py src/

# diff
git diff --no-color > /tmp/security-review.diff
python .agent/skills/code-reviewer/scripts/code_reviewer.py /tmp/security-review.diff .

# 或直接吃 git diff
python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff --staged .
python .agent/skills/code-reviewer/scripts/code_reviewer.py git diff main..HEAD .
```

用途：

- 先抓 obvious secret / syntax / dangerous API 問題
- 幫你縮小人工深挖的檔案範圍
- 把「pattern 已命中」和「exploit path 已證明」明確分開

## 詳細 Checklist

完整的 intake、攻擊面速查表、Hypothesis 模板、Severity / Confidence 準則、Decision rubric 與自檢清單，請閱讀：

- `.agent/skills/security-review-helper/references/security_checklist.md`

## 建議輸出骨架

```markdown
## 🔐 Security Review

### Trigger
- source:
- matches:

### Scope
- Reviewed files:
- Related trust boundaries:

### Findings
| ID | Severity | Confidence | File/Area | Issue | Evidence | Exploit Path | Recommendation |
|----|----------|------------|-----------|-------|----------|--------------|----------------|

### Coverage Gaps
- [哪些區域沒審到 / 哪些 runtime context 缺失，導致只能保留 uncertain]

### Rejected Hypotheses
- [已考慮但證偽的假說]

### Decision
- PASS / PASS_WITH_RISK / FAIL
```
