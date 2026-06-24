# 使用方法ドキュメント 目次

## ドキュメント一覧

| ドキュメント | 内容 |
|---|---|
| [インストール・初期設定](install.md) | インストール手順・設定ファイルの説明 |
| [基本概念](concepts.md) | 平均取得単価の 2 種・端数処理ルールの解説 |
| [持株会管理](plan.md) | `plan add / list / edit` の詳細 |
| [取引管理](transaction.md) | `transaction add / list / edit / delete` の詳細 |
| [保有状況確認・売却シミュレーション](summary.md) | `summary` / `simulate` の詳細 |
| [CSV 入出力](csv.md) | `csv export / import` のフォーマット仕様 |
| [バックアップ・復元](backup.md) | `backup export / import` の詳細 |

## コマンド早見表

```
stock
├── plan
│   ├── add        持株会を追加
│   ├── list       持株会一覧
│   └── edit       持株会を編集
├── transaction
│   ├── add        取引を追加
│   ├── list       取引一覧
│   ├── edit       取引を編集（後続再計算）
│   └── delete     取引を削除（後続再計算）
├── summary        保有状況サマリー
├── simulate       売却シミュレーション
├── csv
│   ├── export     CSVエクスポート
│   └── import     CSVインポート
└── backup
    ├── export     JSONバックアップ
    └── import     JSON復元
```
