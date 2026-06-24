# 持株会管理

持株会（プラン）の追加・一覧表示・編集を行います。

---

## plan add — 持株会を追加

```
stock plan add [OPTIONS]
```

### オプション

| オプション | 必須 | 説明 |
|---|---|---|
| `--id TEXT` | 必須 | プランID（推奨16文字以下。例: `toyota`, `7203-jp`） |
| `--name TEXT` | 必須 | 会社名 |
| `--start DATE` | 必須 | 持株会の開始日（YYYY-MM-DD 形式） |
| `--ticker TEXT` | 任意 | ティッカーシンボル（例: `7203.T`, `AAPL`）。Yahoo Finance形式を推奨。 |

`--id`、`--name`、`--start` を省略するとプロンプトで入力を求められます。

### 実行例

```bash
# 日本株
stock plan add --id toyota --name "トヨタ自動車" --start 2024-01-01 --ticker 7203.T

# 米国株
stock plan add --id apple --name "Apple Inc." --start 2024-01-01 --ticker AAPL

# プロンプト入力
stock plan add
# プランID: toyota
# 会社名: トヨタ自動車
# 開始日 (YYYY-MM-DD): 2024-01-01
```

### 出力例

```
持株会を追加しました: toyota
  会社名: トヨタ自動車
  開始日: 2024-01-01
  ティッカー: 7203.T
```

---

## plan list — 持株会一覧

```
stock plan list
```

登録されているすべての持株会を一覧表示します。

### 出力例

```
ID      会社名                ティッカー    開始日        状態
------  ------------------  ------------  ----------  ----
toyota  トヨタ自動車          7203.T        2024-01-01  有効
apple   Apple Inc.           AAPL          2024-03-01  有効
```

---

## plan edit — 持株会を編集

```
stock plan edit PLAN_ID [OPTIONS]
```

### 引数

| 引数 | 説明 |
|---|---|
| `PLAN_ID` | 編集する持株会の ID |

### オプション

| オプション | 説明 |
|---|---|
| `--name TEXT` | 会社名を変更 |
| `--ticker TEXT` | ティッカーシンボルを変更 |
| `--start DATE` | 開始日を変更（YYYY-MM-DD） |
| `--end DATE` | 終了日を設定（YYYY-MM-DD） |
| `--active` | 有効に変更 |
| `--inactive` | 無効に変更 |

指定したオプションのみ更新されます。プランIDは変更できません。

### 実行例

```bash
# ティッカーを設定
stock plan edit toyota --ticker 7203.T

# 持株会を終了（終了日を設定して無効化）
stock plan edit toyota --end 2024-12-31 --inactive
```
