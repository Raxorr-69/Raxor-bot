import asyncio

import discord
from discord.ext import commands

from datetime import datetime, timezone, date, timedelta

from bot.client import bot

from database.repositories import (
    get_guild,
    create_guild,
    add_spam_warning,
    is_whitelisted,
    get_channel_rules,
    get_afk_user,
    remove_afk,
    get_leaderboard_reward_role,
    get_daily_message_stats,
    get_daily_voice_stats,
    get_message_recovery_state,
    set_message_recovery_state,
    list_pending_recovery_requests,
    delete_recovery_request,
)

from services.statistics import (
    record_message,
)


from services.voice_tracking import (
    ensure_voice_user,
    get_user_voice_session,
    remove_user_voice_session,
    save_user_voice_time,
    save_voice_channel_time,
    start_user_voice_session,
    start_voice_channel_session,
    get_voice_channel_session,
    remove_voice_channel_session,
    update_user_deafen_status,
)

from services.spam_detection import (
    get_spam_action,
    handle_spam_action,
    is_emoji_spam,
    is_message_spam,
    clear_user_spam_history,
)

from services.leveling import (
    award_message_xp,
    get_level_up_data,
)

from services.link_protection import (
    contains_link,
    contains_discord_invite,
    get_link_action,
)

from services.channel_rules import (
    violates_image_only,
    violates_clips_only,
)

from services.invite_tracking import (
    cache_guild_invites,
    clear_guild_invites,
    track_member_invite,
)

from utils.embeds import (
    error_embed,
    normal_embed,
    warning_embed,
)


# =========================
# Helper Functions
# =========================


def _render_event_text(template: str, member: discord.Member, *, level: int | None = None) -> str:
    """Render safe dashboard placeholders for welcome/leave/level-up text."""
    values = {
        "user": member.mention,
        "username": member.name,
        "displayname": member.display_name,
        "server": member.guild.name,
        "member_count": str(member.guild.member_count or len(member.guild.members)),
        "user_id": str(member.id),
        "user_avatar": member.display_avatar.url,
        "level": str(level) if level is not None else "",
    }
    text = str(template or "")
    for key, value in values.items():
        text = text.replace("{" + key + "}", value)
    return text[:4096]


def _apply_optional_gif(embed: discord.Embed, gif_url: str | None) -> None:
    """Attach a dashboard-provided image/GIF URL without changing embed styling."""
    if not gif_url:
        return
    url = str(gif_url).strip()
    if url.startswith(("https://", "http://")):
        embed.set_image(url=url[:1000])


def get_human_members(channel):
    """Return non-bot members currently in a voice channel."""

    return [
        member
        for member in channel.members
        if not member.bot
    ]


def channel_has_humans(channel):
    """Check whether a voice channel has at least one human."""

    return len(get_human_members(channel)) > 0


def channel_has_one_human(channel):
    """Check whether exactly one human is in a voice channel."""

    return len(get_human_members(channel)) == 1


# =========================
# Weekly Leaderboard Rewards
# =========================


_weekly_reward_task = None
_message_recovery_task = None


def get_previous_week_bounds():
    """Return the previous Monday and current Monday."""

    current_date = date.today()

    current_monday = (
        current_date - timedelta(days=current_date.weekday())
    )

    previous_monday = current_monday - timedelta(days=7)

    return previous_monday, current_monday


