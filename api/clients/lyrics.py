"""
Auto-fetch lyrics from public APIs.

Tries multiple sources:
- lrclib.net: Synced lyrics database
- lyrics.ovh: Lyrics API
"""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import quote_plus, urlencode

from config import logger
from api.clients.base import ApiSessionManager

__all__ = ["LyricsClient"]


class LyricsClient:
    """Client for fetching lyrics from multiple sources."""

    def __init__(self, session_manager: ApiSessionManager):
        self._session_manager = session_manager

    async def fetch(self, title: str, artist: str) -> Optional[str]:
        """
        Fetch lyrics from auto-fetch APIs.

        Tries lrclib.net first, then lyrics.ovh.
        Returns plain text lyrics or None.
        """
        clean_title = re.sub(r"\(.*?\)|\[.*?\]", "", title).strip()
        clean_artist = re.split(r",|&|feat\.|ft\.|Ă—| x ", artist, flags=re.IGNORECASE)[0].strip()

        # Try lrclib first
        try:
            status, payload = await self._session_manager.fetch_json(
                f"https://lrclib.net/api/search?{urlencode({'track_name': clean_title, 'artist_name': clean_artist})}",
                timeout=5,
                retries=1,
            )
            if status == 200 and payload:
                plain_lyrics = payload[0].get("plainLyrics")
                if plain_lyrics:
                    return plain_lyrics
        except Exception as exc:
            logger.warning("lrclib failed for %s / %s: %s", title, artist, exc)

        # Try lyrics.ovh as fallback
        try:
            status, payload = await self._session_manager.fetch_json(
                f"https://api.lyrics.ovh/v1/{quote_plus(clean_artist)}/{quote_plus(clean_title)}",
                timeout=5,
                retries=1,
            )
            if status == 200 and payload:
                lyrics = payload.get("lyrics")
                if lyrics:
                    return lyrics
        except Exception as exc:
            logger.warning("lyrics.ovh failed for %s / %s: %s", title, artist, exc)

        return None

    async def fetch_synced(self, title: str, artist: str) -> tuple[Optional[str], Optional[str]]:
        """
        Fetch both plain and synced (LRC) lyrics from lrclib.net.

        Returns (plainLyrics, syncedLyrics). Either value may be None.
        """
        clean_title = re.sub(r"\(.*?\)|\[.*?\]", "", title).strip()
        clean_artist = re.split(r",|&|feat\.|ft\.|×| x ", artist, flags=re.IGNORECASE)[0].strip()
        try:
            status, payload = await self._session_manager.fetch_json(
                f"https://lrclib.net/api/search?{urlencode({'track_name': clean_title, 'artist_name': clean_artist})}",
                timeout=5,
                retries=1,
            )
            if status == 200 and payload:
                hit = payload[0]
                return hit.get("plainLyrics"), hit.get("syncedLyrics")
        except Exception as exc:
            logger.warning("lrclib fetch_synced failed for %s / %s: %s", title, artist, exc)
        return None, None

