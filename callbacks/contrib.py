"""
Contribution callbacks: act_contrib, sub_c, sub_l, act_report.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from callback_registry import CallbackRegistry
from i18n import t
from constants import CB
from db import get_track_key_from_hash, store_track_hash


def register_contrib(registry: CallbackRegistry) -> None:
    @registry.register(CB.ACT_CONTRIB.value.rstrip("_"))
    async def handle_contrib_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return

        track_key = await get_track_key_from_hash(payload)
        if not track_key:
            await query.edit_message_text(t("session_expired", context))
            return
        from handlers import _load_track_from_key  # local import to avoid cycles

        if not await _load_track_from_key(track_key, context):
            await query.edit_message_text(t("session_expired", context))
            return

        track = context.user_data.get("track")
        if not track:
            await query.edit_message_text(t("session_expired", context))
            return

        back_hash = await store_track_hash(track["key"])
        back_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(t("btn_back", context), callback_data=f"m_main_{back_hash}")]]
        )

        track_hash = await store_track_hash(track["key"])
        await query.edit_message_text(
            t("contrib_prompt", context),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Credits", callback_data=f"sub_c_{track_hash}"),
                        InlineKeyboardButton("Lyrics", callback_data=f"sub_l_{track_hash}"),
                    ],
                    [InlineKeyboardButton(t("btn_back", context), callback_data=f"m_main_{track_hash}")],
                ]
            ),
        )

    @registry.register(CB.SUBMIT_CREDITS.value.rstrip("_"))
    async def handle_submit_credits(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return

        track_key = await get_track_key_from_hash(payload)
        if not track_key:
            await query.edit_message_text(t("session_expired", context))
            return
        from handlers import _load_track_from_key  # local import to avoid cycles

        if not await _load_track_from_key(track_key, context):
            await query.edit_message_text(t("session_expired", context))
            return

        track = context.user_data.get("track")
        if not track:
            await query.edit_message_text(t("session_expired", context))
            return

        back_hash = await store_track_hash(track["key"])
        back_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(t("btn_back", context), callback_data=f"m_main_{back_hash}")]]
        )

        context.user_data["state"] = "awaiting_credits"
        await query.edit_message_text(t("req_credits", context))

    @registry.register(CB.SUBMIT_LYRICS.value.rstrip("_"))
    async def handle_submit_lyrics(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return

        track_key = await get_track_key_from_hash(payload)
        if not track_key:
            await query.edit_message_text(t("session_expired", context))
            return
        from handlers import _load_track_from_key  # local import to avoid cycles

        if not await _load_track_from_key(track_key, context):
            await query.edit_message_text(t("session_expired", context))
            return

        track = context.user_data.get("track")
        if not track:
            await query.edit_message_text(t("session_expired", context))
            return

        # Block if lyrics already exist (API or community)
        existing_source = track.get("db_lyrics_source") or track.get("lyrics_source")
        if track.get("db_lyrics") or track.get("lyrics"):
            source_label = existing_source or "Unknown"
            back_hash = await store_track_hash(track["key"])
            await query.edit_message_text(
                t("lyrics_already_exists", context).format(source=source_label),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(t("btn_back", context), callback_data=f"m_main_{back_hash}")]]
                ),
            )
            return

        back_hash = await store_track_hash(track["key"])
        context.user_data["state"] = "awaiting_lyrics1"
        await query.edit_message_text(t("req_lyrics1", context))

    @registry.register(CB.ACT_REPORT.value.rstrip("_"))
    async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return

        track_key = await get_track_key_from_hash(payload)
        if not track_key:
            await query.edit_message_text(t("session_expired", context))
            return
        from handlers import _load_track_from_key  # local import to avoid cycles

        if not await _load_track_from_key(track_key, context):
            await query.edit_message_text(t("session_expired", context))
            return

        track = context.user_data.get("track")
        if not track:
            await query.edit_message_text(t("session_expired", context))
            return

        back_hash = await store_track_hash(track["key"])
        back_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(t("btn_back", context), callback_data=f"m_main_{back_hash}")]]
        )

        context.user_data["state"] = "awaiting_report"
        await query.edit_message_text(t("req_report", context))