async def recalculate_weekly_leaderboard_rewards():
    """Update weekly Top 3 reward roles for every connected server."""

    pool = getattr(bot, "db_pool", None)

    if pool is None:
        return

    week_start, week_end = get_previous_week_bounds()

    for guild in bot.guilds:
        try:
            message_role_id = await get_leaderboard_reward_role(
                pool,
                guild.id,
                "messages",
            )

            voice_role_id = await get_leaderboard_reward_role(
                pool,
                guild.id,
                "voice",
            )

            reward_roles = {}

            if message_role_id is not None:
                role = guild.get_role(message_role_id)
                if role is not None:
                    reward_roles.setdefault(role.id, set())

            if voice_role_id is not None:
                role = guild.get_role(voice_role_id)
                if role is not None:
                    reward_roles.setdefault(role.id, set())

            if not reward_roles:
                continue

            # Find Top 3 message members.
            if message_role_id is not None:
                message_role = guild.get_role(message_role_id)

                if message_role is not None:
                    message_stats = await get_daily_message_stats(
                        pool,
                        guild.id,
                        week_start,
                        week_end,
                    )

                    for row in message_stats[:3]:
                        member = guild.get_member(row["user_id"])
                        if member is not None and not member.bot:
                            reward_roles[message_role.id].add(member.id)

            # Find Top 3 voice members.
            if voice_role_id is not None:
                voice_role = guild.get_role(voice_role_id)

                if voice_role is not None:
                    voice_stats = await get_daily_voice_stats(
                        pool,
                        guild.id,
                        week_start,
                        week_end,
                    )

                    for row in voice_stats[:3]:
                        member = guild.get_member(row["user_id"])
                        if member is not None and not member.bot:
                            reward_roles[voice_role.id].add(member.id)

            # Add the role to current Top 3 and remove it from everyone else.
            # If both leaderboards use the same role, the desired members are
            # combined so one leaderboard does not accidentally remove the role
            # awarded by the other.
            for role_id, desired_member_ids in reward_roles.items():
                role = guild.get_role(role_id)

                if role is None:
                    continue

                for member in list(role.members):
                    if member.id not in desired_member_ids:
                        try:
                            await member.remove_roles(
                                role,
                                reason="Weekly leaderboard reward update",
                            )
                        except discord.Forbidden:
                            continue
                        except discord.HTTPException:
                            continue

                for member_id in desired_member_ids:
                    member = guild.get_member(member_id)

                    if member is None:
                        continue

                    if role in member.roles:
                        continue

                    if role >= guild.me.top_role:
                        continue

                    try:
                        await member.add_roles(
                            role,
                            reason="Weekly leaderboard reward update",
                        )
                    except discord.Forbidden:
                        continue
                    except discord.HTTPException:
                        continue

        except (discord.Forbidden, discord.HTTPException):
            continue


async def weekly_leaderboard_reward_loop():
    """Recalculate weekly leaderboard rewards every Monday."""

    while True:
        try:
            await recalculate_weekly_leaderboard_rewards()
        except Exception as exc:
            print(
                "Weekly leaderboard reward update failed: "
                f"{exc}"
            )

        current_date = date.today()
        days_until_monday = (7 - current_date.weekday()) % 7

        if days_until_monday == 0:
            days_until_monday = 7

        next_monday = current_date + timedelta(
            days=days_until_monday
        )

        next_run = datetime.combine(
            next_monday,
            datetime.min.time(),
            tzinfo=timezone.utc,
        ) + timedelta(minutes=5)

        sleep_seconds = max(
            (next_run - datetime.now(timezone.utc)).total_seconds(),
            60,
        )

        await asyncio.sleep(sleep_seconds)


# =========================
# Message Recovery
# =========================


async def recover_channel_message_statistics(guild, channel) -> int:
    """Recover missed message statistics for a single channel. Shared by
    the automatic post-reconnect sweep below and by
    recovery_request_poll_loop's on-demand rescans, so both paths use
    identical scan logic. Returns the number of messages recovered.

    Raises discord.Forbidden/discord.HTTPException on Discord API
    failures — callers decide how to log/handle those, since the two
    call sites want different bookkeeping (a guild-wide sweep continues
    to the next channel either way; an on-demand request should not be
    silently dropped without at least logging why).
    """

    pool = getattr(bot, "db_pool", None)
    if pool is None:
        return 0

    permissions = channel.permissions_for(guild.me)
    if not permissions.view_channel or not permissions.read_message_history:
        return 0

    checkpoint = await get_message_recovery_state(pool, guild.id, channel.id)

    # First run: establish a safe baseline without counting old history.
    if checkpoint is None:
        await set_message_recovery_state(
            pool, guild.id, channel.id, datetime.now(timezone.utc)
        )
        return 0

    recovered_count = 0
    scan_until = datetime.now(timezone.utc)

    async for message in channel.history(
        after=checkpoint,
        before=scan_until,
        oldest_first=True,
        limit=None,
    ):
        if message.author.bot:
            continue

        message_created_at = message.created_at

        recorded = await record_message(
            pool,
            message.author.id,
            guild.id,
            channel.id,
            message_created_at.date(),
            message.id,
            message_created_at,
        )

        if recorded:
            recovered_count += 1

    # Advance only after the complete scan succeeds.
    await set_message_recovery_state(pool, guild.id, channel.id, scan_until)

    return recovered_count


