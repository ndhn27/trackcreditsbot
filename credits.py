"""
Credits system — the in-bot currency that gates searches and rewards contributions.

Flow:
  • New users receive STARTING_CREDITS when they first /start the bot.
  • Each successful search costs SEARCH_COST credits.
  • Submitting any contribution earns SUBMIT_EARN credits immediately.
  • An approved submission earns APPROVAL_EARN additional credits.
  • Daily login bonus: DAILY_BONUS credits, claimable once every 24 h.
  • Admins can grant arbitrary amounts via /giftcredits.

Public API
──────────
  ensure_user_credits(user_id)         → int  (balance, creating row if new)
  get_balance(user_id)                 → int
  deduct_credits(user_id, amount, reason) → bool  (False = insufficient)
  add_credits(user_id, amount, reason) → int  (new balance)
  claim_daily_bonus(user_id)           → (awarded: int, next_claim_ts: int)
                                           awarded=0 if cooldown not yet elapsed
  credit_history(user_id, limit)       → list[tuple(amount, reason, ts)]
"""
from __future__ import annotations

import time
import logging

from db import db_execute

logger = logging.getLogger("trackcredits.credits")

# ── Constants (override via config if desired) ────────────────────────────
STARTING_CREDITS: int = 20      # free credits on /start
SEARCH_COST: int = 1            # credits spent per search
SUBMIT_EARN: int = 2            # earned for submitting content
APPROVAL_EARN: int = 5          # extra earned when admin approves submission
DAILY_BONUS: int = 3            # daily login bonus
DAILY_BONUS_COOLDOWN: int = 86_400  # seconds between bonus claims (24 h)


# ── Internal helpers ──────────────────────────────────────────────────────

async def _log_transaction(user_id: int, amount: int, reason: str) -> None:
    try:
        await db_execute(
            "INSERT INTO credit_transactions (user_id, amount, reason, created_at) "
            "VALUES ($1, $2, $3, $4)",
            (user_id, amount, reason, int(time.time())),
        )
    except Exception as exc:
        logger.warning("Failed to log credit transaction for user %s: %s", user_id, exc)


# ── Public API ────────────────────────────────────────────────────────────

async def ensure_user_credits(user_id: int, username: str = "") -> int:
    """
    Return the user's credit balance, creating a row with STARTING_CREDITS
    if this is their first interaction.
    """
    row = await db_execute(
        "SELECT balance FROM user_credits WHERE user_id = $1",
        (user_id,),
        fetch=True,
    )
    if row is not None:
        return row[0]

    now = int(time.time())
    await db_execute(
        "INSERT INTO user_credits (user_id, balance, last_daily_at, updated_at) "
        "VALUES ($1, $2, $3, $4) "
        "ON CONFLICT (user_id) DO NOTHING",
        (user_id, STARTING_CREDITS, 0, now),
    )
    await _log_transaction(user_id, STARTING_CREDITS, "welcome_bonus")
    logger.info("New user %s: granted %d starting credits.", user_id, STARTING_CREDITS)
    return STARTING_CREDITS


async def get_balance(user_id: int) -> int:
    """Return current credit balance (0 if user not in table yet)."""
    row = await db_execute(
        "SELECT balance FROM user_credits WHERE user_id = $1",
        (user_id,),
        fetch=True,
    )
    return row[0] if row else 0


async def deduct_credits(user_id: int, amount: int, reason: str) -> bool:
    """
    Deduct *amount* credits from user.
    Returns True on success, False if balance is insufficient.
    """
    row = await db_execute(
        "SELECT balance FROM user_credits WHERE user_id = $1 FOR UPDATE",
        (user_id,),
        fetch=True,
    )
    # Treat missing row as 0 balance — caller should have called ensure_user_credits first
    balance = row[0] if row else 0
    if balance < amount:
        return False

    now = int(time.time())
    await db_execute(
        "UPDATE user_credits SET balance = balance - $2, updated_at = $3 "
        "WHERE user_id = $1",
        (user_id, amount, now),
    )
    await _log_transaction(user_id, -amount, reason)
    return True


async def add_credits(user_id: int, amount: int, reason: str) -> int:
    """
    Add *amount* credits to user (creates row if absent).
    Returns new balance.
    """
    now = int(time.time())
    new_balance = await db_execute(
        "INSERT INTO user_credits (user_id, balance, last_daily_at, updated_at) "
        "VALUES ($1, $2, 0, $3) "
        "ON CONFLICT (user_id) DO UPDATE "
        "SET balance = user_credits.balance + $4, updated_at = $5 "
        "RETURNING balance",
        (user_id, amount, now, amount, now),
        returning=True,
    )
    await _log_transaction(user_id, amount, reason)
    return new_balance or amount


async def claim_daily_bonus(user_id: int) -> tuple[int, int]:
    """
    Attempt to claim the daily login bonus.
    Returns (awarded, next_claim_ts).
    awarded == 0 means cooldown not elapsed yet.
    """
    now = int(time.time())
    row = await db_execute(
        "SELECT balance, last_daily_at FROM user_credits WHERE user_id = $1",
        (user_id,),
        fetch=True,
    )
    if row is None:
        # New user — ensure_user_credits should have been called first
        return 0, now + DAILY_BONUS_COOLDOWN

    _, last_daily_at = row
    next_claim_ts = last_daily_at + DAILY_BONUS_COOLDOWN
    if now < next_claim_ts:
        return 0, next_claim_ts

    await db_execute(
        "UPDATE user_credits "
        "SET balance = balance + $2, last_daily_at = $3, updated_at = $4 "
        "WHERE user_id = $1",
        (user_id, DAILY_BONUS, now, now),
    )
    await _log_transaction(user_id, DAILY_BONUS, "daily_bonus")
    return DAILY_BONUS, now + DAILY_BONUS_COOLDOWN


async def credit_history(user_id: int, limit: int = 10) -> list[tuple]:
    """
    Return the most recent *limit* credit transactions for user.
    Each row: (amount, reason, created_at)
    """
    rows = await db_execute(
        "SELECT amount, reason, created_at "
        "FROM credit_transactions "
        "WHERE user_id = $1 "
        "ORDER BY created_at DESC LIMIT $2",
        (user_id, limit),
        fetch_all=True,
    )
    return rows or []
