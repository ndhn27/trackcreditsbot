"""Tests for cache.py — in-memory cache and rate limiter."""
from __future__ import annotations

import asyncio
import time


import cache as cache_mod
from cache import mem_cache_get, mem_cache_set, mem_cache_pop, check_rate_limit
from constants import Limits


class TestMemCache:
    async def test_set_and_get(self):
        await mem_cache_set("k1", {"val": "hello"})
        assert await mem_cache_get("k1") == {"val": "hello"}

    async def test_missing_key_returns_none(self):
        assert await mem_cache_get("__missing__") is None

    async def test_expired_entry_returns_none(self):
        await mem_cache_set("exp1", {"v": 1}, ttl=60)
        cache_mod._MEM_CACHE["exp1"]["expires_at"] = time.time() - 1
        assert await mem_cache_get("exp1") is None

    async def test_expired_entry_is_removed(self):
        await mem_cache_set("exp2", {"v": 2}, ttl=60)
        cache_mod._MEM_CACHE["exp2"]["expires_at"] = time.time() - 1
        await mem_cache_get("exp2")
        assert "exp2" not in cache_mod._MEM_CACHE

    async def test_overwrite_updates_value(self):
        await mem_cache_set("ov", {"v": 1})
        await mem_cache_set("ov", {"v": 2})
        assert (await mem_cache_get("ov")) == {"v": 2}

    async def test_pop_removes_entry(self):
        await mem_cache_set("pop1", {"v": 99})
        await mem_cache_pop("pop1")
        assert await mem_cache_get("pop1") is None

    async def test_pop_nonexistent_returns_default(self):
        result = await mem_cache_pop("__gone__", default="fb")
        assert result == "fb"

    async def test_lru_eviction_does_not_exceed_max(self):
        # Fill cache to the limit with long TTLs
        for i in range(Limits.MEM_CACHE_MAX):
            await mem_cache_set(f"evict_{i}", {"v": i}, ttl=3600)
        # One more entry should still work — one old entry is evicted
        await mem_cache_set("evict_overflow", {"v": -1}, ttl=3600)
        assert len(cache_mod._MEM_CACHE) <= Limits.MEM_CACHE_MAX

    async def test_concurrent_writes_are_safe(self):
        async def writer(i):
            await mem_cache_set(f"conc_{i}", {"v": i})
        await asyncio.gather(*[writer(i) for i in range(30)])
        # All should be written without race-condition corruption
        for i in range(30):
            result = await mem_cache_get(f"conc_{i}")
            assert result == {"v": i}


class TestRateLimiter:
    async def test_allows_requests_within_limit(self):
        for _ in range(Limits.RATE_MAX):
            assert await check_rate_limit(user_id=1001, chat_id=None) is True

    async def test_blocks_on_user_limit_exceeded(self):
        uid = 2001
        for _ in range(Limits.RATE_MAX):
            await check_rate_limit(user_id=uid, chat_id=None)
        assert await check_rate_limit(user_id=uid, chat_id=None) is False

    async def test_independent_user_buckets(self):
        # Exhaust user 3001
        for _ in range(Limits.RATE_MAX):
            await check_rate_limit(user_id=3001, chat_id=None)
        # user 3002 is unaffected
        assert await check_rate_limit(user_id=3002, chat_id=None) is True

    async def test_chat_rate_limit_applies(self):
        # Different users in the same chat — exhaust chat limit
        for i in range(Limits.CHAT_RATE_MAX):
            await check_rate_limit(user_id=4000 + i, chat_id=9001)
        # A new user in same chat should be blocked
        assert await check_rate_limit(user_id=5000, chat_id=9001) is False

    async def test_stale_entries_expire_from_window(self):
        """Requests older than RATE_WIND should not count against the limit."""
        uid = 7001
        stale = time.time() - Limits.RATE_WIND - 5
        # Inject stale timestamps directly into the bucket
        cache_mod._RATE_BUCKETS[uid].extend([stale] * Limits.RATE_MAX)
        # With all entries stale, next request must be allowed
        assert await check_rate_limit(user_id=uid, chat_id=None) is True

    async def test_private_chat_skips_chat_bucket(self):
        """When chat_id == user_id (private chat), no chat bucket is written."""
        uid = 8001
        await check_rate_limit(user_id=uid, chat_id=uid)
        assert uid not in cache_mod._CHAT_RATE_BUCKETS
