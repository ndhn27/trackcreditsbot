"""
Core business logic for track resolution and data fetching.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from api import ApiClient, merge_track_metadata, parse_yt_credits, pick_lyrics
from cache import cache_lookup, cache_populate, get_approved_data
from db import make_key
from services import search_yt
from config import logger
from api.clients.viet_music import fetch_viet_track, should_try_viet_source

__all__ = ["TrackManager", "TrackResolution", "TrackAmbiguous", "TrackNotFound", "SearchOutcome"]


@dataclass(frozen=True)
class TrackAmbiguous:
    """
    Returned by TrackManager.resolve() khi một text query khớp với nhiều
    nghệ sĩ khác nhau và người dùng cần chọn một.

    Tách biệt rõ ràng "nhiều kết quả" khỏi TrackNotFound ("không tìm thấy gì"),
    cho phép caller xử lý hai trường hợp này bằng isinstance() thay vì
    dùng None làm giá trị ngữ nghĩa — một anti-pattern gây bug khó trace.

    Attributes:
        choices: Danh sách dict từ Genius search, mỗi phần tử có ít nhất
                 "title" và "artist".
    """
    choices: list[dict]


@dataclass(frozen=True)
class TrackNotFound:
    """
    Returned by TrackManager.resolve() khi không có kết quả nào.

    Phân biệt rõ ràng với None (lỗi lập trình / uninitialized) —
    TrackNotFound là kết quả hợp lệ có nghĩa "tìm không thấy",
    còn None không bao giờ được return từ resolve().
    """


class TrackResolution(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    track_key: str
    title: str
    artist: str
    yt_url: str = ""
    thumb: str = ""
    streams: dict = Field(default_factory=dict)
    yt_credits: dict = Field(default_factory=dict)
    lyrics: Optional[str] = None
    synced_lyrics: Optional[str] = None
    lyrics_source: Optional[str] = None
    genius_data: Optional[dict] = None
    mb_data: Optional[dict] = None
    from_cache: bool = False
    is_stale: bool = False

    @property
    def cache_status_key(self) -> str:
        if self.from_cache and not self.is_stale:
            return "cache_hit"
        return "loaded"

    async def get_approved_data(self) -> Optional[tuple]:
        return await get_approved_data(self.track_key)


# Type alias — đặt SAU TrackResolution để Python đã biết tên class này.
# None không xuất hiện — mọi trường hợp đều có kiểu tường minh.
SearchOutcome = TrackResolution | TrackAmbiguous | TrackNotFound


class TrackManager:
    def __init__(self, api: ApiClient):
        self._api = api

    async def resolve_by_key(self, track_key: str) -> SearchOutcome:
        """
        Resolve track bằng track_key (title+artist đã được normalize).

        Dùng bởi _load_track_from_key khi cần khôi phục session từ hash.
        Ưu tiên cache; nếu cache miss thì parse key thành title/artist rồi
        fetch lại.
        """
        cached_data, is_stale = await cache_lookup(track_key)
        if cached_data:
            return TrackResolution(
                track_key=track_key,
                title=cached_data.get("title", ""),
                artist=cached_data.get("artist", ""),
                yt_url=cached_data.get("yt_url", ""),
                thumb=cached_data.get("thumb", ""),
                streams=cached_data.get("streams", {}),
                yt_credits=cached_data.get("yt_credits", {}),
                genius_data=cached_data.get("genius_data"),
                mb_data=cached_data.get("mb_data"),
                lyrics=cached_data.get("lyrics"),
                synced_lyrics=cached_data.get("synced_lyrics"),
                lyrics_source=cached_data.get("lyrics_source"),
                from_cache=True,
                is_stale=is_stale,
            )
        # Cache miss — không đủ thông tin để re-fetch chính xác
        return TrackNotFound()

    async def resolve(self, query: str) -> SearchOutcome:
        if not query or not query.strip():
            return TrackNotFound()
        query = query.strip()
        if query.startswith("http"):
            return await self._resolve_from_url(query)
        return await self._resolve_from_search(query)

    async def _resolve_from_url(self, url: str) -> TrackResolution | TrackNotFound:
        title, artist, thumb, streams = await self._process_url_input(url)
        if not title:
            logger.warning("Could not extract track data from URL: %s", url[:120])
            return TrackNotFound()
        return await self._fetch_and_cache_track(
            title=title, artist=artist, thumb=thumb, streams=streams,
        )

    async def resolve_from_seed(self, seed: dict) -> SearchOutcome:
        """Resolve trực tiếp từ seed dict (title + artist), bỏ qua bước disambiguation."""
        title = seed.get("title", "")
        artist = seed.get("artist", "")
        genius_quick, yt_data = await asyncio.gather(
            self._api.fetch_genius_data(title, artist),
            search_yt(f"{title} {artist}".strip(), artist_name=artist),
        )
        if not yt_data and not genius_quick:
            logger.info("resolve_from_seed: no data found for %r / %r", title, artist)
            return TrackNotFound()
        resolved_title = title or (genius_quick or {}).get("title", "") or (yt_data or {}).get("title", "")
        resolved_artist = artist or (genius_quick or {}).get("artist", "") or (yt_data or {}).get("artist", "")
        return await self._fetch_and_cache_track(
            title=resolved_title,
            artist=resolved_artist,
            thumb=yt_data.get("thumb", "") if yt_data else "",
            streams={},
            prefer_genius=genius_quick,
            prefer_yt_data=yt_data,
        )

    async def _resolve_from_search(self, query: str) -> SearchOutcome:
        search_choices, seed_result = await self._process_text_input(query)

        # Trả về TrackAmbiguous thay vì None — caller biết rõ đây là
        # "cần người dùng chọn", không phải "không tìm thấy kết quả nào".
        if search_choices:
            return TrackAmbiguous(choices=search_choices)

        seed_title = seed_result.get("title", "") if seed_result else query
        seed_artist = seed_result.get("artist", "") if seed_result else ""

        genius_quick, yt_data = await asyncio.gather(
            self._api.fetch_genius_data(seed_title, seed_artist),
            search_yt(f"{seed_title} {seed_artist}".strip(), artist_name=seed_artist),
        )

        if not yt_data and not genius_quick and not seed_result:
            logger.info("No results found for search: %s", query)
            return TrackNotFound()

        title = (
            seed_title
            or (genius_quick or {}).get("title", "")
            or (yt_data or {}).get("title", "")
        )
        artist = (
            seed_artist
            or (genius_quick or {}).get("artist", "")
            or (yt_data or {}).get("artist", "")
        )

        return await self._fetch_and_cache_track(
            title=title,
            artist=artist,
            thumb=yt_data.get("thumb", "") if yt_data else "",
            streams={},
            prefer_genius=genius_quick,   # đã fetch ở trên, truyền vào để tái sử dụng
            prefer_yt_data=yt_data,       # tương tự
        )

    async def _fetch_and_cache_track(
        self,
        title: str,
        artist: str,
        thumb: str = "",
        streams: Optional[dict] = None,
        prefer_genius: Optional[dict] = None,
        prefer_yt_data: Optional[dict] = None,
    ) -> TrackResolution:
        track_key = make_key(title, artist)
        streams = streams or {}

        # Bước 1: Kiểm tra cache — nếu có thì trả về luôn, không cần gọi API
        cached_data, is_stale = await cache_lookup(track_key)
        if cached_data:
            return TrackResolution(
                track_key=track_key,
                title=cached_data.get("title", title),
                artist=cached_data.get("artist", artist),
                yt_url=cached_data.get("yt_url", ""),
                thumb=cached_data.get("thumb", thumb),
                streams=cached_data.get("streams", streams),
                yt_credits=cached_data.get("yt_credits", {}),
                genius_data=cached_data.get("genius_data"),
                mb_data=cached_data.get("mb_data"),
                lyrics=cached_data.get("lyrics"),
                synced_lyrics=cached_data.get("synced_lyrics"),
                lyrics_source=cached_data.get("lyrics_source"),
                from_cache=True,
                is_stale=is_stale,
            )

        # Bước 2: Quyết định những gì cần fetch.
        # Nếu caller đã fetch trước (prefer_*), tái sử dụng — tránh gọi API 2 lần.
        # Nếu chưa có, tạo coroutine để fetch song song bên dưới.
        genius_task = (
            None  # có sẵn rồi, không cần fetch
            if prefer_genius is not None
            else self._api.fetch_genius_data(title, artist)
        )
        yt_task = (
            None  # có sẵn rồi, không cần fetch
            if prefer_yt_data is not None
            else search_yt(f"{title} {artist}".strip(), artist_name=artist)
        )

        # Bước 3: Fetch song song những gì còn thiếu.
        # auto_lyrics và mb_data luôn cần fetch mới (không có prefer_ cho chúng).
        if genius_task is not None and yt_task is not None:
            # Cả hai đều cần fetch — gather cả 4 để tối đa concurrency
            genius_data, yt_data, (auto_lyrics, synced_lyrics), mb_data = await asyncio.gather(
                genius_task,
                yt_task,
                self._api.fetch_synced_lyrics(title, artist),
                self._api.fetch_musicbrainz_data(title, artist),
            )
        elif genius_task is not None:
            # Chỉ cần fetch genius — yt đã có
            genius_data, (auto_lyrics, synced_lyrics), mb_data = await asyncio.gather(
                genius_task,
                self._api.fetch_synced_lyrics(title, artist),
                self._api.fetch_musicbrainz_data(title, artist),
            )
            yt_data = prefer_yt_data
        elif yt_task is not None:
            # Chỉ cần fetch yt — genius đã có
            yt_data, (auto_lyrics, synced_lyrics), mb_data = await asyncio.gather(
                yt_task,
                self._api.fetch_synced_lyrics(title, artist),
                self._api.fetch_musicbrainz_data(title, artist),
            )
            genius_data = prefer_genius
        else:
            # Cả hai đã có sẵn — chỉ fetch auto_lyrics và mb_data
            (auto_lyrics, synced_lyrics), mb_data = await asyncio.gather(
                self._api.fetch_synced_lyrics(title, artist),
                self._api.fetch_musicbrainz_data(title, artist),
            )
            genius_data = prefer_genius
            yt_data = prefer_yt_data

        # Bước 4: Xử lý kết quả — phần này giữ nguyên hoàn toàn so với code gốc
        yt_url = yt_data.get("yt_url", "") if yt_data else ""
        desc = yt_data.get("desc", "") if yt_data else ""
        yt_credits = parse_yt_credits(desc)
        lyrics, lyrics_source = pick_lyrics(genius_data, auto_lyrics)
        # synced_lyrics already unpacked from fetch_synced_lyrics above

        # Bước 4b: Vietnamese source — runs only when title/artist looks Vietnamese,
        # and only when Genius returned no lyrics (avoid overwriting richer data).
        if should_try_viet_source(title, artist) and not lyrics:
            try:
                session = self._api._session_manager._session  # shared aiohttp session
                viet_data = await fetch_viet_track(session, f"{title} {artist}".strip())
                if viet_data:
                    if not yt_data or not yt_data.get("title"):
                        title = viet_data.get("title") or title
                        artist = viet_data.get("artist") or artist
                    if viet_data.get("lyrics"):
                        lyrics = viet_data["lyrics"]
                        lyrics_source = viet_data.get("source", "viet_music")
                    if viet_data.get("thumb") and not (yt_data and yt_data.get("thumb")):
                        thumb = viet_data["thumb"]
            except Exception as _viet_exc:
                logger.debug("viet_music fetch failed for %r: %s", title, _viet_exc)

        if yt_url and not streams:
            odesli = await self._api.get_odesli(yt_url)
            if odesli:
                streams = odesli.get("linksByPlatform", {})
                entity_id = odesli.get("entityUniqueId")
                if entity_id:
                    thumb = (
                        odesli.get("entitiesByUniqueId", {})
                        .get(entity_id, {})
                        .get("thumbnailUrl", "")
                        or thumb
                    )

        merged = merge_track_metadata(
            genius_data=genius_data, mb_data=mb_data, yt_data=yt_data
        )
        final_title = merged["title"] or title
        final_artist = merged["artist"] or artist
        final_thumb = merged["thumb"] or thumb
        final_key = make_key(final_title, final_artist)

        await cache_populate(final_key, {
            "title": final_title,
            "artist": final_artist,
            "genius_data": genius_data,
            "yt_url": yt_url,
            "thumb": final_thumb,
            "streams": streams,
            "yt_credits": yt_credits,
            "lyrics": lyrics,
            "synced_lyrics": synced_lyrics,
            "lyrics_source": lyrics_source,
            "mb_data": mb_data,
        })

        return TrackResolution(
            track_key=final_key,
            title=final_title,
            artist=final_artist,
            yt_url=yt_url,
            thumb=final_thumb,
            streams=streams,
            yt_credits=yt_credits,
            genius_data=genius_data,
            mb_data=mb_data,
            lyrics=lyrics,
            synced_lyrics=synced_lyrics,
            lyrics_source=lyrics_source,
            from_cache=False,
            is_stale=False,
        )

    async def _process_url_input(self, url: str) -> tuple[str, str, str, dict]:
        title = ""
        artist = ""
        thumb = ""
        streams: dict = {}

        odesli = await self._api.get_odesli(url)
        entity_id = odesli.get("entityUniqueId") if odesli else None
        entity = (
            odesli.get("entitiesByUniqueId", {}).get(entity_id, {})
            if entity_id else {}
        )
        # Fallback: if entityUniqueId lookup missed, pick first available entity
        if not entity and odesli:
            entities = odesli.get("entitiesByUniqueId", {})
            if entities:
                entity = next(iter(entities.values()), {})
                logger.debug("Odesli: entityUniqueId %r not in map, using first entity", entity_id)

        title = entity.get("title", "")
        artist = entity.get("artistName", "")
        thumb = entity.get("thumbnailUrl", "")
        streams = odesli.get("linksByPlatform", {}) if odesli else {}

        if title:
            return title, artist, thumb, streams

        # Spotify oEmbed fallback (public API, no auth needed)
        if "open.spotify.com/track" in url:
            try:
                from urllib.parse import urlencode as _urlencode
                oembed_url = f"https://open.spotify.com/oembed?{_urlencode({'url': url})}"
                status, data = await self._api._session_manager.fetch_json(oembed_url, timeout=6)
                if status == 200 and data:
                    raw_title = data.get("title", "")
                    if " - " in raw_title:
                        parts = raw_title.split(" - ", 1)
                        title = parts[0].strip()
                        artist = parts[1].strip()
                    else:
                        title = raw_title
                    thumb = data.get("thumbnail_url", "")
                    if title:
                        logger.info("Spotify oEmbed fallback succeeded for %s: %r / %r", url[:80], title, artist)
                        return title, artist, thumb, streams
            except Exception as exc:
                logger.warning("Spotify oEmbed fallback failed for %s: %s", url[:80], exc)

        try:
            yt_data = await search_yt(url)
            if yt_data and yt_data.get("title"):
                return (
                    yt_data["title"],
                    yt_data.get("artist", ""),
                    yt_data.get("thumb", ""),
                    {"youtube": {"url": url}},
                )
        except Exception as exc:
            logger.warning("URL parsing fallback failed: %s", exc)

        return "", "", "", {}

    async def _process_text_input(
        self, text: str
    ) -> tuple[Optional[list[dict]], Optional[dict]]:
        search_choices = await self._api.fetch_genius_search(text, limit=10)
        if len(search_choices) > 1:
            unique_choices = []
            seen_artists: set[str] = set()
            for choice in search_choices:
                artist = choice.get("artist")
                if artist and artist not in seen_artists:
                    seen_artists.add(artist)
                    unique_choices.append(choice)
                if len(unique_choices) == 7:
                    break
            if len(unique_choices) > 1:
                return unique_choices, None
            return None, unique_choices[0] if unique_choices else None
        return None, search_choices[0] if search_choices else None

    async def get_search_disambiguation(
        self, query: str
    ) -> Optional[list[dict]]:
        choices, _ = await self._process_text_input(query)
        return choices
