"""
Data merging and utility functions for track metadata.

Handles:
- Merging metadata from multiple sources
- Parsing YouTube video credits
- Choosing best lyrics source
"""

from __future__ import annotations

from typing import Dict, Optional

__all__ = [
    "merge_track_metadata",
    "parse_youtube_credits",
    "pick_best_lyrics",
]


def merge_track_metadata(
    *,
    genius_data: Optional[Dict] = None,
    mb_data: Optional[Dict] = None,
    yt_data: Optional[Dict] = None,
) -> Dict:
    """
    Merge track metadata from multiple sources.

    Priority:
    - Title/Artist: Genius > YouTube
    - Album: Genius credits
    - Label: MusicBrainz > Genius
    - ISRC: MusicBrainz
    - Thumbnail: YouTube

    Args:
        genius_data: From Genius API
        mb_data: From MusicBrainz API
        yt_data: From YouTube search

    Returns:
        Merged metadata dict
    """
    genius_data = genius_data or {}
    mb_data = mb_data or {}
    yt_data = yt_data or {}
    genius_credits = genius_data.get("credits", {})

    return {
        "title": genius_data.get("title") or yt_data.get("title") or "",
        "artist": genius_data.get("artist") or yt_data.get("artist") or "",
        "thumb": yt_data.get("thumb") or "",
        "album": genius_credits.get("Album") or "",
        "release_date": genius_credits.get("Released on") or "",
        "label": mb_data.get("label") or genius_credits.get("Label") or "",
        "isrc": mb_data.get("isrc") or "",
    }


def parse_youtube_credits(desc: str) -> Dict[str, str]:
    """
    Parse YouTube video description to extract credits.

    YouTube videos often include credits in the description.
    This extracts them into a structured dict.

    Args:
        desc: YouTube video description

    Returns:
        Dict of credit field → value
    """
    data: Dict[str, str] = {}
    if not desc:
        return data

    field_map = {
        "Provided to YouTube by": "Distributed by",
        "Composer": "Composer",
        "Lyricist": "Lyricist",
        "Writer": "Writers",
        "Producer": "Producer",
        "Mixing Engineer": "Mixing Engineer",
        "Mixer": "Mixing Engineer",
        "Mastering Engineer": "Mastering Engineer",
        "Music Publisher": "Publisher",
        "Released on": "Released on",
        "Label": "Label",
        "Arranger": "Arranger",
        "Recording Engineer": "Recording Engineer",
    }

    for line in desc.split("\n"):
        stripped = line.strip()
        for prefix, mapped in field_map.items():
            if stripped.startswith(prefix):
                value = (
                    stripped.split(":", 1)[-1].strip()
                    if ":" in stripped
                    else stripped.replace(prefix, "").strip()
                )
                if value and mapped not in data:
                    data[mapped] = value
    return data


def pick_best_lyrics(genius_data: Optional[Dict], auto_lyrics: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Pick the best lyrics source (Genius > Auto-fetched > None).

    Args:
        genius_data: From Genius API (may contain lyrics)
        auto_lyrics: From auto-fetch APIs

    Returns:
        (lyrics_text, source_name) tuple
    """
    if genius_data and genius_data.get("lyrics"):
        return genius_data["lyrics"], "Genius"
    if auto_lyrics:
        return auto_lyrics, "Auto-fetched"
    return None, None
