# Security Review Checklist

## 用途

這份 checklist 是 `security-review-helper` 的詳細 reference，負責承載深度安全審查時需要反覆套用的分析框架與輸出標準。

## Intake 順序

### Step 1. Trigger 對帳

先用一句話寫清楚：

- 這次是如何被觸發的
- 命中的 source 是 `user`、`coordinator`、`path-rule`、`keyword-rule` 或 `mixed`
- 具體命中的 path / keyword 是什麼

範例：

```markdown
### Trigger
- source: path-rule
- matches: `/bridge/`, `token`
```

### Step 2. 審查範圍鎖定

至少列出：

- 本次實際審查檔案
- 關聯模組
- 不在本輪審查範圍的區域

### Step 3. 攻擊面盤點

對每個變更點至少回答這五件事：

1. 輸入來源是什麼
2. trust boundary 在哪裡
3. 驗證 / 授權點在哪裡
4. 最危險的 sink 是什麼
5. 攻擊者最可能怎麼利用

### Step 4. 證據收斂

每個疑似 finding 至少要補齊：

- 受影響檔案與行號
- 觸發條件 / 前置條件
- exploit path
- 是否已有 counter-evidence
- 你是從 `code-reviewer` pre-scan 命中，還是人工推理補出的

## 攻擊面速查表

| 類型 | 先看什麼 | 常見風險 |
|------|----------|----------|
| Auth / Permission | 身分來源、角色判定、拒絕路徑 | Broken access control, privilege escalation |
| Token / Session | token 產生、保存、傳遞、失效 | token 泄漏, replay, session fixation |
| Bridge / Subprocess | input 到 command 的路徑、allowlist、escaping | command injection, privilege abuse |
| Upload / File write | path normalize、extension/type check、write target | path traversal, overwrite |
| Template / Render | user input 是否進 template/render sink | XSS, SSTI |
| Query / SQL | query 組裝方式、參數化 | injection, data exposure |

## Finding 準備規則

每個 finding 都先寫成漏洞假說，再決定能否成立。

### Hypothesis 模板

```markdown
- Hypothesis: [攻擊者可如何利用]
- Preconditions: [前置條件]
- Sink: [危險 sink]
- Validation: [你拿什麼證明/證偽]
- Result: confirmed / rejected / uncertain
```

### 分流規則

- `confirmed`：可以進 Findings 表
- `rejected`：放進 `Rejected Hypotheses`
- `uncertain`：不得包裝成已驗證漏洞；只能降成低信心風險或留在 rejected / notes

## Severity / Confidence 準則

### Severity

- `Critical`: 可直接造成高權限取得、敏感資料大量外洩、遠端命令執行
- `High`: 可穩定繞過授權、取得敏感資料、寫入危險位置
- `Medium`: 需特定前置條件，但有可行 exploit path
- `Low`: 影響有限或需要高度受限條件

### Confidence

- `High`: 已能從程式邏輯直接證明 exploit path
- `Medium`: 路徑合理且有明顯證據，但仍缺一段 runtime/context
- `Low`: 只有弱訊號，尚不足以當成 confirmed finding

## Finding 表最小欄位

正式輸出時，每個 finding 至少回答：

- `Issue`
- `Evidence`
- `Exploit Path`
- `Recommendation`

若缺少其中任一欄位，通常代表 finding 還沒收斂完。

## Decision 準則

- `PASS`：未發現可成立漏洞；或只有已證偽 / 不可利用的假說
- `PASS_WITH_RISK`：存在低到中風險問題、需要後續追蹤，但不至於阻斷 QA
- `FAIL`：存在 confirmed 的高風險 exploit path，或 impact 足以阻斷 QA / merge

## 最後自檢

送出前確認：

- 有沒有把 trigger source / matches 寫清楚
- 有沒有把純猜測誤寫成 confirmed
- 有沒有把 exploit path 寫成泛泛建議
- 有沒有把修補建議寫成直接要求某種實作而未解釋風險來源
- `security_review_conclusion` 是否已可被 Coordinator 回填
