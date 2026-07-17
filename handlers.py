"""
Telegram command, message, callback, and inline handlers.
"""

from __future__ import annotations

import io
import csv
import re
import time
from config import ADMIN_CHAT_ID, ADMIN_CHAT_IDS, is_admin, logger
from i18n import t, t_lang
from metrics import get_metrics, get_daily_stats
from utils import escape_html, safe_url
from constants import Limits, Scores
from typing import Dict, List, Optional

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InputFile,
    Update,
)
from telegram.ext import ContextTypes

from api import ApiClient
from cache import (
    approved_cache_invalidate,
    check_rate_limit,
    delete_song_cache,
    promo_cache_invalidate,
)
from credits import (
    ensure_user_credits,
    get_balance,
    deduct_credits,
    add_credits,
    claim_daily_bonus,
    credit_history,
    SEARCH_COST,
    DAILY_BONUS,
    DAILY_BONUS_COOLDOWN,
    SUBMIT_EARN,
    APPROVAL_EARN,
)
from db import db_transaction, make_key, store_track_hash
from repository import (
    approved_data_upsert_credits_tx,
    approved_data_upsert_lyrics_tx,
    leaderboard_add_score_tx,
    leaderboard_get_page,
    promo_links_insert,
    submissions_count_pending,
    submissions_get_by_id,
    submissions_insert,
    submissions_lock_for_update_tx,
    submissions_reject,
    submissions_set_status_tx,
    # New admin/credits repo functions
    bot_users_upsert,
    bot_users_count,
    bot_users_get_all_ids,
    bans_add,
    bans_remove,
    bans_is_banned,
    bans_list,
    submissions_get_pending_page,
    submissions_count_by_status,
    stats_credit_totals,
    stats_top_credit_users,
)
from services import build_main_text, get_kb, schedule_track_cache_refresh
from track_manager import TrackManager, TrackResolution, TrackAmbiguous, TrackNotFound

from callback_registry import CallbackRegistry

_registry: CallbackRegistry | None = None


def _get_registry() -> CallbackRegistry:
    global _registry
    if _registry is None:
        from callbacks import register_all
        _registry = CallbackRegistry()
        register_all(_registry)
    return _registry


async def _load_track_from_key(
    track_key: str, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    manager: TrackManager = context.bot_data.get("track_manager")
    if not manager:
        return False
    result = await manager.resolve_by_key(track_key)
    if not isinstance(result, TrackResolution):
        return False
    approved_row = await result.get_approved_data()
    _set_track_context(context, result, approved_row)
    return True


def _approved_payload(row: Optional[tuple]) -> dict:
    db_lyrics = None
    db_lyrics_source = None
    db_lyrics_contributor = None
    if row and row[2]:
        db_lyrics = row[2]
        db_lyrics_source = row[3] or "Unknown"
        db_lyrics_contributor = row[4] or "Admin"
    return {
        "db_credits": row[0] if row else None,
        "db_cred_cont": row[1] if row else None,
        "db_lyrics": db_lyrics,
        "db_lyrics_source": db_lyrics_source,
        "db_lyrics_contributor": db_lyrics_contributor,
    }


def _set_track_context(
    context: ContextTypes.DEFAULT_TYPE,
    resolution: TrackResolution,
    approved_row: Optional[tuple],
) -> str:
    approved = _approved_payload(approved_row)
    status_key = resolution.cache_status_key
    main_text = build_main_text(
        resolution.title,
        resolution.artist,
        resolution.thumb,
        t(status_key, context),
    )
    context.user_data["track"] = {
        "key": resolution.track_key,
        "title": resolution.title,
        "artist": resolution.artist,
        "yt_url": resolution.yt_url,
        "thumb": resolution.thumb,
        "streams": resolution.streams,
        "yt_credits": resolution.yt_credits,
        "lyrics": resolution.lyrics,
        "synced_lyrics": resolution.synced_lyrics,
        "lyrics_source": resolution.lyrics_source,
        "lyrics_contributor": None,
        "genius_data": resolution.genius_data,
        "mb_data": resolution.mb_data,
        "main_text": main_text,
        **approved,
    }
    return main_text


_LANG_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🇬🇧 English",    callback_data="lang_en"),
        InlineKeyboardButton("🇻🇳 Tiếng Việt", callback_data="lang_vi"),
    ],
    [
        InlineKeyboardButton("🇪🇸 Español",    callback_data="lang_es"),
        InlineKeyboardButton("🇵🇹 Português",  callback_data="lang_pt"),
    ],
    [
        InlineKeyboardButton("🇫🇷 Français",   callback_data="lang_fr"),
        InlineKeyboardButton("🇷🇺 Русский",    callback_data="lang_ru"),
    ],
    [
        InlineKeyboardButton("🇰🇷 한국어",      callback_data="lang_ko"),
        InlineKeyboardButton("🇯🇵 日本語",      callback_data="lang_ja"),
    ],
    [
        InlineKeyboardButton("🇨🇳 中文",        callback_data="lang_zh"),
        InlineKeyboardButton("🇸🇦 العربية",    callback_data="lang_ar"),
    ],
])

