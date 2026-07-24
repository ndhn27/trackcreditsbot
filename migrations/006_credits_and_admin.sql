-- Migration 006: Credits system, user bans, persistent metrics, user registry

-- ── Bot users registry (needed for broadcast + stats) ─────────────────────
CREATE TABLE IF NOT EXISTS bot_users (
    user_id     BIGINT PRIMARY KEY,
    username    TEXT,
    first_seen  BIGINT NOT NULL,
    last_seen   BIGINT NOT NULL
);

-- ── User credits (the in-bot currency) ────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_credits (
    user_id       BIGINT PRIMARY KEY,
    balance       INTEGER NOT NULL DEFAULT 0,
    last_daily_at BIGINT NOT NULL DEFAULT 0,  -- unix ts of last daily bonus claim
    updated_at    BIGINT NOT NULL DEFAULT 0
);

-- ── Credit transaction log ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS credit_transactions (
    id          SERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL,
    amount      INTEGER NOT NULL,   -- positive = earn, negative = spend
    reason      TEXT NOT NULL,
    created_at  BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_credit_tx_user ON credit_transactions (user_id, created_at DESC);

-- ── User bans ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_bans (
    user_id    BIGINT PRIMARY KEY,
    username   TEXT,
    reason     TEXT,
    banned_at  BIGINT NOT NULL,
    banned_by  BIGINT NOT NULL
);

-- ── Persistent metrics ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS persistent_metrics (
    name       TEXT PRIMARY KEY,
    value      BIGINT NOT NULL DEFAULT 0,
    updated_at BIGINT NOT NULL DEFAULT 0
);

-- ── Daily usage stats ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS daily_stats (
    stat_date   TEXT NOT NULL,  -- YYYY-MM-DD
    metric_name TEXT NOT NULL,
    value       BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (stat_date, metric_name)
);
