"""
Shared fixtures and mocks for the test suite.
"""
from __future__ import annotations

import sys
from collections import defaultdict, deque
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Mock heavy native modules BEFORE any project code is imported
# ---------------------------------------------------------------------------
sys.modules.setdefault("asyncpg", MagicMock())
sys.modules.setdefault("yt_dlp", MagicMock())
sys.modules.setdefault("lyricsgenius", MagicMock())

# telegram stubs — only what project code imports at module level
_telegram = MagicMock()
_telegram_ext = MagicMock()
sys.modules.setdefault("telegram", _telegram)
sys.modules.setdefault("telegram.ext", _telegram_ext)


# ---------------------------------------------------------------------------
# Reset shared module-level state between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_mem_cache():
    import cache as c
    c._MEM_CACHE.clear()
    yield
    c._MEM_CACHE.clear()


@pytest.fixture(autouse=True)
def reset_rate_buckets():
    import cache as c
    c._RATE_BUCKETS.clear()
    c._CHAT_RATE_BUCKETS.clear()
    yield
    c._RATE_BUCKETS.clear()
    c._CHAT_RATE_BUCKETS.clear()


# ---------------------------------------------------------------------------
# Fake Telegram context
# ---------------------------------------------------------------------------

class FakeContext:
    """Minimal stand-in for telegram.ext.ContextTypes.DEFAULT_TYPE."""

    def __init__(self, lang: str = "en"):
        self.user_data: dict = {"lang": lang}
        self.bot_data: dict = {}


@pytest.fixture
def ctx_vi():
    return FakeContext(lang="en")


@pytest.fixture
def ctx_en():
    return FakeContext(lang="en")


# ---------------------------------------------------------------------------
# Mock ApiClient
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_api():
    api = MagicMock()
    api.fetch_genius_search = AsyncMock(return_value=[])
    api.fetch_genius_data = AsyncMock(return_value=None)
    api.fetch_musicbrainz_data = AsyncMock(return_value=None)
    api.get_odesli = AsyncMock(return_value=None)
    api.fetch_auto_lyrics = AsyncMock(return_value=None)
    api.fetch_synced_lyrics = AsyncMock(return_value=(None, None))
    return api
