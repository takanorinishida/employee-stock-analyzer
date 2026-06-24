# CLAUDE.md

このファイルは Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## コマンド

```bash
# インストール（編集可能モード、リポジトリルートから）
pip install -e .

# テスト実行
pytest

# 単一テストファイルの実行
pytest test/test_calculation_engine.py

# 単一テストクラス・メソッドの実行
pytest test/test_transaction_service.py::TestAddTransaction::test_contribution

# CLI の実行
stock --help
```

## アーキテクチャ

4 層構造（一方向依存）:

```
CLI (src/cli/)  →  Service (src/service/)  →  Domain (src/domain/)
                                           →  Infrastructure (src/infrastructure/)
```

- **`src/domain/`** — データクラス（`Plan`、`Transaction`）と列挙型（`TransactionType`）。ロジックなし。
- **`src/infrastructure/`** — `DataRepository`（sqlite3 による SQLite）、`ConfigRepository`（config.json 読み込み）。数値フィールドは SQLite に TEXT で保存し、リポジトリ層で `Decimal` に変換。
- **`src/service/`** — ビジネスロジック。`calculation_engine.py` が中核（各取引種別の avg_cost・保有株数を計算する純粋関数群）。`TransactionService._recalculate_from()` が編集・削除時の後続取引の再計算を担う。
- **`src/cli/`** — Click コマンド群。エントリポイント: `stock` → `cli.main:cli`。DB は `~/.stock-analyzer/data.db`、設定は実行ディレクトリの `config.json`。

## 設計上の不変条件

- 金融計算には **`float` を使わず `decimal.Decimal`** を使うこと。
- すべての取引に 2 種の平均取得単価を同時管理: `avg_cost_with`（拠出 + 奨励金 + 配当）と `avg_cost_without`（拠出のみ）。
- 端数処理: 株数は 4 桁切り捨て、avg_cost は半端切り上げ 2 桁、金額は円未満切り捨て。
- **自動再計算**: 取引の編集・削除時に `_recalculate_from(plan_id, from_date)` が後続取引をアトミックに再計算・一括保存する。
- `TransactionType` の値: `CONTRIBUTION`、`DIVIDEND_REINVESTMENT`、`SALE`、`STOCK_SPLIT`、`REVERSE_SPLIT`。

## データパス

| リソース | パス |
|---|---|
| SQLite データベース | `~/.stock-analyzer/data.db` |
| 税率設定ファイル | `./config.json`（実行ディレクトリ） |
