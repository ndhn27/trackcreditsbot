"""
Data-access layer — Repository pattern.

All raw SQL lives here and nowhere else.  Handlers, services, and callbacks
import named functions from this module; they never call db_execute /
db_execute_conn directly.

Convention
──────────
• Functions that run *outside* a transaction accept no ``conn`` parameter
  and acquire their own connection internally via ``db_execute``.
• Functions that must run *inside* a transaction accept ``conn`` as their
  first positional argument (an asyncpg connection yielded by
  ``db_transaction()``).  Their names end with ``_tx`` to make the
  call-site contract obvious.
"""

from __future__ import annotations

import time
from typing import Optional

from db import db_execute, db_execute_conn


# ── Leaderboard ───────────────────────────────────────────────────────────────

async def leaderboard_get_page(limit: int, offset: int) -> list[tuple]:
    """
    Return up to *limit* rows from the leaderboard ordered by score DESC,
    starting at *offset*.  Callers typically request ``limit + 1`` rows to
    detect whether a next page exists without a separate COUNT query.
    """
    return await db_execute(
        "SELECT username, score FROM leaderboard "
        "ORDER BY score DESC LIMIT $1 OFFSET $2",
        (limit, offset),
        fetch_all=True,
    )


async def leaderboard_add_score_tx(
    conn,
    user_id: int,
    username: str,
    points: int,
) -> None:
    """
    Upsert the user's score by *points* inside an existing transaction.
    Creates the leaderboard row if the user has no entry yet.
    """
    await db_execute_conn(
        conn,
        "INSERT INTO leaderboard (user_id, username, score) VALUES ($1, $2, $3) "
        "ON CONFLICT (user_id) DO UPDATE SET "
        "score = leaderboard.score + $4, username = $5",
        (user_id, username, points, points, username),
    )


# ── Submissions ───────────────────────────────────────────────────────────────

async def submissions_count_pending() -> int:
    """Return the number of submissions currently awaiting review."""
    row = await db_execute(
        "SELECT COUNT(*) FROM submissions WHERE status = 'pending'",
        fetch=True,
    )
    return int(row[0]) if row else 0


async def submissions_insert(
    track_title: str,
    track_artist: str,
    track_key: str,
    content_text: str,
    source_text: str,
    sub_type: str,
    submitter_id: int,
    submitter_name: str,
) -> int:
    """
    Insert a new user submission and return its generated primary-key id.
    ``created_at`` is set to the current UNIX timestamp automatically.
    """
    return await db_execute(
        "INSERT INTO submissions "
        "(track_title, track_artist, track_key, content_text, source_text, "
        "sub_type, submitter_id, submitter_name, created_at) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING id",
        (
            track_title,
            track_artist,
            track_key,
            content_text,
            source_text,
            sub_type,
            submitter_id,
            submitter_name,
            int(time.time()),
        ),
        returning=True,
    )


async def submissions_get_by_id(submission_id: int | str) -> Optional[tuple]:
    """
    Fetch a single submission row by primary key.
    Returns ``None`` if not found.

    Column order: id, track_title, track_key, content_text, source_text,
                  sub_type, submitter_id, submitter_name
    """
    return await db_execute(
        "SELECT id, track_title, track_key, content_text, source_text, "
        "sub_type, submitter_id, submitter_name "
        "FROM submissions WHERE id = $1",
        (submission_id,),
        fetch=True,
    )


async def submissions_lock_for_update_tx(
    conn,
    submission_id: int | str,
) -> Optional[tuple]:
    """
    Re-read the submission's ``status`` with a FOR UPDATE row-lock.

    Must be called inside a :func:`db.db_transaction` block.  The lock
    prevents two concurrent admin taps from both seeing ``pending`` and both
    committing a score increment (double-score bug).

    Returns a 1-tuple ``(status,)`` or ``None`` if the row disappeared.
    """
    return await db_execute_conn(
        conn,
        "SELECT status FROM submissions WHERE id = $1 FOR UPDATE",
        (submission_id,),
        fetch=True,
    )


async def submissions_set_status_tx(
    conn,
    submission_id: int | str,
    status: str,
) -> None:
    """Update submission status inside an existing transaction."""
    await db_execute_conn(
        conn,
        "UPDATE submissions SET status = $2 WHERE id = $1",
        (submission_id, status),
    )


async def submissions_reject(submission_id: int | str) -> None:
    """
    Mark a submission as rejected.
    Runs as a standalone statement (no transaction needed for rejection
    because there are no other tables to update atomically).
    """
    await db_execute(
        "UPDATE submissions SET status = 'rejected' WHERE id = $1",
        (submission_id,),
    )


# ── Approved data ─────────────────────────────────────────────────────────────

async def approved_data_upsert_credits_tx(
    conn,
    track_key: str,
    credits_text: str,
    contributor: str,
) -> None:
    """
    Insert or update the credits entry for *track_key* in approved_data.
    Must be called inside a transaction.
    """
    await db_execute_conn(
        conn,
        "INSERT INTO approved_data (track_key, credits_text, credits_contributor) "
        "VALUES ($1, $2, $3) "
        "ON CONFLICT (track_key) DO UPDATE SET "
        "credits_text = EXCLUDED.credits_text, "
        "credits_contributor = EXCLUDED.credits_contributor",
        (track_key, credits_text, contributor),
    )


