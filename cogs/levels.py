import discord
from discord.ext import commands
import aiosqlite
import asyncio
import time
import math
import os

DB_PATH = "death_bot.db"

def xp_for_level(level: int) -> int:
    """XP required to reach a given level."""
    return 5 * (level ** 2) + 50 * level + 100

def level_from_xp(xp: int) -> int:
    """Calculate level from total XP."""
    level = 0
    while xp >= xp_for_level(level):
        xp -= xp_for_level(level)
        level += 1
    return level

def xp_progress(total_xp: int):
    """Returns (current_level, xp_into_level, xp_needed_for_next)."""
    level = 0
    remaining = total_xp
    while remaining >= xp_for_level(level):
        remaining -= xp_for_level(level)
        level += 1
    return level, remaining, xp_for_level(level)


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldown = {}  # user_id -> last_xp_time (60s cooldown)
        self.vc_join_time = {}  # member_id:guild_id -> join timestamp
        if not hasattr(bot, 'level_channels'):
            bot.level_channels = {}  # guild_id -> channel_id
        if not hasattr(bot, 'level_roles'):
            bot.level_roles = {}  # guild_id -> { level: role_id }
        self.bot.loop.create_task(self.setup_db())

    async def setup_db(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS levels (
                    user_id     INTEGER,
                    guild_id    INTEGER,
                    xp          INTEGER DEFAULT 0,
                    messages    INTEGER DEFAULT 0,
                    vc_minutes  INTEGER DEFAULT 0,
                    last_seen   INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS message_log (
                    user_id     INTEGER,
                    guild_id    INTEGER,
                    timestamp   INTEGER
                )
            """)
            await db.commit()

    async def get_user(self, user_id: int, guild_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT xp, messages, vc_minutes FROM levels WHERE user_id=? AND guild_id=?",
                (user_id, guild_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"xp": row[0], "messages": row[1], "vc_minutes": row[2]}
                return {"xp": 0, "messages": 0, "vc_minutes": 0}

    async def add_xp(self, user_id: int, guild_id: int, amount: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO levels (user_id, guild_id, xp, messages, last_seen)
                VALUES (?, ?, ?, 1, ?)
                ON CONFLICT(user_id, guild_id) DO UPDATE SET
                    xp = xp + ?,
                    messages = messages + 1,
                    last_seen = ?
            """, (user_id, guild_id, amount, int(time.time()), amount, int(time.time())))
            await db.commit()

    async def add_vc_minutes(self, user_id: int, guild_id: int, minutes: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO levels (user_id, guild_id, vc_minutes)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, guild_id) DO UPDATE SET
                    vc_minutes = vc_minutes + ?
            """, (user_id, guild_id, minutes, minutes))
            await db.commit()

    async def log_message(self, user_id: int, guild_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO message_log (user_id, guild_id, timestamp) VALUES (?, ?, ?)",
                (user_id, guild_id, int(time.time()))
            )
            await db.commit()

    async def get_rank(self, user_id: int, guild_id: int) -> int:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM levels WHERE guild_id=? AND xp > (SELECT xp FROM levels WHERE user_id=? AND guild_id=?)",
                (guild_id, user_id, guild_id)
            ) as cursor:
                row = await cursor.fetchone()
                return (row[0] + 1) if row else 1

    async def get_leaderboard(self, guild_id: int, limit: int = 10):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT user_id, xp, messages, vc_minutes FROM levels WHERE guild_id=? ORDER BY xp DESC LIMIT ?",
                (guild_id, limit)
            ) as cursor:
                return await cursor.fetchall()

    async def get_monthly_messages(self, user_id: int, guild_id: int) -> int:
        thirty_days_ago = int(time.time()) - (30 * 24 * 60 * 60)
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM message_log WHERE user_id=? AND guild_id=? AND timestamp > ?",
                (user_id, guild_id, thirty_days_ago)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    # ─── Message XP listener ──────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        guild_id = message.guild.id
        now = time.time()

        # Log message for stats
        await self.log_message(user_id, guild_id)

        # XP cooldown — 1 minute between XP gains
        last = self.xp_cooldown.get(f"{user_id}:{guild_id}", 0)
        if now - last < 60:
            return
        self.xp_cooldown[f"{user_id}:{guild_id}"] = now

        # Get XP before
        data_before = await self.get_user(user_id, guild_id)
        level_before = level_from_xp(data_before["xp"])

        # Add 15-25 random XP
        import random
        xp_gained = random.randint(15, 25)
        await self.add_xp(user_id, guild_id, xp_gained)

        # Check level up
        data_after = await self.get_user(user_id, guild_id)
        level_after = level_from_xp(data_after["xp"])

        if level_after > level_before:
            await self.handle_level_up(message, level_after)

    async def handle_level_up(self, message: discord.Message, new_level: int):
        guild = message.guild
        member = message.author

        # Send level up message
        channel_id = self.bot.level_channels.get(guild.id)
        channel = guild.get_channel(channel_id) if channel_id else message.channel

        embed = discord.Embed(
            title="⬆️ Level Up!",
            description=f"🎉 {member.mention} reached **Level {new_level}**!",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

        # Give level role if set
        level_roles = self.bot.level_roles.get(guild.id, {})
        if new_level in level_roles:
            role = guild.get_role(level_roles[new_level])
            if role:
                try:
                    await member.add_roles(role, reason=f"Reached level {new_level}")
                except discord.Forbidden:
                    pass

    # ─── VC time tracking ─────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        key = f"{member.id}:{member.guild.id}"

        # Joined VC
        if before.channel is None and after.channel is not None:
            self.vc_join_time[key] = time.time()

        # Left VC
        elif before.channel is not None and after.channel is None:
            join_time = self.vc_join_time.pop(key, None)
            if join_time:
                minutes = int((time.time() - join_time) / 60)
                if minutes > 0:
                    await self.add_vc_minutes(member.id, member.guild.id, minutes)

    # ─── !rank ────────────────────────────────────────────────────────────────
    @commands.command(name="rank", usage="[@user]")
    async def rank(self, ctx, member: discord.Member = None):
        """Show your rank card with level, XP and stats."""
        member = member or ctx.author
        data = await self.get_user(member.id, ctx.guild.id)
        rank = await self.get_rank(member.id, ctx.guild.id)
        monthly = await self.get_monthly_messages(member.id, ctx.guild.id)

        level, xp_into, xp_needed = xp_progress(data["xp"])
        progress = int((xp_into / xp_needed) * 10) if xp_needed > 0 else 10
        bar = "█" * progress + "░" * (10 - progress)

        hours, mins = divmod(data["vc_minutes"], 60)

        embed = discord.Embed(
            color=member.color if member.color != discord.Color.default() else discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(name=f"{member.display_name}'s Rank", icon_url=member.display_avatar.url)
        embed.add_field(name="🏆 Rank",         value=f"#{rank}",                     inline=True)
        embed.add_field(name="⭐ Level",         value=str(level),                     inline=True)
        embed.add_field(name="✨ Total XP",      value=str(data["xp"]),                inline=True)
        embed.add_field(name="📊 XP Progress",   value=f"`[{bar}]` {xp_into}/{xp_needed}", inline=False)
        embed.add_field(name="💬 Total Messages", value=str(data["messages"]),          inline=True)
        embed.add_field(name="📅 Last 30 Days",  value=f"{monthly} messages",          inline=True)
        embed.add_field(name="🎙️ VC Time",       value=f"{hours}h {mins}m",            inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.reply(embed=embed)

    # ─── !leaderboard ─────────────────────────────────────────────────────────
    @commands.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard(self, ctx):
        """Show the top 10 most active members."""
        rows = await self.get_leaderboard(ctx.guild.id)
        if not rows:
            return await ctx.reply("❌ No data yet — start chatting to earn XP!")

        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for i, (user_id, xp, messages, vc_minutes) in enumerate(rows):
            member = ctx.guild.get_member(user_id)
            name = member.display_name if member else f"Unknown ({user_id})"
            level, _, _ = xp_progress(xp)
            prefix = medals[i] if i < 3 else f"**#{i+1}**"
            hours, mins = divmod(vc_minutes, 60)
            lines.append(f"{prefix} **{name}** — Level {level} • {xp} XP • {messages} msgs • {hours}h {mins}m VC")

        embed = discord.Embed(
            title=f"🏆 {ctx.guild.name} Leaderboard",
            description="\n".join(lines),
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text="Ranked by total XP")
        await ctx.reply(embed=embed)

    # ─── !stats ───────────────────────────────────────────────────────────────
    @commands.command(name="stats", usage="[@user]")
    async def stats(self, ctx, member: discord.Member = None):
        """Show detailed activity stats for a member."""
        member = member or ctx.author
        data = await self.get_user(member.id, ctx.guild.id)
        rank = await self.get_rank(member.id, ctx.guild.id)
        monthly = await self.get_monthly_messages(member.id, ctx.guild.id)
        level, xp_into, xp_needed = xp_progress(data["xp"])
        hours, mins = divmod(data["vc_minutes"], 60)

        # Weekly messages
        seven_days_ago = int(time.time()) - (7 * 24 * 60 * 60)
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM message_log WHERE user_id=? AND guild_id=? AND timestamp > ?",
                (member.id, ctx.guild.id, seven_days_ago)
            ) as cursor:
                row = await cursor.fetchone()
                weekly = row[0] if row else 0

        embed = discord.Embed(
            title=f"📊 Stats — {member.display_name}",
            color=member.color if member.color != discord.Color.default() else discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🏆 Server Rank",    value=f"#{rank}",          inline=True)
        embed.add_field(name="⭐ Level",           value=str(level),          inline=True)
        embed.add_field(name="✨ XP",              value=f"{xp_into}/{xp_needed} (total: {data['xp']})", inline=True)
        embed.add_field(name="💬 Total Messages",  value=str(data["messages"]), inline=True)
        embed.add_field(name="📅 Last 30 Days",    value=f"{monthly} messages", inline=True)
        embed.add_field(name="📆 Last 7 Days",     value=f"{weekly} messages",  inline=True)
        embed.add_field(name="🎙️ Total VC Time",   value=f"{hours}h {mins}m",   inline=True)
        embed.add_field(name="📅 Joined Server",   value=discord.utils.format_dt(member.joined_at, "R"), inline=True)
        embed.add_field(name="🗓️ Account Age",     value=discord.utils.format_dt(member.created_at, "R"), inline=True)
        await ctx.reply(embed=embed)

    # ─── !setlevelchannel ─────────────────────────────────────────────────────
    @commands.command(name="setlevelchannel", usage="[#channel]")
    @commands.has_permissions(administrator=True)
    async def setlevelchannel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel for level up notifications."""
        if channel is None:
            self.bot.level_channels.pop(ctx.guild.id, None)
            return await ctx.reply("✅ Level up notifications will now appear in the same channel as the message.")
        self.bot.level_channels[ctx.guild.id] = channel.id
        await ctx.reply(embed=discord.Embed(
            title="✅ Level Channel Set",
            description=f"Level up notifications will be sent to {channel.mention}.",
            color=discord.Color.green(), timestamp=discord.utils.utcnow(),
        ))

    # ─── !setlevelrole ────────────────────────────────────────────────────────
    @commands.command(name="setlevelrole", usage="<level> <@role>")
    @commands.has_permissions(administrator=True)
    async def setlevelrole(self, ctx, level: int, role: discord.Role):
        """Give a role when members reach a certain level."""
        if ctx.guild.id not in self.bot.level_roles:
            self.bot.level_roles[ctx.guild.id] = {}
        self.bot.level_roles[ctx.guild.id][level] = role.id
        await ctx.reply(embed=discord.Embed(
            title="✅ Level Role Set",
            description=f"Members will receive {role.mention} when they reach **Level {level}**.",
            color=discord.Color.green(), timestamp=discord.utils.utcnow(),
        ))

    # ─── !resetxp ─────────────────────────────────────────────────────────────
    @commands.command(name="resetxp", usage="<@user>")
    @commands.has_permissions(administrator=True)
    async def resetxp(self, ctx, member: discord.Member):
        """Reset a member's XP and stats."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "DELETE FROM levels WHERE user_id=? AND guild_id=?",
                (member.id, ctx.guild.id)
            )
            await db.execute(
                "DELETE FROM message_log WHERE user_id=? AND guild_id=?",
                (member.id, ctx.guild.id)
            )
            await db.commit()
        await ctx.reply(embed=discord.Embed(
            title="🧹 XP Reset",
            description=f"All XP and stats for **{member}** have been reset.",
            color=discord.Color.orange(), timestamp=discord.utils.utcnow(),
        ))


async def setup(bot):
    await bot.add_cog(Levels(bot))
