"""
Vietnamese music metadata client.

Tries two public sources in order:
  1. ZingMP3 public search API  (mp3.zing.vn)
  2. NhacCuaTui scraper         (nhaccuatui.com)

Returns a normalised dict compatible with the rest of the API layer:
  {
    "title": str,
    "artist": str,
    "lyrics": str | None,
    "thumb": str | None,
    "source": "zingmp3" | "nhaccuatui",
  }

If both sources fail or return no result, returns None.

NOTE: These are public, unauthenticated endpoints intended for
      personal / non-commercial use. Respect robots.txt and ToS.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger("trackcredits.viet_music")

# ── Zing MP3 ──────────────────────────────────────────────────────────────
_ZING_SEARCH = "https://zingmp3.vn/api/v2/search?q={query}&type=song&count=5"
_ZING_SONG   = "https://zingmp3.vn/api/v2/lyric?id={song_id}"
_ZING_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)


def _is_vietnamese(text: str) -> bool:
    """Heuristic: check for Vietnamese diacritics."""
    vi_chars = set("àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ")
    return any(c in vi_chars for c in text.lower())


async def _zing_search(session, query: str) -> Optional[dict]:
    """Search ZingMP3 and return first hit or None."""
    from urllib.parse import quote
    url = f"https://zingmp3.vn/api/v2/search?q={quote(query)}&type=song&count=5"
    try:
        async with session.get(url, headers={"User-Agent": _ZING_UA}, timeout=8) as resp:
            if resp.status != 200:
                return None
            data = await resp.json(content_type=None)
            items = (
                data.get("data", {}).get("song", {}).get("items")
                or data.get("data", {}).get("items")
                or []
            )
            if not items:
                return None
            hit = items[0]
            return {
                "title":  hit.get("title", ""),
                "artist": hit.get("artists_names") or hit.get("artistsNames", ""),
                "song_id": hit.get("encodeId") or hit.get("encode_id", ""),
                "thumb":  hit.get("thumbnailM") or hit.get("thumbnail", ""),
                "source": "zingmp3",
            }
    except Exception as exc:
        logger.debug("ZingMP3 search error: %s", exc)
        return None


async def _zing_lyrics(session, song_id: str) -> Optional[str]:
    """Fetch plain-text lyrics for a ZingMP3 song ID."""
    url = f"https://zingmp3.vn/api/v2/lyric?id={song_id}"
    try:
        async with session.get(url, headers={"User-Agent": _ZING_UA}, timeout=8) as resp:
            if resp.status != 200:
                return None
            data = await resp.json(content_type=None)
            file_url = data.get("data", {}).get("file")
            if not file_url:
                return None
            # The lyrics are stored as a plain-text .lrc or .txt file
            async with session.get(file_url, timeout=8) as lr:
                if lr.status != 200:
                    return None
                raw = await lr.text(encoding="utf-8", errors="replace")
                # Strip LRC timestamps: [mm:ss.xx]
                clean = re.sub(r"\[\d{2}:\d{2}\.\d{2,3}\]", "", raw).strip()
                return clean or None
    except Exception as exc:
        logger.debug("ZingMP3 lyrics error for %s: %s", song_id, exc)
        return None


# ── NhacCuaTui (HTML scrape fallback) ─────────────────────────────────────
_NCT_SEARCH = "https://www.nhaccuatui.com/tim-kiem/bai-hat?q={query}"
_NCT_UA = "Mozilla/5.0 (compatible; TrackCreditsBot/1.0)"


async def _nct_search(session, query: str) -> Optional[dict]:
    """Scrape NhacCuaTui search results and return first hit or None."""
    from urllib.parse import quote
    url = f"https://www.nhaccuatui.com/tim-kiem/bai-hat?q={quote(query)}"
    try:
        async with session.get(url, headers={"User-Agent": _NCT_UA}, timeout=10) as resp:
            if resp.status != 200:
                return None
            html = await resp.text(encoding="utf-8", errors="replace")

        # Extract first song from search results
        title_m  = re.search(r'class="name-song"[^>]*>([^<]+)<', html)
        artist_m = re.search(r'class="name-artist"[^>]*>([^<]+)<', html)
        thumb_m  = re.search(r'class="img-song"[^>]*src="([^"]+)"', html)
        link_m   = re.search(r'href="(https://www\.nhaccuatui\.com/bai-hat/[^"]+)"', html)

        if not title_m:
            return None

        return {
            "title":    title_m.group(1).strip(),
            "artist":   artist_m.group(1).strip() if artist_m else "",
            "thumb":    thumb_m.group(1) if thumb_m else None,
            "page_url": link_m.group(1) if link_m else None,
            "source":   "nhaccuatui",
        }
    except Exception as exc:
        logger.debug("NCT search error: %s", exc)
        return None


async def _nct_lyrics(session, page_url: str) -> Optional[str]:
    """Scrape lyrics from a NhacCuaTui song page."""
    try:
        async with session.get(page_url, headers={"User-Agent": _NCT_UA}, timeout=10) as resp:
            if resp.status != 200:
                return None
            html = await resp.text(encoding="utf-8", errors="replace")
        lyr_m = re.search(
            r'<p\s+class="[^"]*lyric[^"]*"[^>]*>(.*?)</p>',
            html, re.DOTALL | re.IGNORECASE
        )
        if not lyr_m:
            return None
        raw = lyr_m.group(1)
        clean = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
        clean = re.sub(r"<[^>]+>", "", clean).strip()
        return clean or None
    except Exception as exc:
        logger.debug("NCT lyrics error for %s: %s", page_url, exc)
        return None


# ── Public API ────────────────────────────────────────────────────────────

async def fetch_viet_track(session, query: str) -> Optional[dict]:
    """
    Try to fetch Vietnamese track metadata + lyrics.

    Only activates when the query contains Vietnamese characters or when
    the caller explicitly passes a Vietnamese-looking title.

    Returns normalised dict or None.
    """
    # Try ZingMP3 first
    hit = await _zing_search(session, query)
    if hit:
        song_id = hit.pop("song_id", "")
        if song_id:
            hit["lyrics"] = await _zing_lyrics(session, song_id)
        else:
            hit["lyrics"] = None
        return hit

    # Fallback: NhacCuaTui
    hit = await _nct_search(session, query)
    if hit:
        page_url = hit.pop("page_url", None)
        if page_url:
            hit["lyrics"] = await _nct_lyrics(session, page_url)
        else:
            hit["lyrics"] = None
        return hit

    return None


def should_try_viet_source(title: str, artist: str = "") -> bool:
    """
    Return True if the query is likely a Vietnamese track.
    Used by track_manager.py to decide whether to call fetch_viet_track.
    """
    return _is_vietnamese(title) or _is_vietnamese(artist)
