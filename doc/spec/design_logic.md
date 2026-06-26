# 持株会管理ツール ロジック詳細設計書

バージョン: 1.0.0
作成日: 2026-06-24
ステータス: ドラフト

---

## 1. 移動平均法による平均取得単価の計算

対応要求: REQ-0008, REQ-0009

2パターンの平均取得単価を常に並行して計算・保持する。

### 変数記号の定義

| 記号 | 対応フィールド | 意味 |
|------|------------|------|
| $n$ | `shares_held_after`（取引前） | 現保有株数 |
| $n'$ | `shares_held_after`（取引後） | 新保有株数 |
| $q$ | `shares_quantity` | 取得・売却株数 |
| $p$ | — | 取得単価（中間計算値） |
| $\bar{c}_{+}$ | `avg_cost_with`（取引前） | 平均取得単価（奨励金・配当金込み） |
| $\bar{c}_{+}'$ | `avg_cost_with`（取引後） | 同上・更新後 |
| $\bar{c}_{-}$ | `avg_cost_without`（取引前） | 平均取得単価（拠出金のみ） |
| $\bar{c}_{-}'$ | `avg_cost_without`（取引後） | 同上・更新後 |
| $r_\text{前}$ | `split_ratio_before` | 分割前比率 |
| $r_\text{後}$ | `split_ratio_after` | 分割後比率 |
| $s$ | `sale_price_per_share` / `current_price` | 売却単価・現在株価 |
| $\tau$ | `capital_gains_tax_rate` | 譲渡所得税率 |
| $G_{+}$ | `realized_gain_loss_with` | 確定損益（込み） |
| $G_{-}$ | `realized_gain_loss_without` | 確定損益（除き） |
| $C$ | `carryover_amount` | 翌月繰越金（CONTRIBUTION 時オプション、省略時 0） |
| $C_\text{prev}$ | 前 CONTRIBUTION の `carryover_amount` | 前月繰越金（前月の $C$、初回は 0） |
| $E_\text{prev}$ | 前 CONTRIBUTION の `employee_carryover_amount` | 前月繰越金の拠出金按分分（計算値、初回は 0） |

---

### パターンA: `avg_cost_with`（奨励金・配当金をコストに含める）

**CONTRIBUTION 時:**

繰越金 $C$（翌月繰越金）が指定された場合、実際の株式購入金額を使って単価を算出する。

$$
\text{実購入額} = C_\text{prev} + \text{拠出金} + \text{奨励金} - C
$$

$$
p = \frac{\text{実購入額}}{q}
$$

$$
\bar{c}_{+}' = \frac{n \cdot \bar{c}_{+} + q \cdot p}{n + q}
$$

> $C = 0$（省略時を含む）かつ $C_\text{prev} = 0$ の場合、$\text{実購入額} = \text{拠出金} + \text{奨励金}$ となり旧来の計算式に縮退する。

**DIVIDEND_REINVESTMENT 時:**

$$
p = \frac{\text{配当再投資額}}{q}
$$

$$
\bar{c}_{+}' = \frac{n \cdot \bar{c}_{+} + q \cdot p}{n + q}
$$

---

### パターンB: `avg_cost_without`（拠出金のみをコストとする）

**CONTRIBUTION 時:**

繰越金のうち拠出金按分分を追跡する。

$$
\text{拠出金可用額} = E_\text{prev} + \text{拠出金}
$$

$$
\text{拠出金実購入額} = \text{拠出金可用額} \times \frac{\text{実購入額}}{C_\text{prev} + \text{拠出金} + \text{奨励金}}
$$

$$
p = \frac{\text{拠出金実購入額}}{q}
$$

$$
\bar{c}_{-}' = \frac{n \cdot \bar{c}_{-} + q \cdot p}{n + q}
$$

翌月繰越金の拠出金按分分（次の計算サイクルの $E_\text{prev}$）:

$$
E = \text{拠出金可用額} \times \frac{C}{C_\text{prev} + \text{拠出金} + \text{奨励金}}
$$

> $C = 0$ かつ $C_\text{prev} = 0$ の場合、$p = \dfrac{\text{拠出金}}{q}$ となり旧来の計算式に縮退する。

**DIVIDEND_REINVESTMENT 時:**

$$
p = 0 \quad (\text{配当再投資はコストとして計上しない})
$$

$$
\bar{c}_{-}' = \frac{n \cdot \bar{c}_{-}}{n + q}
$$

> 株数が増え $p = 0$ のため、$\bar{c}_{-}$ は減少する。

---

### 両パターン共通: SALE 時

$\bar{c}_{+}$, $\bar{c}_{-}$ は変化しない。

$$
n' = n - q
$$

### 両パターン共通: STOCK_SPLIT / REVERSE_SPLIT 時

$$
n' = n \times \frac{r_\text{後}}{r_\text{前}}
$$

$$
\bar{c}_{+}' = \bar{c}_{+} \times \frac{r_\text{前}}{r_\text{後}}
$$

$$
\bar{c}_{-}' = \bar{c}_{-} \times \frac{r_\text{前}}{r_\text{後}}
$$

### 保有株数が 0 になった場合

$$
\bar{c}_{+} = \bar{c}_{-} = 0
$$

