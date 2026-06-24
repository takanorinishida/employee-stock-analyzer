# 持株会管理ツール ロジック詳細設計書

バージョン: 1.0.0
作成日: 2026-06-24
ステータス: ドラフト

---

## 1. 移動平均法による平均取得単価の計算

対応要求: REQ-0008, REQ-0009

2パターンの平均取得単価を常に並行して計算・保持する。

### パターンA: avg_cost_with（奨励金・配当金をコストに含める）

**CONTRIBUTION 時:**

$$
\text{取得単価} = \frac{\text{拠出金} + \text{奨励金}}{\text{取得株数}}
$$

$$
\text{新 avg\_cost\_with} = \frac{\text{現保有株数} \times \text{現 avg\_cost\_with} + \text{取得株数} \times \text{取得単価}}{\text{現保有株数} + \text{取得株数}}
$$

**DIVIDEND_REINVESTMENT 時:**

$$
\text{取得単価} = \frac{\text{配当再投資額}}{\text{取得株数}}
$$

$$
\text{新 avg\_cost\_with} = \frac{\text{現保有株数} \times \text{現 avg\_cost\_with} + \text{取得株数} \times \text{取得単価}}{\text{現保有株数} + \text{取得株数}}
$$

### パターンB: avg_cost_without（拠出金のみをコストとする）

**CONTRIBUTION 時:**

$$
\text{取得単価} = \frac{\text{拠出金}}{\text{取得株数}} \quad (\text{奨励金を除く})
$$

$$
\text{新 avg\_cost\_without} = \frac{\text{現保有株数} \times \text{現 avg\_cost\_without} + \text{取得株数} \times \text{取得単価}}{\text{現保有株数} + \text{取得株数}}
$$

**DIVIDEND_REINVESTMENT 時:**

$$
\text{取得単価} = 0 \quad (\text{配当再投資はコストとして計上しない})
$$

$$
\text{新 avg\_cost\_without} = \frac{\text{現保有株数} \times \text{現 avg\_cost\_without}}{\text{現保有株数} + \text{取得株数}}
$$

> 株数が増え取得単価 0 のため、avg_cost_without は減少する。

### 両パターン共通: SALE 時

$\text{avg\_cost}$ は変化しない。

$$
\text{新保有株数} = \text{現保有株数} - \text{売却株数}
$$

### 両パターン共通: STOCK_SPLIT / REVERSE_SPLIT 時

$$
\text{新保有株数} = \text{現保有株数} \times \frac{\text{split\_ratio\_after}}{\text{split\_ratio\_before}}
$$

$$
\text{新 avg\_cost\_with} = \text{現 avg\_cost\_with} \times \frac{\text{split\_ratio\_before}}{\text{split\_ratio\_after}}
$$

$$
\text{新 avg\_cost\_without} = \text{現 avg\_cost\_without} \times \frac{\text{split\_ratio\_before}}{\text{split\_ratio\_after}}
$$

### 保有株数が 0 になった場合

$$
\text{avg\_cost\_with} = 0, \quad \text{avg\_cost\_without} = 0
$$

---

## 2. 売却損益の計算

対応要求: REQ-0010

$$
\text{realized\_gain\_loss\_with} = (\text{sale\_price\_per\_share} - \text{avg\_cost\_with}) \times \text{売却株数}
$$

$$
\text{realized\_gain\_loss\_without} = (\text{sale\_price\_per\_share} - \text{avg\_cost\_without}) \times \text{売却株数}
$$

---

## 3. 概算税額の計算

対応要求: REQ-0011, REQ-1003

$\text{capital\_gains\_tax\_rate}$ は設定ファイルから読み込む（デフォルト: $0.20315$）。

$$
\text{概算税額} = \max(\text{売却損益},\ 0) \times \text{capital\_gains\_tax\_rate}
$$

$$
\text{税引後手取り} = \text{sale\_price\_per\_share} \times \text{売却株数} - \text{概算税額}
$$

---

## 4. 取引修正後の全件再計算

