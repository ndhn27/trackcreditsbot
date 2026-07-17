"""
Application factory and Dependency Injection setup.

AppContext (from app_context.py) is the single authoritative DI container.
It holds the two long-lived services — db and api — whose lifecycles
(start / stop) are managed here.

bot_data keys set by this module:
  "app_context"   → AppContext instance (canonical reference)
  "api"           → same as app_context.api  (convenience alias for handlers)
  "db"            → same as app_context.db   (convenience alias)
  "track_manager" → TrackManager wired with the injected ApiClient
"""

from __future__ import annotations

from app_context import AppContext, make_default_api, make_default_db
import app_context as _app_context_module
from track_manager import TrackManager
from config import logger
import db as db_module
from metrics import start_metrics_flusher, stop_metrics_flusher


async def setup_app_context(bot_data: dict) -> None:
    """
    Build the AppContext, start all services, and populate bot_data.

    Called once during application startup (main.py).
    The AppContext type-checks both concrete instances against
    DatabaseProto / ApiClientProto at static-analysis time, ensuring
    any future mock or alternative implementation satisfies the contract.
    """
    try:
        logger.info("🚀 Initializing application services...")

        db = make_default_db()
        api = make_default_api()

        # Inject db vào module-level registry TRƯỚC khi AppContext.start() chạy.
        # Điều này đảm bảo cache.py (dùng db_execute) và handlers.py (dùng
        # db_transaction) đều nói chuyện với đúng instance này — không còn
        # singleton thứ hai được tạo âm thầm khi import.
        db_module.set_default_db(db)

        # AppContext.start() calls db.start() + db.init_db() + api.start()
        # in the correct order.  A single await replaces the scattered
        # startup sequence that previously lived here.
        ctx = AppContext(db=db, api=api)
        await ctx.start()
        logger.info("✅ Database and API client initialized")

        track_manager = TrackManager(api=api)
        logger.info("✅ TrackManager initialized")

        # Canonical reference — always prefer this for new code.
        bot_data["app_context"] = ctx

        # Convenience aliases kept for backward compatibility with
        # existing handlers and callbacks that read bot_data["api"] / ["db"].
        bot_data["api"] = ctx.api
        bot_data["db"] = ctx.db
        bot_data["track_manager"] = track_manager

        # Bot reference is set later in main.py post_init via set_bot(app.bot)

        # Start persistent metrics background flusher
        start_metrics_flusher()

        logger.info("✅ All services initialized and injected")

    except Exception as exc:
        logger.error("❌ Failed to initialize app context: %s", exc)
        raise


async def cleanup_app_context(bot_data: dict) -> None:
    """
    Shut down all services via AppContext.stop().

    Called once during application shutdown (main.py).
    """
    try:
        logger.info("🛑 Cleaning up services...")

        # Flush any buffered metrics before shutdown
        await stop_metrics_flusher()

        ctx: AppContext | None = bot_data.get("app_context")
        if ctx:
            # AppContext.stop() calls api.stop() then db.stop() in order.
            await ctx.stop()
            logger.info("✅ All services stopped")
        else:
            # Fallback: clean up individual keys if ctx was never set
            # (e.g., startup crashed mid-way).
            if api := bot_data.get("api"):
                await api.stop()
                logger.info("✅ API client closed (fallback)")
            if db := bot_data.get("db"):
                await db.stop()
                logger.info("✅ Database closed (fallback)")

    except Exception as exc:
        logger.error("❌ Failed to cleanup app context: %s", exc)