_LANG_PROMPT = "Please select your language / Vui lòng chọn ngôn ngữ:"


async def _register_user(update: Update) -> None:
    """Upsert user into bot_users and ensure they have a credits row."""
    user = update.effective_user
    if not user:
        return
    from repository import bot_users_upsert
    await bot_users_upsert(user.id, user.username or "")
    await ensure_user_credits(user.id, user.username or "")


async def _check_banned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Return True and notify user if they are banned. False otherwise."""
    user = update.effective_user
    if not user:
        return False
    from repository import bans_is_banned
    if await bans_is_banned(user.id):
        if update.message:
            await update.message.reply_text("\U0001f6ab You have been banned from using this bot.")
        elif update.callback_query:
            await update.callback_query.answer("\U0001f6ab You are banned.", show_alert=True)
        return True
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if await _check_banned(update, context):
        return
    await _register_user(update)
    await update.message.reply_text(_LANG_PROMPT, reply_markup=_LANG_KEYBOARD)


async def cmd_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text(_LANG_PROMPT, reply_markup=_LANG_KEYBOARD)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text(
        t("help_txt", context),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    context.user_data.pop("state", None)
    context.user_data.pop("t_lyr", None)
    if context.user_data.get("track"):
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(t("btn_continue_track", context), callback_data="m_main")],
                [InlineKeyboardButton(t("btn_new_search", context), callback_data="force_search")],
            ]
        )
        await update.message.reply_text(t("cancel_with_track", context), reply_markup=keyboard)
        return
    await update.message.reply_text(t("cancel_no_track", context))


async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await _send_top_page(update.message.reply_text, context, page=0)


async def _send_top_page(send_fn, context: ContextTypes.DEFAULT_TYPE, page: int = 0, edit_fn=None):
    page = max(0, int(page))
    offset = page * Limits.TOP_PAGE_SIZE

    rows = await leaderboard_get_page(Limits.TOP_PAGE_SIZE + 1, offset)

    if not rows and page == 0:
        await (edit_fn or send_fn)(t("top_empty", context))
        return

    has_next = len(rows) > Limits.TOP_PAGE_SIZE
    rows = rows[:Limits.TOP_PAGE_SIZE]

    medals = ["🥇", "🥈", "🥉"]
    lines = [t("top_title", context).format(page=page + 1) + "\n"]
    for index, (username, score) in enumerate(rows):
        rank = medals[index] if page == 0 and index < 3 else f"{offset + index + 1}."
        lines.append(f"{rank} @{escape_html(username or 'unknown')} - <b>{score}</b>")
    lines.append(f"\n<i>{t('top_footer', context)}</i>")

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(t("top_prev", context), callback_data=f"top_{page - 1}"))
    if has_next:
        nav.append(InlineKeyboardButton(t("top_next", context), callback_data=f"top_{page + 1}"))

    reply_markup = InlineKeyboardMarkup([nav]) if nav else None
    await (edit_fn or send_fn)(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Full admin dashboard: metrics + stats + pending count + action buttons."""
    if not update.message:
        return
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(t("access_denied", context))
        return

    # ── Metrics (now persistent/async) ───────────────────────────────────
    metrics = await get_metrics()
    today_stats = await get_daily_stats()

    lines = ["<b>📊 Persistent Metrics (all-time)</b>"]
    if metrics:
        for key, value in sorted(metrics.items()):
            lines.append(f"  ▪ <code>{key}</code>: <b>{value}</b>")
    else:
        lines.append("  <i>No data yet</i>")

    lines.append("\n<b>📅 Today's Activity</b>")
    if today_stats:
        for key, value in sorted(today_stats.items()):
            lines.append(f"  ▪ <code>{key}</code>: <b>{value}</b>")
    else:
        lines.append("  <i>No activity today</i>")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

    # ── User + submission stats ───────────────────────────────────────────
    total_users = await bot_users_count()
    pending_count = await submissions_count_pending()
    approved_count = await submissions_count_by_status("approved")
    rejected_count = await submissions_count_by_status("rejected")
    credit_stats = await stats_credit_totals()

    stats_text = (
        f"<b>👥 Users:</b> {total_users}\n"
        f"<b>📥 Submissions:</b> {pending_count} pending · {approved_count} approved · {rejected_count} rejected\n"
        f"<b>💎 Credits:</b> {credit_stats['earned']} earned · {credit_stats['spent']} spent · "
        f"{credit_stats['unique_users']} unique spenders"
    )
    await update.message.reply_text(stats_text, parse_mode="HTML")

    # ── Action keyboard ───────────────────────────────────────────────────
    track = context.user_data.get("track")
    if track:
        promo_keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(t("admin_btn_drums", context), callback_data="add_promo_Drums + Bass")],
                [InlineKeyboardButton(t("admin_btn_instrumental", context), callback_data="add_promo_Instrumental")],
                [InlineKeyboardButton(t("admin_btn_custom_promo", context), callback_data="add_promo_custom")],
                [InlineKeyboardButton(t("admin_btn_clear_promo", context), callback_data="clear_promo")],
            ]
        )
        await update.message.reply_text(
            f"<b>{t('admin_promo_title', context)}</b>\n🎵 {escape_html(track['title'])}",
            parse_mode="HTML",
            reply_markup=promo_keyboard,
        )

    quick_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 Pending subs", callback_data="admin_subs_0"),
            InlineKeyboardButton("🚫 Bans list", callback_data="admin_bans_0"),
        ],
        [InlineKeyboardButton("📤 Export CSV", callback_data="admin_export")],
    ])
    await update.message.reply_text(
        "<b>⚡ Quick Actions</b>\nUse /ban &lt;user_id&gt; [reason], /unban &lt;user_id&gt;, "
        "/broadcast &lt;msg&gt;, /giftcredits &lt;user_id&gt; &lt;amount&gt;",
        parse_mode="HTML",
        reply_markup=quick_kb,
    )


