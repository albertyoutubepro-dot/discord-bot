import discord
from discord.ext import commands
import time


def mod_embed(title: str, color: discord.Color, **fields) -> discord.Embed:
    embed = discord.Embed(title=title, color=color, timestamp=discord.utils.utcnow())
    for name, value in fields.items():
        embed.add_field(name=name.replace("_", " ").title(), value=value, inline=True)
    return embed


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.cogs.get("Database")

    async def log(self, guild: discord.Guild, embed: discord.Embed):
        channel_id = self.bot.log_channels.get(guild.id)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

    # ─── !setlog ──────────────────────────────────────────────────────────────
    @commands.command(name="setlog", usage="[#channel]")
    @commands.has_permissions(administrator=True)
    async def setlog(self, ctx, channel: discord.TextChannel = None):
        """Set the log channel for mod actions. Leave blank to clear it."""
        if channel is None:
            self.bot.log_channels.pop(ctx.guild.id, None)
            if self.db:
                await self.db.save_log_channel(ctx.guild.id, None)
            return await ctx.reply(embed=discord.Embed(
                title="📋 Log Channel Cleared",
                description="Mod logs have been disabled.",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow(),
            ))
        self.bot.log_channels[ctx.guild.id] = channel.id
        if self.db:
            await self.db.save_log_channel(ctx.guild.id, channel.id)
        await ctx.reply(embed=discord.Embed(
            title="📋 Log Channel Set",
            description=f"Mod actions will now be logged in {channel.mention}.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        ))

    # ─── !ban ─────────────────────────────────────────────────────────────────
    @commands.command(name="ban", usage="<@user> [days=0] [reason]")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, delete_days: int = 0, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.reply("❌ You can't ban someone with an equal or higher role than you.")
        try:
            await member.send(embed=discord.Embed(
                title=f"You were banned from {ctx.guild.name}",
                color=discord.Color.red(),
            ).add_field(name="Reason", value=reason))
        except discord.Forbidden:
            pass
        await member.ban(delete_message_days=min(max(delete_days, 0), 7), reason=f"{ctx.author}: {reason}")
        embed = mod_embed("🔨 User Banned", discord.Color.red(),
            user=f"{member} ({member.id})", moderator=str(ctx.author), reason=reason)
        await ctx.reply(embed=embed)
        await self.log(ctx.guild, embed)

    # ─── !unban ───────────────────────────────────────────────────────────────
    @commands.command(name="unban", usage="<user_id> [reason]")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"{ctx.author}: {reason}")
            embed = mod_embed("✅ User Unbanned", discord.Color.green(),
                user=f"{user} ({user.id})", moderator=str(ctx.author), reason=reason)
            await ctx.reply(embed=embed)
            await self.log(ctx.guild, embed)
        except discord.NotFound:
            await ctx.reply("❌ That user is not banned or doesn't exist.")

    # ─── !kick ────────────────────────────────────────────────────────────────
    @commands.command(name="kick", usage="<@user> [reason]")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.reply("❌ You can't kick someone with an equal or higher role.")
        try:
            await member.send(embed=discord.Embed(
                title=f"You were kicked from {ctx.guild.name}",
                color=discord.Color.orange(),
            ).add_field(name="Reason", value=reason))
        except discord.Forbidden:
            pass
        await member.kick(reason=f"{ctx.author}: {reason}")
        embed = mod_embed("👢 User Kicked", discord.Color.orange(),
            user=f"{member} ({member.id})", moderator=str(ctx.author), reason=reason)
        await ctx.reply(embed=embed)
        await self.log(ctx.guild, embed)

    # ─── !mute ────────────────────────────────────────────────────────────────
    @commands.command(name="mute", usage="<@user> <minutes> [reason]")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, minutes: int, *, reason: str = "No reason provided"):
        if minutes < 1 or minutes > 40320:
            return await ctx.reply("❌ Duration must be between 1 and 40320 minutes (28 days).")
        import datetime
        until = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
        await member.timeout(until, reason=f"{ctx.author}: {reason}")
        embed = mod_embed("🔇 User Muted", discord.Color.gold(),
            user=f"{member} ({member.id})", duration=f"{minutes} minute(s)",
            moderator=str(ctx.author), reason=reason)
        await ctx.reply(embed=embed)
        await self.log(ctx.guild, embed)

    # ─── !unmute ──────────────────────────────────────────────────────────────
    @commands.command(name="unmute", usage="<@user>")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        await member.timeout(None)
        embed = mod_embed("🔊 User Unmuted", discord.Color.green(),
            user=f"{member} ({member.id})", moderator=str(ctx.author))
        await ctx.reply(embed=embed)
        await self.log(ctx.guild, embed)

    # ─── !warn ────────────────────────────────────────────────────────────────
    @commands.command(name="warn", usage="<@user> <reason>")
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str):
        key = f"{member.id}:{ctx.guild.id}"
        now = time.time()
        warn_entry = {
            "reason": reason,
            "timestamp": now,
            "moderator": str(ctx.author),
        }
        self.bot.warn_data[key].append(warn_entry)
        warn_count = len(self.bot.warn_data[key])

        # Persist
        if self.db:
            await self.db.save_warn(member.id, ctx.guild.id, reason, str(ctx.author), now)

        try:
            await member.send(embed=discord.Embed(
                title=f"⚠️ Warning from {ctx.guild.name}",
                color=discord.Color.yellow(),
            ).add_field(name="Reason", value=reason
            ).add_field(name="Moderator", value=str(ctx.author)
            ).add_field(name="Total Warnings", value=str(warn_count)))
        except discord.Forbidden:
            pass

        embed = mod_embed("⚠️ User Warned", discord.Color.yellow(),
            user=f"{member} ({member.id})", total_warnings=str(warn_count),
            moderator=str(ctx.author), reason=reason)
        await ctx.reply(embed=embed)
        await self.log(ctx.guild, embed)

        if warn_count >= 3:
            auto_reason = f"Auto-ban: reached {warn_count} warnings. Last: {reason}"
            try:
                await member.send(embed=discord.Embed(
                    title=f"🔨 You were auto-banned from {ctx.guild.name}",
                    description=f"You reached **{warn_count} warnings** and have been automatically banned.",
                    color=discord.Color.red(),
                ).add_field(name="Last Reason", value=reason))
            except discord.Forbidden:
                pass
            try:
                await member.ban(reason=auto_reason)
                ban_embed = discord.Embed(
                    title="🔨 Auto-Ban Triggered",
                    description=f"{member.mention} was automatically banned after reaching **{warn_count} warnings**.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow(),
                ).add_field(name="Last Warning", value=reason)
                await ctx.send(embed=ban_embed)
                await self.log(ctx.guild, ban_embed)
            except discord.Forbidden:
                await ctx.send("⚠️ Reached 3 warnings but I couldn't auto-ban (missing permissions).")

    # ─── !warnings ────────────────────────────────────────────────────────────
    @commands.command(name="warnings", usage="<@user>")
    @commands.has_permissions(moderate_members=True)
    async def warnings(self, ctx, member: discord.Member):
        key = f"{member.id}:{ctx.guild.id}"
        warns = self.bot.warn_data.get(key, [])
        if not warns:
            return await ctx.reply(f"✅ **{member}** has no warnings.")
        lines = "\n\n".join(
            f"**#{i+1}** — {w['reason']}\n*by {w['moderator']} • <t:{int(w['timestamp'])}:R>*"
            for i, w in enumerate(warns)
        )
        embed = discord.Embed(
            title=f"⚠️ Warnings for {member}",
            description=lines[:4096],
            color=discord.Color.yellow(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text=f"{len(warns)} total warning(s) • Auto-ban at 3")
        await ctx.reply(embed=embed)

    # ─── !clearwarnings ───────────────────────────────────────────────────────
    @commands.command(name="clearwarnings", usage="<@user>")
    @commands.has_permissions(administrator=True)
    async def clearwarnings(self, ctx, member: discord.Member):
        key = f"{member.id}:{ctx.guild.id}"
        self.bot.warn_data.pop(key, None)
        if self.db:
            await self.db.clear_warns(member.id, ctx.guild.id)
        embed = discord.Embed(
            title="🧹 Warnings Cleared",
            description=f"All warnings for **{member}** have been cleared.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        await ctx.reply(embed=embed)
        await self.log(ctx.guild, embed)

    # ─── !purge ───────────────────────────────────────────────────────────────
    @commands.command(name="purge", usage="<amount 1-100> [@user]")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int, member: discord.Member = None):
        if not 1 <= amount <= 100:
            return await ctx.reply("❌ Amount must be between 1 and 100.")
        await ctx.message.delete()
        def check(m):
            return member is None or m.author == member
        deleted = await ctx.channel.purge(limit=amount, check=check)
        import asyncio
        msg = await ctx.send(embed=discord.Embed(
            title="🗑️ Messages Purged",
            description=f"Deleted **{len(deleted)}** message(s){f' from {member.mention}' if member else ''}.",
            color=discord.Color.blurple(), timestamp=discord.utils.utcnow(),
        ))
        await asyncio.sleep(5)
        await msg.delete()

    # ─── !slowmode ────────────────────────────────────────────────────────────
    @commands.command(name="slowmode", usage="<seconds 0-21600>")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        if not 0 <= seconds <= 21600:
            return await ctx.reply("❌ Slowmode must be between 0 and 21600 seconds.")
        await ctx.channel.edit(slowmode_delay=seconds)
        desc = "Slowmode **disabled**." if seconds == 0 else f"Slowmode set to **{seconds}s**."
        await ctx.reply(embed=discord.Embed(title="🐢 Slowmode Updated", description=desc,
            color=discord.Color.blurple(), timestamp=discord.utils.utcnow()))

    # ─── !lock ────────────────────────────────────────────────────────────────
    @commands.command(name="lock", usage="[reason]")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx, *, reason: str = "No reason provided"):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(title="🔒 Channel Locked", color=discord.Color.red(),
            timestamp=discord.utils.utcnow()).add_field(name="Reason", value=reason)
        await ctx.reply(embed=embed)
        await self.log(ctx.guild, embed)

    # ─── !unlock ──────────────────────────────────────────────────────────────
    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(title="🔓 Channel Unlocked", color=discord.Color.green(),
            timestamp=discord.utils.utcnow())
        await ctx.reply(embed=embed)
        await self.log(ctx.guild, embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
