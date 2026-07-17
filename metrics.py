"""
Persistent metrics counter backed by PostgreSQL.

Replaces the old in-memory threading.Lock() dict — all counters survive
restarts and are queryable for historical analysis.

Public API (backward-compatible with the old in-memory version):
    metric_inc(name)          — increment a counter by 1 (fire-and-forget)
    get_metrics()             — return snapshot dict {name: value}  [now async]

Extended API:
    metric_inc_by(name, n)    — increment by arbitrary amount
    get_daily_stats(date_str) — return {metric: value} for a given day
    record_daily(name)        — increment today's daily bucket
    start_metrics_flusher()   — start background flush task (call at app startup)
    stop_metrics_flusher()    — flush + cancel on shutdown
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("trackcredits.metrics")

# ── In-memory write buffer (batched flush to DB) ──────────────────────────
# Buffer increments to avoid a DB round-trip on every single search.
# A background task flushes every FLUSH_INTERVAL_SECONDS.
FLUSH_INTERVAL_SECONDS = 30

_buffer: dict[str, int] = {}
_daily_buffer: dict[tuple, int] = {}   # (date_str, name) -> delta
_flush_task: Optional[asyncio.Task] = None


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


async def _flush_to_db() -> None:
    """Write buffered counters to PostgreSQL."""
    from db import db_execute   # lazy import — avoids circular dep at module load

    if not _buffer and not _daily_buffer:
        return

    snap = dict(_buffer)
    daily_snap = dict(_daily_buffer)
    _buffer.clear()
    _daily_buffer.clear()

    now = int(time.time())
    try:
        for name, delta in snap.items():
            await db_execute(
                """
                INSERT INTO persistent_metrics (name, value, updated_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (name) DO UPDATE
                    SET value      = persistent_metrics.value + $4,
                        updated_at = $5
                """,
                (name, delta, now, delta, now),
            )
        for (date_str, name), delta in daily_snap.items():
            await db_execute(
                """
                INSERT INTO daily_stats (stat_date, metric_name, value)
                VALUES ($1, $2, $3)
                ON CONFLICT (stat_date, metric_name) DO UPDATE
                    SET value = daily_stats.value + $4
                """,
                (date_str, name, delta, delta),
            )
    except Exception as exc:
        logger.warning("metrics flush failed: %s — re-buffering", exc)
        # Re-buffer lost increments so they are not silently dropped
        for name, delta in snap.items():
            _buffer[name] = _buffer.get(name, 0) + delta
        for key, delta in daily_snap.items():
            _daily_buffer[key] = _daily_buffer.get(key, 0) + delta


async def _flush_loop() -> None:
    """Background coroutine: flush every FLUSH_INTERVAL_SECONDS."""
    while True:
        await asyncio.sleep(FLUSH_INTERVAL_SECONDS)
        await _flush_to_db()


def start_metrics_flusher() -> None:
    """
    Start the background flush task.
    Call once from app_factory.setup_app_context().
    """
    global _flush_task
    if _flush_task is None or _flush_task.done():
        _flush_task = asyncio.create_task(_flush_loop())
        logger.info("Metrics flusher started (interval=%ds).", FLUSH_INTERVAL_SECONDS)


async def stop_metrics_flusher() -> None:
    """Flush remaining buffer and cancel background task on shutdown."""
    global _flush_task
    if _flush_task and not _flush_task.done():
        _flush_task.cancel()
        try:
            await _flush_task
        except asyncio.CancelledError:
            pass
    await _flush_to_db()
    logger.info("Metrics flusher stopped; final flush done.")


# ── Public write API ──────────────────────────────────────────────────────

def metric_inc(name: str) -> None:
    """
    Increment counter by 1. Non-blocking buffer write.
    Fully backward-compatible with the old threading-based version.
    """
    metric_inc_by(name, 1)


def metric_inc_by(name: str, n: int = 1) -> None:
    """Increment counter by n. Non-blocking."""
    today = _today()
    # CPython GIL makes dict mutation atomic for simple operations.
    _buffer[name] = _buffer.get(name, 0) + n
    _daily_buffer[(today, name)] = _daily_buffer.get((today, name), 0) + n


def record_daily(name: str) -> None:
    """Alias for metric_inc — makes intent explicit at call site."""
    metric_inc(name)


# ── Public read API ───────────────────────────────────────────────────────

async def get_metrics() -> dict[str, int]:
    """
    Return snapshot of ALL counters: DB values merged with unflushed buffer.
    NOTE: now async (was sync in old version). Callers must await it.
    """
    from db import db_execute

    try:
        rows = await db_execute(
            "SELECT name, value FROM persistent_metrics ORDER BY name",
            fetch_all=True,
        )
        result: dict[str, int] = {row[0]: row[1] for row in (rows or [])}
    except Exception as exc:
        logger.warning("get_metrics DB read failed: %s", exc)
        result = {}

    # Merge unflushed buffer so the view is always current
    for name, delta in _buffer.items():
        result[name] = result.get(name, 0) + delta

    return result


async def get_daily_stats(date_str: Optional[str] = None) -> dict[str, int]:
    """
    Return {metric_name: value} for date_str (default: today UTC).
    Includes unflushed buffer entries for today.
    """
    from db import db_execute

    if date_str is None:
        date_str = _today()

    try:
        rows = await db_execute(
            "SELECT metric_name, value FROM daily_stats WHERE stat_date = $1",
            (date_str,),
            fetch_all=True,
        )
        result: dict[str, int] = {row[0]: row[1] for row in (rows or [])}
    except Exception as exc:
        logger.warning("get_daily_stats failed: %s", exc)
        result = {}

    if date_str == _today():
        for (d, name), delta in _daily_buffer.items():
            if d == date_str:
                result[name] = result.get(name, 0) + delta

    return result
