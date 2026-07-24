# 🎵 TrackCredits Bot — Setup Guide

> A Telegram bot that looks up song credits, lyrics, and streaming links — just send a track name or paste a Spotify / YouTube / Apple Music link.

---

## ✅ Prerequisites (all options)

Before deploying on any platform, you need three things:

**1. Telegram Bot Token + Command Menu**
1. Open Telegram → search **@BotFather** → send `/newbot`
2. Follow the prompts, then copy the token (e.g. `123456789:AAFxxx...`)
3. Still in BotFather, send `/setcommands` → select your bot → paste the following block **exactly** (this registers all commands so they appear in Telegram's menu when users type `/`):

```
start - Start the bot and select language
help - Usage guide
lang - Switch language
top - Contributor leaderboard
credits - Check credit balance and history
daily - Claim daily bonus credits
buy - Purchase credit packs
terms - Terms of service
privacy - Privacy policy
cancel - Cancel current action
```

> **Note:** Admin commands (`/ban`, `/broadcast`, `/giftcredits`, etc.) are intentionally excluded — they only work for your account anyway, and listing them publicly reveals your bot's admin interface.

**2. Genius API Token**
1. Go to [genius.com/api-clients](https://genius.com/api-clients) → log in → **New API Client**
2. Fill in any name; App Website URL: `https://t.me/your_bot`
3. Copy the **Client Access Token**

**3. Your Telegram User ID** (for the admin panel)
1. Open Telegram → search **@userinfobot** → send `/start`
2. Copy the numeric ID it replies with (e.g. `987654321`)

---

## Deployment options

| Option | Best for | Cost | Difficulty |
|---|---|---|---|
| [A — Railway](#option-a--railway) | Beginners, quick start | Free tier available | Easy |
| [B — Render](#option-b--render) | Free hosting, always-on | Free tier available | Easy |
| [C — Fly.io](#option-c--flyio) | Global low-latency | Free tier available | Medium |
| [D — VPS / cloud server](#option-d--vps--cloud-server-ubuntu--debian) | Full control, production | ~$4–6/mo (e.g. Hetzner CX22) | Medium |
| [E — Docker Compose (any server)](#option-e--docker-compose-any-linux-server) | Docker-first workflow | Depends on server | Easy if Docker-familiar |
| [F — Local](#option-f--run-locally) | Development / testing | Free | Easy |

---

## Option A — Railway

Easiest option. No server management required.

### Step 1 — Upload the code to GitHub

1. Go to [github.com/new](https://github.com/new) → create a new repository (private recommended)
2. Extract the zip → drag all files into the repo → **Commit changes**

### Step 2 — Create the project on Railway

1. Go to [railway.app](https://railway.app) → log in with GitHub
2. **New Project** → **Deploy from GitHub repo** → select your repo
3. Railway will start building (may error — normal, DB not set up yet)

### Step 3 — Add a PostgreSQL database

1. Inside the project → **+ New** → **Database** → **PostgreSQL**
2. Wait ~30s for it to start
3. Click the database → **Variables** tab → copy **DATABASE_URL**

### Step 4 — Set environment variables

Click the bot service → **Variables** tab → add:

| Variable | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From Step 1 of Prerequisites |
| `GENIUS_TOKEN` | From Step 2 of Prerequisites |
| `ADMIN_CHAT_ID` | From Step 3 of Prerequisites |
| `DATABASE_URL` | Copied from the PostgreSQL service |

Railway will redeploy automatically.

### Step 5 — Verify

**Deployments** → latest deployment → **Logs** → look for `🚀 Starting bot...`

---

## Option B — Render

Free tier with always-on web service + managed PostgreSQL.

### Step 1 — Upload the code to GitHub

Same as [Railway Step 1](#step-1--upload-the-code-to-github).

### Step 2 — Create a PostgreSQL database on Render

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New +** → **PostgreSQL**
2. Name: `trackcredits-db` | Region: choose closest to you | Plan: **Free**
3. Click **Create Database** → wait for it to be ready
4. Copy the **Internal Database URL** (use this when both services are on Render)

### Step 3 — Create the bot service

1. **New +** → **Web Service** (a background worker has no HTTP port — use Web Service with a dummy port, or **Background Worker** if available on your plan)
2. Connect your GitHub repo
3. Settings:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
4. **Environment Variables** → add the same four variables as in Option A (use the Internal Database URL from Step 2)
5. Click **Create Web Service**

> **Note on Render free tier:** Free services spin down after 15 minutes of inactivity. For a Telegram bot this causes ~30s cold-start delays on the first message after idle. Upgrade to the Starter plan ($7/mo) for always-on behavior, or use a cron ping service to keep it awake.

---

## Option C — Fly.io

Good choice if you want low-latency globally or want to run the bot close to your users.

### Step 1 — Install the Fly CLI

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex
```

Log in: `fly auth login`

### Step 2 — Initialize the app

```bash
cd TrackCredits-Bot-v1.2.0
fly launch --no-deploy
```

When prompted:
- App name: choose any name (e.g. `trackcredits-bot`)
- Region: pick the one closest to your users
- PostgreSQL: **Yes** → **Development** (free)
- Redis: No

This creates a `fly.toml` file and a managed Postgres cluster. Copy the `DATABASE_URL` shown at the end.

### Step 3 — Set environment variables

```bash
fly secrets set TELEGRAM_BOT_TOKEN="your_token_here"
fly secrets set GENIUS_TOKEN="your_genius_token"
fly secrets set ADMIN_CHAT_ID="your_user_id"
fly secrets set DATABASE_URL="postgres://..."
```

### Step 4 — Deploy

```bash
fly deploy
```

### Step 5 — Check logs

```bash
fly logs
```

Look for `🚀 Starting bot...`

> **Scaling down to save credits:** By default Fly runs 1 machine. To use the free allowance efficiently: `fly scale count 1 --region <your-region>`

---

## Option D — VPS / cloud server (Ubuntu / Debian)

Best option for production use, full control, and no vendor lock-in. Works on any provider: Hetzner, DigitalOcean, Linode, Vultr, AWS EC2, Google Cloud, Oracle Free Tier, etc.

**Minimum specs:** 1 vCPU, 1 GB RAM, Ubuntu 22.04 LTS

### Step 1 — Connect to your server

```bash
ssh root@YOUR_SERVER_IP
```

### Step 2 — Install dependencies

```bash
apt update && apt upgrade -y
apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib git ffmpeg nodejs
```

### Step 3 — Create a PostgreSQL database

```bash
sudo -u postgres psql
```

Inside psql:
```sql
CREATE USER tcbot WITH PASSWORD 'choose_a_strong_password';
CREATE DATABASE tcbot OWNER tcbot;
\q
```

Your `DATABASE_URL` will be:
```
postgresql://tcbot:choose_a_strong_password@localhost:5432/tcbot
```

### Step 4 — Deploy the bot

```bash
# Create a dedicated user (do not run bots as root)
useradd -m -s /bin/bash botuser
su - botuser

# Clone or upload your code
# Option 1 — if you uploaded your code to GitHub first (see Option A Step 1 for instructions):
git clone https://github.com/YOUR_USERNAME/TrackCredits-Bot.git
cd TrackCredits-Bot

# Option 2 — transfer the zip directly from your computer (no GitHub needed):
# Run this on your LOCAL machine, then SSH back in:
#   scp /path/to/TrackCredits-Bot-v1.2.0.zip root@YOUR_SERVER_IP:/home/botuser/
# Then on the server:
#   cd /home/botuser && unzip TrackCredits-Bot-v1.2.0.zip && cd TrackCredits-Bot-v1.2.0

# Create virtualenv and install dependencies
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
nano .env   # fill in your credentials
```

`.env` contents:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://tcbot:choose_a_strong_password@localhost:5432/tcbot
GENIUS_TOKEN=your_genius_token
ADMIN_CHAT_ID=your_telegram_user_id
```

### Step 5 — Run as a systemd service (auto-restart on crash/reboot)

Back as root:

```bash
nano /etc/systemd/system/trackcredits.service
```

Paste:

```ini
[Unit]
Description=TrackCredits Telegram Bot
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/TrackCredits-Bot
EnvironmentFile=/home/botuser/TrackCredits-Bot/.env
ExecStart=/home/botuser/TrackCredits-Bot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
systemctl daemon-reload
systemctl enable trackcredits
systemctl start trackcredits
```

### Step 6 — Check logs

```bash
journalctl -u trackcredits -f
```

Look for `🚀 Starting bot...`

### Useful commands

```bash
systemctl status trackcredits      # check status
systemctl restart trackcredits     # restart after code update
journalctl -u trackcredits -n 100  # last 100 log lines
```

---

## Option E — Docker Compose (any Linux server)

Use this if your server already has Docker installed, or if you prefer container-based deployments. Works on any cloud provider, your own machine, or a Raspberry Pi.

### Step 1 — Install Docker

```bash
curl -fsSL https://get.docker.com | sh
```

### Step 2 — Upload the code

Upload the project folder to your server (via `scp`, `rsync`, `git clone`, etc.).

### Step 3 — Configure environment variables

```bash
cd TrackCredits-Bot-v1.2.0
cp .env.example .env
nano .env
```

Fill in `TELEGRAM_BOT_TOKEN`, `GENIUS_TOKEN`, and `ADMIN_CHAT_ID`.  
Do **not** set `DATABASE_URL` in `.env` — `docker-compose.yml` already sets it to the internal Postgres container.

### Step 4 — Build and start

```bash
docker compose up -d --build
```

This starts two containers: the bot and a PostgreSQL instance. Data is persisted in a Docker volume (`pgdata`) and survives restarts.

### Step 5 — Check logs

```bash
docker compose logs -f bot
```

### Useful commands

```bash
docker compose down              # stop everything
docker compose restart bot       # restart the bot only
docker compose pull && docker compose up -d --build   # update after code changes
docker compose exec postgres psql -U tcbot tcbot       # open a DB shell
```

---

## Option F — Run locally

For development and testing only.

**Requirements:** Python 3.10+, PostgreSQL

```bash
# 1. Enter the project folder
cd TrackCredits-Bot-v1.2.0

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate       # Linux / macOS
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env
cp .env.example .env
# Fill in your credentials

# 5. Run
python main.py
```

---

## Using the bot

Send any of the following:

```
Blinding Lights The Weeknd
```
```
https://open.spotify.com/track/...
```
```
https://www.youtube.com/watch?v=...
```
```
https://music.apple.com/...
```

The bot returns a menu with 5 buttons: **Streams · Credits · Lyrics · Contribute · Wrong track**

**Commands:**

**User commands:**

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
| `/cancel` | Cancel the current action |

**Admin commands:**

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

## ❓ Troubleshooting

**Bot does not respond after deployment**
→ Check your deployment logs. Usually a wrong `TELEGRAM_BOT_TOKEN` or `DATABASE_URL`.

**`Conflict: terminated by other getUpdates request`**
→ You are running the bot in two places at once. Stop the local instance and keep only one running.

**Credits or lyrics are incomplete**
→ Normal — lesser-known tracks may not have full data on Genius or MusicBrainz.

**Odesli HTTP 429 warning in logs**
→ Not a problem — the bot automatically falls back to another source.

**`yt-dlp` warning about JavaScript runtime**
→ Only affects some YouTube metadata. The Docker image already includes Node.js. For bare-metal installs, run `apt install nodejs` (Ubuntu) or add it to your platform's build config.

**PostgreSQL connection refused (VPS)**
→ Make sure PostgreSQL is running: `systemctl status postgresql`. Check that `DATABASE_URL` points to `localhost`, not an external host.

**`ModuleNotFoundError` on startup**
→ Virtual environment is not activated, or `pip install -r requirements.txt` was not run inside it.

---

## 📞 Support

If you run into issues during setup, contact **lindaaov10@gmail.com** with a screenshot of the error or the relevant log output.

---

## 📄 License

MIT — you are free to use, modify, and build commercial products with this code.
See [LICENSE](LICENSE) for full terms.

---

## 💳 Payment Webhooks Setup

Both MoMo and Stripe webhooks run on the **same port as the health check** (`HEALTH_PORT`, default `8080`). No extra server or port needed.

### MoMo (Vietnam)

**Step 1 — Get credentials**
1. Register at [business.momo.vn](https://business.momo.vn)
2. Go to **API Management** → copy `Partner Code`, `Access Key`, `Secret Key`

**Step 2 — Configure environment**
```env
PAYMENT_PROVIDER=momo
MOMO_PARTNER_CODE=MOMOXXXXXXXX
MOMO_ACCESS_KEY=your_access_key
MOMO_SECRET_KEY=your_secret_key
MOMO_IPN_URL=https://your-domain.com/payment/momo/ipn
MOMO_REDIRECT_URL=https://t.me/YourBot
```

**Step 3 — Verify**
After a test payment, check your bot logs for:
```
MoMo IPN: fulfilled tc_... → user ..., new balance ...
```

---

### Stripe (International cards)

**Step 1 — Get credentials**
1. Create account at [stripe.com](https://stripe.com)
2. Dashboard → Developers → API keys → copy **Secret key** (`sk_live_...`)

**Step 2 — Register webhook**
1. Dashboard → Developers → Webhooks → **Add endpoint**
2. URL: `https://your-domain.com/webhook/stripe`
3. Events: select `checkout.session.completed`
4. Click **Add endpoint** → copy **Signing secret** (`whsec_...`)

**Step 3 — Configure environment**
```env
PAYMENT_PROVIDER=stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
BOT_BASE_URL=https://your-domain.com
```

**Step 4 — Test locally (optional)**
```bash
# Install Stripe CLI
stripe listen --forward-to localhost:8080/webhook/stripe
```

---

### Manual payment (default — no config needed)

No webhook setup required. When a user buys a pack, they receive payment instructions. After you receive the payment, run:

```
/confirmpayment <user_id> <pack_id>
```

Example:
```
/confirmpayment 987654321 pack_120
```

---

## 📁 Log Files

To write logs to a file instead of (or in addition to) console output:

```env
LOG_FILE=logs/bot.log
```

The log file rotates automatically at 10 MB, keeping 3 backups.

```bash
# Create log directory before starting
mkdir -p logs
```

---

## 🔁 CI/CD with GitHub Actions

The included `.github/workflows/ci.yml` runs automatically on every push to `main`:

1. **Test** — spins up a PostgreSQL service, runs `pytest tests/`
2. **Docker smoke test** — builds the Docker image to catch build errors
3. **Deploy to Railway** — optional, triggered when `DEPLOY_TARGET=railway` is set in GitHub repo variables

To enable Railway auto-deploy:
1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Add **Secret**: `RAILWAY_TOKEN` (from Railway dashboard → Account → Tokens)
3. Add **Variable**: `DEPLOY_TARGET` = `railway`