async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /ban <user_id> [reason]"""
    if not update.message or not is_admin(update.effective_user.id):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Usage: /ban <user_id> [reason]")
        return
    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user_id.")
        return
    reason = " ".join(args[1:]) if len(args) > 1 else "No reason given"
    await bans_add(target_id, "", reason, update.effective_user.id)
    await update.message.reply_text(f"🚫 User <code>{target_id}</code> banned. Reason: {escape_html(reason)}", parse_mode="HTML")


async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /unban <user_id>"""
    if not update.message or not is_admin(update.effective_user.id):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user_id.")
        return
    removed = await bans_remove(target_id)
    if removed:
        await update.message.reply_text(f"✅ User <code>{target_id}</code> unbanned.", parse_mode="HTML")
    else:
        await update.message.reply_text(f"ℹ️ User <code>{target_id}</code> was not banned.", parse_mode="HTML")


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /broadcast <message> — sends to all registered users."""
    if not update.message or not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message text>")
        return

    text = " ".join(context.args)
    all_ids = await bot_users_get_all_ids()
    if not all_ids:
        await update.message.reply_text("No registered users found.")
        return

    status_msg = await update.message.reply_text(f"📡 Broadcasting to {len(all_ids)} users…")
    sent, failed = 0, 0
    for uid in all_ids:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"📢 <b>Announcement</b>\n\n{escape_html(text)}",
                parse_mode="HTML",
            )
            sent += 1
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ Broadcast complete.\n<b>{sent}</b> delivered · <b>{failed}</b> failed.",
        parse_mode="HTML",
    )


async def cmd_giftcredits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /giftcredits <user_id> <amount>"""
    if not update.message or not is_admin(update.effective_user.id):
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Usage: /giftcredits <user_id> <amount>")
        return
    try:
        target_id = int(args[0])
        amount = int(args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Invalid user_id or amount.")
        return

    new_balance = await add_credits(target_id, amount, f"admin_gift_by_{update.effective_user.id}")
    await update.message.reply_text(
        f"💎 Gifted <b>{amount}</b> credits to <code>{target_id}</code>. "
        f"New balance: <b>{new_balance}</b>.",
        parse_mode="HTML",
    )
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🎁 You received <b>{amount} credits</b> from the admin!\nNew balance: <b>{new_balance}</b>.",
            parse_mode="HTML",
        )
    except Exception:
        pass


