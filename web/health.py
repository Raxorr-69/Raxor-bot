from aiohttp import web


# =========================
# Health Check Handler
# =========================


async def health_check(request: web.Request) -> web.Response:
    """Return a simple JSON payload confirming the bot process is alive."""

    bot = request.app["bot"]

    payload = {
        "status": "ok",
        "bot_ready": bot.is_ready(),
        "guild_count": len(bot.guilds) if bot.is_ready() else 0,
    }

    return web.json_response(payload)
