-- Migration 007: Payment orders table for tracking purchases

CREATE TABLE IF NOT EXISTS payment_orders (
    id          SERIAL PRIMARY KEY,
    order_id    TEXT UNIQUE NOT NULL,
    user_id     BIGINT NOT NULL,
    pack_id     TEXT NOT NULL,
    credits     INTEGER NOT NULL,
    provider    TEXT NOT NULL DEFAULT 'manual',
    status      TEXT NOT NULL DEFAULT 'pending',  -- pending | paid | failed | refunded
    amount_vnd  BIGINT,
    amount_usd  NUMERIC(10,2),
    created_at  BIGINT NOT NULL,
    paid_at     BIGINT
);

CREATE INDEX IF NOT EXISTS idx_payment_orders_user    ON payment_orders (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payment_orders_order   ON payment_orders (order_id);
CREATE INDEX IF NOT EXISTS idx_payment_orders_status  ON payment_orders (status);
