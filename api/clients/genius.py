"""
Genius API client for song credits, metadata, and lyrics.

Handles:
- Song search
- Full song data with credits
- Lyrics fetching
"""

from __future__ import annotations

import asyncio
import difflib
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from config import GENIUS_TOKEN, logger
from optional_deps import get_lyricsgenius_lib
from metrics import metric_inc
from api.clients.base import ApiSessionManager

__all__ = ["GeniusClient"]


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation/parens for fuzzy matching."""
    text = text.lower()
    text = re.sub(r"\(.*?\)|\[.*?\]", "", text)   # remove parenthetical suffixes
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def _pick_best_hit(hits: list, title: str, artist: str) -> dict | None:
    """
    Score top-5 Genius hits against (title, artist) using SequenceMatcher.

    Returns the best matching ``hit["result"]`` dict, or ``None`` if no hit
    exceeds the relevance threshold (0.4).  Falling back to ``hits[0]``
    blindly caused wrong-song results when the first hit was a remix, live
    version, or completely different song with a similar name.
    """
    norm_title = _normalize(title)
    norm_artist = _normalize(artist)
    best_hit = None
    best_score = 0.0

    for hit in hits[:5]:
        result = hit.get("result", {})
        hit_title = _normalize(result.get("title", ""))
        hit_artist = _normalize(
            result.get("primary_artist", {}).get("name", "")
        )
        title_score = difflib.SequenceMatcher(
            None, norm_title, hit_title
        ).ratio()
        artist_score = (
            difflib.SequenceMatcher(None, norm_artist, hit_artist).ratio()
            if norm_artist
            else 0.5   # no artist info — don't penalise
        )
        # Weighted average: title matters more than artist
        score = 0.6 * title_score + 0.4 * artist_score
        if score > best_score:
            best_score = score
            best_hit = result

    if best_score < 0.4:
        return None
    return best_hit


class GeniusClient:
    """Client for Genius.com API."""

    def __init__(self, session_manager: ApiSessionManager, token: str | None = None):
        self._session_manager = session_manager
        self._token = token or GENIUS_TOKEN
        if not self._token:
            logger.warning(
                "GENIUS_TOKEN is not set. Credits and lyrics from Genius will be unavailable. "
                "Get a free token at https://genius.com/api-clients (takes ~2 minutes)."
            )

    async def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for songs on Genius.
        
        Returns list of tracks with basic info (title, artist, thumbnail, etc.)
        """
        if not self._token:
            return []

        try:
            headers = {"Authorization": f"Bearer {self._token}"}
            status, payload = await self._session_manager.fetch_json(
                f"https://api.genius.com/search?q={quote_plus(query)}",
                headers=headers,
                timeout=8,
                retries=2,
            )
            if status != 200 or not payload:
                return []
            
            hits = payload.get("response", {}).get("hits", [])
            results = []
            for hit in hits[:limit]:
                item = hit.get("result", {})
                results.append({
                    "title": item.get("title", ""),
                    "artist": item.get("primary_artist", {}).get("name", ""),
                    "thumb": item.get("song_art_image_thumbnail_url", ""),
                    "album": "",
                    "release_date": "",
                    "isrc": "",
                    "spotify_url": "",
                })
            return results
        except Exception as exc:
            logger.warning("Genius search failed for %r: %s", query, exc)
            return []

    async def fetch_song_data(self, title: str, artist: str) -> Optional[Dict]:
        """
        Fetch full song data including credits and lyrics.
        
        Returns dict with keys:
        - credits: dict of all song credits
        - lyrics: full lyrics text (if available)
        - genius_url: link to song on Genius
        - title: normalized song title
        - artist: normalized artist name
        """
        if not self._token:
            return None

        headers = {"Authorization": f"Bearer {self._token}"}
        search_query = f"{title} {artist}".strip()
        
        try:
            # Search for the song
            search_status, search_payload = await self._session_manager.fetch_json(
                f"https://api.genius.com/search?q={quote_plus(search_query)}",
                headers=headers,
                timeout=8,
                retries=2,
            )
            if search_status != 200 or not search_payload:
                metric_inc("genius_err")
                return None

            hits = search_payload.get("response", {}).get("hits", [])
            if not hits:
                metric_inc("genius_err")
                return None

            best_result = _pick_best_hit(hits, title, artist)
            if best_result is None:
                metric_inc("genius_no_relevant_hit")
                logger.info(
                    "Genius: no relevant hit for %r / %r (top hit: %r)",
                    title, artist,
                    hits[0].get("result", {}).get("title", "?") if hits else "–",
                )
                return None
            song_id = best_result["id"]
            
            # Fetch full details
            detail_status, detail_payload = await self._session_manager.fetch_json(
                f"https://api.genius.com/songs/{song_id}?text_format=plain",
                headers=headers,
                timeout=8,
                retries=2,
            )
            if detail_status != 200 or not detail_payload:
                metric_inc("genius_err")
                return None
        except Exception as exc:
            metric_inc("genius_err")
            logger.warning("Genius API request failed for %s / %s: %s", title, artist, exc)
            return None

        song_data = detail_payload.get("response", {}).get("song", {})
        credits: Dict[str, str] = {}

        # Extract credits from song data
        release_date = song_data.get("release_date_for_display", "")
        if release_date:
            credits["Released on"] = release_date

        album = song_data.get("album")
        if album and album.get("name"):
            credits["Album"] = album["name"]

        label = song_data.get("record_label_user", {})
        if label and label.get("name"):
            credits["Label"] = label["name"]

        producers = [item["name"] for item in song_data.get("producer_artists", []) if item.get("name")]
        if producers:
            credits["Producer"] = ", ".join(producers)

        writers = [item["name"] for item in song_data.get("writer_artists", []) if item.get("name")]
        if writers:
            credits["Writers"] = ", ".join(writers)

        for performance in song_data.get("custom_performances", []):
            label_name = performance.get("label", "").strip()
            artists = [item["name"] for item in performance.get("artists", []) if item.get("name")]
            if label_name and artists:
                credits[label_name] = ", ".join(artists)

        for relation in song_data.get("song_relationships", []):
            relation_type = relation.get("type", "").replace("_", " ").title()
            relation_songs = relation.get("songs", [])
            if relation_type and relation_songs:
                credits[relation_type] = ", ".join(
                    f"{song.get('title', '')} by {song.get('primary_artist', {}).get('name', '')}"
                    for song in relation_songs
                )

        # Fetch lyrics
        lyrics = await self._fetch_lyrics(title, artist)
        metric_inc("genius_ok")
        
        return {
            "credits": credits,
            "lyrics": lyrics,
            "genius_url": best_result.get("url", ""),
            "title": best_result.get("title"),
            "artist": best_result.get("primary_artist", {}).get("name"),
        }

    async def _fetch_lyrics(self, title: str, artist: str) -> Optional[str]:
        """Fetch lyrics using lyricsgenius library (sync method in thread)."""
        _lyricsgenius = get_lyricsgenius_lib()
        if not (_lyricsgenius and self._token):
            return None

        def _run() -> Optional[str]:
            gc = _lyricsgenius.Genius(
                self._token,
                timeout=8,
                retries=1,
                remove_section_headers=False,
            )
            gc.verbose = False
            song_obj = gc.search_song(title, artist)
            if not song_obj or not song_obj.lyrics:
                return None
            lines = song_obj.lyrics.split("\n")
            if lines and lines[0].lower().endswith("lyrics"):
                lines = lines[1:]
            return "\n".join(lines).strip()

        try:
            return await asyncio.to_thread(_run)
        except Exception as exc:
            logger.debug("lyricsgenius failed for %s / %s: %s", title, artist, exc)
            return None
