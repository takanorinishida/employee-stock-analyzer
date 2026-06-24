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
```
取得単価 = (拠出金 + 奨励金) ÷ 取得株数
新 avg_cost_with = (現保有株数 × 現 avg_cost_with + 取得株数 × 取得単価)
                 ÷ (現保有株数 + 取得株数)
```

**DIVIDEND_REINVESTMENT 時:**
```
取得単価 = 配当再投資額 ÷ 取得株数
新 avg_cost_with = (現保有株数 × 現 avg_cost_with + 取得株数 × 取得単価)
                 ÷ (現保有株数 + 取得株数)
```

### パターンB: avg_cost_without（拠出金のみをコストとする）

**CONTRIBUTION 時:**
```
取得単価 = 拠出金 ÷ 取得株数     ← 奨励金を除く
新 avg_cost_without = (現保有株数 × 現 avg_cost_without + 取得株数 × 取得単価)
                    ÷ (現保有株数 + 取得株数)
```

**DIVIDEND_REINVESTMENT 時:**
```
取得単価 = 0                      ← 配当再投資はコストとして計上しない
新 avg_cost_without = (現保有株数 × 現 avg_cost_without)
                    ÷ (現保有株数 + 取得株数)
※ 株数が増え取得単価 0 のため、avg_cost_without は減少する
```

### 両パターン共通: SALE 時
```
avg_cost は変化しない
新保有株数 = 現保有株数 − 売却株数
```

### 両パターン共通: STOCK_SPLIT / REVERSE_SPLIT 時
```
新保有株数         = 現保有株数         × (split_ratio_after ÷ split_ratio_before)
新 avg_cost_with    = 現 avg_cost_with    × (split_ratio_before ÷ split_ratio_after)
新 avg_cost_without = 現 avg_cost_without × (split_ratio_before ÷ split_ratio_after)
```

### 保有株数が 0 になった場合
```
avg_cost_with = 0
avg_cost_without = 0
```

---

## 2. 売却損益の計算

対応要求: REQ-0010

```
realized_gain_loss_with    = (sale_price_per_share − avg_cost_with)    × 売却株数
realized_gain_loss_without = (sale_price_per_share − avg_cost_without) × 売却株数
```

---

## 3. 概算税額の計算

対応要求: REQ-0011, REQ-1003

```
capital_gains_tax_rate = 設定ファイルから読み込み（デフォルト: 0.20315）

概算税額 = MAX(売却損益, 0) × capital_gains_tax_rate
税引後手取り = sale_price_per_share × 売却株数 − 概算税額
```

---

## 4. 取引修正後の全件再計算

対応要求: REQ-1004

```
1. 修正・削除された transaction_date を取得する
2. 同じ plan_id の全取引を transaction_date 昇順で取得する
3. 修正日以降の取引を先頭から順に再計算する:
   a. 前取引の shares_held_after / avg_cost_with / avg_cost_without を引き継ぐ
   b. セクション 1 の計算式で新しい avg_cost と shares_held_after を算出する
   c. transaction_type が SALE の場合は realized_gain_loss も再計算する
4. 全件再計算完了後、対象取引をまとめて一括保存する（アトミックな更新）
```

---

## 5. 売却シミュレーションの計算

対応要求: REQ-0016

```
入力:
  current_price            … 現在株価（ユーザー入力）
  simulation_shares        … シミュレーション売却株数（省略時は全保有株数）

計算:
  評価損益_with    = (current_price − avg_cost_with)    × simulation_shares
  評価損益_without = (current_price − avg_cost_without) × simulation_shares
  概算税額_with    = MAX(評価損益_with, 0)    × capital_gains_tax_rate
  概算税額_without = MAX(評価損益_without, 0) × capital_gains_tax_rate
  税引後手取り_with    = current_price × simulation_shares − 概算税額_with
  税引後手取り_without = current_price × simulation_shares − 概算税額_without

出力:
  評価損益_with / _without, 概算税額_with / _without, 税引後手取り_with / _without
```

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

```
avg_cost_with    = (19 × 1,105.26 + 1 × 950) ÷ 20 = 21,949.94 ÷ 20 = 1,097.50 ✓
avg_cost_without = (19 × 1,052.63 + 1 × 0)   ÷ 20 = 19,999.97 ÷ 20 = 1,000.00 ✓
```

**計算検証（#4: SALE）**

```
realized_gain_loss_with    = (1,300 − 1,097.50) × 5 = 1,012.50
realized_gain_loss_without = (1,300 − 1,000.00) × 5 = 1,500.00
avg_cost は変化しない ✓
```

**計算検証（#5: STOCK_SPLIT 2:1）**

```
新保有株数         = 15 × (2 ÷ 1) = 30.0000 ✓
新 avg_cost_with    = 1,097.50 × (1 ÷ 2) = 548.75 ✓
新 avg_cost_without = 1,000.00 × (1 ÷ 2) = 500.00 ✓
```
