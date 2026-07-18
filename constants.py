"""
Typed constants extracted from hardcoded strings in handlers.py/services.py/cache.py.

NOTE: This module is intentionally stdlib-only and does not change existing call sites yet.
"""

from __future__ import annotations

from enum import Enum

__all__ = ["CB", "State", "AWAITING_PROMO_TEMPLATE", "Limits"]


class _StrEnum(str, Enum):
    """Backport-ish StrEnum for Python < 3.11."""

    def __str__(self) -> str:  # pragma: no cover
        return str(self.value)


class CB(_StrEnum):
    """Callback data tokens/prefixes used by Telegram inline keyboard callbacks."""

    # Prefix for contribution menu callback (built in services.py; routed in handlers.py).
    ACT_CONTRIB = "act_contrib"
    # Prefix for report flow callback (built in services.py; routed in handlers.py).
    ACT_REPORT = "act_report"

    # Prefix for admin promo-link flow callbacks (handlers.py).
    ADD_PROMO_PREFIX = "add_promo"
    # Admin promo type option callback for "Drums + Bass" (handlers.py).
    ADD_PROMO_DRUMS_BASS = "add_promo_Drums + Bass"
    # Admin promo type option callback for "Instrumental" (handlers.py).
    ADD_PROMO_INSTRUMENTAL = "add_promo_Instrumental"
    # Admin promo type option callback for custom type (handlers.py).
    ADD_PROMO_CUSTOM = "add_promo_custom"

    # Prefix for admin submission callbacks (handlers.py).
    ADMIN_PREFIX = "admin"
    # Prefix for admin approve submission callback (handlers.py).
    ADMIN_APPROVE = "admin_app"
    # Prefix for admin reject submission callback (handlers.py).
    ADMIN_REJECT = "admin_rej"

    # Callback to clear promo links for current track (handlers.py).
    CLEAR_PROMO = "clear_promo"

    # Callback to force a new search when user has an active session (handlers.py).
    FORCE_SEARCH = "force_search"

    # Prefix for language-selection callbacks (handlers.py).
    LANG_PREFIX = "lang"
    # Language-selection callback for English (handlers.py).
    LANG_EN = "lang_en"
    # Language-selection callbacks for additional languages (handlers.py).
    LANG_VI = "lang_vi"
    LANG_ES = "lang_es"
    LANG_PT = "lang_pt"
    LANG_FR = "lang_fr"
    LANG_RU = "lang_ru"
    LANG_KO = "lang_ko"
    LANG_JA = "lang_ja"
    LANG_ZH = "lang_zh"
    LANG_AR = "lang_ar"

    # Prefix for Credits menu callback (built in services.py; routed in handlers.py).
    MENU_CREDITS = "m_credits"
    # Prefix for Lyrics menu callback (built in services.py; routed in handlers.py).
    MENU_LYRICS = "m_lyrics"
    # Callback for synced LRC download (callbacks/menu.py).
    MENU_LRC = "m_lrc"
    # Callback for returning to the main menu without a track hash (handlers.py).
    MENU_MAIN = "m_main"
    # Prefix for returning to the main menu with a track hash (handlers.py).
    MENU_MAIN_PREFIX = "m_main"
    # Prefix for Streams menu callback (built in services.py; routed in handlers.py).
    MENU_STREAMS = "m_streams"
    # Prefix for "Wrong track" callback (built in services.py; routed in handlers.py).
    MENU_WRONG = "m_wrong"

    # Prefix for disambiguation choice callbacks (handlers.py).
    PICK_PREFIX = "pick"
    # Callback for disambiguation "none of the above" (handlers.py).
    PICK_NONE = "pick_none"

    # Prefix for "submit credits" callbacks (handlers.py).
    SUBMIT_CREDITS = "sub_c"
    # Prefix for "submit lyrics" callbacks (handlers.py).
    SUBMIT_LYRICS = "sub_l"

    # Prefix for leaderboard pagination callbacks (handlers.py).
    TOP_PREFIX = "top"


class State(_StrEnum):
    """User session state values stored in context.user_data['state'] (handlers.py)."""

    # Waiting for user to submit credits text (handlers.py: process_sub_handler).
    AWAITING_CREDITS = "awaiting_credits"
    # Waiting for lyrics step 1 (lyrics body) (handlers.py: process_sub_handler).
    AWAITING_LYRICS_STEP1 = "awaiting_lyrics1"
    # Waiting for lyrics step 2 (source/author) (handlers.py: process_sub_handler).
    AWAITING_LYRICS_STEP2 = "awaiting_lyrics2"
    # Prefix for admin promo link input state (handlers.py: awaiting_promo_*).
    AWAITING_PROMO_PREFIX = "awaiting_promo_"
    # Waiting for user to submit a report/problem description (handlers.py: process_sub_handler).
    AWAITING_REPORT = "awaiting_report"
    # Waiting for admin to type the custom promo type name (handlers.py).
    AWAITING_PROMO_NAME = "awaiting_promo_name"


# Format template for the admin promo input state key (handlers.py).
# Usage: AWAITING_PROMO_TEMPLATE.format(promo_type=some_type)
AWAITING_PROMO_TEMPLATE: str = "awaiting_promo_{promo_type}"

class Limits:
    """Shared limits and TTLs — single source of truth for cache.py and handlers.py."""

    # --- Cache & Rate Limits ---
    RATE_MAX: int = 10           # cache.check_rate_limit: per-user max events per window.
    RATE_WIND: int = 60          # cache.check_rate_limit: per-user window in seconds.
    CHAT_RATE_MAX: int = 20      # cache.check_rate_limit: per-chat max events per window.
    CHAT_RATE_WIND: int = 60     # cache.check_rate_limit: per-chat window in seconds.

    MEM_TTL: int = 3600                  # cache.mem_cache_get/set: memory cache TTL seconds.
    MEM_CACHE_MAX: int = 1000            # cache.mem_cache_set: max in-memory entries.
    DB_SOFT_TTL: int = 7 * 24 * 3600    # cache.db_cache_get: stale threshold in seconds.
    DB_HARD_TTL: int = 14 * 24 * 3600   # cache.db_cache_get: hard expiry in seconds.

    # --- Handlers & UI Limits ---
    TOP_PAGE_SIZE: int = 10
    MAX_TEXT_QUERY_LEN: int = 1024
    MAX_SUBMIT_CONTENT_LEN: int = 8000
    MAX_SUBMIT_SOURCE_LEN: int = 1000
    ADMIN_PREVIEW_LEN: int = 3500
    DB_BLOB_MAX_LEN: int = 120_000

    # --- Inline Query Limits ---
    INLINE_SEARCH_LIMIT: int = 5
    INLINE_CACHE_EMPTY: int = 10
    INLINE_CACHE_FULL: int = 30

class Scores:
    """Điểm thưởng cho hệ thống Leaderboard"""
    APPROVED_CONTRIB: int = 5
    APPROVED_REPORT: int = 2