async def cmd_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /subs [page] — paginated pending submissions."""
    if not update.message or not is_admin(update.effective_user.id):
        return
    args = context.args or []
    page = max(0, int(args[0]) - 1) if args and args[0].isdigit() else 0
    limit = 5
    rows = await submissions_get_pending_page(limit + 1, page * limit)
    has_next = len(rows) > limit
    rows = rows[:limit]

    if not rows:
        await update.message.reply_text("✅ No pending submissions." if page == 0 else "No more submissions.")
        return

    lines = [f"<b>📥 Pending Submissions — Page {page + 1}</b>\n"]
    for row in rows:
        sub_id, title, artist, sub_type, submitter, created_at = row
        lines.append(
            f"<b>#{sub_id}</b> [{sub_type}] <i>{escape_html(title)} — {escape_html(artist)}</i>\n"
            f"  by @{escape_html(submitter)}"
        )

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"admin_subs_{page - 1}"))
    if has_next:
        nav.append(InlineKeyboardButton("Next ▶", callback_data=f"admin_subs_{page + 1}"))

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([nav]) if nav else None,
    )


async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /export — sends a CSV of all submissions."""
    if not update.message or not is_admin(update.effective_user.id):
        return
    from db import db_execute
    rows = await db_execute(
        "SELECT id, track_title, track_artist, sub_type, submitter_name, status, created_at "
        "FROM submissions ORDER BY created_at DESC LIMIT 2000",
        fetch_all=True,
    )
    if not rows:
        await update.message.reply_text("No submissions data to export.")
        return

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "track_title", "track_artist", "sub_type", "submitter", "status", "created_at"])
    for row in rows:
        writer.writerow(row)

    buf.seek(0)
    await update.message.reply_document(
        document=InputFile(io.BytesIO(buf.getvalue().encode()), filename="submissions_export.csv"),
        caption=f"📤 Export: {len(rows)} submissions",
    )


