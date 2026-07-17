"""
Admin callbacks: admin_app, admin_rej, add_promo, clear_promo.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from callback_registry import CallbackRegistry
from cache import promo_cache_invalidate
from config import is_admin
from i18n import t
from constants import CB
from db import db_execute, store_track_hash


def register_admin(registry: CallbackRegistry) -> None:
    @registry.register(CB.ADMIN_PREFIX.value.rstrip("_"))
    @registry.register(CB.ADMIN_APPROVE.value.rstrip("_"))
    @registry.register(CB.ADMIN_REJECT.value.rstrip("_"))
    async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return
        data = query.data or ""

        if not is_admin(update.effective_user.id):
            await query.edit_message_text(t("access_denied", context))
            return
        from handlers import admin_act

        await admin_act(update, context, data)

    @registry.register(CB.ADD_PROMO_PREFIX.value.rstrip("_"))
    async def handle_add_promo(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return

        if not is_admin(update.effective_user.id):
            await query.edit_message_text(t("access_denied", context))
            return

        promo_type = payload or (query.data or "").replace(CB.ADD_PROMO_PREFIX.value, "")
        if promo_type == "custom":
            context.user_data["state"] = "awaiting_promo_name"
            await query.edit_message_text(t("admin_promo_name_prompt", context))
        else:
            context.user_data["state"] = f"awaiting_promo_{promo_type}"
            await query.edit_message_text(
                t("admin_promo_prompt", context).format(promo_type=promo_type)
            )

    @registry.register(CB.CLEAR_PROMO.value.rstrip("_"))
    async def handle_clear_promo(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query:
            return

        if not is_admin(update.effective_user.id):
            await query.edit_message_text(t("access_denied", context))
            return

        track = context.user_data.get("track")
        if not track:
            await query.edit_message_text(t("session_expired", context))
            return

        back_hash = await store_track_hash(track["key"])
        back_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(t("btn_back", context), callback_data=f"{CB.MENU_MAIN_PREFIX.value}_{back_hash}")]]
        )

        await db_execute("DELETE FROM promo_links WHERE track_key = $1", (track["key"],))
        await promo_cache_invalidate(track["key"])
        await query.edit_message_text(t("admin_promo_cleared", context), reply_markup=back_keyboard)


def register_admin_extended(registry: CallbackRegistry) -> None:
    """Register paginated subs, bans list, and export callbacks."""
    from handlers import (
        escape_html,
        bans_list as _bans_list,
        submissions_get_pending_page as _subs_page,
        submissions_count_by_status,
    )

    @registry.register("admin_subs")
    async def handle_admin_subs(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query or not is_admin(update.effective_user.id):
            return
        page = int(payload) if payload.isdigit() else 0
        limit = 5
        rows = await _subs_page(limit + 1, page * limit)
        has_next = len(rows) > limit
        rows = rows[:limit]

        if not rows:
            await query.answer("No pending submissions." if page == 0 else "No more submissions.")
            return

        lines = [f"<b>📥 Pending — Page {page + 1}</b>\n"]
        for row in rows:
            sub_id, title, artist, sub_type, submitter, _ = row
            lines.append(
                f"<b>#{sub_id}</b> [{sub_type}] <i>{escape_html(title)}</i>\n"
                f"  by @{escape_html(submitter)}"
            )
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"admin_subs_{page - 1}"))
        if has_next:
            nav.append(InlineKeyboardButton("Next ▶", callback_data=f"admin_subs_{page + 1}"))

        await query.edit_message_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([nav]) if nav else None,
        )

    @registry.register("admin_bans")
    async def handle_admin_bans(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query or not is_admin(update.effective_user.id):
            return
        bans = await _bans_list(limit=20)
        if not bans:
            await query.answer("No banned users.")
            return
        lines = ["<b>🚫 Banned Users</b>\n"]
        for user_id, username, reason, banned_at in bans:
            lines.append(f"<code>{user_id}</code> @{escape_html(username or '?')} — {escape_html(reason or '')}")
        await query.edit_message_text("\n".join(lines), parse_mode="HTML")

    @registry.register("admin_export")
    async def handle_admin_export(update: Update, context: ContextTypes.DEFAULT_TYPE, payload: str) -> None:
        query = update.callback_query
        if not query or not is_admin(update.effective_user.id):
            return
        await query.answer("Use /export command to download the CSV.")
