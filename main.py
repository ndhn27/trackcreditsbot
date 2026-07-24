"""
Bot entry point.

Run mode is selected by environment variable:
  • WEBHOOK_URL set  → webhook mode (production-grade, recommended)
  • WEBHOOK_URL unset → polling mode (dev/local)

Health server (always on):
  HEALTH_PORT    Port for /health and /ready endpoints (default 8080)

Payment:
  PAYMENT_PROVIDER  momo | stripe | manual (default: manual)
"""
from __future__ import annotations

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

from app_factory import setup_app_context, cleanup_app_context
from config import (
    TOKEN, WEBHOOK_URL, WEBHOOK_PORT, WEBHOOK_PATH, WEBHOOK_LISTEN,
    WEBHOOK_SECRET_TOKEN, logger,
)
from health import start_health_server, stop_health_server
from handlers import (
    start, cmd_lang, cmd_help, cmd_cancel, cmd_top, cmd_daily, cmd_credits,
    cmd_terms, cmd_privacy, cmd_buy, cmd_confirm_payment,
    cmd_admin, cmd_ban, cmd_unban, cmd_broadcast, cmd_giftcredits, cmd_subs, cmd_export,
    button_handler, process_sub_handler, handle_inline_query,
)


async def post_init(app: Application) -> None:
    await setup_app_context(app.bot_data)
    await start_health_server()
    from app_context import set_bot
    set_bot(app.bot)


async def post_shutdown(app: Application) -> None:
    await stop_health_server()
    await cleanup_app_context(app.bot_data)


def _build_app() -> Application:
    app = Application.builder().token(TOKEN).build()
    app.post_init = post_init
    app.post_shutdown = post_shutdown

    # User commands
    for cmd, fn in [
        ("start", start), ("lang", cmd_lang), ("help", cmd_help),
        ("cancel", cmd_cancel), ("top", cmd_top), ("daily", cmd_daily),
        ("credits", cmd_credits), ("terms", cmd_terms), ("privacy", cmd_privacy),
        ("buy", cmd_buy),
    ]:
        app.add_handler(CommandHandler(cmd, fn))

    # Admin commands
    for cmd, fn in [
        ("admin", cmd_admin), ("ban", cmd_ban), ("unban", cmd_unban),
        ("broadcast", cmd_broadcast), ("giftcredits", cmd_giftcredits),
        ("subs", cmd_subs), ("export", cmd_export),
        ("confirmpayment", cmd_confirm_payment),
    ]:
        app.add_handler(CommandHandler(cmd, fn))

    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(InlineQueryHandler(handle_inline_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_sub_handler))
    return app


def main() -> None:
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment.")
        return

    app = _build_app()

    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL.rstrip('/')}{WEBHOOK_PATH}"
        logger.info("Starting in WEBHOOK mode: %s (port %s)", webhook_url, WEBHOOK_PORT)
        app.run_webhook(
            listen=WEBHOOK_LISTEN, port=WEBHOOK_PORT,
            url_path=WEBHOOK_PATH, webhook_url=webhook_url,
            secret_token=WEBHOOK_SECRET_TOKEN or None,
            allowed_updates=["message", "callback_query", "inline_query"],
            drop_pending_updates=True,
        )
    else:
        logger.info("Starting in POLLING mode.")
        app.run_polling(allowed_updates=["message", "callback_query", "inline_query"])


if __name__ == "__main__":
    main()
