# 🎵 TrackCredits Bot — v1.2.5

> A Telegram bot that looks up song credits, lyrics, and streaming links — just send a track name or paste a Spotify / YouTube / Apple Music link.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-22.7-blue)](https://github.com/python-telegram-bot/python-telegram-bot)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-336791?logo=postgresql)](https://github.com/MagicStack/asyncpg)
[![Version](https://img.shields.io/badge/version-1.2.4-green)](#)
[![Coverage](https://img.shields.io/badge/coverage-30%25-orange)](#)
[![License](https://img.shields.io/badge/License-MIT-green)](#license)
[![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions)](/.github/workflows/ci.yml)

---

## ✨ Features

| | |
|---|---|
| 🎼 **Full Credits** | Producer, Composer, Mixing/Mastering Engineer, Label, ISRC — aggregated from Genius, MusicBrainz, and YouTube |
| 🎤 **Lyrics** | Fetched automatically from Genius → lrclib.net → lyrics.ovh in priority order |
| 🇻🇳 **Vietnamese Music** | Dedicated ZingMP3 → NhacCuaTui integration, activated automatically by diacritics detection |
| 🔗 **Streaming Links** | Spotify, Apple Music, YouTube, Deezer, Tidal, SoundCloud, Amazon Music, and more via Odesli |
| ⚡ **Two-layer Cache** | In-memory (1h TTL) + PostgreSQL (7-day soft / 14-day hard TTL) |
| 👥 **Community Contributions** | Users submit credits/lyrics corrections → admin reviews → published immediately |
| 🏆 **Leaderboard** | Paginated contributor rankings (+10 pts credits/lyrics, +5 pts bug reports) |
| 💎 **Credits System** | Free starting credits, daily bonuses, purchasable packs |
| 💳 **Payment Webhooks** | Automatic fulfillment via MoMo IPN and Stripe webhook |
| 🌐 **10 Languages** | EN · VI · ES · PT · FR · RU · KO · JA · ZH · AR — all 91 keys complete |
| 🛡️ **Rate Limiting** | 10 req/60s per user, 20 req/60s per chat |
| 🔌 **Circuit Breaker** | Per-API breaker (CLOSED → OPEN → HALF_OPEN) |
| 🗄️ **Auto Migrations** | Schema created and updated on startup — no manual SQL |
| 📊 **Web Admin Dashboard** | Full-featured browser UI: metrics, submissions, bans, leaderboard, gift credits — protected by HMAC cookie session |
| 👥 **Multi-admin** | Comma-separated `ADMIN_CHAT_IDS` for multiple Telegram admins |

---

## 🚀 Quick Start

**Search by song name:**
```
Blank Space Taylor Swift
```

**Search by link:**
```
https://open.spotify.com/track/...
https://www.youtube.com/watch?v=...
https://music.apple.com/...
```

The bot returns a menu: **Streams · Credits · Lyrics · Contribute · Wrong track**

---

## 📋 Commands

### User

| Command | Description |
|---|---|
| `/start` | Start the bot and select language |
| `/help` | Usage guide |
| `/lang` | Switch language |
| `/top` | Contributor leaderboard |
| `/credits` | Check credit balance and history |
| `/daily` | Claim daily bonus credits |
| `/buy` | Purchase credit packs |
| `/terms` | Terms of service |
| `/privacy` | Privacy policy |
| `/cancel` | Cancel current action |

### Admin

| Command | Description |
|---|---|
| `/admin` | Dashboard — metrics, pending count, quick actions |
| `/ban <user_id> [reason]` | Ban a user |
| `/unban <user_id>` | Unban a user |
| `/broadcast <msg>` | Message all users |
| `/giftcredits <user_id> <amount>` | Gift credits |
| `/confirmpayment <user_id> <pack_id>` | Manually confirm payment |
| `/subs` | List pending submissions |
| `/export` | Export data |

---

## ⚙️ Environment Variables

### Required

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token from @BotFather |
| `DATABASE_URL` | PostgreSQL connection string |

### Strongly recommended

| Variable | Description |
|---|---|
| `GENIUS_TOKEN` | Free token from [genius.com/api-clients](https://genius.com/api-clients). Without this, credits and lyrics will be unavailable for most tracks. |
| `ADMIN_CHAT_ID` | Your Telegram user ID — enables all admin commands |
| `ADMIN_CHAT_IDS` | Comma-separated list of admin Telegram IDs (e.g. `111,222`). Overrides `ADMIN_CHAT_ID` when set. |
| `DASHBOARD_SECRET` | Password to protect the `/admin/` web dashboard. Set to a strong random string. |

> The bot will log a startup warning if `GENIUS_TOKEN` is missing.

### Payment (optional)

| Variable | Description |
|---|---|
| `PAYMENT_PROVIDER` | `momo` \| `stripe` \| `manual` (default: `manual`) |
| `MOMO_PARTNER_CODE` | MoMo partner code |
| `MOMO_ACCESS_KEY` | MoMo access key |
| `MOMO_SECRET_KEY` | MoMo secret key |
| `MOMO_IPN_URL` | `https://<your-domain>/payment/momo/ipn` |
| `MOMO_REDIRECT_URL` | Redirect after MoMo payment |
| `STRIPE_SECRET_KEY` | Stripe secret key (`sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret (`whsec_...`) |
| `BOT_BASE_URL` | Public URL for Stripe success/cancel redirect |

### System (optional)

| Variable | Default | Description |
|---|---|---|
| `WEBHOOK_URL` | *(unset)* | Enable webhook mode (e.g. `https://yourbot.fly.dev`) |
| `WEBHOOK_PORT` | `8443` | Telegram webhook port |
| `WEBHOOK_SECRET_TOKEN` | *(unset)* | **Required if `WEBHOOK_URL` is set.** Validated against Telegram's `X-Telegram-Bot-Api-Secret-Token` header on every request — without it `/webhook` is a fixed, guessable, unauthenticated URL. Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `HEALTH_PORT` | `8080` | Health + payment webhook + dashboard port |
| `LOG_FILE` | *(unset)* | File path for rotating log (e.g. `logs/bot.log`) |
| `CREDITS_STARTING` | `20` | Credits for new users |
| `CREDITS_SEARCH_COST` | `1` | Credits per search |
| `CREDITS_DAILY_BONUS` | `3` | Credits from `/daily` |
| `DASHBOARD_INSECURE_COOKIE` | *(unset)* | Set to `true` to disable `Secure` cookie flag — **local HTTP dev only** |

---

## 💳 Payment

### MoMo (Vietnam)
1. Register at [business.momo.vn](https://business.momo.vn) → get API credentials
2. Set `MOMO_PARTNER_CODE`, `MOMO_ACCESS_KEY`, `MOMO_SECRET_KEY`
3. Set `MOMO_IPN_URL=https://<your-domain>/payment/momo/ipn`
4. Set `PAYMENT_PROVIDER=momo`

MoMo POSTs confirmations to `/payment/momo/ipn`. Credits added automatically.

### Stripe (International)
1. Create a Stripe account and get your secret key
2. Dashboard → Webhooks → Add endpoint: `https://<your-domain>/webhook/stripe`
3. Select event: `checkout.session.completed` → copy signing secret
4. Set `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `BOT_BASE_URL`
5. Set `PAYMENT_PROVIDER=stripe`

Both webhooks are served on `HEALTH_PORT` (default `8080`).

### Manual (default)
No setup needed. Admin uses `/confirmpayment <user_id> <pack_id>` after receiving payment.

---

## 🇻🇳 Vietnamese Music Support

For queries with Vietnamese diacritics (à á ả ã ạ ă â đ ơ ư ...), the bot automatically fetches from:

1. **ZingMP3** — title, artist, thumbnail, synced LRC lyrics
2. **NhacCuaTui** — fallback scraper if ZingMP3 has no results

This runs in parallel with the international pipeline and supplements missing lyrics or thumbnails.

---

## 🏗️ Architecture

```
main.py
├── app_factory.py       ← DI + service lifecycle
├── handlers.py          ← Command & message handlers
├── callback_registry.py ← Callback routing
└── callbacks/           ← menu / contrib / admin / navigation

├── track_manager.py     ← Core: URL/query → TrackResolution
├── services.py          ← render_credits(), build_main_text()
├── merger.py            ← Multi-source metadata merge

├── api/clients/
│   ├── base.py          ← Circuit breaker, shared aiohttp session
│   ├── genius.py        ← Credits + lyrics
│   ├── musicbrainz.py   ← ISRC + label
│   ├── odesli.py        ← Streaming links
│   ├── lyrics.py        ← lrclib.net + lyrics.ovh fallback
│   └── viet_music.py    ← ZingMP3 + NhacCuaTui

├── health.py            ← /health /ready + /payment/momo/ipn + /webhook/stripe
├── payment.py           ← MoMo + Stripe + manual payment logic
├── cache.py             ← 2-layer cache + rate limiter
├── credits.py           ← Balance, daily bonus, deduction
├── db.py                ← asyncpg pool + migrations
├── i18n.py              ← 10 languages, 91 keys each
└── migrations/          ← Versioned SQL, auto-applied
```

---

## 🛠️ Tech Stack

| Component | Library |
|---|---|
| Bot framework | python-telegram-bot 22.7 |
| Async HTTP | aiohttp 3.11 |
| Database | asyncpg + PostgreSQL |
| Validation | Pydantic v2 |
| YouTube metadata | yt-dlp |
| Credits & Lyrics | Genius API |
| Music metadata | MusicBrainz |
| Platform links | Odesli |
| Vietnamese music | ZingMP3 + NhacCuaTui |
| Payments | MoMo + Stripe |

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

## 👤 Author

**ndhn27**

---

## 📝 Changelog

### v1.2.5
- **Security fix:** Telegram webhook had no `secret_token` — `WEBHOOK_PATH` defaults to a fixed, guessable `/webhook`, and every admin-only command trusts `update.effective_user.id` from the incoming Update with no other check. Anyone who found the endpoint could POST a forged Update JSON (any `from.id`, including a spoofed admin id) straight to the bot. `run_webhook()` now takes `secret_token=WEBHOOK_SECRET_TOKEN`, which PTB validates against Telegram's `X-Telegram-Bot-Api-Secret-Token` header on every request; a startup warning fires if `WEBHOOK_URL` is set without it.
- **Fix:** `deduct_credits()` used `SELECT ... FOR UPDATE` followed by a separate `UPDATE` — but each went through its own `db_execute()` call (its own connection, its own auto-committed implicit transaction), so the row lock was released before the `UPDATE` ran. Two near-simultaneous deductions could both pass the balance check and both apply, overdrawing the account. Now a single atomic `UPDATE ... WHERE balance >= $2 RETURNING balance` — same fix pattern as the v1.2.1 payment idempotency fix, applied to credits.
- **Security fix:** Pasting a non-music URL that Odesli/Spotify oEmbed couldn't resolve fell through to `yt-dlp.extract_info(url)` with the raw, unvalidated URL — yt-dlp's generic extractor will fetch anything, so the bot's server could be made to issue outbound requests to internal/cloud-metadata addresses on a user's behalf. Added a host allowlist (YouTube, Spotify, Apple Music, Deezer, Tidal, SoundCloud, ZingMP3, NhacCuaTui) checked before the URL ever reaches yt-dlp.
- **Tests:** Added `tests/test_credits.py` (deduct/insufficient-balance/race behavior) and `tests/test_url_allowlist.py` (allowed vs. blocked hosts).

### v1.2.4
- **Fix:** `/admin/login` (GET and POST) 500'd unconditionally — `LOGIN_PAGE_HTML.format(error=...)` collided with the page's own embedded CSS (`str.format()` treats every literal `{...}` in the stylesheet, e.g. `{ box-sizing: border-box; }`, as a placeholder). The login page could not render at all; nobody, including the admin, could reach the dashboard. Replaced with `render_login_page()`, which uses `str.replace()` instead.
- **New:** Rate limiting on `/admin/login` — 5 failed attempts within 5 minutes locks the client IP out for 15 minutes (`429` + `Retry-After`), configurable via `DASHBOARD_LOGIN_MAX_ATTEMPTS` / `DASHBOARD_LOGIN_WINDOW_SECONDS` / `DASHBOARD_LOGIN_LOCKOUT_SECONDS`. In-memory, per-process — fine for a single instance; move to Postgres/Redis if this ever runs multiple replicas.
- **New:** `client_ip()` defaults to `request.remote` (not spoofable). Opt in via `DASHBOARD_TRUST_PROXY_HEADERS=true` to trust `X-Real-IP` / the last hop of `X-Forwarded-For` instead — only if this runs behind a reverse proxy you control and you've verified which hop it actually sets.
- **Docs:** Added `deploy/nginx.conf.example` — path-based rate limiting and an optional IP allowlist for `/admin/`, while leaving `/payment/momo/ipn`, `/webhook/stripe`, `/health`, and `/ready` open (they share `HEALTH_PORT` with the dashboard, per `health.py`).

### v1.2.3
- **Fix:** Contribution flow (`callbacks/contrib.py`) was missing the "← Back" button on all three input-request screens (credits, lyrics, report) — users had to `/cancel` and start over if they changed their mind mid-flow. Also removed a leftover duplicate DB lookup.
- **Fix:** Dashboard "Uptime" stat was calculated (`uptime_h`) but never rendered — the metrics page never showed it. Added the missing stat card.
- **Chore:** CI lint step now actually gates the pipeline — removed the `|| true` fallback that silently let lint errors through on every push.
- **Chore:** Added `pytest-cov` and `.coveragerc` (excludes `tests/` from the coverage denominator) so CI reports real test coverage.
- **Chore:** Added `dependabot.yml` — weekly automated PRs for pip, GitHub Actions, and the Docker base image.
- **Chore:** Removed an unused variable and two duplicate imports from `handlers.py`.
- **Docs:** Added coverage badge to README.

### v1.2.2
- **Fix:** CI was failing on every push — 13 tests had drifted out of sync with the codebase (stale mock configuration, an admin-check refactor the tests weren't updated for, and translation strings that no longer matched `i18n.py`). No production code changed; fixes confined to `tests/`.
- **Fix:** `payment.py` imports the `stripe` package when `PAYMENT_PROVIDER=stripe`, but it was missing from `requirements.txt` — a fresh deploy with Stripe enabled would crash with `ModuleNotFoundError` on first checkout. Added `stripe==15.3.1`.

### v1.2.1
- **Fix:** `fulfill_payment()` could double-credit a purchase on MoMo IPN / Stripe webhook retry or replay — the `payment_orders` table (added in v1.2.0's migration `007`) was never actually queried before crediting. Now claims the `order_id` via `INSERT ... ON CONFLICT (order_id) DO NOTHING` before calling `add_credits`, so a given order is fulfilled exactly once regardless of how many times the webhook fires.
- **Fix:** Dashboard flash-message redirects (`handle_approve`, `handle_reject`, ban/gift actions) built the query string with raw f-strings — a submission title or exception message containing `&`/`#`/`%` could corrupt the redirect. Now routed through a single `_flash_redirect()` helper that percent-encodes the value.
- **Tests:** Added `tests/test_payment.py` covering the idempotency fix (first fulfillment, duplicate delivery, unknown package, simulated race).

### v1.2.0
- **New:** Web Admin Dashboard at `/admin/` — full browser UI: metrics overview, submissions review (approve/reject with Telegram notification), ban management, leaderboard, gift credits
- **New:** HMAC cookie session auth for dashboard — protected by `DASHBOARD_SECRET` env var; `Secure` flag set by default
- **New:** Multi-admin support via `ADMIN_CHAT_IDS` (comma-separated Telegram user IDs); backwards-compatible with `ADMIN_CHAT_ID`
- **Fix:** `set_bot()` now correctly wires the PTB Bot instance for Telegram notifications from dashboard and webhook handlers (was silently broken — notifications never sent in v1.1.0)
- **Fix:** Session cookie now includes `Secure` flag on HTTPS deployments (opt-out via `DASHBOARD_INSECURE_COOKIE=true` for local HTTP dev)
- **Docs:** Leaderboard scoring corrected: +10 pts for credits/lyrics submissions, +5 pts for bug reports
- **Docs:** `ADMIN_CHAT_IDS` and `DASHBOARD_INSECURE_COOKIE` added to `.env.example`

### v1.1.0
- **Fix:** i18n.py was truncated — all 10 languages now 100% complete (91 keys)
- **Fix:** Payment webhooks live: MoMo IPN at `/payment/momo/ipn`, Stripe at `/webhook/stripe`
- **Fix:** Vietnamese music (`viet_music.py`) now integrated into track resolution
- **New:** File logging via `LOG_FILE` env var (rotating, 10 MB, 3 backups)
- **New:** Startup warning when `GENIUS_TOKEN` is missing
- **New:** GitHub Actions CI workflow (tests + Docker smoke test + Railway deploy)
- **Docs:** `/buy`, `/daily`, `/credits` documented; payment setup guide added

### v1.0.0 — Initial release
