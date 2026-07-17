"""
Dashboard authentication — simple HMAC cookie session.

No external dependencies. Uses DASHBOARD_SECRET env var.

Usage:
    from dashboard_auth import check_auth, make_login_response, make_logout_response, LOGIN_PAGE_HTML

    # In a route handler:
    if not check_auth(request):
        raise web.HTTPFound('/admin/login')
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
import logging

from aiohttp import web

logger = logging.getLogger("trackcredits.dashboard")

DASHBOARD_SECRET: str = os.environ.get("DASHBOARD_SECRET", "")
SESSION_COOKIE = "tcadmin"
SESSION_TTL = 86_400 * 7  # 7 days


def _sign(payload: str) -> str:
    """HMAC-SHA256 signature of payload using DASHBOARD_SECRET."""
    return hmac.new(
        DASHBOARD_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()


def make_session_token() -> str:
    """Generate a signed session token: {timestamp}.{signature}"""
    ts = str(int(time.time()))
    sig = _sign(ts)
    return f"{ts}.{sig}"


def _verify_token(token: str) -> bool:
    """Return True if token is valid and not expired."""
    if not DASHBOARD_SECRET:
        return False
    try:
        ts_str, sig = token.split(".", 1)
        ts = int(ts_str)
        if time.time() - ts > SESSION_TTL:
            return False
        expected = _sign(ts_str)
        return hmac.compare_digest(expected, sig)
    except Exception:
        return False


def check_auth(request: web.Request) -> bool:
    """Return True if the request carries a valid session cookie."""
    if not DASHBOARD_SECRET:
        logger.warning("DASHBOARD_SECRET is not set — dashboard auth disabled, all requests blocked!")
        return False
    token = request.cookies.get(SESSION_COOKIE, "")
    return _verify_token(token)


def make_login_response(redirect_to: str = "/admin/") -> web.Response:
    """Set session cookie and redirect to admin home."""
    token = make_session_token()
    resp = web.HTTPFound(redirect_to)
    # Secure=True required on HTTPS deployments; allow opt-out for local HTTP dev
    _secure = os.environ.get("DASHBOARD_INSECURE_COOKIE", "").lower() != "true"
    resp.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_TTL,
        httponly=True,
        samesite="Lax",
        secure=_secure,
    )
    return resp


def make_logout_response() -> web.Response:
    """Clear session cookie and redirect to login."""
    resp = web.HTTPFound("/admin/login")
    resp.del_cookie(SESSION_COOKIE)
    return resp


# ── Login page HTML ───────────────────────────────────────────────────────

LOGIN_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TrackCredits Admin · Login</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0f1117; --surface: #1a1d27; --border: #2a2d3a;
    --accent: #6c63ff; --accent-hover: #5a52e0;
    --text: #e2e8f0; --muted: #8892a4; --danger: #f56565;
    --success: #48bb78;
  }
  body { background: var(--bg); color: var(--text); font-family: system-ui, sans-serif;
         display: flex; align-items: center; justify-content: center; min-height: 100vh; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
          padding: 2.5rem; width: 100%; max-width: 380px; }
  .logo { font-size: 1.5rem; font-weight: 700; margin-bottom: .25rem; }
  .logo span { color: var(--accent); }
  .sub { color: var(--muted); font-size: .875rem; margin-bottom: 2rem; }
  label { font-size: .8rem; color: var(--muted); text-transform: uppercase;
          letter-spacing: .05em; display: block; margin-bottom: .4rem; }
  input { width: 100%; padding: .7rem 1rem; background: var(--bg); border: 1px solid var(--border);
          border-radius: 8px; color: var(--text); font-size: 1rem; outline: none; }
  input:focus { border-color: var(--accent); }
  .field { margin-bottom: 1.25rem; }
  button { width: 100%; padding: .75rem; background: var(--accent); color: #fff;
           border: none; border-radius: 8px; font-size: 1rem; font-weight: 600;
           cursor: pointer; transition: background .15s; }
  button:hover { background: var(--accent-hover); }
  .error { color: var(--danger); font-size: .85rem; margin-top: 1rem; text-align: center; }
</style>
</head>
<body>
<div class="card">
  <div class="logo">Track<span>Credits</span></div>
  <div class="sub">Admin Dashboard</div>
  <form method="POST" action="/admin/login">
    <div class="field">
      <label>Secret key</label>
      <input type="password" name="secret" placeholder="Enter dashboard secret" autofocus>
    </div>
    <button type="submit">Sign in</button>
    {error}
  </form>
</div>
</body>
</html>"""
