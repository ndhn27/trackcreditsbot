"""
Caching and rate-limiting helpers.

Refactored to use asyncio.Lock() instead of threading.RLock()
to prevent event loop blocking in async-first application.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple

from metrics import metric_inc
from db import db_execute
from config import logger
from constants import Limits

_MEM_CACHE: Dict[str, Dict] = {}
_MEM_CACHE_LOCK = asyncio.Lock()


async def mem_cache_get(key: str) -> Optional[Dict]:
    """
    Get value from memory cache.

    Async + lock so that the expiry pop is consistent with mem_cache_set/pop.
    Without the lock, the pop (a write) could race with concurrent set calls.
    """
    now = time.time()
    async with _MEM_CACHE_LOCK:
        entry = _MEM_CACHE.get(key)
        if entry and now < entry["expires_at"]:
            return entry["data"]
        _MEM_CACHE.pop(key, None)
        return None


async def mem_cache_set(key: str, data: Dict, ttl: int = Limits.MEM_TTL) -> None:
    """Set value in memory cache with TTL."""
    expires_at = time.time() + ttl
    async with _MEM_CACHE_LOCK:
        if len(_MEM_CACHE) >= Limits.MEM_CACHE_MAX:
            oldest_key = min(_MEM_CACHE, key=lambda cache_key: _MEM_CACHE[cache_key]["expires_at"])
            _MEM_CACHE.pop(oldest_key, None)
        _MEM_CACHE[key] = {"data": data, "expires_at": expires_at}


async def mem_cache_pop(key: str, default=None):
    """Remove value from memory cache."""
    async with _MEM_CACHE_LOCK:
        return _MEM_CACHE.pop(key, default)


async def db_cache_get(key: str) -> Optional[Dict]:
    """Fetch track cache from database."""
    try:
        row = await db_execute(
            "SELECT title, artist, genius_data, yt_url, thumb, streams, "
            "yt_credits, lyrics, lyrics_source, mb_data, cached_at "
            "FROM song_cache WHERE track_key = $1",
            (key,),
            fetch=True,
        )
        if not row:
            return None

        (
            title,
            artist,
            genius_data_raw,
            yt_url,
            thumb,
            streams_raw,
            yt_credits_raw,
            lyrics,
            lyrics_source,
            mb_data_raw,
            cached_at,
        ) = row

        age = time.time() - cached_at
        if age > Limits.DB_HARD_TTL:
            await db_execute("DELETE FROM song_cache WHERE track_key = $1", (key,))
            return None

        data = {
            "title": title,
            "artist": artist,
            "genius_data": json.loads(genius_data_raw) if genius_data_raw else None,
            "yt_url": yt_url or "",
            "thumb": thumb or "",
            "streams": json.loads(streams_raw) if streams_raw else {},
            "yt_credits": json.loads(yt_credits_raw) if yt_credits_raw else {},
            "lyrics": lyrics,
            "lyrics_source": lyrics_source,
            "mb_data": json.loads(mb_data_raw) if mb_data_raw else None,
        }

        if age > Limits.DB_SOFT_TTL:
            data["_stale"] = True
        return data
    except Exception as exc:
        logger.warning("db_cache_get failed for %s: %s", key, exc)
        return None


async def db_cache_set(key: str, data: Dict) -> None:
    """Store track cache in database."""
    def _limit_blob(value: str | None, max_len: int = 120_000) -> str | None:
        if value is None:
            return None
        return value if len(value) <= max_len else value[:max_len]

    try:
        title = data.get("title")
        artist = data.get("artist")
        genius_data = _limit_blob(json.dumps(data.get("genius_data"))) if data.get("genius_data") is not None else None
        yt_url = data.get("yt_url")
        thumb = data.get("thumb")
        streams = _limit_blob(json.dumps(data.get("streams", {})))
        yt_credits = _limit_blob(json.dumps(data.get("yt_credits", {})))
        lyrics = _limit_blob(data.get("lyrics"))
        lyrics_source = data.get("lyrics_source")
        mb_data = _limit_blob(json.dumps(data.get("mb_data"))) if data.get("mb_data") is not None else None
        cached_at = int(time.time())

        await db_execute(
            "INSERT INTO song_cache "
            "(track_key, title, artist, genius_data, yt_url, thumb, streams, yt_credits, lyrics, lyrics_source, mb_data, cached_at) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12) "
            "ON CONFLICT (track_key) DO UPDATE SET "
            "title = EXCLUDED.title, artist = EXCLUDED.artist, genius_data = EXCLUDED.genius_data, "
            "yt_url = EXCLUDED.yt_url, thumb = EXCLUDED.thumb, streams = EXCLUDED.streams, "
            "yt_credits = EXCLUDED.yt_credits, lyrics = EXCLUDED.lyrics, lyrics_source = EXCLUDED.lyrics_source, "
            "mb_data = EXCLUDED.mb_data, cached_at = EXCLUDED.cached_at",
            (
                key,
                title,
                artist,
                genius_data,
                yt_url,
                thumb,
                streams,
                yt_credits,
                lyrics,
                lyrics_source,
                mb_data,
                cached_at,
            ),
        )
    except Exception as exc:
        logger.warning("db_cache_set failed for %s: %s", key, exc)


async def delete_song_cache(key: str) -> None:
    """Delete track from all caches."""
    await mem_cache_pop(key, None)
    try:
        await db_execute("DELETE FROM song_cache WHERE track_key = $1", (key,))
    except Exception as exc:
        logger.warning("delete_song_cache failed for %s: %s", key, exc)


async def cache_lookup(key: str) -> Tuple[Optional[Dict], bool]:
    """
    Lookup track in caches (memory → database).
    
    Returns: (cache_data, is_stale)
    """
    hit = await mem_cache_get(key)
    if hit:
        metric_inc("cache_mem_hit")
        return hit, False

    hit = await db_cache_get(key)
    if hit:
        is_stale = bool(hit.pop("_stale", False))
        await mem_cache_set(key, hit)
        metric_inc("cache_stale" if is_stale else "cache_db_hit")
        return hit, is_stale

    metric_inc("cache_miss")
    return None, False


async def cache_populate(key: str, data: Dict) -> None:
    """Store track in both memory and database caches."""
    await mem_cache_set(key, data)
    await db_cache_set(key, data)


# === Promo Cache (async-safe) ===
_PROMO_CACHE: Dict[str, List] = {}
_PROMO_CACHE_MAX = 1000
_PROMO_CACHE_LOCK = asyncio.Lock()


async def promo_cache_get(track_key: str) -> Optional[List]:
    """Get promo links from cache."""
    async with _PROMO_CACHE_LOCK:
        return _PROMO_CACHE.get(track_key)


async def promo_cache_set(track_key: str, promos: List) -> None:
    """Set promo links in cache."""
    async with _PROMO_CACHE_LOCK:
        if len(_PROMO_CACHE) >= _PROMO_CACHE_MAX:
            _PROMO_CACHE.pop(next(iter(_PROMO_CACHE)))
        _PROMO_CACHE[track_key] = promos


async def promo_cache_invalidate(track_key: str) -> None:
    """Invalidate promo cache."""
    async with _PROMO_CACHE_LOCK:
        _PROMO_CACHE.pop(track_key, None)


async def get_promos(track_key: str) -> List:
    """Get promo links (from cache or DB)."""
    cached = await promo_cache_get(track_key)
    if cached is not None:
        return cached

    rows = await db_execute(
        "SELECT promo_type, promo_url FROM promo_links WHERE track_key = $1",
        (track_key,),
        fetch_all=True,
    ) or []
    await promo_cache_set(track_key, rows)
    return rows


# === Approved Cache (async-safe) ===
_APPROVED_CACHE: Dict[str, Tuple[float, Optional[Tuple]]] = {}
_APPROVED_TTL = 300
_APPROVED_SENTINEL = object()
_APPROVED_CACHE_LOCK = asyncio.Lock()


async def approved_cache_get(track_key: str):
    """Get approved data from cache."""
    now = time.time()
    async with _APPROVED_CACHE_LOCK:
        entry = _APPROVED_CACHE.get(track_key)
        if entry is None:
            return _APPROVED_SENTINEL
        if now < entry[0]:
            return entry[1]
        _APPROVED_CACHE.pop(track_key, None)
        return _APPROVED_SENTINEL


async def approved_cache_set(track_key: str, data: Optional[Tuple]) -> None:
    """Set approved data in cache."""
    async with _APPROVED_CACHE_LOCK:
        _APPROVED_CACHE[track_key] = (time.time() + _APPROVED_TTL, data)


async def approved_cache_invalidate(track_key: str) -> None:
    """Invalidate approved cache."""
    async with _APPROVED_CACHE_LOCK:
        _APPROVED_CACHE.pop(track_key, None)


async def get_approved_data(track_key: str) -> Optional[Tuple]:
    """Get approved credits/lyrics."""
    cached = await approved_cache_get(track_key)
    if cached is not _APPROVED_SENTINEL:
        return cached

    row = await db_execute(
        "SELECT credits_text, credits_contributor, lyrics_text, lyrics_source, lyrics_contributor "
        "FROM approved_data WHERE track_key = $1",
        (track_key,),
        fetch=True,
    )
    await approved_cache_set(track_key, row)
    return row


# === Rate Limiting (FIXED: asyncio.Lock instead of threading.RLock) ===
# asyncio.Lock is correct here: check_rate_limit is async, no blocking I/O inside
# the lock (just dict ops), and it protects _RATE_BUCKETS from concurrent access.
_RATE_BUCKETS: Dict[int, deque] = defaultdict(deque)
_CHAT_RATE_BUCKETS: Dict[int, deque] = defaultdict(deque)
_RATE_LOCK = asyncio.Lock()


async def check_rate_limit(user_id: int, chat_id: Optional[int] = None) -> bool:
    """
    Check if request is allowed (async version).
    
    Return True if allowed, False if rate-limited.
    
    Uses asyncio.Lock to protect shared state without blocking event loop.
    
    Memory-leak fix: after expiring old entries from a bucket, if the deque
    becomes empty it is deleted from the dict.  defaultdict recreates a fresh
    deque on the next access, so the behaviour is identical — but inactive
    users no longer leave an empty deque in RAM forever.
    
    Args:
        user_id: Telegram user ID
        chat_id: Optional chat ID (for group rate limiting)
        
    Returns:
        True if request is allowed, False if rate-limited
    """
    now = time.time()
    cutoff_user = now - Limits.RATE_WIND
    cutoff_chat = now - Limits.CHAT_RATE_WIND

    async with _RATE_LOCK:
        # ── User bucket ───────────────────────────────────────────────────────
        user_bucket = _RATE_BUCKETS[user_id]
        while user_bucket and user_bucket[0] < cutoff_user:
            user_bucket.popleft()

        # All entries expired → free the bucket; defaultdict recreates it on
        # the next access so correctness is unaffected.
        if not user_bucket:
            del _RATE_BUCKETS[user_id]
        user_bucket = _RATE_BUCKETS[user_id]  # fresh deque if just deleted

        if len(user_bucket) >= Limits.RATE_MAX:
            metric_inc("rate_limited")
            return False

        # ── Chat bucket (groups only) ─────────────────────────────────────────
        if chat_id and chat_id != user_id:
            chat_bucket = _CHAT_RATE_BUCKETS[chat_id]
            while chat_bucket and chat_bucket[0] < cutoff_chat:
                chat_bucket.popleft()

            if not chat_bucket:
                del _CHAT_RATE_BUCKETS[chat_id]
            chat_bucket = _CHAT_RATE_BUCKETS[chat_id]

            if len(chat_bucket) >= Limits.CHAT_RATE_MAX:
                return False
            chat_bucket.append(now)

        # Record this request
        user_bucket.append(now)
        return True
