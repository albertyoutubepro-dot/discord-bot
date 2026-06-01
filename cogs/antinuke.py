import discord
from discord.ext import commands
import asyncio
import time
from collections import defaultdict

OWNER_ID = 1446215395358015559

THRESHOLDS = {
    "ban":            (2, 5),
    "kick":           (2, 5),
    "channel_delete": (1, 5),
    "channel_create": (2, 5),
    "role_delete":    (1, 5),
    "webhook_create": (1, 5),
    "bot_add":        (1, 99),
}


class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.action_log = defaultdict(lambda: defaultdict(list))
        self.punished = defaultdict(set)
        self.channel_cache = {}

        if not hasattr(bot, 'antinuke_enabled'):
            bot.antinuke_enabled = set()
        if not hasattr(bot, 'antinuke_whitelist'):
            bot.antinuke_whitelist = defaultdict(set)

    @property
    def db(self):
        return self.bot.cogs.get("Database")

    # ─── Helpers ──────────────────────────────────────────────────────────────
    def is_whitelisted(self, guild_id, user_id):
        if user_id == OWNER_ID:
            return True
        return user_id in self.bot.antinuke_whitelist[guild_id]

    def track(self, guild_id, user_id, action):
        if guild_id not in self.bot.antinuke_enabled:
            return False
        if self.is_whitelisted(guild_id, user_id):
            return False
        limit, window = THRESHOLDS.get(action, (2, 5))
        now = time.time()
        key = f"{user_id}:{action}"
        log = self.action_log[guild_id][key]
        log.append(now)
        self.action_log[guild_id][key] = [t for t in log if now - t < window]
        return len(self.action_log[guild_id][key]) >= limit

    async def get_auditor(self, guild, action, max_age=3):
        await asyncio.sleep(0.5)
        try:
            async for entry in guild.audit_logs(limit=5, action=action):
                age = (discord.utils.utcnow() - entry.created_at).total_seconds()
                if age <= max_age:
                    return entry.user
        except discord.Forbidden:
            pass
        return None

    async def punish(self, guild, member, action, extra=""):
        if member.id in self.punished[guild.id]:
            return
        if self.is_whitelisted(guild.id, member.id):
            return
        self.punished[guild.id].add(member.id)

        try:
            roles_to_remove = [r for r in member.roles if r != guild.default_role and r < guild.me.top_role]
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason=f"Anti-Nuke: {action}")
        except discord.Forbidden:
            pass

        try:
            await guild.ban(member, reason=f"Anti-Nuke: {action}", delete_message_days=0)
        except discord.Forbidden:
            pass

        await self.send_log(guild, member, action, extra, banned=True)

        for key in list(self.action_log[guild.id].keys()):
            if key.startswith(str(member.id)):
                del self.action_log[guild.id][key]

    async def send_log(self, guild, member, action, extra="", banned=False):
        log_channel_id = self.bot.log_channels.get(guild.id)
        if not log_channel_id:
            return
        channel = guild.get_channel(log_channel_id)
        if not channel:
            return
        embed = discord.Embed(
            title="🚨 Anti-Nuke Triggered",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="User",       value=f"{member} ({member.id})", inline=True)
        embed.add_field(name="Action",     value=action,                    inline=True)
        embed.add_field(name="Punishment", value="Banned + Roles Stripped" if banned else "Roles Stripped", inline=True)
        if extra:
            embed.add_field(name="Details", value=extra, inline=False)
        embed.set_footer(text="Anti-Nuke System")
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    async def restore_channel(self, guild, channel_data):
        try:
            category = guild.get_channel(channel_data["category_id"]) if channel_data["category_id"] else None
            if channel_data["type"] == discord.ChannelType.text:
                new_ch = await guild.create_text_channel(
                    name=channel_data["name"], category=category,
                    topic=channel_data.get("topic"), reason="Anti-Nuke: channel restore",
                )
            elif channel_data["type"] == discord.ChannelType.voice:
                new_ch = await guild.create_voice_channel(
                    name=channel_data["name"], category=category, reason="Anti-Nuke: channel restore",
                )
            else:
                return

            for target_id, overwrite_data in channel_data.get("overwrites", {}).items():
                target = guild.get_role(target_id) or guild.get_member(target_id)
                if target:
                    overwrite = discord.PermissionOverwrite(**overwrite_data)
                    await new_ch.set_permissions(target, overwrite=overwrite)

            log_channel_id = self.bot.log_channels.get(guild.id)
            if log_channel_id:
                log_ch = guild.get_channel(log_channel_id)
                if log_ch:
                    await log_ch.send(embed=discord.Embed(
                        title="♻️ Channel Restored",
                        description=f"Recreated **#{channel_data['name']}** after nuke attempt.",
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow(),
                    ))
        except Exception as e:
            print(f"[ANTINUKE] Failed to restore channel: {e}")

    # ─── Channel cache ────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.cache_guild_channels(guild)

    def cache_guild_channels(self, guild):
        self.channel_cache[guild.id] = {}
        for ch in guild.channels:
            self.cache_channel(ch)

    def cache_channel(self, channel):
        overwrites = {}
        for target, overwrite in channel.overwrites.items():
            overwrites[target.id] = dict(iter(overwrite))
        self.channel_cache.setdefault(channel.guild.id, {})[channel.id] = {
            "name":        channel.name,
            "type":        channel.type,
            "category_id": channel.category_id,
            "topic":       getattr(channel, "topic", None),
            "overwrites":  overwrites,
        }

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        self.cache_channel(channel)
        guild = channel.guild
        auditor = await self.get_auditor(guild, discord.AuditLogAction.channel_create)
        if auditor and self.track(guild.id, auditor.id, "channel_create"):
            member = guild.get_member(auditor.id)
            if member:
                await self.punish(guild, member, "Mass Channel Create", f"Created #{channel.name}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        cached = self.channel_cache.get(guild.id, {}).get(channel.id)
        auditor = await self.get_auditor(guild, discord.AuditLogAction.channel_delete)
        if auditor and self.track(guild.id, auditor.id, "channel_delete"):
            member = guild.get_member(auditor.id)
            if member:
                await self.punish(guild, member, "Mass Channel Delete", f"Deleted #{channel.name}")
                if cached and guild.id in self.bot.antinuke_enabled:
                    await self.restore_channel(guild, cached)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild = role.guild
        auditor = await self.get_auditor(guild, discord.AuditLogAction.role_delete)
        if auditor and self.track(guild.id, auditor.id, "role_delete"):
            member = guild.get_member(auditor.id)
            if member:
                await self.punish(guild, member, "Mass Role Delete", f"Deleted @{role.name}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        auditor = await self.get_auditor(guild, discord.AuditLogAction.ban)
        if auditor and self.track(guild.id, auditor.id, "ban"):
            member = guild.get_member(auditor.id)
            if member:
                await self.punish(guild, member, "Mass Ban", f"Banned {user}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        auditor = await self.get_auditor(guild, discord.AuditLogAction.kick)
        if auditor and auditor.id != member.id:
            if self.track(guild.id, auditor.id, "kick"):
                kicker = guild.get_member(auditor.id)
                if kicker:
                    await self.punish(guild, kicker, "Mass Kick", f"Kicked {member}")

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        guild = channel.guild
        auditor = await self.get_auditor(guild, discord.AuditLogAction.webhook_create)
        if auditor and self.track(guild.id, auditor.id, "webhook_create"):
            member = guild.get_member(auditor.id)
            if member:
                await self.punish(guild, member, "Mass Webhook Create", f"In #{channel.name}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
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
            try:
                await member.kick(reason="Anti-Nuke: unauthorized bot add")
            except discord.Forbidden:
                pass

    # ─── Commands ─────────────────────────────────────────────────────────────
    @commands.group(name="antinuke", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx):
        await ctx.reply("\n".join([
            "**Anti-Nuke Commands:**",
            "`!antinuke enable`            — Enable anti-nuke",
            "`!antinuke disable`           — Disable anti-nuke",
            "`!antinuke status`            — Check status & thresholds",
            "`!antinuke whitelist @user`   — Whitelist a trusted user",
            "`!antinuke unwhitelist @user` — Remove from whitelist",
            "`!antinuke test`              — Send a test alert",
        ]))

    @antinuke.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def antinuke_enable(self, ctx):
        self.bot.antinuke_enabled.add(ctx.guild.id)
        self.punished[ctx.guild.id].clear()
        self.cache_guild_channels(ctx.guild)
        if self.db:
            await self.db.save_antinuke_enabled(ctx.guild.id, True)
        await ctx.reply(embed=discord.Embed(
            title="🛡️ Anti-Nuke Enabled",
            description="\n".join([
                "Your server is now protected.",
                "",
                "**Triggers on:**",
                "• 2+ bans in 5s → **banned**",
                "• 2+ kicks in 5s → **banned**",
                "• 1+ channel delete in 5s → **banned + channel restored**",
                "• 2+ channel creates in 5s → **banned**",
                "• 1+ role delete in 5s → **banned**",
                "• 1+ webhook create in 5s → **banned**",
                "• Any unauthorized bot add → **banned + bot kicked**",
            ]),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        ))

    @antinuke.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def antinuke_disable(self, ctx):
        self.bot.antinuke_enabled.discard(ctx.guild.id)
        if self.db:
            await self.db.save_antinuke_enabled(ctx.guild.id, False)
        await ctx.reply(embed=discord.Embed(
            title="🛡️ Anti-Nuke Disabled",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        ))

    @antinuke.command(name="status")
    @commands.has_permissions(administrator=True)
    async def antinuke_status(self, ctx):
        enabled = ctx.guild.id in self.bot.antinuke_enabled
        whitelist = self.bot.antinuke_whitelist[ctx.guild.id]
        wl_mentions = ", ".join(f"<@{uid}>" for uid in whitelist) if whitelist else "None"
        cached = len(self.channel_cache.get(ctx.guild.id, {}))
        embed = discord.Embed(
            title="🛡️ Anti-Nuke Status",
            color=discord.Color.green() if enabled else discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Status",          value="🟢 Enabled" if enabled else "🔴 Disabled", inline=True)
        embed.add_field(name="Cached Channels", value=str(cached),  inline=True)
        embed.add_field(name="Whitelist",       value=wl_mentions,  inline=False)
        embed.add_field(name="Punishment",      value="Ban + Role Strip", inline=True)
        embed.add_field(name="Channel Restore", value="✅ Enabled",  inline=True)
        await ctx.reply(embed=embed)

    @antinuke.command(name="whitelist")
    @commands.has_permissions(administrator=True)
    async def antinuke_whitelist_cmd(self, ctx, member: discord.Member):
        self.bot.antinuke_whitelist[ctx.guild.id].add(member.id)
        if self.db:
            await self.db.save_antinuke_whitelist_add(ctx.guild.id, member.id)
        await ctx.reply(embed=discord.Embed(
            title="✅ Whitelisted",
            description=f"{member.mention} is now exempt from anti-nuke.",
            color=discord.Color.green(), timestamp=discord.utils.utcnow(),
        ))

    @antinuke.command(name="unwhitelist")
    @commands.has_permissions(administrator=True)
    async def antinuke_unwhitelist_cmd(self, ctx, member: discord.Member):
        self.bot.antinuke_whitelist[ctx.guild.id].discard(member.id)
        if self.db:
            await self.db.save_antinuke_whitelist_remove(ctx.guild.id, member.id)
        await ctx.reply(embed=discord.Embed(
            title="❌ Removed from Whitelist",
            description=f"{member.mention} is no longer exempt.",
            color=discord.Color.orange(), timestamp=discord.utils.utcnow(),
        ))

    @antinuke.command(name="test")
    @commands.has_permissions(administrator=True)
    async def antinuke_test(self, ctx):
        if ctx.guild.id not in self.bot.antinuke_enabled:
            return await ctx.reply("❌ Anti-nuke is not enabled. Run `!antinuke enable` first.")
        log_channel_id = self.bot.log_channels.get(ctx.guild.id)
        if not log_channel_id:
            return await ctx.reply("❌ No log channel set. Run `!setlog #channel` first.")
        channel = ctx.guild.get_channel(log_channel_id)
        if not channel:
            return await ctx.reply("❌ Log channel not found.")
        embed = discord.Embed(
            title="🚨 Anti-Nuke Triggered",
            description="⚠️ **This is a TEST** — no real action was taken.",
            color=discord.Color.red(), timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="User",       value=f"{ctx.author} ({ctx.author.id})", inline=True)
        embed.add_field(name="Action",     value="Mass Channel Delete (simulated)",  inline=True)
        embed.add_field(name="Punishment", value="Ban + Roles Stripped (simulated)", inline=True)
        embed.set_footer(text="Anti-Nuke System — TEST MODE")
        await channel.send(embed=embed)
        await ctx.reply(f"✅ Test alert sent to {channel.mention}!")


async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
