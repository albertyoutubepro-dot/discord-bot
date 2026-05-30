import discord
from discord.ext import commands
import time
from collections import defaultdict

OWNER_ID = 1446215395358015559

# Thresholds — actions within TIME_WINDOW seconds
THRESHOLDS = {
    "ban":            (3, 5),   # 3 bans in 5 seconds
    "kick":           (3, 5),   # 3 kicks in 5 seconds
    "channel_delete": (2, 5),   # 2 channel deletes in 5 seconds
    "channel_create": (3, 5),   # 3 channel creates in 5 seconds
    "role_delete":    (2, 5),   # 2 role deletes in 5 seconds
    "webhook_create": (2, 5),   # 2 webhook creates in 5 seconds
    "bot_add":        (1, 5),   # any bot add
}


class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # guild_id -> { "action_type" -> [timestamps] }
        self.action_log = defaultdict(lambda: defaultdict(list))
        # guild_id -> set of already-punished user IDs (to avoid double punish)
        self.punished = defaultdict(set)

        if not hasattr(bot, 'antinuke_enabled'):
            bot.antinuke_enabled = set()  # set of guild_ids with antinuke on
        if not hasattr(bot, 'antinuke_whitelist'):
            bot.antinuke_whitelist = defaultdict(set)  # guild_id -> set of user_ids

    # ─── Helpers ──────────────────────────────────────────────────────────────
    def is_whitelisted(self, guild_id: int, user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        return user_id in self.bot.antinuke_whitelist[guild_id]

    def track(self, guild_id: int, user_id: int, action: str) -> bool:
        """Track an action. Returns True if threshold is exceeded."""
        if guild_id not in self.bot.antinuke_enabled:
            return False
        if self.is_whitelisted(guild_id, user_id):
            return False

        limit, window = THRESHOLDS.get(action, (3, 5))
        now = time.time()
        log = self.action_log[guild_id][f"{user_id}:{action}"]
        log.append(now)
        # Clean old entries outside window
        self.action_log[guild_id][f"{user_id}:{action}"] = [t for t in log if now - t < window]
        return len(self.action_log[guild_id][f"{user_id}:{action}"]) >= limit

    async def punish(self, guild: discord.Guild, member: discord.Member, action: str, extra: str = ""):
        """Strip all roles and DM the punished user."""
        if member.id in self.punished[guild.id]:
            return
        self.punished[guild.id].add(member.id)

        # Remove all dangerous permissions by stripping roles (keep @everyone)
        try:
            roles_to_remove = [r for r in member.roles if r != guild.default_role and r < guild.me.top_role]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason=f"Anti-Nuke: {action}")
        except discord.Forbidden:
            pass

        # DM the punished user
        try:
            await member.send(embed=discord.Embed(
                title=f"⚠️ Anti-Nuke Action — {guild.name}",
                description=f"Your roles have been removed for triggering the anti-nuke system.\n**Action:** {action}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow(),
            ))
        except discord.Forbidden:
            pass

        # Log to mod channel
        log_channel_id = self.bot.log_channels.get(guild.id)
        if log_channel_id:
            channel = guild.get_channel(log_channel_id)
            if channel:
                embed = discord.Embed(
                    title="🚨 Anti-Nuke Triggered",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow(),
                )
                embed.add_field(name="User",   value=f"{member} ({member.id})", inline=True)
                embed.add_field(name="Action", value=action,                    inline=True)
                embed.add_field(name="Punishment", value="All roles removed",   inline=True)
                if extra:
                    embed.add_field(name="Details", value=extra, inline=False)
                embed.set_footer(text="Anti-Nuke System")
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

        # Clear their action log so they don't keep triggering
        for key in list(self.action_log[guild.id].keys()):
            if key.startswith(str(member.id)):
                del self.action_log[guild.id][key]

    async def get_auditor(self, guild: discord.Guild, action: discord.AuditLogAction):
        """Get the user who performed the last audit log action."""
        try:
            async for entry in guild.audit_logs(limit=1, action=action):
                return entry.user
        except discord.Forbidden:
            pass
        return None

    # ─── Commands ─────────────────────────────────────────────────────────────
    @commands.group(name="antinuke", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx):
        await ctx.reply("\n".join([
            "**Anti-Nuke Commands:**",
            "`!antinuke enable`           — Enable anti-nuke",
            "`!antinuke disable`          — Disable anti-nuke",
            "`!antinuke status`           — Check current status",
            "`!antinuke whitelist @user`  — Whitelist a trusted user",
            "`!antinuke unwhitelist @user`— Remove from whitelist",
        ]))

    @antinuke.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def antinuke_enable(self, ctx):
        self.bot.antinuke_enabled.add(ctx.guild.id)
        # Clear punished cache on enable
        self.punished[ctx.guild.id].clear()
        await ctx.reply(embed=discord.Embed(
            title="🛡️ Anti-Nuke Enabled",
            description="\n".join([
                "Your server is now protected against nukes.",
                "",
                "**Protects against:**",
                "• Mass bans (3+ in 5s)",
                "• Mass kicks (3+ in 5s)",
                "• Mass channel deletes (2+ in 5s)",
                "• Mass channel creates (3+ in 5s)",
                "• Mass role deletes (2+ in 5s)",
                "• Mass webhook creates (2+ in 5s)",
                "• Unauthorized bot adds",
                "",
                "**Punishment:** All roles stripped instantly.",
                f"**Whitelisted:** You (owner) are always exempt.",
            ]),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        ))

    @antinuke.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def antinuke_disable(self, ctx):
        self.bot.antinuke_enabled.discard(ctx.guild.id)
        await ctx.reply(embed=discord.Embed(
            title="🛡️ Anti-Nuke Disabled",
            description="Anti-nuke protection has been turned off.",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        ))

    @antinuke.command(name="status")
    @commands.has_permissions(administrator=True)
    async def antinuke_status(self, ctx):
        enabled = ctx.guild.id in self.bot.antinuke_enabled
        whitelist = self.bot.antinuke_whitelist[ctx.guild.id]
        wl_mentions = ", ".join(f"<@{uid}>" for uid in whitelist) if whitelist else "None"

        embed = discord.Embed(
            title="🛡️ Anti-Nuke Status",
            color=discord.Color.green() if enabled else discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Status",      value="🟢 Enabled" if enabled else "🔴 Disabled", inline=True)
        embed.add_field(name="Whitelist",   value=wl_mentions, inline=False)
        embed.add_field(name="Thresholds",  value="\n".join([
            "• 3 bans / 5s",
            "• 3 kicks / 5s",
            "• 2 channel deletes / 5s",
            "• 3 channel creates / 5s",
            "• 2 role deletes / 5s",
            "• 2 webhook creates / 5s",
            "• Any bot add",
        ]), inline=False)
        await ctx.reply(embed=embed)

    @antinuke.command(name="whitelist")
    @commands.has_permissions(administrator=True)
    async def antinuke_whitelist(self, ctx, member: discord.Member):
        self.bot.antinuke_whitelist[ctx.guild.id].add(member.id)
        await ctx.reply(embed=discord.Embed(
            title="✅ Whitelisted",
            description=f"{member.mention} is now exempt from anti-nuke.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        ))

    @antinuke.command(name="unwhitelist")
    @commands.has_permissions(administrator=True)
    async def antinuke_unwhitelist(self, ctx, member: discord.Member):
        self.bot.antinuke_whitelist[ctx.guild.id].discard(member.id)
        await ctx.reply(embed=discord.Embed(
            title="❌ Removed from Whitelist",
            description=f"{member.mention} is no longer exempt from anti-nuke.",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        ))

    # ─── Listeners ────────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        auditor = await self.get_auditor(guild, discord.AuditLogAction.ban)
        if auditor and self.track(guild.id, auditor.id, "ban"):
            member = guild.get_member(auditor.id)
            if member:
                await self.punish(guild, member, "Mass Ban", f"Banned {user}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        auditor = await self.get_auditor(guild, discord.AuditLogAction.kick)
        if auditor and auditor.id != member.id:
            if self.track(guild.id, auditor.id, "kick"):
                kicker = guild.get_member(auditor.id)
                if kicker:
                    await self.punish(guild, kicker, "Mass Kick", f"Kicked {member}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        auditor = await self.get_auditor(guild, discord.AuditLogAction.channel_delete)
        if auditor and self.track(guild.id, auditor.id, "channel_delete"):
            member = guild.get_member(auditor.id)
            if member:
                await self.punish(guild, member, "Mass Channel Delete", f"Deleted #{channel.name}")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        auditor = await self.get_auditor(guild, discord.AuditLogAction.channel_create)
        if auditor and self.track(guild.id, auditor.id, "channel_create"):
            member = guild.get_member(auditor.id)
            if member:
                await self.punish(guild, member, "Mass Channel Create", f"Created #{channel.name}")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        guild = role.guild
        auditor = await self.get_auditor(guild, discord.AuditLogAction.role_delete)
        if auditor and self.track(guild.id, auditor.id, "role_delete"):
            member = guild.get_member(auditor.id)
            if member:
                await self.punish(guild, member, "Mass Role Delete", f"Deleted @{role.name}")

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.TextChannel):
        guild = channel.guild
        auditor = await self.get_auditor(guild, discord.AuditLogAction.webhook_create)
        if auditor and self.track(guild.id, auditor.id, "webhook_create"):
            member = guild.get_member(auditor.id)
            if member:
                await self.punish(guild, member, "Mass Webhook Create", f"In #{channel.name}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not member.bot:
            return
        guild = member.guild
        if guild.id not in self.bot.antinuke_enabled:
            return
        auditor = await self.get_auditor(guild, discord.AuditLogAction.bot_add)
        if auditor and not self.is_whitelisted(guild.id, auditor.id):
            adder = guild.get_member(auditor.id)
            if adder:
                await self.punish(guild, adder, "Unauthorized Bot Add", f"Added {member} ({member.id})")
            # Kick the bot
            try:
                await member.kick(reason="Anti-Nuke: unauthorized bot add")
            except discord.Forbidden:
                pass


async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
