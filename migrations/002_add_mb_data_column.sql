-- Migration 002: Add mb_data column to song_cache
ALTER TABLE song_cache ADD COLUMN IF NOT EXISTS mb_data TEXT;
