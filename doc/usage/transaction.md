# 取引管理

取引の追加・一覧表示・編集・削除を行います。

---

## 取引種別と必須フィールド

| 取引種別 | 値 | 必須オプション |
|---|---|---|
| 拠出 | `CONTRIBUTION` | `--shares`, `--contribution`, `--incentive` |
| 配当再投資 | `DIVIDEND_REINVESTMENT` | `--shares`, `--dividend` |
| 売却 | `SALE` | `--shares`, `--price` |
| 株式分割 | `STOCK_SPLIT` | `--split-before`, `--split-after` |
| 株式合併 | `REVERSE_SPLIT` | `--split-before`, `--split-after` |

---

## transaction add — 取引を追加

```
stock transaction add PLAN_ID [OPTIONS]
```

### 引数

| 引数 | 説明 |
|---|---|
| `PLAN_ID` | 取引を追加する持株会の ID |

### オプション

| オプション | 説明 |
|---|---|
| `--type TEXT` | 取引種別（必須、上表の値を指定） |
| `--date DATE` | 取引日（必須、YYYY-MM-DD 形式） |
| `--shares DECIMAL` | 取得 / 売却株数 |
| `--contribution DECIMAL` | 拠出金額（円） |
| `--incentive DECIMAL` | 奨励金額（円） |
| `--dividend DECIMAL` | 配当金額（円） |
| `--price DECIMAL` | 売却単価（円/株） |
| `--split-before INT` | 分割・合併前の株数比率 |
| `--split-after INT` | 分割・合併後の株数比率 |

`--type` と `--date` を省略するとプロンプトで入力を求められます。

### 実行例

```bash
# 拠出: 10,000円拠出・500円奨励で10株取得
stock transaction add <plan_id> \
  --type CONTRIBUTION --date 2024-01-10 \
  --shares 10 --contribution 10000 --incentive 500

# 配当再投資: 950円配当で1株取得
stock transaction add <plan_id> \
  --type DIVIDEND_REINVESTMENT --date 2024-03-01 \
  --shares 1 --dividend 950

# 売却: 5株を1,300円で売却
stock transaction add <plan_id> \
  --type SALE --date 2024-06-01 \
  --shares 5 --price 1300

# 株式分割: 1株→2株（2:1分割）
stock transaction add <plan_id> \
  --type STOCK_SPLIT --date 2024-09-01 \
  --split-before 1 --split-after 2

# 株式合併: 2株→1株（2:1合併）
stock transaction add <plan_id> \
  --type REVERSE_SPLIT --date 2024-09-01 \
  --split-before 2 --split-after 1
```

### 出力例

```
取引を追加しました: a1b2c3d4-e5f6-7890-abcd-ef1234567890
  種別: CONTRIBUTION  日付: 2024-01-10
  保有株数: 10.0000  平均取得単価(奨励込): 1050.00  (拠出のみ): 1000.00
```

---

## transaction list — 取引一覧

```
stock transaction list PLAN_ID
```

指定した持株会の取引を取引日順に一覧表示します。

### 出力例

```
ID                                    日付          種別                       株数       平均(込)    平均(除)    損益(込)
----------------------------------------------------------------------------------------------------------------------------------
a1b2c3d4-...  2024-01-10  CONTRIBUTION               10        1050.00     1000.00          -
b2c3d4e5-...  2024-03-01  DIVIDEND_REINVESTMENT        1        1097.50     1000.00          -
c3d4e5f6-...  2024-06-01  SALE                         5        1097.50     1000.00       1012
```

---

## transaction edit — 取引を編集

```
stock transaction edit TRANSACTION_ID [OPTIONS]
```

取引内容を変更します。**変更した取引日以降のすべての取引が自動的に再計算されます。**

### 引数

| 引数 | 説明 |
|---|---|
| `TRANSACTION_ID` | 編集する取引の ID |

### オプション

`transaction add` と同じオプションが指定できます（`--type` は変更不可）。

### 実行例

```bash
# 拠出金額を修正
stock transaction edit <transaction_id> --contribution 12000

# 取引日を変更
stock transaction edit <transaction_id> --date 2024-01-15
```

---

## transaction delete — 取引を削除

```
stock transaction delete TRANSACTION_ID
```

取引を削除します。**削除した取引日以降のすべての取引が自動的に再計算されます。**

削除前に確認プロンプトが表示されます。

### 実行例

```bash
stock transaction delete <transaction_id>
# この取引を削除してよいですか？ [y/N]: y
# 取引を削除しました: <transaction_id>
```