async def cmd_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User: /daily — claim daily bonus credits."""
    if not update.message:
        return
    if await _check_banned(update, context):
        return
    user = update.effective_user
    if not user:
        return

    await ensure_user_credits(user.id, user.username or "")
    awarded, next_ts = await claim_daily_bonus(user.id)

    if awarded == 0:
        import datetime
        next_dt = datetime.datetime.fromtimestamp(next_ts, tz=datetime.timezone.utc)
        remaining = next_ts - int(time.time())
        h, m = divmod(remaining // 60, 60)
        await update.message.reply_text(
            f"⏳ Daily bonus already claimed!\n"
            f"Next bonus available in <b>{h}h {m}m</b>.",
            parse_mode="HTML",
        )
        return

    balance = await get_balance(user.id)
    await update.message.reply_text(
        f"🎁 <b>+{awarded} credits</b> daily bonus!\n"
        f"💎 New balance: <b>{balance}</b>.",
        parse_mode="HTML",
    )


async def cmd_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User: /credits — check balance and recent history."""
    if not update.message:
        return
    if await _check_banned(update, context):
        return
    user = update.effective_user
    if not user:
        return

    balance = await ensure_user_credits(user.id, user.username or "")
    history = await credit_history(user.id, limit=5)

    lines = [f"💎 <b>Your Credits: {balance}</b>\n"]
    if history:
        lines.append("<b>Recent transactions:</b>")
        for amount, reason, ts in history:
            sign = "+" if amount > 0 else ""
            lines.append(f"  {sign}{amount} — <code>{escape_html(reason)}</code>")
    lines.append(f"\n<i>Each search costs {SEARCH_COST} credit. Use /daily for a free bonus.</i>")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def ask_disambiguation(msg, context, choices: List[Dict]):
    session = context.user_data.get("disambig") or {}
    query_text = session.get("query", "")
    lines = [t("disambig_prompt", context).format(query=escape_html(query_text)) + "\n"]
    keyboard = [
        [InlineKeyboardButton(f"👤 {choice['artist']}", callback_data=f"pick_{index}")]
        for index, choice in enumerate(choices)
    ]
    keyboard.append([InlineKeyboardButton(t("disambig_none", context), callback_data="pick_none")])
    await msg.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if await _check_banned(update, context):
        return
    if not context.user_data.get("lang"):
        await start(update, context)
        return

    user = update.effective_user
    user_id = user.id
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not await check_rate_limit(user_id, chat_id):
        await update.message.reply_text(t("rate_limited", context))
        return

    text = update.message.text.strip()
    if len(text) > Limits.MAX_TEXT_QUERY_LEN:
        await update.message.reply_text(t("input_too_long", context))
        return

    # ── Credits gate ───────────────────────────────────────────────────────
    balance = await ensure_user_credits(user_id, user.username or "")
    if balance < SEARCH_COST:
        await update.message.reply_text(
            f"💸 <b>Not enough credits!</b>\n"
            f"You need {SEARCH_COST} credit to search but have {balance}.\n"
            f"Use /daily to claim your daily bonus or /credits to check your balance.",
            parse_mode="HTML",
        )
        return

    msg = await update.message.reply_text(t("analyzing", context))
    spent = await deduct_credits(user_id, SEARCH_COST, "search")
    if not spent:
        await msg.edit_text("💸 Could not deduct credits. Please try again.")
        return

    manager: TrackManager = context.bot_data["track_manager"]
    result = await manager.resolve(text)

    if isinstance(result, TrackAmbiguous):
        context.user_data["disambig"] = {
            "choices": result.choices,
            "query": text,
            "message_id": msg.message_id,
            "created_at": int(time.time()),
        }
        await ask_disambiguation(msg, context, result.choices)
        return

    if isinstance(result, TrackNotFound):
        if text.startswith("http"):
            await msg.edit_text(t("url_extract_failed", context))
        else:
            await msg.edit_text(t("not_found", context))
        return

    resolution: TrackResolution = result

    if resolution.is_stale:
        schedule_track_cache_refresh(
            resolution.track_key, resolution.title, resolution.artist,
            context.bot_data["api"],
        )

    approved_row = await resolution.get_approved_data()
    main_text = _set_track_context(context, resolution, approved_row)

    await msg.edit_text(
        main_text,
        parse_mode="HTML",
        reply_markup=await get_kb(context, resolution.track_key),
    )


