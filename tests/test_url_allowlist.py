"""
Tests for track_manager._is_allowed_music_url() — the host allowlist gating
which URLs are handed to yt-dlp's generic extractor.

Without this check, any URL a user pastes that Odesli/Spotify oEmbed can't
resolve falls through to yt-dlp, which will fetch arbitrary hosts (internal
services, cloud metadata endpoints, etc.) on the bot server's behalf.
"""
from __future__ import annotations

from track_manager import _is_allowed_music_url


class TestAllowedHosts:
    def test_youtube_watch_url(self):
        assert _is_allowed_music_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_youtu_be_short_url(self):
        assert _is_allowed_music_url("https://youtu.be/dQw4w9WgXcQ")

    def test_spotify_track_url(self):
        assert _is_allowed_music_url("https://open.spotify.com/track/abc123")

    def test_apple_music_url(self):
        assert _is_allowed_music_url("https://music.apple.com/us/album/x/123")

    def test_zingmp3_url(self):
        assert _is_allowed_music_url("https://zingmp3.vn/bai-hat/ten-bai/ZW.html")


class TestBlockedHosts:
    def test_cloud_metadata_ip_blocked(self):
        assert not _is_allowed_music_url("http://169.254.169.254/latest/meta-data/")

    def test_localhost_blocked(self):
        assert not _is_allowed_music_url("http://localhost:5432/")

    def test_internal_hostname_blocked(self):
        assert not _is_allowed_music_url("http://internal-admin.local/secrets")

    def test_lookalike_subdomain_blocked(self):
        """Hostname must match exactly — "youtube.com.evil.com" is a
        different host from "youtube.com", not a subdomain trick that
        should sneak through."""
        assert not _is_allowed_music_url("https://youtube.com.evil.com/watch?v=x")

    def test_arbitrary_domain_blocked(self):
        assert not _is_allowed_music_url("https://example.com/some-page")

    def test_malformed_url_blocked(self):
        assert not _is_allowed_music_url("http://[::not-valid")