async def recover_guild_message_statistics(guild):
    """Recover message statistics missed while the bot was offline."""

    for channel in guild.text_channels:
        try:
            recovered_count = await recover_channel_message_statistics(guild, channel)

            if recovered_count:
                print(
                    f"Recovered {recovered_count} message(s) "
                    f"in #{channel.name} ({guild.name})."
                )

        except discord.Forbidden:
            # Keep the old checkpoint so the history can be recovered later.
            continue
        except discord.HTTPException as exc:
            print(
                f"Message recovery failed for #{channel.name} "
                f"({guild.name}): {exc}"
            )
        except Exception as exc:
            print(
                f"Unexpected message recovery error for #{channel.name} "
                f"({guild.name}): {exc}"
            )


async def recover_message_statistics():
    """Recover message statistics for every connected guild."""

    pool = getattr(bot, "db_pool", None)
    if pool is None:
        return

    for guild in bot.guilds:
        try:
            await recover_guild_message_statistics(guild)
        except Exception as exc:
            print(f"Message recovery failed for guild {guild.name}: {exc}")


async def message_recovery_loop():
    """Run message recovery once after the bot becomes ready."""

    await recover_message_statistics()


_recovery_request_poll_task = None


async def recovery_request_poll_loop():
    """Poll for on-demand rescan requests queued by the dashboard's
    Recovery page (see database/repositories.py's recovery_requests
    functions) and act on them.

    Runs forever at a fixed interval rather than being woken up by
    anything, since the dashboard and bot are separate processes with
    no direct connection between them — the shared database row is the
    only signal. 20 seconds keeps a manual "Rescan" click feeling
    responsive without hammering the DB or Discord's history API.
    """

    await bot.wait_until_ready()

    pool = getattr(bot, "db_pool", None)
    if pool is None:
        return

    while not bot.is_closed():
        try:
            requests = await list_pending_recovery_requests(pool)

            for request in requests:
                guild = bot.get_guild(request["guild_id"])
                channel = guild.get_channel(request["channel_id"]) if guild else None

                if guild is None or channel is None:
                    # Bot isn't in the guild (anymore) or the channel was
                    # deleted — nothing to scan, drop the stale request.
                    await delete_recovery_request(pool, request["guild_id"], request["channel_id"])
                    continue

                try:
                    recovered_count = await recover_channel_message_statistics(guild, channel)
                    print(
                        f"On-demand rescan recovered {recovered_count} message(s) "
                        f"in #{channel.name} ({guild.name})."
                    )
                except (discord.Forbidden, discord.HTTPException) as exc:
                    print(
                        f"On-demand rescan failed for #{channel.name} "
                        f"({guild.name}): {exc}"
                    )
                finally:
                    # Always clear the request once attempted, successful
                    # or not — a permanently-failing request (e.g. missing
                    # permissions) would otherwise retry forever every
                    # poll interval.
                    await delete_recovery_request(pool, request["guild_id"], request["channel_id"])

        except Exception as exc:
            print(f"Recovery request poll failed: {exc}")

        await asyncio.sleep(20)


# =========================
# Runtime Recovery Helpers
# =========================


async def initialize_voice_sessions():
    """Rebuild in-memory voice sessions after startup/reconnect.

    Discord does not replay every historical voice event after a reconnect,
    so active members are seeded from the current cache. Tracking starts at
    recovery time; no unverified offline duration is invented.
    """

    pool = getattr(bot, "db_pool", None)
    if pool is None:
        return

    for guild in bot.guilds:
        try:
            settings = await get_guild(pool, guild.id)
            if settings is None:
                await create_guild(pool, guild.id)
                settings = await get_guild(pool, guild.id)
            if settings is None or not settings["voice_tracking_enabled"]:
                continue

            for channel in guild.voice_channels:
                humans = get_human_members(channel)
                if not humans:
                    continue

                if get_voice_channel_session(guild.id, channel.id) is None:
                    start_voice_channel_session(guild.id, channel.id)

                for member in humans:
                    if get_user_voice_session(guild.id, member.id) is None:
                        await ensure_voice_user(pool, guild.id, member.id)
                        start_user_voice_session(
                            guild.id,
                            member.id,
                            channel.id,
                            (member.voice.self_deaf or member.voice.deaf) if member.voice else False,
                        )
        except (discord.Forbidden, discord.HTTPException) as exc:
            print(f"Voice session recovery failed for {guild.name}: {exc}")
        except Exception as exc:
            print(f"Unexpected voice recovery error for {guild.name}: {exc}")


