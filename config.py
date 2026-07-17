"""
Application configuration: environment variables and logging setup.
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()

# ── Logging setup ─────────────────────────────────────────────────────────
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

_LOG_FILE = os.environ.get("LOG_FILE", "")
if _LOG_FILE:
    _file_handler = RotatingFileHandler(
        _LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    _file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    _handlers.append(_file_handler)

logging.basicConfig(format=_LOG_FORMAT, level=logging.INFO, handlers=_handlers)
logger = logging.getLogger("trackcredits")

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GENIUS_TOKEN = os.environ.get("GENIUS_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

if not GENIUS_TOKEN:
    logger.warning(
        "GENIUS_TOKEN is not set. Credits and lyrics from Genius will be unavailable. "
        "Get a free token at https://genius.com/api-clients"
    )

# ── Multi-admin support ───────────────────────────────────────────────────
# ADMIN_CHAT_IDS accepts a comma-separated list of Telegram user IDs.
# Legacy ADMIN_CHAT_ID (single value) is still supported for backwards compat.
_admin_ids_raw = os.environ.get("ADMIN_CHAT_IDS") or os.environ.get("ADMIN_CHAT_ID")
ADMIN_CHAT_IDS: set[int] = set()
if _admin_ids_raw:
    for _part in _admin_ids_raw.split(","):
        _part = _part.strip()
        if _part:
            try:
                ADMIN_CHAT_IDS.add(int(_part))
            except ValueError:
                logger.warning("Invalid admin ID %r — skipped.", _part)

# First element kept as ADMIN_CHAT_ID for backwards compatibility.
ADMIN_CHAT_ID: int | None = next(iter(ADMIN_CHAT_IDS), None)

if not ADMIN_CHAT_IDS:
    logger.warning("No valid ADMIN_CHAT_IDS configured; admin features disabled.")


def is_admin(user_id: int) -> bool:
    """Return True if user_id belongs to a configured admin."""
    return user_id in ADMIN_CHAT_IDS

# ── Webhook config (set WEBHOOK_URL to enable webhook mode) ───────────────
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")           # e.g. https://mybot.fly.dev
WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", "8443"))
WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH", "/webhook")
WEBHOOK_LISTEN = os.environ.get("WEBHOOK_LISTEN", "0.0.0.0")

# ── Credits system config ────────────────────────────────────────────────
CREDITS_STARTING = int(os.environ.get("CREDITS_STARTING", "20"))
CREDITS_SEARCH_COST = int(os.environ.get("CREDITS_SEARCH_COST", "1"))
CREDITS_DAILY_BONUS = int(os.environ.get("CREDITS_DAILY_BONUS", "3"))
