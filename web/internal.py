import asyncio
import re
import secrets
import time
from collections import defaultdict, deque

import discord
from aiohttp import web

from config.settings import DASHBOARD_INTERNAL_KEY


_CHANNEL_CREATION_LOCK = asyncio.Lock()
_ROLE_CREATION_LOCK = asyncio.Lock()
_INTERNAL_RATE: dict[str, deque[float]] = defaultdict(deque)
_INTERNAL_RATE_LOCK = asyncio.Lock()

# token -> (guild_id, resource_id, kind, expires_at_monotonic). A rollback
# is only ever attempted in the few seconds right after a Save's Discord
# resource creation fails to write to Postgres, so tokens have no reason
# to live longer than this — without a TTL, every successful create (the
# overwhelming majority, since most Saves succeed) would leave its token
# in memory forever, growing unbounded for as long as the bot runs.
_ROLLBACK_TOKEN_TTL_SECONDS = 300
_ROLLBACK_TOKENS: dict[str, tuple[int, int, str, float]] = {}
_ROLLBACK_TOKENS_LOCK = asyncio.Lock()


def _prune_expired_rollback_tokens() -> None:
    """Drop expired entries. Caller must hold _ROLLBACK_TOKENS_LOCK."""
    now = time.monotonic()
    expired = [token for token, (_, _, _, expires_at) in _ROLLBACK_TOKENS.items() if expires_at <= now]
    for token in expired:
        del _ROLLBACK_TOKENS[token]


async def _rate_limited(request: web.Request, limit: int = 120, window: int = 60) -> bool:
    """Small in-process limiter for the bot's public-facing internal API.

    The endpoint is already protected by a high-entropy shared secret; this
    second layer limits damage from a leaked key and accidental request loops.
    """
    forwarded = request.headers.get("X-Forwarded-For", "")
    ip = forwarded.split(",", 1)[0].strip() if forwarded else (request.remote or "unknown")
    key = f"{ip}:{request.path}"
    now = time.monotonic()
    async with _INTERNAL_RATE_LOCK:
        bucket = _INTERNAL_RATE[key]
        cutoff = now - window
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            return True
        bucket.append(now)
    return False


# =========================
# Internal Dashboard API
# =========================
#
# Read-only guild data for the dashboard's channel/role selectors and
# username search (see ../dashboard/backend/services/discord.py). Lives
# on the bot's own already-running aiohttp server (web/app.py) and reads
# straight from discord.py's in-memory cache / gateway — no extra
# Discord REST calls, and critically, no Discord bot token is ever
# handed to the dashboard. Everything here is protected by
# DASHBOARD_INTERNAL_KEY, a separate secret with no Discord privileges
# of its own beyond what these three handlers expose.


def _authorized(request: web.Request) -> bool:
    if not DASHBOARD_INTERNAL_KEY:
        return False

    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return False

    provided = header[len("Bearer "):]
    return secrets.compare_digest(provided, DASHBOARD_INTERNAL_KEY)


def _require_auth(request: web.Request) -> web.Response | None:
    if not DASHBOARD_INTERNAL_KEY:
        return web.json_response(
            {"detail": "Dashboard integration is not configured on this bot."},
            status=503,
        )
    if not _authorized(request):
        return web.json_response({"detail": "Unauthorized."}, status=401)
    return None


def _get_guild(request: web.Request, guild_id: int):
    bot = request.app["bot"]
    return bot.get_guild(guild_id)


async def get_channels(request: web.Request) -> web.Response:
    """List a guild's text-capable channels (text + announcement)."""

    unauthorized = _require_auth(request)
    if unauthorized:
        return unauthorized
    if await _rate_limited(request):
        return web.json_response({"detail": "Too many requests."}, status=429, headers={"Retry-After": "10"})

    try:
        guild_id = int(request.match_info["guild_id"])
    except ValueError:
        return web.json_response({"detail": "Invalid guild id."}, status=400)

    guild = _get_guild(request, guild_id)
    if guild is None:
        return web.json_response({"detail": "Bot is not in this guild."}, status=404)

    channels = [
        {"id": str(channel.id), "name": channel.name, "position": channel.position}
        for channel in guild.channels
        if isinstance(channel, discord.TextChannel)
    ]
    return web.json_response(channels)


async def get_roles(request: web.Request) -> web.Response:
    """List a guild's roles, excluding @everyone."""

    unauthorized = _require_auth(request)
    if unauthorized:
        return unauthorized
    if await _rate_limited(request):
        return web.json_response({"detail": "Too many requests."}, status=429, headers={"Retry-After": "10"})

    try:
        guild_id = int(request.match_info["guild_id"])
    except ValueError:
        return web.json_response({"detail": "Invalid guild id."}, status=400)

    guild = _get_guild(request, guild_id)
    if guild is None:
        return web.json_response({"detail": "Bot is not in this guild."}, status=404)

    roles = [
        {"id": str(role.id), "name": role.name, "position": role.position}
        for role in guild.roles
        if not role.is_default()
    ]
    return web.json_response(roles)