async def _handle_known_track(msg, context: ContextTypes.DEFAULT_TYPE, title: str, artist: str, seed: dict | None = None):
    manager: TrackManager = context.bot_data["track_manager"]
    if seed:
        resolution = await manager.resolve_from_seed(seed)
    else:
        resolution = await manager.resolve(f"{title} {artist}")

    if not isinstance(resolution, TrackResolution):
        await msg.edit_text(t("track_load_failed", context))
        return

    if resolution.is_stale:
        schedule_track_cache_refresh(
            resolution.track_key, resolution.title, resolution.artist,
            context.bot_data["api"],
        )

    approved_row = await resolution.get_approved_data()
    main_text = _set_track_context(context, resolution, approved_row)

    await msg.edit_text(
        main_text,
        parse_mode="HTML",
        reply_markup=await get_kb(context, resolution.track_key),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return
    try:
        await _get_registry().dispatch(update, context)
    except ValueError as e:
        if "No callback route" in str(e):
            logger.warning("Unknown callback: %r", query.data)
        else:
            logger.exception("Error in callback handler: %r", query.data)
    except Exception:
        logger.exception("Error in callback handler: %r", query.data)


async def process_sub_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    state = context.user_data.get("state")
    if not state:
        await handle_input(update, context)
        return

    text = update.message.text.strip()
    track = context.user_data.get("track")
    user = update.effective_user

    if state == "awaiting_promo_name":
        if not is_admin(user.id):
            context.user_data.pop("state", None)
            await update.message.reply_text(t("access_denied", context))
            return
        if not text:
            await update.message.reply_text(t("admin_promo_name_prompt", context))
            return
        custom_name = text.strip()
        context.user_data["state"] = f"awaiting_promo_{custom_name}"
        await update.message.reply_text(
            t("admin_promo_prompt", context).format(promo_type=custom_name)
        )
        return

    if state.startswith("awaiting_promo_"):
        if not is_admin(user.id):
            context.user_data.pop("state", None)
            await update.message.reply_text(t("access_denied", context))
            return
        if not track:
            context.user_data.pop("state", None)
            await update.message.reply_text(t("promo_session_expired", context))
            return
        promo_type = state.replace("awaiting_promo_", "")
        await promo_links_insert(track["key"], promo_type, text)
        await promo_cache_invalidate(track["key"])
        return

    if state == "awaiting_lyrics1":
        context.user_data["t_lyr"] = text
        context.user_data["state"] = "awaiting_lyrics2"
        await update.message.reply_text(t("req_lyrics2", context))
        return

    submission_type = state.replace("awaiting_", "")
    content_text = text
    source_text = ""
    if state == "awaiting_lyrics2":
        content_text = context.user_data.pop("t_lyr", "")
        source_text = text
        submission_type = "lyrics"

    if not track:
        context.user_data.pop("state", None)
        await update.message.reply_text(t("session_expired", context))
        return
    if len(content_text) > Limits.MAX_SUBMIT_CONTENT_LEN:
        await update.message.reply_text(t("content_too_long", context))
        return

    submission_id = await submissions_insert(
        track["title"],
        track["artist"],
        track["key"],
        content_text,
        source_text,
        submission_type,
        user.id,
        user.username or user.first_name,
    )
    context.user_data.pop("state", None)

    # Reward submit credits
    new_bal = await add_credits(user.id, SUBMIT_EARN, f"submit_{submission_type}")
    await update.message.reply_text(
        t("submitted", context) + f"\n\n💎 <b>+{SUBMIT_EARN} credits</b> for contributing! Balance: <b>{new_bal}</b>.",
        parse_mode="HTML",
    )

    if ADMIN_CHAT_IDS:
        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("Approve", callback_data=f"admin_app_{submission_id}"),
                InlineKeyboardButton("Reject", callback_data=f"admin_rej_{submission_id}"),
            ]]
        )
        for admin_id in ADMIN_CHAT_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"<b>NEW {submission_type.upper()}</b>\n"
                        f"{escape_html(track['title'])} by @{escape_html(user.username or user.first_name or str(user.id))}\n\n"
                        f"<code>{escape_html(content_text[:Limits.ADMIN_PREVIEW_LEN])}</code>"
                    ),
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )
            except Exception as exc:
                logger.warning("Failed to notify admin %s about submission %s: %s", admin_id, submission_id, exc)