# =========================
# Bot Ready Event
# =========================


@bot.event
async def on_ready():
    """Runs when the bot successfully connects to Discord."""

    print(f"Logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print("Bot is ready!")

    global _weekly_reward_task
    global _message_recovery_task
    global _recovery_request_poll_task

    if _weekly_reward_task is None or _weekly_reward_task.done():
        _weekly_reward_task = asyncio.create_task(
            weekly_leaderboard_reward_loop()
        )

    if _message_recovery_task is None or _message_recovery_task.done():
        _message_recovery_task = asyncio.create_task(
            message_recovery_loop()
        )

    if _recovery_request_poll_task is None or _recovery_request_poll_task.done():
        _recovery_request_poll_task = asyncio.create_task(
            recovery_request_poll_loop()
        )

    # Cache invite uses for every server so joins can be
    # matched to the invite that was used. A single guild
    # without invite permissions must not prevent the bot
    # from finishing its ready event for other guilds.
    for guild in bot.guilds:
        try:
            # A guild record is guaranteed before any message/voice event
            # depends on configuration. ON CONFLICT keeps this idempotent.
            await create_guild(bot.db_pool, guild.id)
            await cache_guild_invites(guild)
        except discord.Forbidden:
            continue
        except discord.HTTPException as exc:
            print(
                f"Invite cache failed for {guild.name}: {exc}"
            )

    # Rebuild active voice sessions after reconnect/startup.
    await initialize_voice_sessions()


# =========================
# Command Error Handling
# =========================


@bot.event
async def on_command_error(
    ctx: commands.Context,
    error: commands.CommandError,
):
    """Handle errors raised while processing prefix commands."""

    # Unknown command — ignore silently.
    if isinstance(error, commands.CommandNotFound):
        return

    # Command was run outside of a server.
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send(
            embed=error_embed(
                title="Server Only",
                description="This command can only be used inside a server.",
            )
        )
        return

    # Permission checks (admin_only / developer_only / server_owner_only).
    if isinstance(error, commands.CheckFailure):
        await ctx.send(
            embed=error_embed(
                title="Permission Denied",
                description=(
                    "You don't have permission to use this command."
                ),
            )
        )
        return

    # A required argument was not provided.
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            embed=error_embed(
                title="Missing Argument",
                description=(
                    f"Missing required argument: `{error.param.name}`.\n\n"
                    f"Usage: `{ctx.prefix}{ctx.command.qualified_name} "
                    f"{ctx.command.signature}`"
                ),
            )
        )
        return

    # Any other bad input (invalid member/role/channel, bad union, etc.).
    if isinstance(error, commands.UserInputError):
        await ctx.send(
            embed=error_embed(
                title="Invalid Argument",
                description=(
                    "One or more arguments were invalid.\n\n"
                    f"Usage: `{ctx.prefix}{ctx.command.qualified_name} "
                    f"{ctx.command.signature}`"
                ),
            )
        )
        return

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            embed=error_embed(
                title="Cooldown",
                description=(
                    "This command is on cooldown. Try again in "
                    f"{error.retry_after:.1f} seconds."
                ),
            )
        )
        return

    # Unexpected error — log it and let the user know without crashing.
    print(f"Unhandled error in command '{ctx.command}': {error!r}")

    await ctx.send(
        embed=error_embed(
            title="Error",
            description="Something went wrong while running that command.",
        )
    )


# =========================
# Voice State Update
# =========================


