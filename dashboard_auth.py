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


# ── Login rate limiting ────────────────────────────────────────────────────
# In-memory, per-process. Resets on restart and does NOT share state across
# multiple replicas — fine for this project's deploy (docker-compose /
# railway.toml both run a single instance). If you ever scale to >1
# replica, move the counters into Postgres or Redis instead.

_LOGIN_MAX_ATTEMPTS = int(os.environ.get("DASHBOARD_LOGIN_MAX_ATTEMPTS", "5"))
_LOGIN_WINDOW_SECONDS = int(os.environ.get("DASHBOARD_LOGIN_WINDOW_SECONDS", "300"))    # 5 min
_LOGIN_LOCKOUT_SECONDS = int(os.environ.get("DASHBOARD_LOGIN_LOCKOUT_SECONDS", "900"))  # 15 min
_LOGIN_MAX_TRACKED_IPS = 5_000  # opportunistic cleanup trigger

_login_attempts: dict[str, list[float]] = {}     # ip -> failed-attempt timestamps
_login_locked_until: dict[str, float] = {}       # ip -> unix ts lockout ends


_TRUST_PROXY_HEADERS = os.environ.get("DASHBOARD_TRUST_PROXY_HEADERS", "").lower() == "true"


def client_ip(request: web.Request) -> str:
    """
    Best-effort client IP for the login rate limiter.

    Defaults to request.remote — the direct TCP peer aiohttp sees.
    Always accurate, never spoofable, but if this process sits behind
    ANY reverse proxy / PaaS edge (Railway, Fly, nginx, Cloudflare...),
    request.remote is the *proxy's* IP for every request — the limiter
    would then treat all visitors as one IP and could lock everyone out
    together instead of isolating the attacker.

    Set DASHBOARD_TRUST_PROXY_HEADERS=true to instead trust X-Real-IP,
    or the last hop of X-Forwarded-For (the entry your own proxy
    appended — not anything a client could have prepended), IF you have
    exactly one reverse proxy you control in front and it's configured
    to set these correctly (e.g. nginx: `proxy_set_header X-Real-IP
    $remote_addr;`).

    Do NOT enable this blindly on Railway: their community/support
    threads currently disagree on whether the first or last
    X-Forwarded-For hop is trustworthy, and behavior has reportedly
    changed as they roll out new edge/CDN infrastructure. Verify
    empirically for your own deployment first (hit an endpoint that
    echoes request.remote + all headers from a known IP) — don't just
    assume. Wrong here means an attacker can pick whatever IP they want
    and the limiter never triggers.
    """
    if _TRUST_PROXY_HEADERS:
        real_ip = request.headers.get("X-Real-IP", "").strip()
        if real_ip:
            return real_ip
        xff = request.headers.get("X-Forwarded-For", "")
        if xff:
            return xff.split(",")[-1].strip()
    return request.remote or "unknown"


def _cleanup_stale(now: float) -> None:
    """Drop IPs with no recent attempts and no active lockout."""
    for ip in list(_login_attempts):
        if not _login_attempts[ip] or now - _login_attempts[ip][-1] > _LOGIN_WINDOW_SECONDS:
            _login_attempts.pop(ip, None)
    for ip in list(_login_locked_until):
        if _login_locked_until[ip] <= now:
            _login_locked_until.pop(ip, None)


def is_login_locked(ip: str) -> int:
    """Return remaining lockout seconds for ip (0 if not locked)."""
    until = _login_locked_until.get(ip)
    if until is None:
        return 0
    remaining = int(until - time.time())
    if remaining <= 0:
        _login_locked_until.pop(ip, None)
        return 0
    return remaining


def record_login_attempt(ip: str, success: bool) -> None:
    """Record a login attempt; lock the IP out after too many failures in a row."""
    now = time.time()
    if len(_login_attempts) > _LOGIN_MAX_TRACKED_IPS:
        _cleanup_stale(now)

    if success:
        _login_attempts.pop(ip, None)
        _login_locked_until.pop(ip, None)
        return

    attempts = [t for t in _login_attempts.get(ip, []) if now - t < _LOGIN_WINDOW_SECONDS]
    attempts.append(now)
    _login_attempts[ip] = attempts

    if len(attempts) >= _LOGIN_MAX_ATTEMPTS:
        _login_locked_until[ip] = now + _LOGIN_LOCKOUT_SECONDS
        _login_attempts.pop(ip, None)
        logger.warning(
            "Dashboard login: %s locked out for %ds after %d failed attempts.",
            ip, _LOGIN_LOCKOUT_SECONDS, _LOGIN_MAX_ATTEMPTS,
        )


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


def render_login_page(error: str = "") -> str:
    """
    Render the login page with an optional error message.

    Uses str.replace(), NOT str.format() — the CSS above is full of
    literal `{...}` blocks (`{ box-sizing: ... }`, `:root { ... }`, etc.)
    which collide with str.format()'s placeholder syntax. Calling
    LOGIN_PAGE_HTML.format(error=...) raises KeyError on the first CSS
    rule it hits, e.g. KeyError(' box-sizing'), before ever reaching the
    real `{error}` placeholder. In practice this meant GET/POST
    /admin/login 500'd unconditionally — the login page could not be
    rendered at all. Pre-existing bug, unrelated to the rate limiter
    above; fixed here since every caller goes through this function now.
    """
    return LOGIN_PAGE_HTML.replace("{error}", error)
