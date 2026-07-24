-- Migration 004: Add missing indexes to prevent full-table scans
--
-- Affected queries
-- ─────────────────────────────────────────────────────────────────────────────
-- leaderboard  → SELECT … ORDER BY score DESC (LIMIT + OFFSET) in /top
--                Without an index Postgres sorts the whole table on every page
--                request.  A DESC index lets it read rows in order with no sort.
--
-- submissions  → SELECT … WHERE status = 'pending'         (admin dashboard)
--                SELECT COUNT(*) WHERE status = 'pending'
--                SELECT … WHERE id = $1 FOR UPDATE          (admin_act)
--                The FOR UPDATE row-lock is instant on the PK, but the
--                status filter used in COUNT / queue listing needs its own
--                index; otherwise Postgres seq-scans the whole table to count.
--
-- promo_links  → SELECT … WHERE track_key = $1             (every track view)
--                No index means a seq-scan on every song lookup.
-- ─────────────────────────────────────────────────────────────────────────────

-- leaderboard: ORDER BY score DESC
CREATE INDEX IF NOT EXISTS idx_leaderboard_score_desc
    ON leaderboard (score DESC);

-- submissions: WHERE status = 'pending' / 'approved' / 'rejected'
CREATE INDEX IF NOT EXISTS idx_submissions_status
    ON submissions (status);

-- submissions: WHERE track_key = $1  (lookup by song)
CREATE INDEX IF NOT EXISTS idx_submissions_track_key
    ON submissions (track_key);

-- promo_links: WHERE track_key = $1
CREATE INDEX IF NOT EXISTS idx_promo_links_track_key
    ON promo_links (track_key);
