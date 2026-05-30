import discord
from discord.ext import commands


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="userinfo", usage="[@user]")
    async def userinfo(self, ctx, member: discord.Member = None):
        """Display info about a user (defaults to yourself)."""
        member = member or ctx.author
        key = f"{member.id}:{ctx.guild.id}"
        warn_count = len(self.bot.warn_data.get(key, []))
        roles = [r.mention for r in reversed(member.roles) if r != ctx.guild.default_role]

        embed = discord.Embed(
            title=f"👤 {member}",
            color=member.color if member.color != discord.Color.default() else discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID",              value=member.id,                                             inline=True)
        embed.add_field(name="Bot",             value="Yes" if member.bot else "No",                         inline=True)
        embed.add_field(name="Warnings",        value=f"{warn_count}/3 (auto-ban at 3)",                     inline=True)
        embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, "R"),      inline=True)
        embed.add_field(name="Joined Server",   value=discord.utils.format_dt(member.joined_at, "R"),       inline=True)
        embed.add_field(name="Nickname",        value=member.nick or "None",                                 inline=True)
        if member.is_timed_out():
            embed.add_field(name="Timed Out Until",
                            value=discord.utils.format_dt(member.timed_out_until, "R"), inline=True)
        if roles:
            embed.add_field(
                name=f"Roles ({len(roles)})",
                value=" ".join(roles[:15]) + ("..." if len(roles) > 15 else ""),
                inline=False,
            )
        await ctx.reply(embed=embed)

    @commands.command(name="serverinfo")
    async def serverinfo(self, ctx):
        """Display info about this server."""
        guild = ctx.guild
        bots   = sum(1 for m in guild.members if m.bot)
        humans = guild.member_count - bots

        embed = discord.Embed(title=f"🏠 {guild.name}", color=discord.Color.blurple(), timestamp=discord.utils.utcnow())
        if guild.icon:   embed.set_thumbnail(url=guild.icon.url)
        if guild.banner: embed.set_image(url=guild.banner.url)
        if guild.description: embed.description = guild.description

        log_ch = self.bot.log_channels.get(guild.id)
        log_val = f"<#{log_ch}>" if log_ch else "Not set"

        embed.add_field(name="Owner",        value=f"<@{guild.owner_id}>",                                    inline=True)
        embed.add_field(name="ID",           value=guild.id,                                                   inline=True)
        embed.add_field(name="Created",      value=discord.utils.format_dt(guild.created_at, "R"),            inline=True)
        embed.add_field(name="Members",      value=f"{guild.member_count} ({humans} humans, {bots} bots)",    inline=True)
        embed.add_field(name="Channels",     value=str(len(guild.channels)),                                   inline=True)
        embed.add_field(name="Roles",        value=str(len(guild.roles)),                                      inline=True)
        embed.add_field(name="Boost Level",  value=f"Level {guild.premium_tier} ({guild.premium_subscription_count} boosts)", inline=True)
        embed.add_field(name="Verification", value=str(guild.verification_level).title(),                      inline=True)
        embed.add_field(name="Log Channel",  value=log_val,                                                    inline=True)
        await ctx.reply(embed=embed)

    @commands.command(name="help", usage="[command]")
    async def help(self, ctx, command_name: str = None):
        """Show all commands or info about a specific command."""
        if command_name:
            cmd = self.bot.get_command(command_name)
            if not cmd:
                return await ctx.reply(f"❌ Command `{command_name}` not found.")
            embed = discord.Embed(title=f"!{cmd.qualified_name}",
                description=cmd.help or "No description.", color=discord.Color.blurple())
            embed.add_field(name="Usage", value=f"`!{cmd.qualified_name} {cmd.usage or ''}`".strip())
            return await ctx.reply(embed=embed)

        embed = discord.Embed(
            title="🤖 Bot Commands",
            description="Prefix: `!`",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="🛡️ Anti-Raid", inline=False, value="\n".join([
            "`!lockdown enable` — Activate lockdown",
            "`!lockdown lift`   — Lift lockdown",
            "`!lockdown status` — Check status",
        ]))
        embed.add_field(name="🔨 Moderation", inline=False, value="\n".join([
            "`!ban <@user> [days] [reason]`    — Ban (auto-ban at 3 warns)",
            "`!unban <user_id>`                — Unban by ID",
            "`!kick <@user> [reason]`          — Kick",
            "`!mute <@user> <minutes>`         — Timeout",
            "`!unmute <@user>`                 — Remove timeout",
            "`!warn <@user> <reason>`          — Warn (auto-bans at 3)",
            "`!warnings <@user>`               — View warnings",
            "`!clearwarnings <@user>`          — Clear warnings",
            "`!purge <amount> [@user]`         — Bulk delete",
            "`!slowmode <seconds>`             — Set slowmode",
            "`!lock / !unlock`                 — Lock channel",
            "`!setlog [#channel]`              — Set mod log channel",
        ]))
        embed.add_field(name="🎉 Fun", inline=False, value="\n".join([
            "`!8ball <question>` — Magic 8ball",
            "`!coinflip`         — Flip a coin",
            "`!roll [sides]`     — Roll a dice",
            "`!rps <choice>`     — Rock paper scissors",
            "`!pp [@user]`       — PP size checker",
            "`!rate <thing>`     — Rate anything",
            "`!ship <@u1> <@u2>` — Ship two people",
            "`!truth`            — Truth question",
            "`!dare`             — Dare challenge",
            "`!wyr`              — Would you rather",
            "`!poll <question>`  — Create a poll",
            "`!joke`             — Random joke",
            "`!choose a | b | c` — Pick an option",
            "`!crypto`           — Random crypto gif",
            "`!kiss [@user]`     — Send a kiss gif",
            "`!hug [@user]`      — Send a hug gif",
            "`!slap [@user]`     — Slap someone",
            "`!cuddle [@user]`   — Send a cuddle gif",
        ]))
        embed.add_field(name="👋 Welcome & Autorole", inline=False, value="\n".join([
            "`!setwelcome set <#channel> <message>` — Set welcome message",
            "`!setwelcome disable`  — Disable welcome messages",
            "`!setwelcome test`     — Send a test welcome",
            "`!setwelcome status`   — View welcome config",
            "`!autorole set <@role>` — Set auto-role for new members",
            "`!autorole disable`    — Disable autorole",
            "`!autorole status`     — View autorole config",
        ]))
        embed.add_field(name="🔍 Snipe", inline=False, value="\n".join([
            "`!snipe`     — Last deleted message",
            "`!editsnipe` — Last edited message",
        ]))
        embed.add_field(name="💤 AFK", inline=False, value="\n".join([
            "`!afk [reason]` — Set your AFK status",
        ]))
        embed.add_field(name="ℹ️ Info", inline=False, value="\n".join([
            "`!userinfo [@user]` — User info",
            "`!serverinfo`       — Server info",
            "`!help [command]`   — This menu",
        ]))
        embed.set_footer(text="Auto-ban triggers at 3 warnings • Anti-raid at 5 joins/10s")
        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Info(bot))