async def admin_act(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    query = update.callback_query
    if not is_admin(update.effective_user.id):
        await query.edit_message_text(t("access_denied", context))
        return

    match = re.match(r"^admin_(app|rej)_(\d+)$", data)
    if not match:
        await query.edit_message_text(t("admin_invalid_request", context))
        return
    action, submission_id = match.group(1), int(match.group(2))

    submission = await submissions_get_by_id(submission_id)
    if not submission:
        await query.edit_message_text(t("admin_sub_not_found", context))
        return

    _, title, track_key, content_text, source_text, submission_type, user_id, username = submission

    if action == "app":
        async with db_transaction() as conn:
            status_row = await submissions_lock_for_update_tx(conn, submission_id)
            if not status_row or status_row[0] != "pending":
                await query.edit_message_text(t("admin_already_processed", context))
                return

            if submission_type == "credits":
                await approved_data_upsert_credits_tx(conn, track_key, content_text, username)
            elif submission_type == "lyrics":
                await approved_data_upsert_lyrics_tx(conn, track_key, content_text, source_text, username)

            points = (
                Scores.APPROVED_REPORT
                if submission_type == "report"
                else Scores.APPROVED_CONTRIB
            )
            await leaderboard_add_score_tx(conn, user_id, username, points)
            await submissions_set_status_tx(conn, submission_id, "approved")

        await delete_song_cache(track_key)
        await approved_cache_invalidate(track_key)

        # Reward extra approval credits (outside the transaction is fine here)
        try:
            new_bal = await add_credits(user_id, APPROVAL_EARN, f"approved_{submission_type}")
        except Exception as exc:
            logger.warning("Failed to grant approval credits to %s: %s", user_id, exc)
            new_bal = None

        await query.edit_message_text(
            t("admin_approved", context).format(sub_type=submission_type, title=escape_html(title)),
            parse_mode="HTML",
        )
        try:
            back_hash = await store_track_hash(track_key)
            user_keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    t_lang("btn_view_song", "en"),
                    callback_data=f"m_main_{back_hash}",
                )
            ]])
            credit_note = f"\n💎 <b>+{APPROVAL_EARN} bonus credits</b> added! Balance: <b>{new_bal}</b>." if new_bal else ""
            await context.bot.send_message(
                chat_id=user_id,
                text=t("user_contrib_approved", context).format(
                    sub_type=submission_type,
                    title=escape_html(title),
                ) + credit_note,
                parse_mode="HTML",
                reply_markup=user_keyboard,
            )
        except Exception as exc:
            logger.warning("Failed to notify user %s after approval: %s", user_id, exc)
        return

    await submissions_reject(submission_id)
    await query.edit_message_text(
        t("admin_rejected", context).format(sub_type=submission_type, title=escape_html(title)),
        parse_mode="HTML",
    )
    # Notify submitter so they know their contribution was reviewed
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=t("user_contrib_rejected", context).format(
                sub_type=submission_type,
                title=escape_html(title),
            ),
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.warning("Failed to notify user %s after rejection: %s", user_id, exc)


async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.inline_query.query.strip()
    if not query_text or len(query_text) < 2:
        await update.inline_query.answer([], cache_time=10)
        return

    api: ApiClient = context.bot_data["api"]
    tracks = await api.fetch_genius_search(query_text, limit=5)

    bot_user = context.bot.username or "TrackCreditsBot"
    results = []
    seen = set()

    for track in tracks or []:
        title = track.get("title", "")
        artist = track.get("artist", "")
        if not title:
            continue
        key = make_key(title, artist)
        if key in seen:
            continue
        seen.add(key)

        lines = [f"🎵 <b>{escape_html(title)}</b> — <i>{escape_html(artist)}</i>"]
        if track.get("album"):
            lines.append(f"💿 {escape_html(track['album'])}")
        if track.get("release_date"):
            lines.append(f"📅 {escape_html(track['release_date'])}")
        if track.get("isrc"):
            lines.append(f"🔖 ISRC: <code>{track['isrc']}</code>")
        if track.get("spotify_url"):
            lines.append(f"🎧 <a href='{safe_url(track['spotify_url'])}'>Listen on Spotify</a>")
        lines.append(
            f"\n🤖 Open <a href='https://t.me/{bot_user}'>@{bot_user}</a> for full credits & lyrics"
        )

        desc_parts = [
            part
            for part in [artist, track.get("album"), (track.get("release_date", "")[:4] or None)]
            if part
        ]
        results.append(
            InlineQueryResultArticle(
                id=key[:64],
                title=f"🎵 {title}",
                description=" · ".join(desc_parts),
                thumbnail_url=track.get("thumb") or None,
                input_message_content=InputTextMessageContent(
                    "\n".join(lines),
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                ),
            )
        )

    genius_data = None
    if not results:
        genius_data = await api.fetch_genius_data(query_text, "")
    if not results and genius_data:
        title = genius_data.get("title", "")
        artist = genius_data.get("artist", "")
        if title:
            key = make_key(title, artist)
            results.append(
                InlineQueryResultArticle(
                    id=key[:64],
                    title=f"🎵 {title}",
                    description=artist,
                    input_message_content=InputTextMessageContent(
                        f"🎵 <b>{escape_html(title)}</b> — <i>{escape_html(artist)}</i>\n\n"
                        f"🤖 Open <a href='https://t.me/{bot_user}'>@{bot_user}</a> for full credits & lyrics",
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    ),
                )
            )

    await update.inline_query.answer(results or [], cache_time=30)


