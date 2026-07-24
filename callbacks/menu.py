"""
Menu callbacks: m_main, m_wrong, m_streams, m_credits, m_lyrics.
"""

from __future__ import annotations

import time
from urllib.parse import quote_plus

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from callback_registry import CallbackRegistry
from i18n import t
from utils import escape_html, safe_url
from constants import CB
from db import get_track_key_from_hash, store_track_hash
from services import get_kb, render_credits, truncate_text_naturally


def register_menu(registry: CallbackRegistry) -> None:
    @registry.register(CB.MENU_MAIN_PREFIX.value.rstrip("_"))
    async def handle_main(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return

        if payload:
            track_key = await get_track_key_from_hash(payload)
            if not track_key:
                await query.edit_message_text(t("session_expired", context))
                return
            from handlers import _load_track_from_key

            if not await _load_track_from_key(track_key, context):
                await query.edit_message_text(t("session_expired", context))
                return

        track = context.user_data.get("track")
        if not track:
            await query.edit_message_text(t("session_expired", context))
            return

        await query.edit_message_text(
            track["main_text"],
            parse_mode="HTML",
            reply_markup=await get_kb(context, track["key"]),
        )

    @registry.register(CB.MENU_WRONG.value.rstrip("_"))
    async def handle_wrong(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return

        track_key = await get_track_key_from_hash(payload)
        if not track_key:
            await query.edit_message_text(t("session_expired", context))
            return
        from handlers import _load_track_from_key, ask_disambiguation

        if not await _load_track_from_key(track_key, context):
            await query.edit_message_text(t("session_expired", context))
            return

        track = context.user_data.get("track")
        if not track:
            await query.edit_message_text(t("session_expired", context))
            return

        back_hash = await store_track_hash(track["key"])
        back_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(t("btn_back", context), callback_data=f"{CB.MENU_MAIN_PREFIX.value}_{back_hash}")]]
        )

        title = track["title"]
        await query.edit_message_text(
            t("searching_other_artists", context).format(title=escape_html(title)),
            parse_mode="HTML",
        )
        search_choices = await context.bot_data["api"].fetch_genius_search(title, limit=10)
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
            context.user_data["disambig"] = {
                "choices": unique_choices,
                "query": title,
                "message_id": query.message.message_id,
                "created_at": int(time.time()),
            }
            await ask_disambiguation(query.message, context, unique_choices)
            return
        await query.edit_message_text(
            t("no_other_artists", context).format(title=escape_html(title)),
            parse_mode="HTML",
            reply_markup=back_keyboard,
        )

    @registry.register(CB.MENU_STREAMS.value.rstrip("_"))
    async def handle_streams(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return

        track_key = await get_track_key_from_hash(payload)
        if not track_key:
            await query.edit_message_text(t("session_expired", context))
            return
        from handlers import _load_track_from_key

        if not await _load_track_from_key(track_key, context):
            await query.edit_message_text(t("session_expired", context))
            return

        track = context.user_data.get("track")
        if not track:
            await query.edit_message_text(t("session_expired", context))
            return

        back_hash = await store_track_hash(track["key"])
        back_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(t("btn_back", context), callback_data=f"{CB.MENU_MAIN_PREFIX.value}_{back_hash}")]]
        )

        text = t("streams_title", context) + "\n"
        platform_icons = {
            "spotify": "🎵",
            "youtube": "▶️",
            "youtubeMusic": "🎵",
            "appleMusic": "🍎",
            "deezer": "🎧",
            "tidal": "🌊",
            "soundcloud": "☁️",
            "amazonMusic": "📦",
        }
        for platform, payload_item in track["streams"].items():
            url = payload_item.get("url") if isinstance(payload_item, dict) else str(payload_item)
            text += f"{platform_icons.get(platform, '🔗')} {platform}: {escape_html(url)}\n"

        query_text = quote_plus(f"{track['title']} {track['artist']}")
        text += f"\n{t('search_links', context)}\n"
        if "spotify" not in track["streams"]:
            text += f"Spotify: https://open.spotify.com/search/{query_text}\n"
        if "appleMusic" not in track["streams"]:
            text += f"Apple Music: https://music.apple.com/search?term={query_text}\n"
        text += f"SoundCloud: https://soundcloud.com/search?q={query_text}\n"
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=back_keyboard,
        )

    @registry.register(CB.MENU_CREDITS.value.rstrip("_"))
    async def handle_credits(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return

        track_key = await get_track_key_from_hash(payload)
        if not track_key:
            await query.edit_message_text(t("session_expired", context))
            return
        from handlers import _load_track_from_key

        if not await _load_track_from_key(track_key, context):
            await query.edit_message_text(t("session_expired", context))
            return

        track = context.user_data.get("track")
        if not track:
            await query.edit_message_text(t("session_expired", context))
            return

        back_hash = await store_track_hash(track["key"])
        back_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(t("btn_back", context), callback_data=f"{CB.MENU_MAIN_PREFIX.value}_{back_hash}")]]
        )

        lang = (context.user_data or {}).get("lang", "en")
        text = render_credits(
            track.get("genius_data"),
            track.get("yt_credits", {}),
            track.get("db_credits"),
            track["title"],
            track["artist"],
            mb_data=track.get("mb_data"),
            lang=lang,
        )
        if track.get("db_cred_cont"):
            text += t("credits_community_by", context).format(contributor=escape_html(track["db_cred_cont"]))
        genius_url = (track.get("genius_data") or {}).get("genius_url")
        if genius_url:
            text += f"\n\n<a href='{safe_url(genius_url)}'>{t('view_on_genius', context)}</a>"
        spotify_url = (track.get("streams", {}).get("spotify") or {}).get("url")
        if spotify_url:
            text += f"\n<a href='{safe_url(spotify_url)}'>{t('listen_on_spotify', context)}</a>"
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=back_keyboard,
        )

    @registry.register(CB.MENU_LYRICS.value.rstrip("_"))
    async def handle_lyrics(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        """Handle lyrics display callback."""
        query = update.callback_query
        if not query:
            return

        track_key = await get_track_key_from_hash(payload)
        if not track_key:
            await query.edit_message_text(t("session_expired", context))
            return

        from handlers import _load_track_from_key
        if not await _load_track_from_key(track_key, context):
            await query.edit_message_text(t("session_expired", context))
            return

        track = context.user_data.get("track")
        if not track:
            await query.edit_message_text(t("session_expired", context))
            return

        back_hash = await store_track_hash(track["key"])
        back_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(t("btn_back", context), callback_data=f"{CB.MENU_MAIN_PREFIX.value}_{back_hash}")]]
        )

        parts = [f"<b>{t('lyrics_title', context)}</b>"]

        if track.get("db_lyrics"):
            raw_lyrics = truncate_text_naturally(track["db_lyrics"], 3000)
            parts.append(escape_html(raw_lyrics))

            if track.get("db_lyrics_source"):
                parts.append(
                    f"\n<i>{t('lyrics_source_label', context).format(source=escape_html(track['db_lyrics_source']))}</i>"
                )
            if track.get("db_lyrics_contributor"):
                parts.append(
                    t("community_contrib_label", context).format(
                        contributor=escape_html(track["db_lyrics_contributor"])
                    )
                )
        elif track.get("lyrics"):
            raw_lyrics = truncate_text_naturally(track["lyrics"], 3000)
            parts.append(escape_html(raw_lyrics))

            if track.get("lyrics_source"):
                parts.append(
                    f"\n<i>{t('lyrics_source_label', context).format(source=escape_html(track['lyrics_source']))}</i>"
                )
        else:
            parts.append(t("no_lyrics", context))

        # If synced lyrics available, offer a download button
        if track.get("synced_lyrics"):
            lrc_hash = await store_track_hash(track["key"])
            back_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(t("btn_back", context), callback_data=f"{CB.MENU_MAIN_PREFIX.value}_{back_hash}"),
                    InlineKeyboardButton(t("btn_lrc", context), callback_data=f"{CB.MENU_LRC.value}_{lrc_hash}"),
                ],
            ])

        await query.edit_message_text(
            "\n".join(parts),
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=back_keyboard,
        )

    @registry.register(CB.MENU_LRC.value.rstrip("_"))
    async def handle_lrc(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        """Send the synced LRC file for download."""
        query = update.callback_query
        if not query:
            return

        track_key = await get_track_key_from_hash(payload)
        if not track_key:
            await query.answer(t("session_expired", context), show_alert=True)
            return

        from handlers import _load_track_from_key
        if not await _load_track_from_key(track_key, context):
            await query.answer(t("session_expired", context), show_alert=True)
            return

        track = context.user_data.get("track")
        synced = track.get("synced_lyrics") if track else None
        if not synced:
            await query.answer(t("no_lyrics", context), show_alert=True)
            return

        from telegram import InputFile
        import io
        safe_title = (track.get("title") or "lyrics").replace("/", "-").replace("\\", "-")
        filename = f"{safe_title}.lrc"
        await query.answer()
        await query.message.reply_document(
            document=InputFile(io.BytesIO(synced.encode("utf-8")), filename=filename),
            caption=t("lrc_title", context),
        )
