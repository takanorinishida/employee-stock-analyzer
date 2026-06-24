# インストール・初期設定

## 必要環境

- Python 3.11 以上
- pip

## インストール手順

```bash
git clone <このリポジトリのURL>
cd employee-stock-analyzer
pip install -e .
```

インストールが完了すると `stock` コマンドが使えるようになります。

```bash
stock --help
```

## データ保存先

初回コマンド実行時に自動でディレクトリとデータベースが作成されます。

| 種類 | パス |
|---|---|
| データベース | `~/.stock-analyzer/data.db`（SQLite） |

データを削除したい場合は `~/.stock-analyzer/data.db` を削除してください。

## 設定ファイル（config.json）

`stock` コマンドを実行するディレクトリに `config.json` を置くと設定を変更できます。

```json
{
  "capital_gains_tax_rate": "0.20315"
}
```

| キー | 説明 | デフォルト |
|---|---|---|
| `capital_gains_tax_rate` | 譲渡所得税率（小数） | `0.20315`（20.315%） |

税率は `simulate` コマンドの税額計算に使用されます。
`config.json` が存在しない場合はデフォルト値（20.315%）が適用されます。

### 税率変更例

NISA 口座など非課税の場合は 0 に設定します。

```json
{
  "capital_gains_tax_rate": "0"
}
```