# ══════════════════════════════════════════════════════════════════════════
# FIX #11 — Terms of Service & Privacy Policy
# ══════════════════════════════════════════════════════════════════════════

async def cmd_terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/terms — Show Terms of Service."""
    if not update.message:
        return
    await update.message.reply_text(t("terms_text", context), parse_mode="HTML",
                                    disable_web_page_preview=True)


async def cmd_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/privacy — Show Privacy Policy."""
    if not update.message:
        return
    await update.message.reply_text(t("privacy_text", context), parse_mode="HTML",
                                    disable_web_page_preview=True)


# ══════════════════════════════════════════════════════════════════════════
# FIX #14 — /buy and /confirmpayment
# ══════════════════════════════════════════════════════════════════════════

async def cmd_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/buy — Show credit packages and initiate payment."""
    if not update.message:
        return
    if await _check_banned(update, context):
        return

    from payment import CREDIT_PACKAGES, PROVIDER, create_payment
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    user = update.effective_user
    balance = await ensure_user_credits(user.id, user.username or "")

    lines = [f"💎 <b>Buy Credits</b>\n\nCurrent balance: <b>{balance} credits</b>\n"]
    keyboard = []
    for pack in CREDIT_PACKAGES:
        lines.append(f"• {pack['label']}")
        keyboard.append([InlineKeyboardButton(
            pack["label"], callback_data=f"buy_{pack['id']}"
        )])

    provider_note = {"momo": "💳 Payment via MoMo", "stripe": "💳 Payment via Stripe (card)",
                     "manual": "🏦 Manual bank transfer — admin confirms"}.get(PROVIDER, "")
    lines.append(f"\n<i>{provider_note}</i>")

    await update.message.reply_text(
        "\n".join(lines), parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_buy_callback(update: Update, context, pack_id: str):
    """Called from button_handler when callback_data starts with 'buy_'."""
    query = update.callback_query
    if not query:
        return

    from payment import create_payment, CREDIT_PACKAGES, get_package
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    pack = get_package(pack_id)
    if not pack:
        await query.answer("Unknown package.", show_alert=True)
        return

    user = update.effective_user
    try:
        result = await create_payment(user.id, pack_id)
    except RuntimeError as exc:
        await query.edit_message_text(
            f"⚠️ Payment error: {escape_html(str(exc))}", parse_mode="HTML"
        )
        return

    if result.get("pay_url"):
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("💳 Pay Now", url=result["pay_url"])
        ]])
        await query.edit_message_text(
            f"💎 <b>{pack['credits']} credits</b> — click below to pay.\n"
            f"Order: <code>{result['order_id']}</code>",
            parse_mode="HTML", reply_markup=keyboard,
        )
    else:
        # Manual transfer
        await query.edit_message_text(
            result.get("instructions", "Contact admin to complete payment."),
            parse_mode="HTML",
        )


async def cmd_confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /confirmpayment <user_id> <pack_id> [order_id]"""
    if not update.message:
        return
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(t("access_denied", context))
        return

    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: /confirmpayment &lt;user_id&gt; &lt;pack_id&gt; [order_id]\n"
            "Example: /confirmpayment 123456789 pack_120",
            parse_mode="HTML",
        )
        return

    try:
        target_id = int(args[0])
        pack_id = args[1]
        order_id = args[2] if len(args) > 2 else f"manual_admin_{int(time.time())}"
    except ValueError:
        await update.message.reply_text("Invalid user_id.")
        return

    from payment import fulfill_payment
    try:
        new_balance = await fulfill_payment(target_id, pack_id, order_id)
    except ValueError as exc:
        await update.message.reply_text(f"Error: {exc}")
        return

    await update.message.reply_text(
        f"✅ Payment confirmed for <code>{target_id}</code>.\n"
        f"New balance: <b>{new_balance} credits</b>.",
        parse_mode="HTML",
    )
    try:
        from payment import get_package
        pack = get_package(pack_id)
        if pack:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🎉 Payment confirmed! <b>+{pack['credits']} credits</b> added.\n"
                     f"New balance: <b>{new_balance} credits</b>.",
                parse_mode="HTML",
            )
    except Exception as exc:
        logger.warning("Could not notify user %s about payment: %s", target_id, exc)