---

## 2. 売却損益の計算

対応要求: REQ-0010

$$
G_{+} = (s - \bar{c}_{+}) \times q
$$

$$
G_{-} = (s - \bar{c}_{-}) \times q
$$

---

## 3. 概算税額の計算

対応要求: REQ-0011, REQ-1003

$\tau$（`capital_gains_tax_rate`）は設定ファイルから読み込む（デフォルト: $0.20315$）。

$$
\text{概算税額} = \max(G,\ 0) \times \tau
$$

$$
\text{税引後手取り} = s \times q - \text{概算税額}
$$

---

## 4. 取引修正後の全件再計算

対応要求: REQ-1004

1. 修正・削除された `transaction_date` を取得する
2. 同じ `plan_id` の全取引を `transaction_date` 昇順で取得する
3. 修正日以降の取引を先頭から順に再計算する:
   1. 前取引の `shares_held_after` / `avg_cost_with` / `avg_cost_without` を引き継ぐ
   2. CONTRIBUTION 取引が存在する場合、修正日より前の直近 CONTRIBUTION の `carryover_amount`（$C_\text{prev}$）と `employee_carryover_amount`（$E_\text{prev}$）を初期値として引き継ぎ、各 CONTRIBUTION 処理後に更新する
   3. セクション 1 の計算式で新しい `avg_cost` と `shares_held_after` を算出する
   4. `transaction_type` が `SALE` の場合は `realized_gain_loss` も再計算する
4. 全件再計算完了後、対象取引をまとめて一括保存する（アトミックな更新）

---

## 5. 売却シミュレーションの計算

対応要求: REQ-0016

入力:
- $s$（`current_price`）: 現在株価（ユーザー入力）
- $q$（`simulation_shares`）: シミュレーション売却株数（省略時は全保有株数）

$$
\text{評価損益}_{+} = (s - \bar{c}_{+}) \times q
$$

$$
\text{評価損益}_{-} = (s - \bar{c}_{-}) \times q
$$

$$
\text{概算税額}_{+} = \max(\text{評価損益}_{+},\ 0) \times \tau
$$

$$
\text{概算税額}_{-} = \max(\text{評価損益}_{-},\ 0) \times \tau
$$

$$
\text{税引後手取り}_{+} = s \times q - \text{概算税額}_{+}
$$

$$
\text{税引後手取り}_{-} = s \times q - \text{概算税額}_{-}
$$

出力: 評価損益 / 概算税額 / 税引後手取り（各 $+$ / $-$）

---

## 6. 端数処理ルール

対応要求: REQ-1001, REQ-1002

| 対象 | 精度 | 処理 |
|------|------|------|
| 保有株数 | 小数点以下 4 桁 | 切り捨て |
| 平均取得単価 | 小数点以下 2 桁 | 四捨五入（中間計算は高精度を維持） |
| 売却損益 | 円未満 | 切り捨て |
| 概算税額 | 円未満 | 切り捨て |

> 中間計算では端数処理を行わず、最終値への変換時にのみ適用する。

---

## 7. 数値例

前提: 保有 0 株からスタート

| # | イベント | 詳細 | `avg_cost_with` | `avg_cost_without` | 保有株数 |
|---|---------|------|:---:|:---:|:---:|
| 1 | CONTRIBUTION | 拠出 10,000・奨励 500・取得 10 株 | 1,050.00 | 1,000.00 | 10.0000 |
| 2 | CONTRIBUTION | 拠出 10,000・奨励 500・取得 9 株 | 1,105.26 | 1,052.63 | 19.0000 |
| 3 | DIVIDEND_REINVESTMENT | 配当 950 円・再投資 1 株 | 1,097.50 | 1,000.00 | 20.0000 |
| 4 | SALE | 5 株を 1,300 円で売却 | 1,097.50 | 1,000.00 | 15.0000 |
| 5 | STOCK_SPLIT 2:1 | — | 548.75 | 500.00 | 30.0000 |

**計算検証（#3: DIVIDEND_REINVESTMENT）**

$$
\bar{c}_{+}' = \frac{19 \times 1{,}105.26 + 1 \times 950}{20} = \frac{21{,}949.94}{20} = 1{,}097.50 \checkmark
$$

$$
\bar{c}_{-}' = \frac{19 \times 1{,}052.63 + 1 \times 0}{20} = \frac{19{,}999.97}{20} = 1{,}000.00 \checkmark
$$

**計算検証（#4: SALE）**

$$
G_{+} = (1{,}300 - 1{,}097.50) \times 5 = 1{,}012.50
$$

$$
G_{-} = (1{,}300 - 1{,}000.00) \times 5 = 1{,}500.00
$$

$\bar{c}_{+}$, $\bar{c}_{-}$ は変化しない $\checkmark$

**計算検証（#5: STOCK_SPLIT 2:1）**

$$
n' = 15 \times \frac{2}{1} = 30.0000 \checkmark
$$

$$
\bar{c}_{+}' = 1{,}097.50 \times \frac{1}{2} = 548.75 \checkmark
$$

$$
\bar{c}_{-}' = 1{,}000.00 \times \frac{1}{2} = 500.00 \checkmark
$$
