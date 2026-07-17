from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Dict

import yt_dlp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from api import merge_track_metadata, parse_yt_credits, pick_lyrics
from cache import cache_populate, delete_song_cache, get_promos
from config import logger
from i18n import t
from utils import escape_html, safe_url
from db import make_key, store_track_hash

if TYPE_CHECKING:
    from app_context import ApiClientProto

ALLOWED_FIELDS = [
    "Released on",
    "Album",
    "Label",
    "ISRC",
    "Genre",
    "Popularity",
    "Producer",
    "Writers",
    "Composer",
    "Lyricist",
    "Mixing Engineer",
    "Mastering Engineer",
    "Arranger",
    "Recording Engineer",
    "Distributed by",
    "Publisher",
    "Interpolates",
    "Samples",
    "Cover Of",
    "Copyright ©",
    "Phonographic Copyright ℗",
]

_CACHE_REFRESH_SEMAPHORE = asyncio.Semaphore(3)
_REFRESH_TASKS: dict[str, asyncio.Task] = {}


def build_main_text(title: str, artist: str, thumb: str, status_text: str) -> str:
    thumb_anchor = f"<a href='{safe_url(thumb)}'>&#8203;</a>" if thumb else ""
    return (
        f"{thumb_anchor}"
        f"🎵 <b>{escape_html(title)}</b> — <i>{escape_html(artist)}</i>\n\n"
        f"{status_text}"
    )


