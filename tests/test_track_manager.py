"""Tests for TrackManager — core resolution logic."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from track_manager import TrackManager, TrackResolution, TrackAmbiguous, TrackNotFound


def _make_manager(mock_api) -> TrackManager:
    return TrackManager(api=mock_api)


def _genius_hit(title="Blinding Lights", artist="The Weeknd"):
    return {"title": title, "artist": artist, "credits": {}, "lyrics": None}


def _yt_hit(title="Blinding Lights", artist="The Weeknd"):
    return {
        "title": title,
        "artist": artist,
        "yt_url": "https://youtube.com/watch?v=abc",
        "desc": "",
        "thumb": "https://img.example.com/t.jpg",
    }


_CACHE_MISS = (None, False)
_CACHE_POPULATED = AsyncMock()


# ---------------------------------------------------------------------------
# Empty / blank input
# ---------------------------------------------------------------------------

class TestEmptyInput:
    async def test_empty_string(self, mock_api):
        assert isinstance(await _make_manager(mock_api).resolve(""), TrackNotFound)

    async def test_whitespace_only(self, mock_api):
        assert isinstance(await _make_manager(mock_api).resolve("   "), TrackNotFound)


# ---------------------------------------------------------------------------
# URL resolution path
# ---------------------------------------------------------------------------

class TestUrlPath:
    async def test_spotify_url_resolved_via_odesli(self, mock_api):
        mock_api.get_odesli.return_value = {
            "entityUniqueId": "SPOTIFY::abc",
            "entitiesByUniqueId": {
                "SPOTIFY::abc": {
                    "title": "Blinding Lights",
                    "artistName": "The Weeknd",
                    "thumbnailUrl": "",
                }
            },
            "linksByPlatform": {},
        }
        mock_api.fetch_genius_data.return_value = _genius_hit()
        mock_api.fetch_musicbrainz_data.return_value = None
        mock_api.fetch_auto_lyrics.return_value = None

        with patch("track_manager.cache_lookup", AsyncMock(return_value=_CACHE_MISS)), \
             patch("track_manager.cache_populate", AsyncMock()), \
             patch("services.search_yt", AsyncMock(return_value=_yt_hit())):
            result = await _make_manager(mock_api).resolve("https://open.spotify.com/track/abc")

        assert isinstance(result, TrackResolution)
        assert result.title == "Blinding Lights"
        assert result.from_cache is False

    async def test_bad_url_returns_not_found(self, mock_api):
        mock_api.get_odesli.return_value = None
        with patch("services.search_yt", AsyncMock(return_value=None)):
            result = await _make_manager(mock_api).resolve("https://example.com/bad")
        assert isinstance(result, TrackNotFound)


# ---------------------------------------------------------------------------
# Text search path
# ---------------------------------------------------------------------------

class TestTextSearch:
    async def test_single_artist_returns_resolution(self, mock_api):
        mock_api.fetch_genius_search.return_value = [
            {"title": "Blinding Lights", "artist": "The Weeknd"}
        ]
        mock_api.fetch_genius_data.return_value = _genius_hit()
        mock_api.fetch_musicbrainz_data.return_value = None
        mock_api.fetch_auto_lyrics.return_value = None
        mock_api.get_odesli.return_value = None

        with patch("track_manager.cache_lookup", AsyncMock(return_value=_CACHE_MISS)), \
             patch("track_manager.cache_populate", AsyncMock()), \
             patch("services.search_yt", AsyncMock(return_value=_yt_hit())):
            result = await _make_manager(mock_api).resolve("Blinding Lights The Weeknd")

        assert isinstance(result, TrackResolution)
        assert result.title == "Blinding Lights"
        assert result.from_cache is False

    async def test_multiple_artists_returns_ambiguous(self, mock_api):
        mock_api.fetch_genius_search.return_value = [
            {"title": "Find Me", "artist": "Artist A"},
            {"title": "Find Me", "artist": "Artist B"},
        ]
        result = await _make_manager(mock_api).resolve("Find Me")
        assert isinstance(result, TrackAmbiguous)
        assert len(result.choices) == 2

    async def test_no_results_returns_not_found(self, mock_api):
        mock_api.fetch_genius_search.return_value = []
        with patch("services.search_yt", AsyncMock(return_value=None)):
            result = await _make_manager(mock_api).resolve("xyznonexistent999")
        assert isinstance(result, TrackNotFound)

    async def test_deduplicates_same_artist_in_choices(self, mock_api):
        """Duplicate artist entries are collapsed — only unique artists shown."""
        mock_api.fetch_genius_search.return_value = [
            {"title": "Song", "artist": "Artist A"},
            {"title": "Song (Remix)", "artist": "Artist A"},  # same artist, different title
            {"title": "Song", "artist": "Artist B"},
        ]
        result = await _make_manager(mock_api).resolve("Song")
        # Should be TrackAmbiguous with only 2 unique artists
        assert isinstance(result, TrackAmbiguous)
        artists = [c["artist"] for c in result.choices]
        assert len(set(artists)) == len(artists), "Duplicate artists leaked into choices"


# ---------------------------------------------------------------------------
# Cache hit path
# ---------------------------------------------------------------------------

class TestCacheHit:
    def _cached(self, title="Cached Track", artist="Cached Artist"):
        return {
            "title": title, "artist": artist,
            "yt_url": "", "thumb": "", "streams": {}, "yt_credits": {},
            "lyrics": None, "lyrics_source": None, "genius_data": None, "mb_data": None,
        }

    async def test_cache_hit_skips_api_calls(self, mock_api):
        mock_api.fetch_genius_search.return_value = [
            {"title": "Cached Track", "artist": "Cached Artist"}
        ]
        # track_manager does `from cache import cache_lookup` — patch the name
        # as it lives in the track_manager module's namespace.
        with patch("track_manager.cache_lookup", AsyncMock(return_value=(self._cached(), False))):
            result = await _make_manager(mock_api).resolve("Cached Track")

        assert isinstance(result, TrackResolution)
        assert result.from_cache is True
        # MusicBrainz, Odesli and yt-dlp should NOT be called on a cache hit.
        # (Genius IS called once during text-search seed resolution — that is
        # by design; the cache skip happens inside _fetch_and_cache_track.)
        mock_api.fetch_musicbrainz_data.assert_not_called()
        mock_api.get_odesli.assert_not_called()

    async def test_stale_cache_sets_is_stale(self, mock_api):
        mock_api.fetch_genius_search.return_value = [
            {"title": "Stale Track", "artist": "Artist"}
        ]
        with patch("track_manager.cache_lookup", AsyncMock(return_value=(self._cached("Stale Track", "Artist"), True))):
            result = await _make_manager(mock_api).resolve("Stale Track")

        assert isinstance(result, TrackResolution)
        assert result.is_stale is True

    async def test_fresh_cache_is_not_stale(self, mock_api):
        mock_api.fetch_genius_search.return_value = [
            {"title": "Fresh Track", "artist": "Artist"}
        ]
        with patch("track_manager.cache_lookup", AsyncMock(return_value=(self._cached("Fresh Track", "Artist"), False))):
            result = await _make_manager(mock_api).resolve("Fresh Track")

        assert result.is_stale is False


# ---------------------------------------------------------------------------
# resolve_by_key()
# ---------------------------------------------------------------------------

class TestResolveByKey:
    def _cached(self):
        return {
            "title": "Known Track", "artist": "Known Artist",
            "yt_url": "", "thumb": "", "streams": {}, "yt_credits": {},
            "lyrics": None, "lyrics_source": None, "genius_data": None, "mb_data": None,
        }

    async def test_cache_hit_returns_resolution(self, mock_api):
        with patch("track_manager.cache_lookup", AsyncMock(return_value=(self._cached(), False))):
            result = await _make_manager(mock_api).resolve_by_key("known artist__known track")
        assert isinstance(result, TrackResolution)
        assert result.from_cache is True

    async def test_cache_miss_returns_not_found(self, mock_api):
        with patch("track_manager.cache_lookup", AsyncMock(return_value=(None, False))):
            result = await _make_manager(mock_api).resolve_by_key("missing__key")
        assert isinstance(result, TrackNotFound)


# ---------------------------------------------------------------------------
# TrackResolution.cache_status_key property
# ---------------------------------------------------------------------------

class TestCacheStatusKey:
    def _r(self, from_cache=False, is_stale=False):
        return TrackResolution(
            track_key="k", title="T", artist="A",
            from_cache=from_cache, is_stale=is_stale,
        )

    def test_fresh_cache_hit(self):
        assert self._r(from_cache=True, is_stale=False).cache_status_key == "cache_hit"

    def test_fresh_load(self):
        assert self._r(from_cache=False, is_stale=False).cache_status_key == "loaded"

    def test_stale_cache_counts_as_loaded(self):
        assert self._r(from_cache=True, is_stale=True).cache_status_key == "loaded"

    def test_non_cached_stale_counts_as_loaded(self):
        assert self._r(from_cache=False, is_stale=True).cache_status_key == "loaded"
