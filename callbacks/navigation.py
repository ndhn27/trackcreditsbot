"""
Navigation callbacks: lang, top, force_search, pick, pick_none.
"""

from __future__ import annotations

import time

from telegram import Update
from telegram.ext import ContextTypes

from callback_registry import CallbackRegistry
from i18n import t
from constants import CB


def register_navigation(registry: CallbackRegistry) -> None:
    @registry.register(CB.TOP_PREFIX.value.rstrip("_"))
    async def handle_top(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return

        try:
            page = max(0, int(payload))
        except (TypeError, ValueError):
            await query.edit_message_text(t("invalid_page", context))
            return

        from handlers import _send_top_page

        await _send_top_page(
            send_fn=None,
            context=context,
            page=page,
            edit_fn=lambda text, **kwargs: query.edit_message_text(text, **kwargs),
        )

    @registry.register(CB.LANG_PREFIX.value.rstrip("_"))
    async def handle_lang(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return
        data = query.data or ""

        if payload:
            context.user_data["lang"] = payload
        else:
            parts = data.split("_", 1)
            context.user_data["lang"] = parts[1] if len(parts) > 1 else ""
        await query.edit_message_text(t("welcome", context), parse_mode="HTML")

    @registry.register(CB.FORCE_SEARCH.value.rstrip("_"))
    async def handle_force_search(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return
        await query.edit_message_text(t("search_prompt", context))

    @registry.register(CB.PICK_NONE.value.rstrip("_"))
    @registry.register(CB.PICK_PREFIX.value.rstrip("_"))
    async def handle_pick(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return
        data = query.data or ""

        disambig = context.user_data.get("disambig") or {}
        if not disambig or (int(time.time()) - disambig.get("created_at", 0)) > 300:
            context.user_data.pop("disambig", None)
            await query.edit_message_text(t("session_expired", context))
            return
        choices = disambig.get("choices", [])
        query_text = disambig.get("query", "")
        if data == CB.PICK_NONE.value or not choices:
            context.user_data.pop("disambig", None)
            await query.edit_message_text(t("wrong_result", context), parse_mode="HTML")
            return
        try:
            index = int(payload) if payload else int(data.split("_")[1])
        except (IndexError, ValueError):
            await query.edit_message_text(t("invalid_choice", context))
            return
        if index < 0 or index >= len(choices):
            await query.edit_message_text(t("choice_expired", context))
            return
        chosen = choices[index]
        context.user_data.pop("disambig", None)
        await query.edit_message_text(t("analyzing", context))

        from handlers import _handle_known_track

        await _handle_known_track(query.message, context, title=query_text, artist=chosen["artist"], seed=chosen)
