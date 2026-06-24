CREATE TABLE IF NOT EXISTS plans (
    plan_id     TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    stock_code  TEXT,
    start_date  TEXT NOT NULL,
    end_date    TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id          TEXT PRIMARY KEY,
    plan_id                 TEXT NOT NULL REFERENCES plans(plan_id),
    transaction_type        TEXT NOT NULL,
    transaction_date        TEXT NOT NULL,
    shares_quantity         TEXT,
    contribution_amount     TEXT,
    incentive_amount        TEXT,
    dividend_amount         TEXT,
    sale_price_per_share    TEXT,
    split_ratio_before      INTEGER,
    split_ratio_after       INTEGER,
    avg_cost_with           TEXT NOT NULL,
    avg_cost_without        TEXT NOT NULL,
    shares_held_after       TEXT NOT NULL,
    realized_gain_loss_with  TEXT,
    realized_gain_loss_without TEXT,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_plan_date
    ON transactions(plan_id, transaction_date, created_at);
