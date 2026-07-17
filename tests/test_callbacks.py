"""
Tests for callbacks/menu.py, callbacks/contrib.py, callbacks/admin.py.

Strategy
--------
All Telegram objects (Update, CallbackQuery, Message, User) are mocked with
AsyncMock / MagicMock so no real bot connection is needed.  Heavy native
modules (asyncpg, yt_dlp, lyricsgenius) are already patched in conftest.py.

External I/O patched per-test:
  - db.get_track_key_from_hash
  - db.store_track_hash
  - db.db_execute
  - cache.promo_cache_invalidate
  - handlers._load_track_from_key
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_query(data: str = "m_main_abc") -> MagicMock:
    """Return a minimal CallbackQuery mock."""
    query = MagicMock()
    query.data = data
    query.edit_message_text = AsyncMock()
    query.message = MagicMock()
    query.message.message_id = 42
    return query


def _make_update(query: MagicMock, user_id: int = 1) -> MagicMock:
    update = MagicMock()
    update.callback_query = query
    update.effective_user = MagicMock()
    update.effective_user.id = user_id
    update.inline_query = None
    return update


def _make_context(lang: str = "en", track: dict | None = None) -> MagicMock:
    ctx = MagicMock()
    ctx.user_data = {"lang": lang}
    ctx.bot_data = {}
    if track is not None:
        ctx.user_data["track"] = track
    return ctx


FAKE_TRACK = {
    "key": "find-me-painful::phung-khanh-linh",
    "title": "Find Me Painful",
    "artist": "Phung Khanh Linh",
    "main_text": "<b>Find Me Painful</b>",
    "streams": {"spotify": {"url": "https://open.spotify.com/track/abc"}},
    "lyrics": "Some lyrics here",
    "lyrics_source": "Genius",
    "db_lyrics": None,
    "db_lyrics_contributor": None,
    "db_lyrics_source": None,
    "genius_data": {"genius_url": "https://genius.com/track/abc"},
    "mb_data": None,
    "yt_credits": {},
    "db_credits": None,
    "db_cred_cont": None,
}


# ============================================================================
# menu.py
# ============================================================================

class TestHandleMain:
    """CB.MENU_MAIN_PREFIX handler."""

    @pytest.mark.asyncio
    async def test_session_expired_when_hash_not_found(self, ctx_vi):
        from callbacks.menu import register_menu
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        register_menu(registry)

        query = _make_query("m_main_deadbeef")
        update = _make_update(query)

        with patch("callbacks.menu.get_track_key_from_hash", new=AsyncMock(return_value=None)):
            handler = registry._handlers.get("m_main")
            await handler(update, ctx_vi, "deadbeef")

        query.edit_message_text.assert_awaited_once()
        args = query.edit_message_text.call_args[0]
        assert "expired" in args[0].lower() or "hết hạn" in args[0].lower()

    @pytest.mark.asyncio
    async def test_renders_main_text_when_track_loaded(self, ctx_vi):
        from callbacks.menu import register_menu
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        register_menu(registry)

        ctx_vi.user_data["track"] = FAKE_TRACK

        with (
            patch("callbacks.menu.get_track_key_from_hash", new=AsyncMock(return_value=FAKE_TRACK["key"])),
            patch("callbacks.menu.store_track_hash", new=AsyncMock(return_value="newhash")),
            patch("callbacks.menu.get_kb", new=AsyncMock(return_value=MagicMock())),
            patch("handlers._load_track_from_key", new=AsyncMock(return_value=True)),
        ):
            query = _make_query("m_main_abc")
            update = _make_update(query)
            handler = registry._handlers.get("m_main")
            await handler(update, ctx_vi, "abc")

        query.edit_message_text.assert_awaited_once()
        call_kwargs = query.edit_message_text.call_args
        assert FAKE_TRACK["main_text"] in call_kwargs[0] or FAKE_TRACK["main_text"] in str(call_kwargs)


class TestHandleStreams:
    """CB.MENU_STREAMS handler."""

    @pytest.mark.asyncio
    async def test_session_expired_when_hash_missing(self, ctx_vi):
        from callbacks.menu import register_menu
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        register_menu(registry)

        query = _make_query()
        update = _make_update(query)

        with patch("callbacks.menu.get_track_key_from_hash", new=AsyncMock(return_value=None)):
            handler = registry._handlers.get("m_streams")
            await handler(update, ctx_vi, "xyz")

        query.edit_message_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_streams_text_contains_spotify_url(self, ctx_vi):
        from callbacks.menu import register_menu
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        register_menu(registry)

        ctx_vi.user_data["track"] = FAKE_TRACK

        with (
            patch("callbacks.menu.get_track_key_from_hash", new=AsyncMock(return_value=FAKE_TRACK["key"])),
            patch("callbacks.menu.store_track_hash", new=AsyncMock(return_value="h1")),
            patch("handlers._load_track_from_key", new=AsyncMock(return_value=True)),
        ):
            query = _make_query()
            update = _make_update(query)
            handler = registry._handlers.get("m_streams")
            await handler(update, ctx_vi, "h1")

        called_text = query.edit_message_text.call_args[0][0]
        assert "spotify" in called_text.lower()


class TestHandleCredits:
    """CB.MENU_CREDITS handler."""

    @pytest.mark.asyncio
    async def test_renders_credits_section(self, ctx_vi):
        from callbacks.menu import register_menu
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        register_menu(registry)

        ctx_vi.user_data["track"] = FAKE_TRACK

        with (
            patch("callbacks.menu.get_track_key_from_hash", new=AsyncMock(return_value=FAKE_TRACK["key"])),
            patch("callbacks.menu.store_track_hash", new=AsyncMock(return_value="h2")),
            patch("callbacks.menu.render_credits", return_value="<b>Credits section</b>"),
            patch("handlers._load_track_from_key", new=AsyncMock(return_value=True)),
        ):
            query = _make_query()
            update = _make_update(query)
            handler = registry._handlers.get("m_credits")
            await handler(update, ctx_vi, "h2")

        query.edit_message_text.assert_awaited_once()
        text = query.edit_message_text.call_args[0][0]
        assert "Credits" in text

    @pytest.mark.asyncio
    async def test_session_expired_on_missing_hash(self, ctx_vi):
        from callbacks.menu import register_menu
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        register_menu(registry)

        with patch("callbacks.menu.get_track_key_from_hash", new=AsyncMock(return_value=None)):
            query = _make_query()
            update = _make_update(query)
            handler = registry._handlers.get("m_credits")
            await handler(update, ctx_vi, "nope")

        query.edit_message_text.assert_awaited_once()


class TestHandleLyrics:
    """CB.MENU_LYRICS handler."""

    @pytest.mark.asyncio
    async def test_shows_lyrics_when_available(self, ctx_vi):
        from callbacks.menu import register_menu
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        register_menu(registry)

        ctx_vi.user_data["track"] = FAKE_TRACK

        with (
            patch("callbacks.menu.get_track_key_from_hash", new=AsyncMock(return_value=FAKE_TRACK["key"])),
            patch("callbacks.menu.store_track_hash", new=AsyncMock(return_value="h3")),
            patch("callbacks.menu.truncate_text_naturally", side_effect=lambda t, _: t),
            patch("handlers._load_track_from_key", new=AsyncMock(return_value=True)),
        ):
            query = _make_query()
            update = _make_update(query)
            handler = registry._handlers.get("m_lyrics")
            await handler(update, ctx_vi, "h3")

        text = query.edit_message_text.call_args[0][0]
        assert "Some lyrics here" in text

    @pytest.mark.asyncio
    async def test_shows_no_lyrics_message_when_empty(self, ctx_vi):
        from callbacks.menu import register_menu
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        register_menu(registry)

        track_no_lyrics = {**FAKE_TRACK, "lyrics": None, "db_lyrics": None}
        ctx_vi.user_data["track"] = track_no_lyrics

        with (
            patch("callbacks.menu.get_track_key_from_hash", new=AsyncMock(return_value=FAKE_TRACK["key"])),
            patch("callbacks.menu.store_track_hash", new=AsyncMock(return_value="h4")),
            patch("handlers._load_track_from_key", new=AsyncMock(return_value=True)),
        ):
            query = _make_query()
            update = _make_update(query)
            handler = registry._handlers.get("m_lyrics")
            await handler(update, ctx_vi, "h4")

        text = query.edit_message_text.call_args[0][0]
        # t("no_lyrics") resolves to a non-empty string
        assert len(text) > 0


# ============================================================================
# contrib.py
# ============================================================================

class TestHandleContribMenu:
    """CB.ACT_CONTRIB handler — shows Credits / Lyrics / Back buttons."""

    @pytest.mark.asyncio
    async def test_session_expired_on_missing_hash(self, ctx_vi):
        from callbacks.contrib import register_contrib
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        register_contrib(registry)

        with patch("callbacks.contrib.get_track_key_from_hash", new=AsyncMock(return_value=None)):
            query = _make_query()
            update = _make_update(query)
            handler = registry._handlers.get("act_contrib")
            await handler(update, ctx_vi, "bad")

        query.edit_message_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_shows_contrib_menu_with_buttons(self, ctx_vi):
        from callbacks.contrib import register_contrib
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        register_contrib(registry)

        ctx_vi.user_data["track"] = FAKE_TRACK

        with (
            patch("callbacks.contrib.get_track_key_from_hash", new=AsyncMock(return_value=FAKE_TRACK["key"])),
            patch("callbacks.contrib.store_track_hash", new=AsyncMock(return_value="ch")),
            patch("handlers._load_track_from_key", new=AsyncMock(return_value=True)),
        ):
            query = _make_query()
            update = _make_update(query)
            handler = registry._handlers.get("act_contrib")
            await handler(update, ctx_vi, "ch")

        query.edit_message_text.assert_awaited_once()
        # reply_markup should have been passed (keyboard with Credits / Lyrics buttons)
        call_kwargs = query.edit_message_text.call_args[1]
        assert "reply_markup" in call_kwargs


class TestHandleSubmitCredits:
    """CB.SUBMIT_CREDITS handler — sets state to awaiting_credits."""

    @pytest.mark.asyncio
    async def test_sets_awaiting_credits_state(self, ctx_vi):
        from callbacks.contrib import register_contrib
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        register_contrib(registry)

        ctx_vi.user_data["track"] = FAKE_TRACK

        with (
            patch("callbacks.contrib.get_track_key_from_hash", new=AsyncMock(return_value=FAKE_TRACK["key"])),
            patch("callbacks.contrib.store_track_hash", new=AsyncMock(return_value="sh")),
            patch("handlers._load_track_from_key", new=AsyncMock(return_value=True)),
        ):
            query = _make_query()
            update = _make_update(query)
            handler = registry._handlers.get("sub_c")
            await handler(update, ctx_vi, "sh")

        assert ctx_vi.user_data.get("state") == "awaiting_credits"


class TestHandleSubmitLyrics:
    """CB.SUBMIT_LYRICS handler — sets state to awaiting_lyrics1."""

    @pytest.mark.asyncio
    async def test_sets_awaiting_lyrics_state(self, ctx_vi):
        from callbacks.contrib import register_contrib
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        register_contrib(registry)

        ctx_vi.user_data["track"] = FAKE_TRACK

        with (
            patch("callbacks.contrib.get_track_key_from_hash", new=AsyncMock(return_value=FAKE_TRACK["key"])),
            patch("callbacks.contrib.store_track_hash", new=AsyncMock(return_value="lh")),
            patch("handlers._load_track_from_key", new=AsyncMock(return_value=True)),
        ):
            query = _make_query()
            update = _make_update(query)
            handler = registry._handlers.get("sub_l")
            await handler(update, ctx_vi, "lh")

        assert ctx_vi.user_data.get("state") == "awaiting_lyrics1"


class TestHandleReport:
    """CB.ACT_REPORT handler — sets state to awaiting_report."""

    @pytest.mark.asyncio
    async def test_sets_awaiting_report_state(self, ctx_vi):
        from callbacks.contrib import register_contrib
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        register_contrib(registry)

        ctx_vi.user_data["track"] = FAKE_TRACK

        with (
            patch("callbacks.contrib.get_track_key_from_hash", new=AsyncMock(return_value=FAKE_TRACK["key"])),
            patch("callbacks.contrib.store_track_hash", new=AsyncMock(return_value="rh")),
            patch("handlers._load_track_from_key", new=AsyncMock(return_value=True)),
        ):
            query = _make_query()
            update = _make_update(query)
            handler = registry._handlers.get("act_report")
            await handler(update, ctx_vi, "rh")

        assert ctx_vi.user_data.get("state") == "awaiting_report"


# ============================================================================
# admin.py
# ============================================================================

ADMIN_ID = 999


class TestHandleAdmin:
    """CB.ADMIN_APPROVE / REJECT — admin-only gate."""

    @pytest.mark.asyncio
    async def test_non_admin_gets_access_denied(self, ctx_vi):
        from callbacks.admin import register_admin
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        with patch("callbacks.admin.ADMIN_CHAT_ID", ADMIN_ID):
            register_admin(registry)

        query = _make_query("admin_app_1")
        update = _make_update(query, user_id=12345)  # not admin

        handler = registry._handlers.get("admin_app")
        await handler(update, ctx_vi, "1")

        query.edit_message_text.assert_awaited_once()
        text = query.edit_message_text.call_args[0][0]
        assert "denied" in text.lower() or "quyền" in text.lower() or "từ chối" in text.lower()

    @pytest.mark.asyncio
    async def test_admin_dispatches_to_admin_act(self, ctx_vi):
        from callbacks.admin import register_admin
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        with patch("callbacks.admin.ADMIN_CHAT_ID", ADMIN_ID):
            register_admin(registry)

        query = _make_query("admin_app_1")
        update = _make_update(query, user_id=ADMIN_ID)

        with patch("handlers.admin_act", new=AsyncMock()) as mock_act:
            handler = registry._handlers.get("admin_app")
            await handler(update, ctx_vi, "1")
            mock_act.assert_awaited_once()


class TestHandleAddPromo:
    """CB.ADD_PROMO_PREFIX handler — sets awaiting_promo_<type> state."""

    @pytest.mark.asyncio
    async def test_non_admin_blocked(self, ctx_vi):
        from callbacks.admin import register_admin
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        with patch("callbacks.admin.ADMIN_CHAT_ID", ADMIN_ID):
            register_admin(registry)

        query = _make_query("add_promo_youtube")
        update = _make_update(query, user_id=555)

        handler = registry._handlers.get("add_promo")
        await handler(update, ctx_vi, "youtube")

        query.edit_message_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_admin_sets_promo_state(self, ctx_vi):
        from callbacks.admin import register_admin
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        with patch("callbacks.admin.ADMIN_CHAT_ID", ADMIN_ID):
            register_admin(registry)

        query = _make_query("add_promo_youtube")
        update = _make_update(query, user_id=ADMIN_ID)

        handler = registry._handlers.get("add_promo")
        await handler(update, ctx_vi, "youtube")

        assert ctx_vi.user_data.get("state") == "awaiting_promo_youtube"


class TestHandleClearPromo:
    """CB.CLEAR_PROMO handler — deletes promo links for current track."""

    @pytest.mark.asyncio
    async def test_non_admin_blocked(self, ctx_vi):
        from callbacks.admin import register_admin
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        with patch("callbacks.admin.ADMIN_CHAT_ID", ADMIN_ID):
            register_admin(registry)

        query = _make_query("clear_promo_")
        update = _make_update(query, user_id=555)

        handler = registry._handlers.get("clear_promo")
        await handler(update, ctx_vi, "")

        query.edit_message_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_clears_promo_and_invalidates_cache(self, ctx_vi):
        from callbacks.admin import register_admin
        from callback_registry import CallbackRegistry

        registry = CallbackRegistry()
        with patch("callbacks.admin.ADMIN_CHAT_ID", ADMIN_ID):
            register_admin(registry)

        ctx_vi.user_data["track"] = FAKE_TRACK

        with (
            patch("callbacks.admin.db_execute", new=AsyncMock()) as mock_db,
            patch("callbacks.admin.promo_cache_invalidate", new=AsyncMock()) as mock_cache,
            patch("callbacks.admin.store_track_hash", new=AsyncMock(return_value="ph")),
        ):
            query = _make_query("clear_promo_")
            update = _make_update(query, user_id=ADMIN_ID)
            handler = registry._handlers.get("clear_promo")
            await handler(update, ctx_vi, "")

        mock_db.assert_awaited_once()
        mock_cache.assert_awaited_once_with(FAKE_TRACK["key"])
        query.edit_message_text.assert_awaited_once()
