"""
Admin dashboard route handlers.

Mounted under /admin/* by health.py.
All routes are protected by dashboard_auth.check_auth().

Pages:
  GET  /admin/              — Overview (metrics, users, credits summary)
  GET  /admin/submissions   — Pending submissions list (paginated)
  POST /admin/submissions/{id}/approve
  POST /admin/submissions/{id}/reject
  GET  /admin/bans          — Ban list + ban/unban form
  POST /admin/bans/add
  POST /admin/bans/remove
  GET  /admin/metrics       — All-time counters + top credit users
  POST /admin/gift          — Gift credits to a user
  GET  /admin/login         — Login page (public)
  POST /admin/login         — Process login (public, rate-limited — see
                               dashboard_auth: 5 failed attempts / 5 min
                               triggers a 15 min lockout per client IP)
  GET  /admin/logout        — Clear session cookie
"""
from __future__ import annotations

import html
import logging
import time
from datetime import datetime, timezone
from urllib.parse import quote

from aiohttp import web

from dashboard_auth import (
    DASHBOARD_SECRET,
    check_auth,
    make_login_response,
    make_logout_response,
    client_ip,
    is_login_locked,
    record_login_attempt,
    render_login_page,
)

logger = logging.getLogger("trackcredits.dashboard")

# ── CSS / layout shared across all pages ─────────────────────────────────

_BASE_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #0f1117; --surface: #1a1d27; --surface2: #21253a;
  --border: #2a2d3a; --accent: #6c63ff; --accent-h: #5a52e0;
  --text: #e2e8f0; --muted: #8892a4; --danger: #f56565; --success: #48bb78;
  --warn: #ed8936;
}
body { background: var(--bg); color: var(--text);
       font-family: system-ui,-apple-system,sans-serif; font-size: 15px; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
/* Layout */
.shell { display: flex; min-height: 100vh; }
.sidebar { width: 220px; background: var(--surface); border-right: 1px solid var(--border);
           padding: 1.5rem 1rem; flex-shrink: 0; position: fixed; height: 100vh; overflow-y: auto; }
.main { margin-left: 220px; flex: 1; padding: 2rem; max-width: 1200px; }
/* Sidebar */
.brand { font-size: 1.1rem; font-weight: 700; margin-bottom: 2rem; color: var(--text); }
.brand span { color: var(--accent); }
.nav-item { display: block; padding: .55rem .75rem; border-radius: 7px; color: var(--muted);
            margin-bottom: .15rem; font-size: .9rem; transition: background .12s, color .12s; }
.nav-item:hover, .nav-item.active { background: var(--surface2); color: var(--text); text-decoration: none; }
.nav-item.active { color: var(--accent); }
.nav-section { font-size: .7rem; text-transform: uppercase; letter-spacing: .07em;
               color: var(--muted); padding: .75rem .75rem .3rem; }
/* Cards */
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
        padding: 1.25rem 1.5rem; }
.stat-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(170px,1fr)); gap: 1rem;
             margin-bottom: 1.5rem; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
             padding: 1rem 1.25rem; }
.stat-label { font-size: .75rem; text-transform: uppercase; letter-spacing: .06em;
              color: var(--muted); margin-bottom: .4rem; }
.stat-value { font-size: 1.9rem; font-weight: 700; }
.stat-card.accent .stat-value { color: var(--accent); }
.stat-card.success .stat-value { color: var(--success); }
.stat-card.warn .stat-value { color: var(--warn); }
.stat-card.danger .stat-value { color: var(--danger); }
/* Table */
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: .875rem; }
th { text-align: left; padding: .6rem 1rem; border-bottom: 1px solid var(--border);
     color: var(--muted); font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; font-weight: 600; }
td { padding: .65rem 1rem; border-bottom: 1px solid var(--border); vertical-align: middle; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--surface2); }
/* Buttons */
.btn { display: inline-block; padding: .4rem .9rem; border-radius: 6px; font-size: .8rem;
       font-weight: 600; cursor: pointer; border: none; transition: opacity .12s; }
