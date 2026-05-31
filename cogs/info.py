import discord
from discord.ext import commands


CATEGORIES = {
    "antiraid": {
        "label": "🛡️ Anti-Raid",
        "color": discord.Color.red(),
        "commands": [
            ("!lockdown enable", "Activate lockdown — new members auto-kicked"),
            ("!lockdown lift",   "Lift lockdown — members can join normally"),
            ("!lockdown status", "Check current raid detection status"),
        ]
    },
    "moderation": {
        "label": "🔨 Moderation",
        "color": discord.Color.orange(),
        "commands": [
            ("!ban @user [days] [reason]",    "Ban a user. Auto-bans at 3 warnings"),
            ("!unban <user_id>",              "Unban a user by ID"),
            ("!kick @user [reason]",          "Kick a user"),
            ("!mute @user <minutes>",         "Timeout a user"),
            ("!unmute @user",                 "Remove timeout"),
            ("!warn @user <reason>",          "Warn a user (auto-bans at 3)"),
            ("!warnings @user",               "View all warnings"),
            ("!clearwarnings @user",          "Clear all warnings"),
            ("!purge <amount> [@user]",       "Bulk delete up to 100 messages"),
            ("!slowmode <seconds>",           "Set channel slowmode"),
            ("!lock [reason]",                "Lock this channel"),
            ("!unlock",                       "Unlock this channel"),
            ("!setlog [#channel]",            "Set mod log channel"),
            ("!history @user",                "Full mod action history for a user"),
        ]
    },
    "antinuke": {
        "label": "🚨 Anti-Nuke",
        "color": discord.Color.dark_red(),
        "commands": [
            ("!antinuke enable",              "Enable anti-nuke protection"),
            ("!antinuke disable",             "Disable anti-nuke"),
            ("!antinuke status",              "View protection status & thresholds"),
            ("!antinuke whitelist @user",     "Whitelist a trusted user"),
            ("!antinuke unwhitelist @user",   "Remove from whitelist"),
            ("!antinuke test",                "Send a fake nuke alert to test logs"),
        ]
    },
    "welcome": {
        "label": "👋 Welcome & Autorole",
        "color": discord.Color.green(),
        "commands": [
            ("!setwelcome set #ch <msg>",     "Set welcome channel and message"),
            ("!setwelcome disable",           "Disable welcome messages"),
            ("!setwelcome test",              "Send a test welcome message"),
            ("!setwelcome status",            "View welcome config"),
            ("!autorole set @role",           "Auto-assign role to new members"),
            ("!autorole disable",             "Disable autorole"),
            ("!autorole status",              "View autorole config"),
        ]
    },
    "snipe": {
        "label": "🔍 Snipe",
        "color": discord.Color.blurple(),
        "commands": [
            ("!snipe",      "Show last deleted message in this channel"),
            ("!editsnipe",  "Show last edited message (before & after)"),
        ]
    },
    "fun": {
        "label": "🎉 Fun",
        "color": discord.Color.purple(),
        "commands": [
            ("!8ball <question>",   "Ask the magic 8ball"),
            ("!coinflip",           "Flip a coin"),
            ("!roll [sides]",       "Roll a dice"),
            ("!rps <choice>",       "Rock paper scissors"),
            ("!pp [@user]",         "PP size checker"),
            ("!rate <thing>",       "Rate anything out of 10"),
            ("!ship @u1 @u2",       "Ship two people"),
            ("!truth",              "Random truth question"),
            ("!dare",               "Random dare"),
            ("!wyr",                "Would you rather"),
            ("!poll <question>",    "Create a yes/no poll"),
            ("!joke",               "Random joke"),
            ("!choose a | b | c",   "Pick from options"),
            ("!kiss [@user]",       "Kiss someone"),
            ("!hug [@user]",        "Hug someone"),
            ("!slap [@user]",       "Slap someone"),
            ("!cuddle [@user]",     "Cuddle someone"),
            ("!kill [@user]",       "Kill someone"),
        ]
    },
    "info": {
        "label": "ℹ️ Info",
        "color": discord.Color.blurple(),
        "commands": [
            ("!userinfo [@user]",   "Info about a user"),
            ("!serverinfo",         "Info about this server"),
            ("!botstatus",          "Bot uptime, ping, memory & stats"),
            ("!help",               "This menu"),
        ]
    },
    "levels": {
        "label": "⭐ Levels & Stats",
        "color": discord.Color.gold(),
        "commands": [
            ("!rank [@user]",               "Your level, XP, stats"),
            ("!stats [@user]",              "Detailed activity stats"),
            ("!leaderboard",               "Top 10 most active members"),
            ("!setlevelchannel #channel",   "Set level up notification channel"),
            ("!setlevelrole <level> @role", "Give role at a certain level"),
            ("!resetxp @user",             "Reset a member's XP (Admin)"),
        ]
    },
    "social": {
        "label": "💘 Social",
        "color": discord.Color.magenta(),
        "commands": [
            ("!marry @user",    "Propose to someone"),
            ("!divorce @user",  "Divorce your partner"),
            ("!afk [reason]",   "Set your AFK status"),
        ]
    },
    "ai": {
        "label": "🤖 AI",
        "color": discord.Color.blurple(),
        "commands": [
            ("!ask <question>",  "Ask the AI anything"),
            ("!roastai @user",   "AI generates a savage roast"),
            ("!storytime",       "AI writes a story with server members"),
        ]
    },
}


