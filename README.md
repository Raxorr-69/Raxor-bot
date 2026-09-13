# Raxor Discord Bot — Final Merged

Production-oriented merge of the Raxor Cloud and GPT versions.

## Included
- Discord bot + automatic command loading
- Member/message/voice intents and tracking
- Moderation, warnings, automod and restrictions
- Invite tracking and inviter attribution
- Announcements/broadcasting
- Leveling and leaderboard rewards
- Link protection and spam detection
- PostgreSQL persistence
- Optional aiohttp health endpoints (`/` and `/health`)

## Setup
1. Copy `.env.example` to `.env`.
2. Fill in `DISCORD_TOKEN`, `BOT_OWNER_ID`, and `DATABASE_URL`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Run: `python main.py`.

Never commit `.env` or expose your Discord bot token.

## Web dashboard

A separate web dashboard (FastAPI + React) can sit alongside this bot —
see `../dashboard/README.md`. It's a different codebase with its own
setup, its own `.env`, and its own process — it never runs this bot's
code or opens a gateway connection. It connects in two ways:

- **Database.** It reads and writes the same `DATABASE_URL` Postgres
  database this bot uses, through the tables `database/models.py`
  creates, including a small `recovery_requests` table it can insert
  into to ask for an on-demand channel rescan — `recovery_request_poll_loop`
  in `bot/events.py` is what actually picks that up and runs it. It
  also creates and owns one small table of its own, `dashboard_sessions`,
  for its login sessions — see its own README for why.
- **Internal API (optional), a separate secret from the bot token.**
  This bot's own health-check web server (`web/app.py`) exposes three
  extra read-only routes (`web/internal.py`) — list a guild's channels,
  list its roles, search its members by name — that the dashboard calls
  for its channel/role selectors and username search, protected by
  `DASHBOARD_INTERNAL_KEY`. Set the exact same value in both `.env`
  files to turn this on. The dashboard never receives `DISCORD_TOKEN`
  itself; `DASHBOARD_INTERNAL_KEY` has no privileges beyond those three
  lookups, so a compromised dashboard can't use it to send messages,
  ban/kick, or do anything else this bot can do.

Running the dashboard is entirely optional and this bot works the same
with or without it. If you rename or add a column in
`database/models.py`, mirror the change in the dashboard's
`backend/db/repositories.py` — the two aren't wired together by imports,
so nothing will warn you if they drift apart.

## Render deployment

This bot is a long-running process (a persistent Discord gateway
connection), not a request/response server, so it's a fundamentally
different kind of Render service from the dashboard's — no Dockerfile
is needed here, Render's native Python runtime is enough.

**Which service type to pick decides whether the dashboard integration
works:**

- **Background Worker** — simplest option if you don't need the
  dashboard's live channel/role selectors or username search. Leave
  `PORT` and `DASHBOARD_INTERNAL_KEY` unset; the bot runs with no web
  server at all. Background Workers on Render don't get a public URL,
  so nothing could reach `web/internal.py` even if you configured it.
- **Web Service** — required if the dashboard's `BOT_INTERNAL_API_URL`
  needs to actually reach this bot. Render sets `PORT` for you
  automatically for this service type, which is exactly what
  `config/settings.py`'s optional `PORT` handling and `main.py`'s
  `if PORT: web_runner = await start_web_server(...)` already expect —
  nothing to change in the code either way. Render will also start
  running its own health checks against this service once it's a Web
  Service, which `/health` (see `web/health.py`) answers.

### Render settings

- Runtime: **Python 3**
- Build command: `pip install -r requirements.txt`
- Start command: `python main.py`
- Service type: Background Worker or Web Service (see above)

Set these environment variables on the Render service:

```text
DISCORD_TOKEN=<bot token, from the Discord Developer Portal>
BOT_OWNER_ID=<your Discord user id>
DATABASE_URL=<same PostgreSQL URL as the Dashboard service>
ENVIRONMENT=production
# Only if deploying as a Web Service and enabling dashboard integration:
DASHBOARD_INTERNAL_KEY=<same random secret configured on the Dashboard service>
```

`PORT` itself doesn't need to be set manually — leave it unset for a
Background Worker, and Render supplies it automatically for a Web
Service. If deploying as a Web Service for the dashboard integration,
the Dashboard service's `BOT_INTERNAL_API_URL` should point at this
service's Render-assigned internal or public URL (Render's private
service-to-service networking, if both services are in the same
Render account/region, avoids exposing `web/internal.py` to the public
internet at all — check Render's current docs for the exact hostname
format, since that detail can change).

## Safe hardening pass

This build preserves the existing command and service behavior. The hardening pass only adds defensive error handling for invite-cache/tracking events, validates the optional web-server port, and cleans up the health-check server during shutdown. The leveling implementation and its public functions are unchanged.

### Dashboard channel setup

The dashboard may call the authenticated `/internal/guilds/{guild_id}/channels/ensure` endpoint when a channel-backed feature is enabled without a selected channel. Raxor creates or reuses the managed text channel and returns its Discord ID; the dashboard then stores that ID in PostgreSQL. This endpoint is protected by `DASHBOARD_INTERNAL_KEY` and is only intended for the dashboard's explicit Save action.