async def approved_data_upsert_lyrics_tx(
    conn,
    track_key: str,
    lyrics_text: str,
    lyrics_source: str,
    contributor: str,
) -> None:
    """
    Insert or update the lyrics entry for *track_key* in approved_data.
    Must be called inside a transaction.
    """
    await db_execute_conn(
        conn,
        "INSERT INTO approved_data "
        "(track_key, lyrics_text, lyrics_source, lyrics_contributor) "
        "VALUES ($1, $2, $3, $4) "
        "ON CONFLICT (track_key) DO UPDATE SET "
        "lyrics_text = EXCLUDED.lyrics_text, "
        "lyrics_source = EXCLUDED.lyrics_source, "
        "lyrics_contributor = EXCLUDED.lyrics_contributor",
        (track_key, lyrics_text, lyrics_source, contributor),
    )


# ── Promo links ───────────────────────────────────────────────────────────────

async def promo_links_insert(
    track_key: str,
    promo_type: str,
    promo_url: str,
) -> None:
    """Insert or update a promo link for a track (upsert by track_key + promo_type)."""
    await db_execute(
        "INSERT INTO promo_links (track_key, promo_type, promo_url) "
        "VALUES ($1, $2, $3) "
        "ON CONFLICT (track_key, promo_type) DO UPDATE SET promo_url = EXCLUDED.promo_url",
        (track_key, promo_type, promo_url),
    )


# ── Bot users registry ────────────────────────────────────────────────────

async def bot_users_upsert(user_id: int, username: str) -> None:
    """Register/update a user's last-seen timestamp."""
    now = int(__import__("time").time())
    await db_execute(
        "INSERT INTO bot_users (user_id, username, first_seen, last_seen) "
        "VALUES ($1, $2, $3, $3) "
        "ON CONFLICT (user_id) DO UPDATE "
        "SET username = $4, last_seen = $5",
        (user_id, username or "", now, username or "", now),
    )


async def bot_users_count() -> int:
    row = await db_execute("SELECT COUNT(*) FROM bot_users", fetch=True)
    return int(row[0]) if row else 0


async def bot_users_get_all_ids() -> list[int]:
    rows = await db_execute("SELECT user_id FROM bot_users", fetch_all=True)
    return [r[0] for r in (rows or [])]


# ── User bans ─────────────────────────────────────────────────────────────

async def bans_add(user_id: int, username: str, reason: str, banned_by: int) -> None:
    await db_execute(
        "INSERT INTO user_bans (user_id, username, reason, banned_at, banned_by) "
        "VALUES ($1, $2, $3, $4, $5) "
        "ON CONFLICT (user_id) DO UPDATE SET reason = $6, banned_at = $7",
        (user_id, username or "", reason, int(__import__("time").time()), banned_by,
         reason, int(__import__("time").time())),
    )


async def bans_remove(user_id: int) -> bool:
    n = await db_execute("DELETE FROM user_bans WHERE user_id = $1", (user_id,))
    return n > 0


async def bans_is_banned(user_id: int) -> bool:
    row = await db_execute(
        "SELECT 1 FROM user_bans WHERE user_id = $1", (user_id,), fetch=True
    )
    return row is not None


async def bans_list(limit: int = 50) -> list[tuple]:
    """Returns list of (user_id, username, reason, banned_at)."""
    return await db_execute(
        "SELECT user_id, username, reason, banned_at FROM user_bans "
        "ORDER BY banned_at DESC LIMIT $1",
        (limit,),
        fetch_all=True,
    ) or []


# ── Submissions (admin paginated view) ────────────────────────────────────

async def submissions_get_pending_page(limit: int, offset: int) -> list[tuple]:
    """
    Returns pending submissions for paginated admin review.
    Columns: id, track_title, track_artist, sub_type, submitter_name, created_at
    """
    return await db_execute(
        "SELECT id, track_title, track_artist, sub_type, submitter_name, created_at "
        "FROM submissions WHERE status = 'pending' "
        "ORDER BY created_at ASC LIMIT $1 OFFSET $2",
        (limit, offset),
        fetch_all=True,
    ) or []


async def submissions_count_by_status(status: str) -> int:
    row = await db_execute(
        "SELECT COUNT(*) FROM submissions WHERE status = $1", (status,), fetch=True
    )
    return int(row[0]) if row else 0


# ── Revenue / usage stats ─────────────────────────────────────────────────

async def stats_credit_totals() -> dict:
    """Return aggregate credit stats for admin dashboard."""
    row = await db_execute(
        "SELECT "
        "  COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) AS earned, "
        "  COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) AS spent, "
        "  COUNT(DISTINCT user_id) AS unique_users "
        "FROM credit_transactions",
        fetch=True,
    )
    if not row:
        return {"earned": 0, "spent": 0, "unique_users": 0}
    return {"earned": row[0], "spent": row[1], "unique_users": row[2]}


async def stats_top_credit_users(limit: int = 10) -> list[tuple]:
    """Returns (user_id, balance) for top credit holders."""
    return await db_execute(
        "SELECT uc.user_id, bu.username, uc.balance "
        "FROM user_credits uc "
        "LEFT JOIN bot_users bu ON bu.user_id = uc.user_id "
        "ORDER BY uc.balance DESC LIMIT $1",
        (limit,),
        fetch_all=True,
    ) or []
