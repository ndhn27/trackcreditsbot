"""
Lightweight HTTP health-check server.

Runs on HEALTH_PORT (default 8080) alongside the Telegram bot.
Exposes two endpoints:
  GET /health  — liveness: always 200 {"status": "ok"}
  GET /ready   — readiness: 200 if DB pool is up, 503 otherwise

Railway, Fly.io, Docker HEALTHCHECK, and UptimeRobot all work with this.

Usage (app_factory.py):
    from health import start_health_server, stop_health_server
    await start_health_server()   # call in setup_app_context
    await stop_health_server()    # call in cleanup_app_context
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Optional

from aiohttp import web

logger = logging.getLogger("trackcredits.health")

HEALTH_PORT: int = int(os.environ.get("HEALTH_PORT", "8080"))

_runner: Optional[web.AppRunner] = None
_start_time: float = time.time()


async def _handle_health(request: web.Request) -> web.Response:
    """Liveness probe — always 200 if the process is alive."""
    return web.Response(
        content_type="application/json",
        text=json.dumps({"status": "ok", "uptime_s": int(time.time() - _start_time)}),
    )


async def _handle_ready(request: web.Request) -> web.Response:
    """Readiness probe — 200 only when the DB pool is responsive."""
    try:
        from db import db_execute
        await db_execute("SELECT 1", fetch=True)
        return web.Response(
            content_type="application/json",
            text=json.dumps({"status": "ready"}),
        )
    except Exception as exc:
        logger.warning("Readiness check failed: %s", exc)
        return web.Response(
            status=503,
            content_type="application/json",
            text=json.dumps({"status": "unavailable", "error": str(exc)}),
        )


async def _handle_momo_ipn(request: web.Request) -> web.Response:
    """MoMo IPN (Instant Payment Notification) webhook handler."""
    try:
        body = await request.json()
    except Exception:
        return web.Response(status=400, text="Bad JSON")

    from payment import verify_momo_ipn, fulfill_payment, get_package
    if not verify_momo_ipn(body):
        logger.warning("MoMo IPN: invalid signature — %s", body.get("orderId"))
        return web.Response(status=400, text="Invalid signature")

    result_code = body.get("resultCode", -1)
    order_id: str = body.get("orderId", "")
    # orderId format: tc_{user_id}_{pack_id}_{ts}  e.g. tc_123456789_pack_120_1714000000
    parts = order_id.split("_")
    if len(parts) < 3 or not parts[1].isdigit():
        logger.warning("MoMo IPN: unparseable orderId %s", order_id)
        return web.Response(status=400, text="Invalid orderId")

    if result_code != 0:
        logger.info("MoMo IPN: payment not successful (resultCode=%s) for %s", result_code, order_id)
        return web.Response(text="ok")

    user_id = int(parts[1])
    # pack_id reconstruction: parts[2] + '_' + parts[3] = e.g. "pack_120"
    pack_id = f"{parts[2]}_{parts[3]}" if len(parts) >= 4 else parts[2]
    try:
        new_balance = await fulfill_payment(user_id, pack_id, order_id)
        logger.info("MoMo IPN: fulfilled %s → user %s, new balance %s", order_id, user_id, new_balance)
    except Exception as exc:
        logger.error("MoMo IPN: fulfill_payment failed for %s: %s", order_id, exc)
        return web.Response(status=500, text="Internal error")

    # Notify user via Telegram bot (best-effort)
    try:
        from app_context import _BOT_INSTANCE  # set in app_factory.py
        bot = _BOT_INSTANCE
        pack = get_package(pack_id)
        if bot and pack:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"\U0001f389 MoMo payment confirmed!\n"
                    f"<b>+{pack['credits']} credits</b> added.\n"
                    f"New balance: <b>{new_balance}</b>."
                ),
                parse_mode="HTML",
            )
    except Exception as exc:
        logger.warning("MoMo IPN: could not notify user %s: %s", user_id, exc)

    return web.Response(text="ok")


async def _handle_stripe_webhook(request: web.Request) -> web.Response:
    """Stripe webhook handler (checkout.session.completed)."""
    payload = await request.read()
    sig_header = request.headers.get("Stripe-Signature", "")

    from payment import verify_stripe_webhook, fulfill_payment, get_package
    event = verify_stripe_webhook(payload, sig_header)
    if event is None:
        return web.Response(status=400, text="Invalid signature")

    if event.get("type") != "checkout.session.completed":
        return web.Response(text="ok")  # Ignore other events

    session_obj = event.get("data", {}).get("object", {})
    meta = session_obj.get("metadata", {})
    try:
        user_id = int(meta.get("user_id", 0))
        pack_id = meta.get("pack_id", "")
        session_id = session_obj.get("id", f"stripe_{int(time.time())}")
    except (ValueError, TypeError) as exc:
        logger.warning("Stripe webhook: bad metadata — %s", exc)
        return web.Response(status=400, text="Bad metadata")

    try:
        new_balance = await fulfill_payment(user_id, pack_id, session_id)
        logger.info("Stripe webhook: fulfilled %s → user %s, balance %s", session_id, user_id, new_balance)
    except Exception as exc:
        logger.error("Stripe webhook: fulfill_payment failed: %s", exc)
        return web.Response(status=500, text="Internal error")

    try:
        from app_context import _BOT_INSTANCE
        bot = _BOT_INSTANCE
        pack = get_package(pack_id)
        if bot and pack:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"\U0001f389 Stripe payment confirmed!\n"
                    f"<b>+{pack['credits']} credits</b> added.\n"
                    f"New balance: <b>{new_balance}</b>."
                ),
                parse_mode="HTML",
            )
    except Exception as exc:
        logger.warning("Stripe webhook: could not notify user %s: %s", user_id, exc)

    return web.Response(text="ok")


async def start_health_server() -> None:
    """Start the HTTP health + payment webhook + admin dashboard server."""
    global _runner
    app = web.Application()
    app.router.add_get("/health", _handle_health)
    app.router.add_get("/ready", _handle_ready)
    app.router.add_get("/", _handle_health)
    # Payment webhooks — same port as health to avoid opening extra ports
    app.router.add_post("/payment/momo/ipn", _handle_momo_ipn)
    app.router.add_post("/webhook/stripe", _handle_stripe_webhook)

    # Admin dashboard — protected by DASHBOARD_SECRET cookie session
    try:
        from dashboard import register_dashboard
        register_dashboard(app)
        logger.info("Admin dashboard registered at /admin/")
    except Exception as exc:  # pragma: no cover
        logger.warning("Dashboard registration failed: %s", exc)

    _runner = web.AppRunner(app)
    await _runner.setup()
    site = web.TCPSite(_runner, "0.0.0.0", HEALTH_PORT)
    await site.start()
    logger.info(
        "Health+webhook+dashboard server on port %d  "
        "routes: /health /ready /payment/momo/ipn /webhook/stripe /admin/*",
        HEALTH_PORT,
    )


async def stop_health_server() -> None:
    """Gracefully shut down the health server."""
    global _runner
    if _runner:
        await _runner.cleanup()
        _runner = None
        logger.info("Health server stopped.")
