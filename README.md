# 社員持株会管理ツール

社員持株会の拠出・売却・株式分割などの取引を記録し、平均取得単価・損益・税額を管理する CLI ツールです。

## 機能

- **複数プラン管理** — 複数の持株会（会社）を個別に管理
- **取引記録** — 拠出・配当再投資・売却・株式分割・株式合併を記録
- **平均取得単価の自動計算** — 奨励金・配当を含む場合と含まない場合の 2 軸で管理
- **過去取引の修正・削除** — 修正日以降の取引を自動で再計算
- **保有状況サマリー** — 保有株数・平均単価・累計損益を一覧表示
- **売却シミュレーション** — 指定株価での税引後手取りを試算
- **CSV 入出力** — 取引データのエクスポート・インポート
- **バックアップ / 復元** — 全データを JSON ファイルへ保存・復元

## 必要環境

- Python 3.11 以上
- pip

## インストール

```bash
git clone <このリポジトリのURL>
cd employee-stock-analyzer
pip install -e .
```

インストール後、`stock` コマンドが使えるようになります。

```bash
stock --help
```

## クイックスタート

### 1. 持株会を登録する

```bash
stock plan add --id sample --name "サンプル株式会社" --start 2024-01-01
```

### 2. プラン ID を確認する

```bash
stock plan list
```

### 3. 取引を登録する

```bash
# 拠出（毎月の積み立て）
stock transaction add sample --type CONTRIBUTION --date 2024-01-10 \
  --shares 10 --contribution 10000 --incentive 500

# 配当再投資
stock transaction add sample --type DIVIDEND_REINVESTMENT --date 2024-03-01 \
  --shares 1 --dividend 950

# 売却
stock transaction add sample --type SALE --date 2024-06-01 \
  --shares 5 --price 1300

# 株式分割（1株→2株）
stock transaction add sample --type STOCK_SPLIT --date 2024-09-01 \
  --split-before 1 --split-after 2
```

### 4. 保有状況を確認する

```bash
stock summary sample
```

### 5. 売却シミュレーションを実行する

```bash
# 現在株価 1500 円で全株売却した場合を試算
stock simulate sample --price 1500
```

## コマンド一覧

| コマンド | 説明 |
|---|---|
| `plan add` | 持株会を追加 |
| `plan list` | 持株会一覧を表示 |
| `plan edit sample` | 持株会を編集 |
| `transaction add sample` | 取引を追加 |
| `transaction list sample` | 取引一覧を表示 |
| `transaction edit <transaction_id>` | 取引を編集（後続を自動再計算） |
| `transaction delete <transaction_id>` | 取引を削除（後続を自動再計算） |
| `summary sample` | 保有状況サマリーを表示 |
| `simulate sample` | 売却シミュレーションを実行 |
| `csv export sample <output>` | 取引を CSV にエクスポート |
| `csv import sample <input>` | CSV から取引をインポート |
| `backup export <output>` | 全データを JSON にバックアップ |
| `backup import <input>` | JSON からデータを復元 |

## データ保存先

| 種類 | パス |
|---|---|
| データベース | `~/.stock-analyzer/data.db`（SQLite） |
| 設定ファイル | 実行ディレクトリの `config.json` |

## 詳細ドキュメント

- [インストール・初期設定](doc/usage/install.md)
- [基本概念（平均取得単価・端数処理）](doc/usage/concepts.md)
- [持株会管理](doc/usage/plan.md)
- [取引管理](doc/usage/transaction.md)
- [保有状況確認・売却シミュレーション](doc/usage/summary.md)
- [CSV 入出力](doc/usage/csv.md)
- [バックアップ・復元](doc/usage/backup.md)
