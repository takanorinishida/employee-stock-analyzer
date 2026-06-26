# 持株会管理ツール データモデル設計書

バージョン: 1.0.0
作成日: 2026-06-24
ステータス: ドラフト

---

## 1. エンティティ関係

```
Plan（持株会） 1 ──< Transaction（取引履歴）
```

---

## 2. Plan エンティティ

対応要求: REQ-0001, REQ-0002

| フィールド | 型 | 必須 | 説明 |
|-----------|---|:---:|------|
| plan_id | 文字列 | ○ | 主キー。`plan add --id` でユーザーが指定（推奨16文字以下）。使用可能文字: 英数字・ハイフン・アンダースコア・ピリオド（`[a-zA-Z0-9._-]`）。重複不可。 |
| company_name | 文字列 | ○ | 会社名 |
| ticker | 文字列 | — | ティッカーシンボル（例: "7203.T", "AAPL"）。Yahoo Finance形式を推奨。将来の株価自動取得に使用予定。 |
| start_date | 日付 | ○ | 持株会加入日 |
| end_date | 日付 | — | 退会日（NULL = 継続中） |
| is_active | 真偽値 | ○ | 有効フラグ（デフォルト: true） |
| created_at | 日時 | ○ | 作成日時 |
| updated_at | 日時 | ○ | 更新日時 |

---

## 3. Transaction エンティティ

対応要求: REQ-0003, REQ-0005〜REQ-0011

| フィールド | 型 | 必須 | 説明 |
|-----------|---|:---:|------|
| transaction_id | UUID | ○ | 主キー |
| plan_id | UUID | ○ | Plan への外部キー |
| transaction_type | 列挙値 | ○ | 取引種別（下記参照） |
| transaction_date | 日付 | ○ | 取引発生日 |
| shares_quantity | 数値(4dp) | 条件付 | 取得・売却株数（CONTRIBUTION / DIVIDEND_REINVESTMENT / SALE時） |
| contribution_amount | 数値 | 条件付 | 拠出金（CONTRIBUTION時） |
| incentive_amount | 数値 | 条件付 | 奨励金（CONTRIBUTION時、0可） |
| dividend_amount | 数値 | 条件付 | 配当再投資額（DIVIDEND_REINVESTMENT時） |
| sale_price_per_share | 数値 | 条件付 | 売却単価（SALE時） |
| split_ratio_before | 整数 | 条件付 | 分割前比率（STOCK_SPLIT / REVERSE_SPLIT時） |
| split_ratio_after | 整数 | 条件付 | 分割後比率（STOCK_SPLIT / REVERSE_SPLIT時） |
| avg_cost_with | 数値(2dp) | ○ | 取引後の平均取得単価（奨励金・配当金コスト込み）（REQ-0008） |
| avg_cost_without | 数値(2dp) | ○ | 取引後の平均取得単価（拠出金のみベース）（REQ-0009） |
| shares_held_after | 数値(4dp) | ○ | 取引後の保有株数 |
| realized_gain_loss_with | 数値 | 条件付 | 確定損益・コスト込み（SALE時）（REQ-0010） |
| realized_gain_loss_without | 数値 | 条件付 | 確定損益・拠出金のみ（SALE時）（REQ-0010） |
| carryover_amount | 数値 | — | 翌月繰越金（CONTRIBUTION時、オプション）。当月購入後に翌月へ持ち越す残高。（REQ-0017） |
| employee_carryover_amount | 数値 | — | 繰越金の拠出金按分分（計算値）。avg_cost_without チェーン計算に使用。（REQ-0018） |
| created_at | 日時 | ○ | 作成日時 |
| updated_at | 日時 | ○ | 更新日時 |

### transaction_type 列挙値

| 値 | 意味 | 必須フィールド | 対応要求 |
|----|-----|-------------|---------|
| CONTRIBUTION | 毎月の積立購入（拠出金＋奨励金） | contribution_amount, incentive_amount, shares_quantity（carryover_amount は任意） | REQ-0003, REQ-0017 |
| DIVIDEND_REINVESTMENT | 配当金による再投資 | dividend_amount, shares_quantity | REQ-0005 |
| SALE | 株式売却 | sale_price_per_share, shares_quantity | REQ-0006 |
| STOCK_SPLIT | 株式分割 | split_ratio_before, split_ratio_after | REQ-0007 |
| REVERSE_SPLIT | 株式合併（逆分割） | split_ratio_before, split_ratio_after | REQ-0007 |

---

## 4. 派生データ（永続化しない）

取引履歴または入力値から都度計算して返却する。

| 派生データ | 算出元 | 対応要求 |
|----------|-------|---------|
| PortfolioSummary（保有株数・平均取得単価・累積拠出額・確定損益累計） | Transaction の集計 | REQ-0012, REQ-0010 |
| SaleSimulation（評価損益・概算税額・手取り額） | 最新 Transaction + 入力株価 | REQ-0016 |

---

## 5. 設定ファイル仕様

対応要求: REQ-1003

外部設定ファイル（例: `config.json`）でシステム定数を管理する。
ファイルが存在しない場合はデフォルト値を使用する。

| 設定キー | デフォルト値 | 説明 |
|---------|-----------|------|
| capital_gains_tax_rate | 0.20315 | 譲渡所得税率（将来の税制変更に備え変更可能） |