async def search_members(request: web.Request) -> web.Response:
    """Search a guild's members by username/nickname prefix, via
    discord.py's gateway member-query (requires the Members intent,
    already enabled — see bot/client.py) rather than a REST call."""

    unauthorized = _require_auth(request)
    if unauthorized:
        return unauthorized
    if await _rate_limited(request):
        return web.json_response({"detail": "Too many requests."}, status=429, headers={"Retry-After": "10"})

    try:
        guild_id = int(request.match_info["guild_id"])
    except ValueError:
        return web.json_response({"detail": "Invalid guild id."}, status=400)

    query = request.query.get("query", "").strip()
    try:
        limit = max(1, min(int(request.query.get("limit", 10)), 100))
    except ValueError:
        limit = 10

    if not query:
        return web.json_response([])

    guild = _get_guild(request, guild_id)
    if guild is None:
        return web.json_response({"detail": "Bot is not in this guild."}, status=404)

    try:
        members = await guild.query_members(query=query, limit=limit, presences=False)
    except Exception as exc:
        return web.json_response(
            {"detail": f"Member search failed: {exc}"}, status=502
        )

    results = [
        {
            "id": str(member.id),
            "username": member.name,
            "display_name": member.display_name,
        }
        for member in members
        if not member.bot
    ]
    return web.json_response(results)


async def ensure_text_channel(request: web.Request) -> web.Response:
    """Ensure a managed text channel exists for a dashboard feature.

    The dashboard calls this only when the user presses Save and a
    channel-backed feature is enabled without a selected channel. The
    bot performs the Discord API operation using its own token, then the
    dashboard stores the returned channel ID in PostgreSQL.
    """

    unauthorized = _require_auth(request)
    if unauthorized:
        return unauthorized
    if await _rate_limited(request):
        return web.json_response({"detail": "Too many requests."}, status=429, headers={"Retry-After": "10"})

    try:
        guild_id = int(request.match_info["guild_id"])
    except ValueError:
        return web.json_response({"detail": "Invalid guild id."}, status=400)

    guild = _get_guild(request, guild_id)
    if guild is None:
        return web.json_response({"detail": "Bot is not in this guild."}, status=404)

    try:
        payload = await request.json()
    except Exception:
        return web.json_response({"detail": "Invalid JSON body."}, status=400)

    name = str(payload.get("name", "")).strip().lower()
    if not name:
        return web.json_response({"detail": "Channel name is required."}, status=400)

    # Keep names predictable and Discord-safe. Do not accept arbitrary
    # channel creation parameters from the dashboard.
    allowed_names = {"level-up", "announcements", "verification", "welcome", "leave", "image-only", "clips-only", "restricted"}
    if name not in allowed_names:
        return web.json_response({"detail": "Unsupported managed channel."}, status=400)

    # Serialize check-and-create so two near-simultaneous Save requests
    # cannot create duplicate managed channels in the same bot process.
    async with _CHANNEL_CREATION_LOCK:
        # Reuse an existing managed channel if one already exists.
        for channel in guild.text_channels:
            if channel.name.lower() == name:
                return web.json_response({
                    "id": str(channel.id),
                    "name": channel.name,
                    "created": False,
                })

        try:
            channel = await guild.create_text_channel(
                name,
                reason="Raxor Dashboard: automatic channel setup on Save Changes",
            )
        except discord.Forbidden:
            return web.json_response(
                {"detail": "Raxor lacks permission to create channels in this server."},
                status=403,
            )
        except discord.HTTPException as exc:
            return web.json_response(
                {"detail": f"Discord rejected channel creation: {exc}"},
                status=502,
            )
    token = secrets.token_urlsafe(32)
    async with _ROLLBACK_TOKENS_LOCK:
        _prune_expired_rollback_tokens()
        _ROLLBACK_TOKENS[token] = (guild_id, channel.id, "channel", time.monotonic() + _ROLLBACK_TOKEN_TTL_SECONDS)
    return web.json_response({
        "id": str(channel.id),
        "name": channel.name,
        "created": True,
        "rollback_token": token,
    })