@bot.event
async def on_voice_state_update(
    member,
    before,
    after,
):
    """Handle voice channel and deafen state changes."""

    # Ignore bots
    if member.bot:
        return

    # Ignore DMs
    if member.guild is None:
        return

    # Make sure database pool exists
    pool = getattr(
        bot,
        "db_pool",
        None,
    )

    if pool is None:
        print(
            "Voice tracking skipped: "
            "database pool is not available."
        )
        return

    guild_id = member.guild.id
    user_id = member.id

    now = datetime.now(timezone.utc)

    # =========================
    # Guild Voice Tracking Check
    # =========================

    guild_settings = await get_guild(
        pool,
        guild_id,
    )

    if guild_settings is None:
        await create_guild(pool, guild_id)
        guild_settings = await get_guild(pool, guild_id)

    if guild_settings is None:
        return

    if not guild_settings[
        "voice_tracking_enabled"
    ]:
        return

    # =========================
    # Deafen State
    # =========================

    deafened_before = (
        before.self_deaf
        or before.deaf
    )

    deafened_after = (
        after.self_deaf
        or after.deaf
    )

    # =========================
    # Voice Channel Join
    # =========================

    if (
        before.channel is None
        and after.channel is not None
    ):

        channel_id = after.channel.id

        # Make sure user exists
        await ensure_voice_user(
            pool,
            guild_id,
            user_id,
        )

        # Start user's individual session
        start_user_voice_session(
            guild_id,
            user_id,
            channel_id,
            deafened_after,
        )

        # If this is the first human
        # in the channel, start channel timer
        if channel_has_one_human(
            after.channel
        ):

            start_voice_channel_session(
                guild_id,
                channel_id,
            )

        return

    # =========================
    # Voice Channel Leave
    # =========================

    if (
        before.channel is not None
        and after.channel is None
    ):

        session = get_user_voice_session(
            guild_id,
            user_id,
        )

        # Save user's non-deafened time
        if session is not None:

            counted_started_at = (
                session[
                    "counted_started_at"
                ]
            )

            if counted_started_at is not None:

                await save_user_voice_time(
                    pool,
                    guild_id,
                    user_id,
                    session["channel_id"],
                    counted_started_at,
                    now,
                )

            remove_user_voice_session(
                guild_id,
                user_id,
            )

        # If the channel is now empty
        # save its active duration
        if not channel_has_humans(
            before.channel
        ):

            channel_started_at = (
                get_voice_channel_session(
                    guild_id,
                    before.channel.id,
                )
            )

            if channel_started_at is not None:

                await save_voice_channel_time(
                    pool,
                    guild_id,
                    before.channel.id,
                    channel_started_at,
                    now,
                )

                remove_voice_channel_session(
                    guild_id,
                    before.channel.id,
                )

        return

    # =========================
    # Voice Channel Change
    # =========================

    if (
        before.channel is not None
        and after.channel is not None
        and before.channel.id != after.channel.id
    ):

        session = get_user_voice_session(
            guild_id,
            user_id,
        )

        # =========================
        # Save Old User Session
        # =========================

        if session is not None:

            counted_started_at = (
                session[
                    "counted_started_at"
                ]
            )

            if counted_started_at is not None:

                await save_user_voice_time(
                    pool,
                    guild_id,
                    user_id,
                    session["channel_id"],
                    counted_started_at,
                    now,
                )

            remove_user_voice_session(
                guild_id,
                user_id,
            )

        # =========================
        # Close Old Channel
        # =========================

        if not channel_has_humans(
            before.channel
        ):

            channel_started_at = (
                get_voice_channel_session(
                    guild_id,
                    before.channel.id,
                )
            )

            if channel_started_at is not None:

                await save_voice_channel_time(
                    pool,
                    guild_id,
                    before.channel.id,
                    channel_started_at,
                    now,
                )

                remove_voice_channel_session(
                    guild_id,
                    before.channel.id,
                )

        # =========================
        # Start New User Session
        # =========================

        await ensure_voice_user(
            pool,
            guild_id,
            user_id,
        )

        start_user_voice_session(
            guild_id,
            user_id,
            after.channel.id,
            deafened_after,
        )

        # =========================
        # Start New Channel
        # =========================

        if channel_has_one_human(
            after.channel
        ):

            start_voice_channel_session(
                guild_id,
                after.channel.id,
            )

        return

    # =========================
    # Deafen / Undeafen
    # =========================

    if deafened_before != deafened_after:

        session = get_user_voice_session(
            guild_id,
            user_id,
        )

        if session is None:
            return

        # =========================
        # Became Deafened
        # =========================

        if deafened_after:

            counted_started_at = (
                session[
                    "counted_started_at"
                ]
            )

            if counted_started_at is not None:

                await save_user_voice_time(
                    pool,
                    guild_id,
                    user_id,
                    session["channel_id"],
                    counted_started_at,
                    now,
                )

            update_user_deafen_status(
                guild_id,
                user_id,
                True,
            )

        # =========================
        # Became Undeafened
        # =========================

        else:

            update_user_deafen_status(
                guild_id,
                user_id,
                False,
            )




