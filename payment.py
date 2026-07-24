"""
Payment gateway integration.

Supports two providers selectable via PAYMENT_PROVIDER env var:
  • "momo"   — MoMo QR / deep-link (Vietnam, no server-side SDK needed)
  • "stripe" — Stripe Checkout (international)
  • "manual" — Admin manually confirms payment (default / fallback)

Flow
────
1. User sends /buy → shown credit packages
2. User picks a package → payment link / QR generated
3. User pays → webhook (Stripe) or admin confirms (MoMo/manual)
4. Credits are added via credits.add_credits()

Environment variables
─────────────────────
PAYMENT_PROVIDER       = momo | stripe | manual
STRIPE_SECRET_KEY      = sk_live_...
STRIPE_WEBHOOK_SECRET  = whsec_...
MOMO_PARTNER_CODE      = MOMO...
MOMO_ACCESS_KEY        = ...
MOMO_SECRET_KEY        = ...
MOMO_REDIRECT_URL      = https://t.me/YourBot
MOMO_IPN_URL           = https://yourbot.fly.dev/payment/momo/ipn
BOT_BASE_URL           = https://yourbot.fly.dev   (for Stripe success/cancel URLs)
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
import uuid
from typing import Optional

logger = logging.getLogger("trackcredits.payment")

# ── Credit packages (customise freely) ────────────────────────────────────
CREDIT_PACKAGES: list[dict] = [
    {"id": "pack_50",   "credits": 50,   "price_usd": 1.99,  "price_vnd": 49_000,  "label": "50 credits  — $1.99 / 49K₫"},
    {"id": "pack_120",  "credits": 120,  "price_usd": 3.99,  "price_vnd": 99_000,  "label": "120 credits — $3.99 / 99K₫  🔥"},
    {"id": "pack_300",  "credits": 300,  "price_usd": 7.99,  "price_vnd": 199_000, "label": "300 credits — $7.99 / 199K₫"},
    {"id": "pack_1000", "credits": 1000, "price_usd": 19.99, "price_vnd": 499_000, "label": "1000 credits — $19.99 / 499K₫ 💎"},
]

PROVIDER: str = os.environ.get("PAYMENT_PROVIDER", "manual").lower()


def get_package(pack_id: str) -> Optional[dict]:
    return next((p for p in CREDIT_PACKAGES if p["id"] == pack_id), None)


# ══════════════════════════════════════════════════════════════════════════
# MOMO
# ══════════════════════════════════════════════════════════════════════════

MOMO_PARTNER_CODE  = os.environ.get("MOMO_PARTNER_CODE", "")
MOMO_ACCESS_KEY    = os.environ.get("MOMO_ACCESS_KEY", "")
MOMO_SECRET_KEY    = os.environ.get("MOMO_SECRET_KEY", "")
MOMO_REDIRECT_URL  = os.environ.get("MOMO_REDIRECT_URL", "https://t.me/TrackCreditsBot")
MOMO_IPN_URL       = os.environ.get("MOMO_IPN_URL", "")
MOMO_ENDPOINT      = "https://payment.momo.vn/v2/gateway/api/create"


def _momo_signature(raw: str) -> str:
    return hmac.new(
        MOMO_SECRET_KEY.encode(), raw.encode(), hashlib.sha256
    ).hexdigest()


async def create_momo_payment(user_id: int, pack: dict) -> dict:
    """
    Create a MoMo QR payment request.
    Returns {"pay_url": str, "order_id": str} or raises RuntimeError.
    """
    import aiohttp

    if not all([MOMO_PARTNER_CODE, MOMO_ACCESS_KEY, MOMO_SECRET_KEY, MOMO_IPN_URL]):
        raise RuntimeError("MoMo credentials not fully configured. Set MOMO_PARTNER_CODE, "
                           "MOMO_ACCESS_KEY, MOMO_SECRET_KEY, MOMO_IPN_URL.")

    order_id    = f"tc_{user_id}_{pack['id']}_{int(time.time())}"
    request_id  = str(uuid.uuid4())
    amount      = pack["price_vnd"]
    order_info  = f"TrackCredits: {pack['credits']} credits"
    extra_data  = ""

    raw = (
        f"accessKey={MOMO_ACCESS_KEY}"
        f"&amount={amount}"
        f"&extraData={extra_data}"
        f"&ipnUrl={MOMO_IPN_URL}"
        f"&orderId={order_id}"
        f"&orderInfo={order_info}"
        f"&partnerCode={MOMO_PARTNER_CODE}"
        f"&redirectUrl={MOMO_REDIRECT_URL}"
        f"&requestId={request_id}"
        f"&requestType=payWithMethod"
    )
    signature = _momo_signature(raw)

    payload = {
        "partnerCode":   MOMO_PARTNER_CODE,
        "accessKey":     MOMO_ACCESS_KEY,
        "requestId":     request_id,
        "amount":        amount,
        "orderId":       order_id,
        "orderInfo":     order_info,
        "redirectUrl":   MOMO_REDIRECT_URL,
        "ipnUrl":        MOMO_IPN_URL,
        "extraData":     extra_data,
        "requestType":   "payWithMethod",
        "signature":     signature,
        "lang":          "vi",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(MOMO_ENDPOINT, json=payload, timeout=10) as resp:
            data = await resp.json(content_type=None)

    if data.get("resultCode") != 0:
        raise RuntimeError(f"MoMo error {data.get('resultCode')}: {data.get('message')}")

    return {"pay_url": data["payUrl"], "order_id": order_id}


def verify_momo_ipn(body: dict) -> bool:
    """Verify MoMo IPN signature. Call from your webhook handler."""
    raw = (
        f"accessKey={MOMO_ACCESS_KEY}"
        f"&amount={body.get('amount')}"
        f"&extraData={body.get('extraData', '')}"
        f"&message={body.get('message')}"
        f"&orderId={body.get('orderId')}"
        f"&orderInfo={body.get('orderInfo')}"
        f"&orderType={body.get('orderType')}"
        f"&partnerCode={body.get('partnerCode')}"
        f"&payType={body.get('payType')}"
        f"&requestId={body.get('requestId')}"
        f"&responseTime={body.get('responseTime')}"
        f"&resultCode={body.get('resultCode')}"
        f"&transId={body.get('transId')}"
    )
    expected = _momo_signature(raw)
    return hmac.compare_digest(expected, body.get("signature", ""))


# ══════════════════════════════════════════════════════════════════════════
# STRIPE
# ══════════════════════════════════════════════════════════════════════════

STRIPE_SECRET_KEY      = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET  = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
BOT_BASE_URL           = os.environ.get("BOT_BASE_URL", "https://t.me/TrackCreditsBot")


async def create_stripe_session(user_id: int, pack: dict) -> dict:
    """
    Create a Stripe Checkout session.
    Returns {"pay_url": str, "session_id": str} or raises RuntimeError.
    """
    try:
        import stripe  # pip install stripe
    except ImportError:
        raise RuntimeError("stripe package not installed. Run: pip install stripe")

    if not STRIPE_SECRET_KEY:
        raise RuntimeError("STRIPE_SECRET_KEY not configured.")

    stripe.api_key = STRIPE_SECRET_KEY
    price_cents = int(pack["price_usd"] * 100)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency":     "usd",
                "unit_amount":  price_cents,
                "product_data": {
                    "name":        f"TrackCredits — {pack['credits']} credits",
                    "description": "In-bot credits for TrackCredits Telegram bot",
                },
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{BOT_BASE_URL}?start=paid_{user_id}_{pack['id']}",
        cancel_url=f"{BOT_BASE_URL}?start=cancel",
        metadata={"user_id": str(user_id), "pack_id": pack["id"], "credits": str(pack["credits"])},
    )
    return {"pay_url": session.url, "session_id": session.id}


def verify_stripe_webhook(payload: bytes, sig_header: str) -> Optional[dict]:
    """
    Verify and parse a Stripe webhook event.
    Returns the event dict on success, None on failure.
    """
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        return event
    except Exception as exc:
        logger.warning("Stripe webhook verification failed: %s", exc)
        return None


# ══════════════════════════════════════════════════════════════════════════
# Unified public API
# ══════════════════════════════════════════════════════════════════════════

async def create_payment(user_id: int, pack_id: str) -> dict:
    """
    Create a payment request for user_id buying pack_id.
    Returns {"pay_url": str, "order_id": str, "provider": str}.
    Raises ValueError for unknown pack, RuntimeError for provider errors.
    """
    pack = get_package(pack_id)
    if not pack:
        raise ValueError(f"Unknown package: {pack_id}")

    if PROVIDER == "momo":
        result = await create_momo_payment(user_id, pack)
        return {**result, "provider": "momo", "credits": pack["credits"]}

    if PROVIDER == "stripe":
        result = await create_stripe_session(user_id, pack)
        return {**result, "provider": "stripe", "credits": pack["credits"]}

    # Manual — admin confirms via /confirmPayment <user_id> <pack_id>
    order_id = f"manual_{user_id}_{pack_id}_{int(time.time())}"
    return {
        "pay_url":  None,
        "order_id": order_id,
        "provider": "manual",
        "credits":  pack["credits"],
        "instructions": (
            f"Transfer {pack['price_vnd']:,}₫ to the bank account shown below.\n"
            f"Reference: <code>{order_id}</code>\n"
            f"Admin will add <b>{pack['credits']} credits</b> after confirmation."
        ),
    }


async def fulfill_payment(user_id: int, pack_id: str, order_id: str) -> int:
    """
    Called after payment is confirmed (webhook or admin /confirmPayment).
    Adds credits and logs the transaction. Returns new balance.

    Idempotent by order_id: MoMo IPN and Stripe webhooks both retry on
    non-2xx / slow responses, and Stripe will happily replay a validly-signed
    event within its timestamp-tolerance window. Without a guard here, a
    retried/replayed call would credit the same purchase twice. We claim the
    order via the UNIQUE constraint on payment_orders.order_id (migration
    007) — INSERT ... ON CONFLICT DO NOTHING is atomic, so this is race-safe
    even if two webhook deliveries land at the same time.
    """
    from credits import add_credits, get_balance
    from db import db_execute

    pack = get_package(pack_id)
    if not pack:
        raise ValueError(f"Unknown package: {pack_id}")

    claimed = await db_execute(
        "INSERT INTO payment_orders "
        "(order_id, user_id, pack_id, credits, provider, status, amount_vnd, amount_usd, created_at, paid_at) "
        "VALUES ($1, $2, $3, $4, $5, 'paid', $6, $7, $8, $8) "
        "ON CONFLICT (order_id) DO NOTHING "
        "RETURNING id",
        (
            order_id, user_id, pack_id, pack["credits"], PROVIDER,
            pack.get("price_vnd"), pack.get("price_usd"), int(time.time()),
        ),
        returning=True,
    )
    if claimed is None:
        logger.warning("Order %s already fulfilled — skipping duplicate credit (idempotent).", order_id)
        return await get_balance(user_id)

    new_balance = await add_credits(user_id, pack["credits"], f"payment_{order_id}")
    logger.info("Fulfilled %s credits for user %s (order %s)", pack["credits"], user_id, order_id)
    return new_balance