async def ensure_role(request: web.Request) -> web.Response:
    unauthorized = _require_auth(request)
    if unauthorized:
        return unauthorized
    if await _rate_limited(request):
        return web.json_response({"detail": "Too many requests."}, status=429, headers={"Retry-After": "10"})
    try:
        guild_id = int(request.match_info["guild_id"])
    except ValueError:
        return web.json_response({"detail": "Invalid guild id."}, status=400)
    guild = _get_guild(request, guild_id)
    if guild is None:
        return web.json_response({"detail": "Bot is not in this guild."}, status=404)
    try:
        payload = await request.json()
    except Exception:
        return web.json_response({"detail": "Invalid JSON body."}, status=400)
    name = str(payload.get("name", "")).strip()
    allowed_names = {"Verified", "weekly-top-messages", "weekly-top-voice"}
    is_level_role = bool(re.fullmatch(r"Level [1-9][0-9]{0,3}", name))
    if name not in allowed_names and not is_level_role:
        return web.json_response({"detail": "Unsupported managed role."}, status=400)
    async with _ROLE_CREATION_LOCK:
        existing = discord.utils.find(lambda r: r.name.lower() == name.lower(), guild.roles)
        me = guild.me
        if existing:
            if existing.managed:
                return web.json_response({"detail": "The existing role is managed by Discord and cannot be assigned by Raxor."}, status=409)
            if me and existing >= me.top_role:
                return web.json_response({"detail": "The existing role is at or above Raxor's highest role. Move it below Raxor or choose another role."}, status=409)
            return web.json_response({"id": str(existing.id), "name": existing.name, "created": False})
        try:
            role = await guild.create_role(name=name, reason="Raxor Dashboard: automatic role setup on Save Changes")
            if me and role >= me.top_role:
                # Discord normally creates it below the bot, but keep an explicit
                # safety check in case role ordering changes unexpectedly.
                await role.delete(reason="Raxor Dashboard: role hierarchy safety rollback")
                return web.json_response({"detail": "The new role cannot be managed by Raxor because of role hierarchy."}, status=409)
        except discord.Forbidden:
            return web.json_response({"detail": "Raxor lacks permission to create roles in this server."}, status=403)
        except discord.HTTPException as exc:
            return web.json_response({"detail": f"Discord rejected role creation: {exc}"}, status=502)
    token = secrets.token_urlsafe(32)
    async with _ROLLBACK_TOKENS_LOCK:
        _prune_expired_rollback_tokens()
        _ROLLBACK_TOKENS[token] = (guild_id, role.id, "role", time.monotonic() + _ROLLBACK_TOKEN_TTL_SECONDS)
    return web.json_response({"id": str(role.id), "name": role.name, "created": True, "rollback_token": token})


async def _rollback_token_matches(request: web.Request, guild_id: int, resource_id: int, kind: str) -> bool:
    """Validate a token for a resource created by this bot process."""
    token = request.headers.get("X-Rollback-Token", "")
    if not token:
        return False
    async with _ROLLBACK_TOKENS_LOCK:
        entry = _ROLLBACK_TOKENS.get(token)
        if entry is None:
            return False
        entry_guild_id, entry_resource_id, entry_kind, expires_at = entry
        if expires_at <= time.monotonic():
            del _ROLLBACK_TOKENS[token]
            return False
        return (entry_guild_id, entry_resource_id, entry_kind) == (guild_id, resource_id, kind)


async def _consume_rollback_token(request: web.Request) -> None:
    token = request.headers.get("X-Rollback-Token", "")
    async with _ROLLBACK_TOKENS_LOCK:
        _ROLLBACK_TOKENS.pop(token, None)


async def delete_channel(request: web.Request) -> web.Response:
    """Rollback a channel only when this bot process created it during this Save."""
    unauthorized = _require_auth(request)
    if unauthorized:
        return unauthorized
    if await _rate_limited(request):
        return web.json_response({"detail": "Too many requests."}, status=429, headers={"Retry-After": "10"})
    try:
        guild_id = int(request.match_info["guild_id"])
        payload = await request.json()
        channel_id = int(payload.get("channel_id"))
    except Exception:
        return web.json_response({"detail": "Valid guild and channel ids are required."}, status=400)
    if not await _rollback_token_matches(request, guild_id, channel_id, "channel"):
        return web.json_response({"detail": "Invalid or expired rollback token."}, status=403)
    guild = _get_guild(request, guild_id)
    channel = guild.get_channel(channel_id) if guild else None
    if guild is None or channel is None:
        return web.json_response({"detail": "Channel not found."}, status=404)
    try:
        await channel.delete(reason="Raxor Dashboard: rollback failed Save")
    except discord.Forbidden:
        return web.json_response({"detail": "Raxor cannot delete the rollback channel."}, status=403)
    except discord.HTTPException as exc:
        return web.json_response({"detail": f"Discord rejected rollback: {exc}"}, status=502)
    await _consume_rollback_token(request)
    return web.json_response({"deleted": True})