.btn:hover { opacity: .85; text-decoration: none; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-success { background: var(--success); color: #0f1117; }
.btn-danger  { background: var(--danger); color: #fff; }
.btn-sm { padding: .3rem .65rem; font-size: .75rem; }
/* Forms */
input[type=text], input[type=number], input[type=password], select, textarea {
  background: var(--bg); border: 1px solid var(--border); border-radius: 6px;
  color: var(--text); padding: .45rem .75rem; font-size: .875rem; outline: none; }
input:focus, select:focus, textarea:focus { border-color: var(--accent); }
.form-row { display: flex; gap: .6rem; align-items: center; flex-wrap: wrap; }
/* Badges */
.badge { display: inline-block; padding: .2rem .55rem; border-radius: 20px;
         font-size: .7rem; font-weight: 700; text-transform: uppercase; }
.badge-pending { background: #2d2a12; color: var(--warn); }
.badge-credits  { background: #12222d; color: #63b3ed; }
.badge-lyrics   { background: #1a2d1a; color: var(--success); }
.badge-report   { background: #2d1a1a; color: var(--danger); }
/* Page header */
.page-header { margin-bottom: 1.5rem; }
.page-header h1 { font-size: 1.4rem; font-weight: 700; }
.page-header p  { color: var(--muted); font-size: .875rem; margin-top: .2rem; }
/* Flash / alert */
.alert { padding: .7rem 1rem; border-radius: 7px; margin-bottom: 1rem; font-size: .875rem; }
.alert-success { background: #143021; color: var(--success); border: 1px solid #1e4d32; }
.alert-error   { background: #2d1a1a; color: var(--danger); border: 1px solid #4d2020; }
/* Pagination */
.pagination { display: flex; gap: .5rem; margin-top: 1rem; justify-content: flex-end; }
.pagination a, .pagination span { padding: .3rem .75rem; border-radius: 6px;
  border: 1px solid var(--border); font-size: .8rem; }
.pagination a { color: var(--text); }
.pagination a:hover { background: var(--surface2); text-decoration: none; }
.pagination .cur { background: var(--accent); border-color: var(--accent); color: #fff; }
/* Responsive sidebar toggle */
@media(max-width:768px){
  .sidebar { display: none; }
  .main { margin-left: 0; padding: 1rem; }
}
"""


def _page(title: str, active: str, body: str, flash: str = "") -> web.Response:
    """Wrap content in the shared shell layout."""
    nav_links = [
        ("overview", "/admin/", "📊 Overview"),
        ("submissions", "/admin/submissions", "📥 Submissions"),
        ("bans", "/admin/bans", "🚫 Bans"),
        ("metrics", "/admin/metrics", "📈 Metrics"),
        ("gift", "/admin/metrics#gift", "🎁 Gift Credits"),
        ("leaderboard", "/admin/leaderboard", "🏆 Leaderboard"),
    ]
    nav_html = "".join(
        '<a class="nav-item{active}" href="{url}">{label}</a>'.format(
            active=" active" if active == key else "",
            url=url,
            label=label,
        )
        for key, url, label in nav_links
    )
    flash_html = ""
    if flash:
        kind = "success" if flash.startswith("✓") else "error"
        flash_html = f'<div class="alert alert-{kind}">{html.escape(flash)}</div>'

    return web.Response(
        content_type="text/html",
        text=f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{html.escape(title)} · TrackCredits Admin</title>
<style>{_BASE_CSS}</style>
</head>
<body>
<div class="shell">
  <aside class="sidebar">
    <div class="brand">Track<span>Credits</span></div>
    <div class="nav-section">Navigation</div>
    {nav_html}
    <div class="nav-section" style="margin-top:auto"></div>
    <a class="nav-item" href="/admin/logout">⬡ Sign out</a>
  </aside>
  <main class="main">
    {flash_html}
    {body}
  </main>
</div>
</body>
</html>""",
    )


def _esc(val) -> str:
    return html.escape(str(val)) if val is not None else ""


def _flash_redirect(path: str, flash: str) -> web.Response:
    """
    Redirect to *path* with a flash message, percent-encoded.

    Flash text often embeds dynamic values (submission title, exception
    text). Building the query string with a raw f-string means a title
    containing '&', '#' or '%' truncates/corrupts the flash message on the
    next page. quote() makes this safe; the receiving handler still runs
    html.escape() on the decoded value before rendering (see _page), so
    this is a correctness fix, not a new XSS guard — that was already covered.
    """
    return web.HTTPFound(f"{path}?flash={quote(flash, safe='')}")


def _fmt_ts(ts) -> str:
    """Format a UNIX timestamp as human-readable UTC."""
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ts)


# ── Auth routes ───────────────────────────────────────────────────────────

async def handle_login_get(request: web.Request) -> web.Response:
    return web.Response(
        content_type="text/html",
        text=render_login_page(),
    )


async def handle_login_post(request: web.Request) -> web.Response:
    ip = client_ip(request)
    locked_for = is_login_locked(ip)
    if locked_for:
        mins = locked_for // 60 + 1
        return web.Response(
            status=429,
            content_type="text/html",
            headers={"Retry-After": str(locked_for)},
            text=render_login_page(
                f'<div class="error">Too many attempts. Try again in {mins} min.</div>'
            ),
        )

    data = await request.post()
    secret = data.get("secret", "")
    if not DASHBOARD_SECRET:
        return web.Response(
            content_type="text/html",
            text=render_login_page(
                '<div class="error">DASHBOARD_SECRET is not configured on the server.</div>'
            ),
        )
    import hmac as _hmac
    if _hmac.compare_digest(secret, DASHBOARD_SECRET):
        record_login_attempt(ip, success=True)
        return make_login_response("/admin/")

    record_login_attempt(ip, success=False)
    return web.Response(
        content_type="text/html",
        text=render_login_page('<div class="error">Invalid secret key.</div>'),
    )


async def handle_logout(request: web.Request) -> web.Response:
    return make_logout_response()


# ── Guard helper ──────────────────────────────────────────────────────────

def _require_auth(request: web.Request) -> web.Response | None:
    """Return redirect response if not authed, else None."""
    if not check_auth(request):
        return web.HTTPFound("/admin/login")
    return None


# ── Overview page ─────────────────────────────────────────────────────────

async def handle_overview(request: web.Request) -> web.Response:
    redir = _require_auth(request)
    if redir:
        return redir

    from metrics import get_metrics, get_daily_stats
    from repository import (
        bot_users_count, stats_credit_totals, submissions_count_pending,
        submissions_count_by_status,
    )

    metrics, daily, total_users, credit_totals, pending = await _gather(
        get_metrics(),
        get_daily_stats(),
        bot_users_count(),
        stats_credit_totals(),
        submissions_count_pending(),
    )
    approved_count = await submissions_count_by_status("approved")
    rejected_count = await submissions_count_by_status("rejected")

    searches_today = daily.get("search", 0)
    searches_total = metrics.get("search", 0)

    uptime_s = int(time.time()) - int(metrics.get("_start_time", time.time()))
    uptime_h = uptime_s // 3600
    uptime_label = f"{uptime_h // 24}d {uptime_h % 24}h" if uptime_h >= 24 else f"{uptime_h}h"

    stats_html = f"""
<div class="stat-grid">
  <div class="stat-card accent">
    <div class="stat-label">Total users</div>
    <div class="stat-value">{total_users:,}</div>
  </div>
  <div class="stat-card success">
    <div class="stat-label">Credits earned (all)</div>
    <div class="stat-value">{credit_totals["earned"]:,}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Credits spent (all)</div>
    <div class="stat-value">{credit_totals["spent"]:,}</div>
  </div>
  <div class="stat-card warn">
    <div class="stat-label">Pending submissions</div>
    <div class="stat-value">{pending}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Searches today</div>
    <div class="stat-value">{searches_today:,}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Searches (all time)</div>
    <div class="stat-value">{searches_total:,}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Uptime</div>
    <div class="stat-value">{uptime_label}</div>
  </div>
</div>"""

    # Today's daily counters
    daily_rows = "".join(
        f"<tr><td>{_esc(k)}</td><td style='text-align:right'><b>{v:,}</b></td></tr>"
        for k, v in sorted(daily.items())
    ) or "<tr><td colspan='2' style='color:var(--muted)'>No events yet today.</td></tr>"

    # Submission counts
    sub_summary = f"""
<div class="card" style="margin-top:1.5rem">
  <div style="display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap">
    <div><span class="badge badge-pending">Pending</span> &nbsp;<b>{pending}</b></div>
    <div style="color:var(--success)">✓ Approved: <b>{approved_count}</b></div>
    <div style="color:var(--danger)">✗ Rejected: <b>{rejected_count}</b></div>
    <a href="/admin/submissions" class="btn btn-primary btn-sm" style="margin-left:auto">Review submissions →</a>
  </div>
</div>"""

    body = f"""
<div class="page-header">
  <h1>📊 Overview</h1>
  <p>Live snapshot — refreshes on page load.</p>
</div>
{stats_html}
<div class="card">
  <div style="font-weight:600;margin-bottom:.75rem">Today's activity</div>
  <div class="table-wrap">
    <table><tr><th>Metric</th><th style="text-align:right">Count</th></tr>
    {daily_rows}
    </table>
  </div>
</div>
{sub_summary}"""

    return _page("Overview", "overview", body)


# ── Submissions page ──────────────────────────────────────────────────────

_PAGE_SIZE = 15

async def handle_submissions(request: web.Request) -> web.Response:
    redir = _require_auth(request)
    if redir:
        return redir

    from repository import submissions_get_pending_page, submissions_count_pending

    flash = request.rel_url.query.get("flash", "")
    try:
        page = max(0, int(request.rel_url.query.get("page", "0")))
    except ValueError:
        page = 0

    total_pending = await submissions_count_pending()
    rows = await submissions_get_pending_page(_PAGE_SIZE + 1, page * _PAGE_SIZE)
    has_next = len(rows) > _PAGE_SIZE
    rows = rows[:_PAGE_SIZE]

    if not rows:
        table_html = "<p style='color:var(--muted);padding:1rem 0'>No pending submissions. 🎉</p>"
    else:
        def badge(sub_type):
            cls = {"credits": "badge-credits", "lyrics": "badge-lyrics", "report": "badge-report"}.get(sub_type, "badge-pending")
            return f'<span class="badge {cls}">{_esc(sub_type)}</span>'

        tbody = "".join(
            f"""<tr>
              <td><code>#{row[0]}</code></td>
              <td>{_esc(row[1])}</td>
              <td>{_esc(row[2])}</td>
              <td>{badge(row[3])}</td>
              <td>@{_esc(row[4])}</td>
              <td style="color:var(--muted);font-size:.8rem">{_fmt_ts(row[5])}</td>
              <td>
                <form method="POST" action="/admin/submissions/{row[0]}/approve" style="display:inline">
                  <button class="btn btn-success btn-sm" type="submit">✓ Approve</button>
                </form>
                &nbsp;
                <form method="POST" action="/admin/submissions/{row[0]}/reject" style="display:inline"
                      onsubmit="return confirm('Reject submission #{row[0]}?')">
                  <button class="btn btn-danger btn-sm" type="submit">✗ Reject</button>
                </form>
              </td>
            </tr>"""
            for row in rows
        )
        table_html = f"""<div class="table-wrap">
          <table>
            <tr><th>#</th><th>Title</th><th>Artist</th><th>Type</th><th>By</th><th>Submitted</th><th>Actions</th></tr>
            {tbody}
          </table>
        </div>"""

    # Pagination
    total_pages = max(1, (total_pending + _PAGE_SIZE - 1) // _PAGE_SIZE)
    pager = '<div class="pagination">'
    if page > 0:
        pager += f'<a href="/admin/submissions?page={page-1}">← Prev</a>'
    pager += f'<span class="cur">{page+1} / {total_pages}</span>'
    if has_next:
        pager += f'<a href="/admin/submissions?page={page+1}">Next →</a>'
    pager += "</div>"

    body = f"""
<div class="page-header" style="display:flex;justify-content:space-between;align-items:start">
  <div>
    <h1>📥 Pending Submissions</h1>
    <p>{total_pending} submission{'s' if total_pending != 1 else ''} awaiting review.</p>
  </div>
</div>
<div class="card">
  {table_html}
  {pager}
</div>"""

    return _page("Submissions", "submissions", body, flash)


async def handle_approve(request: web.Request) -> web.Response:
    redir = _require_auth(request)
    if redir:
        return redir

    sub_id = int(request.match_info["id"])

    from repository import (
        submissions_get_by_id, submissions_lock_for_update_tx, submissions_set_status_tx,
        approved_data_upsert_credits_tx, approved_data_upsert_lyrics_tx,
        leaderboard_add_score_tx,
    )
    from credits import add_credits, APPROVAL_EARN
    from cache import approved_cache_invalidate
    from db import db_transaction

    submission = await submissions_get_by_id(sub_id)
    if not submission:
        return web.HTTPFound("/admin/submissions?flash=Submission+not+found")

    _, title, track_key, content_text, source_text, sub_type, user_id, username = submission

    try:
        async with db_transaction() as conn:
            status_row = await submissions_lock_for_update_tx(conn, sub_id)
            if not status_row or status_row[0] != "pending":
                return web.HTTPFound("/admin/submissions?flash=Already+processed")

            if sub_type == "credits":
                await approved_data_upsert_credits_tx(conn, track_key, content_text, username)
            elif sub_type == "lyrics":
                await approved_data_upsert_lyrics_tx(conn, track_key, content_text, source_text, username)

            # Score: credits/lyrics = 10, report = 5 (same as Telegram admin)
            points = 5 if sub_type == "report" else 10
            await leaderboard_add_score_tx(conn, user_id, username, points)
            await submissions_set_status_tx(conn, sub_id, "approved")

        await approved_cache_invalidate(track_key)

        try:
            from cache import delete_song_cache
            await delete_song_cache(track_key)
        except Exception:
            pass

        try:
            new_bal = await add_credits(user_id, APPROVAL_EARN, f"approved_{sub_type}")
        except Exception:
            new_bal = None

        # Notify user via Telegram (best-effort)
        try:
            from app_context import _BOT_INSTANCE
            if _BOT_INSTANCE and user_id:
                credit_note = f"\n💎 <b>+{APPROVAL_EARN} bonus credits</b>! Balance: <b>{new_bal}</b>." if new_bal else ""
                await _BOT_INSTANCE.send_message(
                    chat_id=user_id,
                    text=(
                        f"✅ Your <b>{_esc(sub_type)}</b> submission for "
                        f"<i>{_esc(title)}</i> was <b>approved</b> by admin!{credit_note}"
                    ),
                    parse_mode="HTML",
                )
        except Exception as exc:
            logger.warning("Dashboard approve: could not notify user %s: %s", user_id, exc)

        return _flash_redirect("/admin/submissions", f"✓ Approved #{sub_id} — {title}")

    except Exception as exc:
        logger.error("Dashboard approve error: %s", exc)
        return _flash_redirect("/admin/submissions", f"Error: {exc}")


async def handle_reject(request: web.Request) -> web.Response:
    redir = _require_auth(request)
    if redir:
        return redir

    sub_id = int(request.match_info["id"])

    from repository import submissions_get_by_id, submissions_reject

    submission = await submissions_get_by_id(sub_id)
    if not submission:
        return web.HTTPFound("/admin/submissions?flash=Submission+not+found")

    _, title, track_key, content_text, source_text, sub_type, user_id, username = submission

    try:
        await submissions_reject(sub_id)

        try:
            from app_context import _BOT_INSTANCE
            if _BOT_INSTANCE and user_id:
                await _BOT_INSTANCE.send_message(
                    chat_id=user_id,
                    text=(
                        f"❌ Your <b>{_esc(sub_type)}</b> submission for "
                        f"<i>{_esc(title)}</i> was rejected by admin."
                    ),
                    parse_mode="HTML",
                )
        except Exception as exc:
            logger.warning("Dashboard reject: could not notify user %s: %s", user_id, exc)

        return _flash_redirect("/admin/submissions", f"✓ Rejected #{sub_id}")

    except Exception as exc:
        logger.error("Dashboard reject error: %s", exc)
        return _flash_redirect("/admin/submissions", f"Error: {exc}")


# ── Bans page ─────────────────────────────────────────────────────────────

async def handle_bans(request: web.Request) -> web.Response:
    redir = _require_auth(request)
    if redir:
        return redir

    from repository import bans_list

    flash = request.rel_url.query.get("flash", "")
    bans = await bans_list(limit=100)

    if not bans:
        table_html = "<p style='color:var(--muted);padding:1rem 0'>No banned users.</p>"
    else:
        tbody = "".join(
            f"""<tr>
              <td><code>{row[0]}</code></td>
              <td>@{_esc(row[1] or "?")}</td>
              <td>{_esc(row[2] or "")}</td>
              <td style="color:var(--muted);font-size:.8rem">{_fmt_ts(row[3])}</td>
              <td>
                <form method="POST" action="/admin/bans/remove" style="display:inline">
                  <input type="hidden" name="user_id" value="{row[0]}">
                  <button class="btn btn-success btn-sm" type="submit">Unban</button>
                </form>
              </td>
            </tr>"""
            for row in bans
        )
        table_html = f"""<div class="table-wrap">
          <table>
            <tr><th>User ID</th><th>Username</th><th>Reason</th><th>Banned at</th><th></th></tr>
            {tbody}
          </table>
        </div>"""

    add_form = """
<div class="card" style="margin-bottom:1.5rem">
  <div style="font-weight:600;margin-bottom:.75rem">Ban a user</div>
  <form method="POST" action="/admin/bans/add">
    <div class="form-row">
      <input type="number" name="user_id" placeholder="Telegram user ID" required style="width:160px">
      <input type="text" name="username" placeholder="@username (optional)" style="width:180px">
      <input type="text" name="reason" placeholder="Reason" required style="flex:1;min-width:160px">
      <button class="btn btn-danger" type="submit">Ban user</button>
    </div>
  </form>
</div>"""

    body = f"""
<div class="page-header">
  <h1>🚫 User Bans</h1>
  <p>{len(bans)} banned user{'s' if len(bans) != 1 else ''}.</p>
</div>
{add_form}
<div class="card">{table_html}</div>"""

    return _page("Bans", "bans", body, flash)


async def handle_bans_add(request: web.Request) -> web.Response:
    redir = _require_auth(request)
    if redir:
        return redir

    data = await request.post()
    try:
        user_id = int(data.get("user_id", 0))
        username = str(data.get("username", "")).lstrip("@").strip()
        reason = str(data.get("reason", "")).strip()
        if not user_id or not reason:
            return web.HTTPFound("/admin/bans?flash=Invalid input — user_id and reason required")
        from repository import bans_add
        await bans_add(user_id, username, reason, banned_by=0)
        return _flash_redirect("/admin/bans", f"✓ Banned user {user_id}")
    except Exception as exc:
        return _flash_redirect("/admin/bans", f"Error: {exc}")


async def handle_bans_remove(request: web.Request) -> web.Response:
    redir = _require_auth(request)
    if redir:
        return redir

    data = await request.post()
    try:
        user_id = int(data.get("user_id", 0))
        from repository import bans_remove
        removed = await bans_remove(user_id)
        if removed:
            return _flash_redirect("/admin/bans", f"✓ Unbanned user {user_id}")
        return web.HTTPFound("/admin/bans?flash=User not found in ban list")
    except Exception as exc:
        return _flash_redirect("/admin/bans", f"Error: {exc}")


# ── Metrics page ──────────────────────────────────────────────────────────

async def handle_metrics(request: web.Request) -> web.Response:
    redir = _require_auth(request)
    if redir:
        return redir

    from metrics import get_metrics, get_daily_stats
    from repository import stats_top_credit_users, stats_credit_totals

    flash = request.rel_url.query.get("flash", "")
    all_metrics, today_stats, top_users, credit_totals = await _gather(
        get_metrics(),
        get_daily_stats(),
        stats_top_credit_users(limit=15),
        stats_credit_totals(),
    )

    # All-time counters table
    metrics_rows = "".join(
        f"<tr><td>{_esc(k)}</td><td style='text-align:right'><b>{v:,}</b></td></tr>"
        for k, v in sorted(all_metrics.items())
    ) or "<tr><td colspan='2' style='color:var(--muted)'>No metrics recorded yet.</td></tr>"

    # Top credit holders
    top_rows = "".join(
        f"<tr><td>{i+1}</td><td><code>{row[0]}</code></td><td>@{_esc(row[1] or '?')}</td>"
        f"<td style='text-align:right'><b>{row[2]:,}</b></td></tr>"
        for i, row in enumerate(top_users or [])
    ) or "<tr><td colspan='4' style='color:var(--muted)'>No data.</td></tr>"

    # Gift credits form
    gift_form = """
<div class="card" style="margin-top:1.5rem" id="gift">
  <div style="font-weight:600;margin-bottom:.75rem">🎁 Gift credits to a user</div>
  <form method="POST" action="/admin/gift">
    <div class="form-row">
      <input type="number" name="user_id" placeholder="Telegram user ID" required style="width:160px">
      <input type="number" name="amount" placeholder="Credits" required min="1" style="width:100px">
      <input type="text" name="reason" placeholder="Reason (e.g. promo)" style="flex:1;min-width:160px">
      <button class="btn btn-primary" type="submit">Gift credits</button>
    </div>
  </form>
</div>"""

    body = f"""
<div class="page-header">
  <h1>📈 Metrics & Stats</h1>
  <p>All-time counters, top users, gift credits.</p>
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem">
  <div class="card">
    <div style="font-weight:600;margin-bottom:.75rem">All-time counters</div>
    <div class="table-wrap">
      <table><tr><th>Metric</th><th style="text-align:right">Value</th></tr>
        {metrics_rows}
      </table>
    </div>
  </div>
  <div class="card">
    <div style="font-weight:600;margin-bottom:.75rem">Top credit holders</div>
    <div class="table-wrap">
      <table><tr><th>#</th><th>User ID</th><th>Username</th><th style="text-align:right">Balance</th></tr>
        {top_rows}
      </table>
    </div>
  </div>
</div>
{gift_form}"""

    return _page("Metrics", "metrics", body, flash)


async def handle_gift(request: web.Request) -> web.Response:
    redir = _require_auth(request)
    if redir:
        return redir

    data = await request.post()
    try:
        user_id = int(data.get("user_id", 0))
        amount = int(data.get("amount", 0))
        reason = str(data.get("reason", "admin_gift")).strip() or "admin_gift"
        if not user_id or amount <= 0:
            return web.HTTPFound("/admin/metrics?flash=Invalid input")
        from credits import add_credits
        new_bal = await add_credits(user_id, amount, reason)
        try:
            from app_context import _BOT_INSTANCE
            if _BOT_INSTANCE:
                await _BOT_INSTANCE.send_message(
                    chat_id=user_id,
                    text=(
                        f"🎁 An admin gifted you <b>{amount} credits</b>!\\n"
                        f"New balance: <b>{new_bal}</b>."
                    ),
                    parse_mode="HTML",
                )
        except Exception:
            pass
        return _flash_redirect("/admin/metrics", f"✓ Gifted {amount} credits to {user_id} — new balance {new_bal}")
    except Exception as exc:
        return _flash_redirect("/admin/metrics", f"Error: {exc}")


# ── Route registration ────────────────────────────────────────────────────

def register_dashboard(app: web.Application) -> None:
    """Register all /admin/* routes on an aiohttp Application."""
    app.router.add_get("/admin/login", handle_login_get)
    app.router.add_post("/admin/login", handle_login_post)
    app.router.add_get("/admin/logout", handle_logout)

    app.router.add_get("/admin/", handle_overview)
    app.router.add_get("/admin", handle_overview)

    app.router.add_get("/admin/submissions", handle_submissions)
    app.router.add_post("/admin/submissions/{id}/approve", handle_approve)
    app.router.add_post("/admin/submissions/{id}/reject", handle_reject)

    app.router.add_get("/admin/bans", handle_bans)
    app.router.add_post("/admin/bans/add", handle_bans_add)
    app.router.add_post("/admin/bans/remove", handle_bans_remove)

    app.router.add_get("/admin/metrics", handle_metrics)
    app.router.add_post("/admin/gift", handle_gift)

    app.router.add_get("/admin/leaderboard", handle_leaderboard)


# ── Async gather helper ───────────────────────────────────────────────────

async def _gather(*coros):
    import asyncio
    return await asyncio.gather(*coros)


# ── Leaderboard page ──────────────────────────────────────────────────────

async def handle_leaderboard(request: web.Request) -> web.Response:
    redir = _require_auth(request)
    if redir:
        return redir

    from repository import leaderboard_get_page

    try:
        page = max(0, int(request.rel_url.query.get("page", "0")))
    except ValueError:
        page = 0

    limit = 20
    rows = await leaderboard_get_page(limit + 1, page * limit)
    has_next = len(rows) > limit
    rows = rows[:limit]

    if not rows:
        table_html = "<p style='color:var(--muted);padding:1rem 0'>No leaderboard data yet.</p>"
    else:
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        tbody = "".join(
            f"""<tr>
              <td style="font-size:1.1rem">{medals.get(page * limit + i, str(page * limit + i + 1))}</td>
              <td>@{_esc(row[0] or "?")}</td>
              <td style="text-align:right"><b>{row[1]:,}</b></td>
            </tr>"""
            for i, row in enumerate(rows)
        )
        table_html = f"""<div class="table-wrap">
          <table>
            <tr><th>Rank</th><th>Username</th><th style="text-align:right">Score</th></tr>
            {tbody}
          </table>
        </div>"""

    pager = '<div class="pagination">'
    if page > 0:
        pager += f'<a href="/admin/leaderboard?page={page-1}">← Prev</a>'
    pager += f'<span class="cur">Page {page + 1}</span>'
    if has_next:
        pager += f'<a href="/admin/leaderboard?page={page+1}">Next →</a>'
    pager += "</div>"

    body = f"""
<div class="page-header">
  <h1>🏆 Leaderboard</h1>
  <p>Top contributors ranked by score.</p>
</div>
<div class="card">
  {table_html}
  {pager}
</div>"""

    return _page("Leaderboard", "leaderboard", body)