def truncate_text_naturally(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    boundary = max(text.rfind("\n", 0, limit), text.rfind(" ", 0, limit))
    if boundary < int(limit * 0.6):
        boundary = limit
    return text[:boundary].rstrip() + "..."


def render_credits(
    genius_data: dict | None,
    yt_credits: dict,
    db_credits: str | None,
    track_title: str,
    track_artist: str,
    *,
    mb_data: dict | None = None,
    lang: str = "en",
) -> str:
    from i18n import t_lang

    merged: dict = {}

    if genius_data and genius_data.get("credits"):
        merged.update(genius_data.get("credits", {}))

    for key, value in yt_credits.items():
        if key not in merged and value:
            merged[key] = value

    if mb_data:
        if mb_data.get("isrc") and "ISRC" not in merged:
            merged["ISRC"] = mb_data.get("isrc")
        if mb_data.get("label") and "Label" not in merged:
            merged["Label"] = mb_data.get("label")

    clean_title = re.sub(
        rf"^{re.escape(track_artist)}\s*\s*",
        "",
        track_title,
        flags=re.IGNORECASE,
    ).strip()

    lines = [f"<b>{escape_html(clean_title or track_title)}</b> — <i>{escape_html(track_artist)}</i>", ""]

    has_original_credits = False
    for field in ALLOWED_FIELDS:
        if field in merged:
            lines.append(f"▪ <b>{field}:</b> {escape_html(str(merged[field]))}")
            has_original_credits = True

    if not has_original_credits:
        lines.append(t_lang("credits_no_data", lang))

    if db_credits and db_credits.strip():
        lines.append(f"\n{t_lang('credits_community_section', lang)}")
        
        # Filter db_credits - only include lines with colons
        filtered_lines = [line.strip() for line in db_credits.split('\n') if ':' in line and line.strip()]
        if filtered_lines:
            raw_community = truncate_text_naturally('\n'.join(filtered_lines), 1800)
            lines.append(escape_html(raw_community))

    lines.append(f"\n{t_lang('credits_rights', lang).format(artist=escape_html(track_artist))}")
    return "\n".join(lines)


async def get_kb(ctx: ContextTypes.DEFAULT_TYPE, track_key: str) -> InlineKeyboardMarkup:
    track_hash = await store_track_hash(track_key)
    rows = []
    for promo_type, promo_url in await get_promos(track_key):
        safe_promo_url = safe_url(promo_url)
        if safe_promo_url != "#":
            rows.append([InlineKeyboardButton(f"🎧 {promo_type} từ kênh Admin", url=safe_promo_url)])
    rows.extend(
        [
            [
                InlineKeyboardButton(t("btn_streams", ctx), callback_data=f"m_streams_{track_hash}"),
                InlineKeyboardButton(t("btn_credits", ctx), callback_data=f"m_credits_{track_hash}"),
            ],
            [InlineKeyboardButton(t("btn_lyrics", ctx), callback_data=f"m_lyrics_{track_hash}")],
            [
                InlineKeyboardButton(t("btn_contrib", ctx), callback_data=f"act_contrib_{track_hash}"),
                InlineKeyboardButton(t("btn_report", ctx), callback_data=f"act_report_{track_hash}"),
            ],
            [InlineKeyboardButton(t("btn_wrong", ctx), callback_data=f"m_wrong_{track_hash}")],
        ]
    )
    return InlineKeyboardMarkup(rows)


async def search_yt(query: str, artist_name: str = "") -> dict | None:
    def _parse(info: dict) -> dict:
        title = re.sub(
            r"\s*(Official.*?|Lyrics?.*?|Audio.*?|MV.*?|Video.*?)]",
            "",
            info.get("title", "Unknown"),
            flags=re.IGNORECASE,
        ).strip()
        return {
            "title": title,
            "artist": (info.get("channel") or "").replace(" - Topic", "").replace("VEVO", "").strip(),
            "yt_url": info.get("webpage_url", f"https://www.youtube.com/watch?v={info.get('id')}"),
            "desc": info.get("description", ""),
            "thumb": info.get("thumbnail", ""),
        }

    def _run() -> dict | None:
        options = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": False,
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            try:
                if query.startswith("http"):
                    info = ydl.extract_info(query, download=False)
                    return _parse(info)

                search_queries = [query]
                for search_query in search_queries:
                    result = ydl.extract_info(f"ytsearch:{search_query}", download=False)
                    entries = [entry for entry in result.get("entries", []) if entry]
                    if not entries:
                        continue
                    if artist_name:
                        normalized_artist = re.sub(r"\s+", "", artist_name.lower())
                        for entry in entries:
                            channel = re.sub(
                                r"\s+",
                                "",
                                (entry.get("channel") or "").lower().replace(" - topic", "").replace("vevo", ""),
                            )
                            if normalized_artist in channel or channel in normalized_artist:
                                return _parse(entry)
                    return _parse(entries[0]) if entries else None
            except Exception as exc:
                logger.warning("yt-dlp search failed for %s: %s", query, exc)
                return None
        return None

    return await asyncio.to_thread(_run)


async def _refresh_track_cache(
    track_key: str,
    title: str,
    artist: str,
    api: "ApiClientProto",
) -> None:
    async with _CACHE_REFRESH_SEMAPHORE:
        try:
            genius_data, yt_data, auto_lyrics, mb_data = await asyncio.gather(
                api.fetch_genius_data(title, artist),
                search_yt(f"{title} {artist}".strip(), artist_name=artist),
                api.fetch_auto_lyrics(title, artist),
                api.fetch_musicbrainz_data(title, artist),
            )
            yt_url = yt_data.get("yt_url", "") if yt_data else ""
            desc = yt_data.get("desc", "") if yt_data else ""
            odesli = await api.get_odesli(yt_url) if yt_url else None
            streams = odesli.get("linksByPlatform", {}) if odesli else {}
            ent_id = odesli.get("entityUniqueId") if odesli else None
            thumb = odesli.get("entitiesByUniqueId", {}).get(ent_id, {}).get("thumbnailUrl", "") if ent_id else ""

            merged = merge_track_metadata(genius_data=genius_data, mb_data=mb_data, yt_data=yt_data)
            final_title = merged.get("title") or title
            final_artist = merged.get("artist") or artist
            final_thumb = merged.get("thumb") or thumb
            final_key = make_key(final_title, final_artist)
            lyrics, lyrics_source = pick_lyrics(genius_data, auto_lyrics)

            await cache_populate(
                final_key,
                {
                    "title": final_title,
                    "artist": final_artist,
                    "genius_data": genius_data,
                    "yt_url": yt_url,
                    "thumb": final_thumb,
                    "streams": streams,
                    "yt_credits": parse_yt_credits(desc),
                    "lyrics": lyrics,
                    "lyrics_source": lyrics_source,
                    "mb_data": mb_data,
                },
            )
            if final_key != track_key:
                await delete_song_cache(track_key)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Background cache refresh failed for %s: %s", track_key, exc)


_REFRESH_TASKS_MAX: int = 500


def schedule_track_cache_refresh(
    track_key: str,
    title: str,
    artist: str,
    api: "ApiClientProto",
) -> asyncio.Task | None:
    existing = _REFRESH_TASKS.get(track_key)
    if existing and not existing.done():
        return existing

    if len(_REFRESH_TASKS) >= _REFRESH_TASKS_MAX:
        logger.warning(
            "schedule_track_cache_refresh: task queue full (%d), skipping refresh for %s",
            _REFRESH_TASKS_MAX,
            track_key,
        )
        return None

    task = asyncio.create_task(_refresh_track_cache(track_key, title, artist, api))
    _REFRESH_TASKS[track_key] = task

    def _cleanup(done_task: asyncio.Task) -> None:
        current = _REFRESH_TASKS.get(track_key)
        if current is done_task:
            _REFRESH_TASKS.pop(track_key, None)

    task.add_done_callback(_cleanup)
    return task


async def shutdown_background_tasks() -> None:
    tasks = [task for task in _REFRESH_TASKS.values() if not task.done()]
    if not tasks:
        return
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    _REFRESH_TASKS.clear()
