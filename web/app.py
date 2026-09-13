from aiohttp import web

from web.health import health_check
from web.internal import get_channels, get_roles, search_members, ensure_text_channel, ensure_role, delete_channel, delete_role, configure_verification


# =========================
# Web Application Factory
# =========================


def create_app(bot) -> web.Application:
    """Build the aiohttp web application used for health checks and the
    optional dashboard-integration routes (see web/internal.py)."""

    app = web.Application()

    app["bot"] = bot

    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    app.router.add_get("/internal/guilds/{guild_id}/channels", get_channels)
    app.router.add_get("/internal/guilds/{guild_id}/roles", get_roles)
    app.router.add_get("/internal/guilds/{guild_id}/members/search", search_members)
    app.router.add_post("/internal/guilds/{guild_id}/channels/ensure", ensure_text_channel)
    app.router.add_post("/internal/guilds/{guild_id}/roles/ensure", ensure_role)
    app.router.add_post("/internal/guilds/{guild_id}/channels/delete", delete_channel)
    app.router.add_post("/internal/guilds/{guild_id}/roles/delete", delete_role)
    app.router.add_post("/internal/guilds/{guild_id}/verification/configure", configure_verification)

    return app


# =========================
# Web Server Runner
# =========================


async def start_web_server(
    bot,
    host: str = "0.0.0.0",
    port: int = 8080,
):
    """Start the health check web server in the background."""

    app = create_app(bot)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    return runner
