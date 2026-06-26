# CSV 入出力

取引データを CSV ファイルへエクスポート、または CSV ファイルからインポートできます。

---

## csv export — CSV エクスポート

```
stock csv export PLAN_ID OUTPUT_PATH
```

指定した持株会の全取引を CSV ファイルに書き出します。

### 引数

| 引数 | 説明 |
|---|---|
| `PLAN_ID` | エクスポートする持株会の ID |
| `OUTPUT_PATH` | 出力先ファイルパス |

### 実行例

```bash
stock csv export toyota ./transactions.csv
# 15 件をエクスポートしました: ./transactions.csv
```

### CSV フォーマット

文字コード: **UTF-8 BOM 付き**（Excel で直接開けます）

| 列名 | 説明 |
|---|---|
| `transaction_date` | 取引日（YYYY-MM-DD） |
| `transaction_type` | 取引種別 |
| `shares_quantity` | 株数 |
| `contribution_amount` | 拠出金額 |
| `incentive_amount` | 奨励金額 |
| `dividend_amount` | 配当金額 |
| `sale_price_per_share` | 売却単価 |
| `split_ratio_before` | 分割・合併前の比率 |
| `split_ratio_after` | 分割・合併後の比率 |
| `avg_cost_with` | 平均取得単価（奨励込） |
| `avg_cost_without` | 平均取得単価（拠出のみ） |
| `shares_held_after` | 取引後保有株数 |
| `realized_gain_loss_with` | 実現損益（奨励込） |
| `realized_gain_loss_without` | 実現損益（拠出のみ） |
| `carryover_amount` | 翌月繰越金（CONTRIBUTION 時のみ、入力値） |
| `employee_carryover_amount` | 繰越金の拠出金按分分（計算値・参照用） |

`avg_cost_with` 〜 `realized_gain_loss_without` および `employee_carryover_amount` は計算済み値のためインポート時には無視されます。`carryover_amount` は入力値のためインポート対象です。

---

## csv import — CSV インポート

```
stock csv import PLAN_ID INPUT_PATH
```

CSV ファイルから取引を読み込み、指定した持株会に追加します。

### 引数

| 引数 | 説明 |
|---|---|
| `PLAN_ID` | インポート先の持株会の ID |
| `INPUT_PATH` | 入力ファイルパス |

### 実行例

```bash
stock csv import toyota ./transactions.csv
# 15 件をインポートしました。
```

### インポート用 CSV のフォーマット

インポートに必要な列は以下の 10 列です。

| 列名 | 説明 |
|---|---|
| `transaction_date` | 取引日（YYYY-MM-DD） |
| `transaction_type` | 取引種別 |
| `shares_quantity` | 株数 |
| `contribution_amount` | 拠出金額 |
| `incentive_amount` | 奨励金額 |
| `dividend_amount` | 配当金額 |
| `sale_price_per_share` | 売却単価 |
| `split_ratio_before` | 分割・合併前の比率（整数） |
| `split_ratio_after` | 分割・合併後の比率（整数） |
| `carryover_amount` | 翌月繰越金（CONTRIBUTION 時のみ、省略可） |

使用しない列は空欄で構いません。

### CSV サンプル

```csv
transaction_date,transaction_type,shares_quantity,contribution_amount,incentive_amount,dividend_amount,sale_price_per_share,split_ratio_before,split_ratio_after,carryover_amount
2024-01-10,CONTRIBUTION,10,10000,500,,,,,1000
2024-03-01,DIVIDEND_REINVESTMENT,1,,,950,,,,
2024-06-01,SALE,5,,,,1300,,,
2024-09-01,STOCK_SPLIT,,,,,,1,2,
```

### バリデーションルール

インポート前に全行のバリデーションが実行されます。1 行でもエラーがある場合はインポートが中止されます。

| チェック内容 | エラー例 |
|---|---|
| `transaction_date` が日付形式か | `行 2: transaction_date が無効です（値: '2024/01/10'）` |
| `transaction_type` が有効な値か | `行 3: transaction_type が無効です（値: 'BUY'）` |
| 取引種別ごとの必須フィールドが埋まっているか | `行 4: shares_quantity は CONTRIBUTION に必須です` |
| 数値フィールドが数値か | `行 5: contribution_amount が数値ではありません（値: 'abc'）` |
| `split_ratio_*` が整数か | `行 6: split_ratio_before が整数ではありません（値: '1.5'）` |
| `carryover_amount` が数値か（指定時のみ） | `行 7: carryover_amount が数値ではありません（値: 'abc'）` |