# =========================
# Message Event
# =========================


@bot.event
async def on_message(message):
    """Handle incoming messages, statistics, XP, and level-ups."""

    # =========================
    # Ignore Bots
    # =========================

    if message.author.bot:
        return

    # =========================
    # Ignore DMs
    # =========================

    if message.guild is None:
        return

    # =========================
    # Get Database Pool
    # =========================

    pool = getattr(
        bot,
        "db_pool",
        None,
    )

    if pool is None:
        print(
            "Message tracking skipped: "
            "database pool is not available."
        )
        return

    # =========================
    # Get Guild Settings
    # =========================

    guild_settings = await get_guild(
        pool,
        message.guild.id,
    )

    if guild_settings is None:
        await create_guild(pool, message.guild.id)
        guild_settings = await get_guild(pool, message.guild.id)

    if guild_settings is None:
        return


    # AFK Handling

    # Remove AFK when the user sends a message.
    afk_user = await get_afk_user(
        pool,
        message.guild.id,
        message.author.id,
    )

    if afk_user is not None:
        await remove_afk(
            pool,
            message.guild.id,
            message.author.id,
        )

        embed = normal_embed(
            title="Welcome Back!",
            description=(
                f"{message.author.mention}, your AFK status has been removed."
            ),
        )

        await message.channel.send(embed=embed)

    # Notify when an AFK user is mentioned.
    #
    # Capped and batched into a single message: a message can mention
    # up to 100 users, so looping unbounded and sending one embed per
    # mentioned AFK user let anyone spam the channel (and the bot's
    # rate limit) with a single crafted message.
    MAX_AFK_MENTIONS_CHECKED = 5

    afk_notices = []

    for mentioned_user in message.mentions[:MAX_AFK_MENTIONS_CHECKED]:
        if mentioned_user.bot:
            continue

        afk_data = await get_afk_user(
            pool,
            message.guild.id,
            mentioned_user.id,
        )

        if afk_data is None:
            continue

        reason = afk_data["reason"] or "AFK"

        afk_notices.append(
            f"**{mentioned_user.display_name}** — {reason}"
        )

    if afk_notices:
        embed = normal_embed(
            title="AFK",
            description="\n".join(afk_notices),
        )

        await message.channel.send(embed=embed)


    # =========================
    # Channel Restrictions
    # =========================

    channel_rules = await get_channel_rules(
        pool,
        message.guild.id,
        message.channel.id,
    )

    if channel_rules is not None:

        # =========================
        # Image-Only Channel
        # =========================

        if channel_rules["image_only"]:

            whitelisted = await is_whitelisted(
                pool,
                message.guild.id,
                message.author.id,
                "image_only",
            )

            if not whitelisted:
                for role in message.author.roles:
                    if await is_whitelisted(
                        pool,
                        message.guild.id,
                        role.id,
                        "image_only",
                    ):
                        whitelisted = True
                        break

            if (
                not whitelisted
                and violates_image_only(message)
            ):
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass

                try:
                    await message.channel.send(
                        embed=warning_embed(
                            "Channel Restriction",
                            (
                                f"{message.author.mention}, this channel "
                                "only allows images.\n\n"
                                "Your message was removed."
                            ),
                        ),
                        delete_after=5,
                    )
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass

                return

        # =========================
        # Clips-Only Channel
        # =========================

        if channel_rules["clips_only"]:

            whitelisted = await is_whitelisted(
                pool,
                message.guild.id,
                message.author.id,
                "clips_only",
            )

            if not whitelisted:
                for role in message.author.roles:
                    if await is_whitelisted(
                        pool,
                        message.guild.id,
                        role.id,
                        "clips_only",
                    ):
                        whitelisted = True
                        break

            if (
                not whitelisted
                and violates_clips_only(message)
            ):
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass

                try:
                    await message.channel.send(
                        embed=warning_embed(
                            "Channel Restriction",
                            (
                                f"{message.author.mention}, this channel "
                                "only allows clips.\n\n"
                                "Your message was removed."
                            ),
                        ),
                        delete_after=5,
                    )
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass

                return



    # =========================
    # Link Protection
    # =========================

    if guild_settings["link_protection_enabled"]:
        has_link = contains_link(message.content)
        has_invite = contains_discord_invite(message.content)

        if has_link or has_invite:
            action = get_link_action(
                guild_settings["link_action"]
            )

            if action == "warn":
                await add_spam_warning(
                    pool,
                    message.guild.id,
                    message.author.id,
                    "Link protection triggered",
                )

            elif action == "delete":
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass

                return

            elif action == "timeout":
                timeout_seconds = guild_settings[
                    "link_timeout_seconds"
                ]

                try:
                    await message.author.timeout(
                        discord.utils.utcnow()
                        + timedelta(seconds=timeout_seconds),
                        reason="Link protection triggered",
                    )
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass

                return



    # =========================
    # Message Spam Detection
    # =========================

    if guild_settings["spam_enabled"]:

        message_spam = is_message_spam(
            message.guild.id,
            message.author.id,
            guild_settings["spam_message_limit"],
            guild_settings["spam_message_window"],
        )

        if message_spam:

            action = get_spam_action(
                guild_settings["spam_action"]
            )

            result = await handle_spam_action(
                message,
                action,
                guild_settings["spam_timeout_seconds"],
            )

            if result == "warn":

                await add_spam_warning(
                    pool,
                    message.guild.id,
                    message.author.id,
                    "Message spam detected",
                )

            clear_user_spam_history(
                message.guild.id,
                message.author.id,
            )

            if result in {
                "delete",
                "timeout",
            }:
                return

    # =========================
    # Emoji Spam Detection
    # =========================

    if guild_settings["spam_enabled"]:

        emoji_spam = is_emoji_spam(
            message.content,
            guild_settings["emoji_spam_limit"],
        )

        if emoji_spam:

            action = get_spam_action(
                guild_settings["emoji_spam_action"]
            )

            result = await handle_spam_action(
                message,
                action,
                guild_settings[
                    "emoji_spam_timeout_seconds"
                ],
            )

            if result == "warn":

                await add_spam_warning(
                    pool,
                    message.guild.id,
                    message.author.id,
                    "Emoji spam detected",
                )

            clear_user_spam_history(
                message.guild.id,
                message.author.id,
            )

            if result in {
                "delete",
                "timeout",
            }:
                return

    # =========================
    # Record Message Statistics
    # =========================

    if guild_settings["message_tracking_enabled"]:
        await record_message(
            pool,
            message.author.id,
            message.guild.id,
            message.channel.id,
            message.created_at.date(),
            message.id,
            message.created_at,
        )

    # =========================
    # Award Message XP
    # =========================

    xp_result = await award_message_xp(
        pool,
        message.author.id,
        message.guild.id,
    )

    # =========================
    # Handle Level-Up
    # =========================

    if xp_result and xp_result["level_up"]:

        level_up_data = await get_level_up_data(
            pool,
            message.guild.id,
            xp_result["old_level"],
            xp_result["new_level"],
        )

        # =========================
        # Assign Reward Roles
        # =========================

        for reward in level_up_data["reward_roles"]:

            role = message.guild.get_role(
                reward["role_id"]
            )

            if role is None:
                continue

            # User already has the role
            if role in message.author.roles:
                continue

            # Bot cannot manage this role
            if role >= message.guild.me.top_role:
                continue

            try:

                await message.author.add_roles(
                    role,
                    reason="Level-up reward",
                )

            except discord.Forbidden:
                continue

            except discord.HTTPException:
                continue

        # =========================
        # Level-Up Announcement
        # =========================

        announcement = level_up_data[
            "announcement"
        ]

        if announcement["enabled"]:

            channel = None

            # Use configured level-up channel
            if announcement["channel_id"]:

                channel = message.guild.get_channel(
                    announcement["channel_id"]
                )

            # Fallback to current message channel
            if channel is None:
                channel = message.channel

            guild_config = await get_guild(pool, message.guild.id)
            level_message = (
                guild_config["level_up_message"]
                if guild_config and guild_config["level_up_message"]
                else "{user} reached **Level {level}**! 🎉"
            )
            level_gif = guild_config["level_up_gif_url"] if guild_config else None
            embed = normal_embed(
                title="Level Up!",
                description=_render_event_text(
                    level_message, message.author, level=xp_result["new_level"]
                ),
            )
            _apply_optional_gif(embed, level_gif)

            try:

                await channel.send(
                    embed=embed,
                )

            except discord.Forbidden:
                pass

            except discord.HTTPException:
                pass

    # =========================
    # Process Bot Commands
    # =========================

    await bot.process_commands(message)



