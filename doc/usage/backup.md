# バックアップ・復元

全持株会と全取引データを JSON ファイルへ保存・復元できます。
PC 移行や定期的なデータ保全に使用してください。

---

## backup export — バックアップ

```
stock backup export OUTPUT_PATH
```

すべての持株会・取引データを JSON ファイルにエクスポートします。

### 引数

| 引数 | 説明 |
|---|---|
| `OUTPUT_PATH` | 出力先ファイルパス |

### 実行例

```bash
stock backup export ./backup_20240101.json
# エクスポート完了: 持株会 2 件, 取引 45 件 → ./backup_20240101.json
```

### JSON フォーマット

```json
{
  "exported_at": "2024-01-01T12:00:00.000000",
  "plans": [
    {
      "plan_id": "550e8400-...",
      "company_name": "サンプル株式会社",
      "stock_code": "1234",
      "start_date": "2024-01-01",
      "end_date": null,
      "is_active": true,
      "created_at": "2024-01-01T09:00:00",
      "updated_at": "2024-01-01T09:00:00"
    }
  ],
  "transactions": [
    {
      "transaction_id": "a1b2c3d4-...",
      "plan_id": "550e8400-...",
      "transaction_type": "CONTRIBUTION",
      "transaction_date": "2024-01-10",
      "shares_quantity": "10",
      "contribution_amount": "10000",
      "incentive_amount": "500",
      "avg_cost_with": "1050.00",
      "avg_cost_without": "1000.00",
      "shares_held_after": "10.0000",
      ...
    }
  ]
}
```

---

## backup import — 復元

```
stock backup import INPUT_PATH
```

JSON バックアップファイルからデータを復元します。
**既存のデータに上書きされます**（同一 ID のレコードは置き換えられます）。

### 引数

| 引数 | 説明 |
|---|---|
| `INPUT_PATH` | 入力ファイルパス |

### 実行例

```bash
stock backup import ./backup_20240101.json
# 既存データに上書きインポートします。よいですか？ [y/N]: y
# インポート完了: 持株会 2 件, 取引 45 件
```

---

## 運用例

### 定期バックアップ

バックアップファイルは日付付きで保存することを推奨します。

```bash
stock backup export ./backup_$(date +%Y%m%d).json
```

### PC 移行手順

1. 旧 PC でバックアップを取る
   ```bash
   stock backup export ./stock_backup.json
   ```

2. `stock_backup.json` と `config.json` を新 PC に転送する

3. 新 PC でインストール後、復元する
   ```bash
   stock backup import ./stock_backup.json
   ```