def build_category_embed(cat_key: str) -> discord.Embed:
    cat = CATEGORIES[cat_key]
    embed = discord.Embed(
        title=cat["label"],
        color=cat["color"],
        timestamp=discord.utils.utcnow(),
    )
    lines = "\n".join(f"`{cmd}` — {desc}" for cmd, desc in cat["commands"])
    embed.description = lines
    embed.set_footer(text="Death Bot • Prefix: !")
    return embed


def build_home_embed() -> discord.Embed:
    embed = discord.Embed(
        title="💀 Death Bot — Help",
        description="Select a category below to view commands.",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow(),
    )
    for cat in CATEGORIES.values():
        embed.add_field(
            name=cat["label"],
            value=f"{len(cat['commands'])} commands",
            inline=True,
        )
    embed.set_footer(text="Death Bot • Prefix: !")
    return embed


def build_view(current: str = "home") -> discord.ui.View:
    view = discord.ui.View(timeout=120)

    # Home button
    home_btn = discord.ui.Button(
        label="Home",
        emoji="🏠",
        style=discord.ButtonStyle.danger if current == "home" else discord.ButtonStyle.secondary,
        custom_id="help_home",
        row=0,
    )
    view.add_item(home_btn)

    # Category buttons
    styles = {
        "antiraid":   (discord.ButtonStyle.danger,    "🛡️", 0),
        "moderation": (discord.ButtonStyle.danger,    "🔨", 0),
        "antinuke":   (discord.ButtonStyle.danger,    "🚨", 1),
        "welcome":    (discord.ButtonStyle.success,   "👋", 1),
        "snipe":      (discord.ButtonStyle.primary,   "🔍", 1),
        "fun":        (discord.ButtonStyle.primary,   "🎉", 2),
        "info":       (discord.ButtonStyle.secondary, "ℹ️", 2),
        "levels":     (discord.ButtonStyle.success,   "⭐", 3),
        "social":     (discord.ButtonStyle.primary,   "💘", 3),
        "ai":         (discord.ButtonStyle.primary,   "🤖", 4),
    }

    for key, (style, emoji, row) in styles.items():
        active = current == key
        btn = discord.ui.Button(
            label=CATEGORIES[key]["label"].split(" ", 1)[1],
            emoji=emoji,
            style=discord.ButtonStyle.danger if active else style,
            custom_id=f"help_{key}",
            row=row,
            disabled=active,
        )
        view.add_item(btn)

    return view


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
        """Show all commands with interactive category buttons."""
        if command_name:
            cmd = self.bot.get_command(command_name)
            if not cmd:
                return await ctx.reply(f"❌ Command `{command_name}` not found.")
            embed = discord.Embed(title=f"!{cmd.qualified_name}",
                description=cmd.help or "No description.", color=discord.Color.blurple())
            embed.add_field(name="Usage", value=f"`!{cmd.qualified_name} {cmd.usage or ''}`".strip())
            return await ctx.reply(embed=embed)

        await ctx.reply(embed=build_home_embed(), view=build_view("home"))

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.data or not str(interaction.data.get("custom_id", "")).startswith("help_"):
            return

        cat_key = interaction.data["custom_id"].replace("help_", "")

        if cat_key == "home":
            await interaction.response.edit_message(embed=build_home_embed(), view=build_view("home"))
        elif cat_key in CATEGORIES:
            await interaction.response.edit_message(embed=build_category_embed(cat_key), view=build_view(cat_key))


async def setup(bot):
    await bot.add_cog(Info(bot))
