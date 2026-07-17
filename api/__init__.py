from __future__ import annotations
from typing import Any, Dict, List, Optional

# Import từ thư mục api/clients/
from api.clients.base import ApiSessionManager
from api.clients.genius import GeniusClient
from api.clients.musicbrainz import MusicBrainzClient
from api.clients.odesli import OdesliClient
from api.clients.lyrics import LyricsClient

# Import từ file merger.py ở thư mục gốc
from merger import merge_track_metadata, parse_youtube_credits, pick_best_lyrics

__all__ = [
    "ApiClient",
    "merge_track_metadata",
    "parse_yt_credits",
    "pick_lyrics",
]

class ApiClient:
    """
    High-level API client orchestrating all service clients.
    """
    def __init__(self):
        self._session_manager = ApiSessionManager()
        self._genius = GeniusClient(self._session_manager)
        self._musicbrainz = MusicBrainzClient(self._session_manager)
        self._odesli = OdesliClient(self._session_manager)
        self._lyrics = LyricsClient(self._session_manager)

    async def start(self) -> None:
        await self._session_manager.start()

    async def stop(self) -> None:
        await self._session_manager.stop()

    async def fetch_genius_search(self, query: str, limit: int = 10) -> List[Dict]:
        return await self._genius.search(query, limit=limit)

    async def fetch_genius_data(self, title: str, artist: str) -> Optional[Dict]:
        return await self._genius.fetch_song_data(title, artist)

    async def fetch_musicbrainz_data(self, title: str, artist: str) -> Optional[Dict]:
        return await self._musicbrainz.fetch_metadata(title, artist)

    async def get_odesli(self, url: str) -> Optional[Dict]:
        return await self._odesli.fetch_links(url)

    async def fetch_auto_lyrics(self, title: str, artist: str) -> Optional[str]:
        return await self._lyrics.fetch(title, artist)

    async def fetch_synced_lyrics(self, title: str, artist: str) -> tuple[Optional[str], Optional[str]]:
        """Return (plainLyrics, syncedLyrics) from lrclib; either may be None."""
        return await self._lyrics.fetch_synced(title, artist)

    async def async_get_text(self, url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 8) -> str:
        _, text = await self._session_manager.fetch_text(url, headers=headers, timeout=timeout)
        return text

    async def async_get_json(self, url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 8) -> Any:
        _, payload = await self._session_manager.fetch_json(url, headers=headers, timeout=timeout)
        return payload

# Pure utility wrappers — no I/O, no singleton, safe to import anywhere.
def parse_yt_credits(desc: str) -> Dict:
    return parse_youtube_credits(desc)

def pick_lyrics(genius_data: Optional[Dict], auto_lyrics: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    return pick_best_lyrics(genius_data, auto_lyrics)
