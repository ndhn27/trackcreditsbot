-- Migration 001: Initial schema
CREATE TABLE IF NOT EXISTS approved_data (
    track_key           TEXT PRIMARY KEY,
    credits_text        TEXT,
    credits_contributor TEXT,
    lyrics_text         TEXT,
    lyrics_source       TEXT,
    lyrics_contributor  TEXT,
    approved_at         BIGINT
);

CREATE TABLE IF NOT EXISTS submissions (
    id              SERIAL PRIMARY KEY,
    track_title     TEXT,
    track_artist    TEXT,
    track_key       TEXT,
    content_text    TEXT,
    source_text     TEXT,
    sub_type        TEXT,
    submitter_id    BIGINT,
    submitter_name  TEXT,
    status          TEXT DEFAULT 'pending',
    created_at      BIGINT
);

CREATE TABLE IF NOT EXISTS leaderboard (
    user_id     BIGINT PRIMARY KEY,
    username    TEXT,
    score       INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS promo_links (
    id          SERIAL PRIMARY KEY,
    track_key   TEXT,
    promo_type  TEXT,
    promo_url   TEXT
);

CREATE TABLE IF NOT EXISTS song_cache (
    track_key     TEXT PRIMARY KEY,
    title         TEXT,
    artist        TEXT,
    genius_data   TEXT,
    yt_url        TEXT,
    thumb         TEXT,
    streams       TEXT,
    yt_credits    TEXT,
    lyrics        TEXT,
    lyrics_source TEXT,
    cached_at     BIGINT
);

CREATE TABLE IF NOT EXISTS track_hashes (
    track_hash  TEXT PRIMARY KEY,
    track_key   TEXT NOT NULL,
    expires_at  BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_track_hashes_expires_at ON track_hashes (expires_at);