対応要求: REQ-1004

1. 修正・削除された `transaction_date` を取得する
2. 同じ `plan_id` の全取引を `transaction_date` 昇順で取得する
3. 修正日以降の取引を先頭から順に再計算する:
   1. 前取引の `shares_held_after` / `avg_cost_with` / `avg_cost_without` を引き継ぐ
   2. セクション 1 の計算式で新しい `avg_cost` と `shares_held_after` を算出する
   3. `transaction_type` が `SALE` の場合は `realized_gain_loss` も再計算する
4. 全件再計算完了後、対象取引をまとめて一括保存する（アトミックな更新）

---

## 5. 売却シミュレーションの計算

対応要求: REQ-0016

入力:
- $\text{current\_price}$: 現在株価（ユーザー入力）
- $\text{simulation\_shares}$: シミュレーション売却株数（省略時は全保有株数）

$$
\text{評価損益\_with} = (\text{current\_price} - \text{avg\_cost\_with}) \times \text{simulation\_shares}
$$

$$
\text{評価損益\_without} = (\text{current\_price} - \text{avg\_cost\_without}) \times \text{simulation\_shares}
$$

$$
\text{概算税額\_with} = \max(\text{評価損益\_with},\ 0) \times \text{capital\_gains\_tax\_rate}
$$

$$
\text{概算税額\_without} = \max(\text{評価損益\_without},\ 0) \times \text{capital\_gains\_tax\_rate}
$$

$$
\text{税引後手取り\_with} = \text{current\_price} \times \text{simulation\_shares} - \text{概算税額\_with}
$$

$$
\text{税引後手取り\_without} = \text{current\_price} \times \text{simulation\_shares} - \text{概算税額\_without}
$$

出力: 評価損益 / 概算税額 / 税引後手取り（各 with / without）

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

| # | イベント | 詳細 | avg_cost_with | avg_cost_without | 保有株数 |
|---|---------|------|:---:|:---:|:---:|
| 1 | CONTRIBUTION | 拠出 10,000・奨励 500・取得 10 株 | 1,050.00 | 1,000.00 | 10.0000 |
| 2 | CONTRIBUTION | 拠出 10,000・奨励 500・取得 9 株 | 1,105.26 | 1,052.63 | 19.0000 |
| 3 | DIVIDEND_REINVESTMENT | 配当 950 円・再投資 1 株 | 1,097.50 | 1,000.00 | 20.0000 |
| 4 | SALE | 5 株を 1,300 円で売却 | 1,097.50 | 1,000.00 | 15.0000 |
| 5 | STOCK_SPLIT 2:1 | — | 548.75 | 500.00 | 30.0000 |

**計算検証（#3: DIVIDEND_REINVESTMENT）**

$$
\text{avg\_cost\_with} = \frac{19 \times 1{,}105.26 + 1 \times 950}{20} = \frac{21{,}949.94}{20} = 1{,}097.50 \checkmark
$$

$$
\text{avg\_cost\_without} = \frac{19 \times 1{,}052.63 + 1 \times 0}{20} = \frac{19{,}999.97}{20} = 1{,}000.00 \checkmark
$$

**計算検証（#4: SALE）**

$$
\text{realized\_gain\_loss\_with} = (1{,}300 - 1{,}097.50) \times 5 = 1{,}012.50
$$

$$
\text{realized\_gain\_loss\_without} = (1{,}300 - 1{,}000.00) \times 5 = 1{,}500.00
$$

$\text{avg\_cost}$ は変化しない $\checkmark$

**計算検証（#5: STOCK_SPLIT 2:1）**

$$
\text{新保有株数} = 15 \times \frac{2}{1} = 30.0000 \checkmark
$$

$$
\text{新 avg\_cost\_with} = 1{,}097.50 \times \frac{1}{2} = 548.75 \checkmark
$$

$$
\text{新 avg\_cost\_without} = 1{,}000.00 \times \frac{1}{2} = 500.00 \checkmark
$$