async def delete_role(request: web.Request) -> web.Response:
    """Rollback a role only when this bot process created it during this Save."""
    unauthorized = _require_auth(request)
    if unauthorized:
        return unauthorized
    if await _rate_limited(request):
        return web.json_response({"detail": "Too many requests."}, status=429, headers={"Retry-After": "10"})
    try:
        guild_id = int(request.match_info["guild_id"])
        payload = await request.json()
        role_id = int(payload.get("role_id"))
    except Exception:
        return web.json_response({"detail": "Valid guild and role ids are required."}, status=400)
    if not await _rollback_token_matches(request, guild_id, role_id, "role"):
        return web.json_response({"detail": "Invalid or expired rollback token."}, status=403)
    guild = _get_guild(request, guild_id)
    role = guild.get_role(role_id) if guild else None
    if guild is None or role is None:
        return web.json_response({"detail": "Role not found."}, status=404)
    try:
        await role.delete(reason="Raxor Dashboard: rollback failed Save")
    except discord.Forbidden:
        return web.json_response({"detail": "Raxor cannot delete the rollback role."}, status=403)
    except discord.HTTPException as exc:
        return web.json_response({"detail": f"Discord rejected rollback: {exc}"}, status=502)
    await _consume_rollback_token(request)
    return web.json_response({"deleted": True})


async def configure_verification(request: web.Request) -> web.Response:
    unauthorized = _require_auth(request)
    if unauthorized:
        return unauthorized
    if await _rate_limited(request):
        return web.json_response({"detail": "Too many requests."}, status=429, headers={"Retry-After": "10"})
    try:
        guild_id = int(request.match_info["guild_id"])
    except ValueError:
        return web.json_response({"detail": "Invalid guild id."}, status=400)
    guild = _get_guild(request, guild_id)
    if guild is None:
        return web.json_response({"detail": "Bot is not in this guild."}, status=404)
    try:
        payload = await request.json()
        channel_id = int(payload.get("channel_id"))
        role_id = int(payload.get("role_id"))
    except Exception:
        return web.json_response({"detail": "Valid channel_id and role_id are required."}, status=400)
    channel = guild.get_channel(channel_id)
    role = guild.get_role(role_id)
    if not isinstance(channel, discord.TextChannel) or role is None:
        return web.json_response({"detail": "Verification channel or role was not found."}, status=404)
    me = guild.me
    if role.managed:
        return web.json_response({"detail": "The verification role is managed by Discord and cannot be assigned."}, status=409)
    if me and role >= me.top_role:
        return web.json_response({"detail": "The verification role is at or above Raxor's highest role. Move it below Raxor."}, status=409)
    try:
        await channel.set_permissions(guild.default_role, view_channel=True, send_messages=False, read_message_history=True, reason="Raxor verification setup")
        await channel.set_permissions(role, view_channel=True, send_messages=False, read_message_history=True, reason="Raxor verification setup")
        if me:
            await channel.set_permissions(me, view_channel=True, send_messages=True, read_message_history=True, reason="Raxor verification setup")
        embed = discord.Embed(title="Server Verification", description="Click the button below to verify and unlock the server.", color=discord.Color.blurple())
        view = VerificationView()
        bot_user = request.app["bot"].user
        async for message in channel.history(limit=25):
            if bot_user and message.author.id == bot_user.id and message.components:
                await message.edit(embed=embed, view=view)
                return web.json_response({"ok": True, "message_id": str(message.id)})
        message = await channel.send(embed=embed, view=view)
        return web.json_response({"ok": True, "message_id": str(message.id)})
    except discord.Forbidden:
        return web.json_response({"detail": "Raxor lacks required channel/role permissions."}, status=403)
    except discord.HTTPException as exc:
        return web.json_response({"detail": f"Discord rejected verification setup: {exc}"}, status=502)


class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.success, custom_id="raxor:verify")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used inside a server.", ephemeral=True)
            return
        pool = getattr(interaction.client, "db_pool", None)
        role_id = None
        if pool is not None:
            row = await pool.fetchrow("SELECT verification_role_id FROM guilds WHERE guild_id = $1 AND verification_enabled = TRUE", guild.id)
            role_id = row["verification_role_id"] if row else None
        role = guild.get_role(role_id) if role_id else None
        if role is None:
            await interaction.response.send_message("Verification is not configured right now.", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.response.send_message("You are already verified.", ephemeral=True)
            return
        if guild.me and role >= guild.me.top_role:
            await interaction.response.send_message("I cannot assign the verification role because it is above my highest role.", ephemeral=True)
            return
        try:
            await interaction.user.add_roles(role, reason="Raxor verification")
            await interaction.response.send_message("You are verified! Welcome to the server.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to assign the verification role.", ephemeral=True)
        except discord.HTTPException:
            await interaction.response.send_message("Discord rejected the verification request. Please try again.", ephemeral=True)
