"""
Pydantic v2 models for data shapes passed around as Dict[str, Any].

This module is standalone (no DB/network side effects) and safe to import in tests.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

__all__ = [
    "MusicBrainzData",
    "GeniusData",
    "YtData",
    "TrackCacheEntry",
    "StreamEntry",
]

_logger = logging.getLogger(__name__)


class MusicBrainzData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    isrc: str = ""
    label: str = ""
    mb_id: str = ""
    score: int = 0


class GeniusData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = ""
    artist: str = ""
    credits: dict[str, str] = Field(default_factory=dict)
    lyrics: str | None = None
    url: str = ""


class YtData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = ""
    artist: str = ""
    yt_url: str = ""
    desc: str = ""
    thumb: str = ""


class TrackCacheEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    artist: str
    yt_url: str = ""
    thumb: str = ""
    streams: dict[str, Any] = Field(default_factory=dict)
    yt_credits: dict[str, str] = Field(default_factory=dict)
    lyrics: str | None = None
    lyrics_source: str | None = None
    genius_data: GeniusData | None = None
    mb_data: MusicBrainzData | None = None

    @classmethod
    def from_cache_dict(cls, d: dict) -> "TrackCacheEntry | None":
        try:
            return cls.model_validate(d)
        except ValidationError as exc:
            _logger.warning("TrackCacheEntry validation failed: %s", exc)
            return None


class StreamEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    platform: str
    url: str