# =========================
# Invite Tracking Events
# =========================


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Cache invite uses as soon as the bot joins a new server."""

    pool = getattr(bot, "db_pool", None)
    if pool is not None:
        try:
            await create_guild(pool, guild.id)
        except Exception as exc:
            print(f"Guild initialization failed for {guild.name}: {exc}")

    try:
        await cache_guild_invites(guild)
    except discord.Forbidden:
        print(f"Invite cache unavailable for {guild.name}: missing permissions.")
    except discord.HTTPException as exc:
        print(f"Invite cache failed for {guild.name}: {exc}")


@bot.event
async def on_guild_remove(guild: discord.Guild):
    """Drop cached invites for a server the bot has left."""

    clear_guild_invites(guild.id)


@bot.event
async def on_invite_create(invite: discord.Invite):
    """Keep the invite cache up to date when a new invite is made."""

    try:
        await cache_guild_invites(invite.guild)
    except discord.Forbidden:
        return
    except discord.HTTPException:
        return


@bot.event
async def on_invite_delete(invite: discord.Invite):
    """Keep the invite cache up to date when an invite is removed."""

    try:
        await cache_guild_invites(invite.guild)
    except discord.Forbidden:
        return
    except discord.HTTPException:
        return


@bot.event
async def on_member_join(member: discord.Member):
    """Track invites and optionally send the configured welcome embed."""
    if member.bot:
        return

    pool = getattr(bot, "db_pool", None)
    if pool is None:
        return

    try:
        await track_member_invite(pool, member)
    except (discord.Forbidden, discord.HTTPException) as exc:
        print(f"Invite tracking failed for {member} in {member.guild.name}: {exc}")

    try:
        guild_config = await get_guild(pool, member.guild.id)
        if not guild_config or not guild_config["welcome_enabled"]:
            return
        channel_id = guild_config["welcome_channel_id"]
        channel = member.guild.get_channel(channel_id) if channel_id else None
        if channel is None:
            return
        embed = normal_embed(
            title="Welcome!",
            description=_render_event_text(
                guild_config["welcome_message"], member
            ),
        )
        _apply_optional_gif(embed, guild_config["welcome_gif_url"])
        await channel.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException) as exc:
        print(f"Welcome message failed for {member} in {member.guild.name}: {exc}")


@bot.event
async def on_member_remove(member: discord.Member):
    """Send the configured leave embed when a human member leaves."""
    if member.bot:
        return
    pool = getattr(bot, "db_pool", None)
    if pool is None:
        return
    try:
        guild_config = await get_guild(pool, member.guild.id)
        if not guild_config or not guild_config["leave_enabled"]:
            return
        channel_id = guild_config["leave_channel_id"]
        channel = member.guild.get_channel(channel_id) if channel_id else None
        if channel is None:
            return
        embed = normal_embed(
            title="Goodbye!",
            description=_render_event_text(
                guild_config["leave_message"], member
            ),
        )
        _apply_optional_gif(embed, guild_config["leave_gif_url"])
        await channel.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException) as exc:
        print(f"Leave message failed for {member} in {member.guild.name}: {exc}")

# =========================
# Slash Command Error Handling
# =========================


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: discord.app_commands.AppCommandError,
):
    """Handle errors raised while processing slash commands."""

    if isinstance(error, discord.app_commands.CommandOnCooldown):
        embed = error_embed(
            "Cooldown",
            (
                "This command is on cooldown. Try again in "
                f"{error.retry_after:.1f} seconds."
            ),
        )
    elif isinstance(error, discord.app_commands.CheckFailure):
        embed = error_embed(
            "Permission Denied",
            "You don't have permission to use this command.",
        )
    else:
        print(f"Unhandled app command error: {error!r}")
        embed = error_embed(
            "Error",
            "Something went wrong while running that command.",
        )

    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)
