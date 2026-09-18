import os

from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


# =========================
# Bot Configuration
# =========================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0"))
TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID", "0"))


# =========================
# Application Configuration
# =========================

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DATABASE_URL = os.getenv("DATABASE_URL")

# Optional port for the health-check web server (see web/app.py).
# Only used if set — leave unset to skip starting the web server.
PORT = os.getenv("PORT")

if PORT is not None:
    PORT = PORT.strip()
    if not PORT:
        PORT = None
    else:
        try:
            _port_value = int(PORT)
        except ValueError as exc:
            raise ValueError("PORT must be a valid integer.") from exc

        if not 1 <= _port_value <= 65535:
            raise ValueError("PORT must be between 1 and 65535.")

        PORT = str(_port_value)


# =========================
# Dashboard Integration (optional)
# =========================
#
# A separate, purpose-built secret — NOT the Discord bot token — that
# lets the dashboard (see ../dashboard/backend) ask this already-running
# bot process for read-only guild data (channel list, role list, member
# search) it can't get through a user's own Discord OAuth login. The
# dashboard never sees DISCORD_TOKEN itself; it only holds this key,
# which the web server below only accepts on the /internal/* routes and
# which can't send messages, ban/kick, or do anything a real bot token
# can. If a compromised dashboard leaks this key, the blast radius is
# "someone can list channels/roles/members of guilds Raxor is in" — not
# full control of the bot.
#
# Leave unset to disable these routes entirely (web/internal.py returns
# 503 for all of them). Requires PORT to also be set, since these routes
# live on the same web server as the health check.

DASHBOARD_INTERNAL_KEY = os.getenv("DASHBOARD_INTERNAL_KEY") or None


# =========================
# Validation
# =========================

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing from .env")

if BOT_OWNER_ID == 0:
    raise ValueError("BOT_OWNER_ID is missing from .env")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from .env")
