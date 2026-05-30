import discord
from discord.ext import commands

OWNER_ID = 1446215395358015559

def is_owner():
    async def predicate(ctx):
        if ctx.author.id != OWNER_ID:
            await ctx.reply("❌ This command is restricted to the bot owner.")
            return False
        return True
    return commands.check(predicate)


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ─── !say ─────────────────────────────────────────────────────────────────
    @commands.command(name="say", usage="[#channel] <message>")
    @is_owner()
    async def say(self, ctx, channel: discord.TextChannel = None, *, message: str):
        """Make the bot send a message in a channel."""
        target = channel or ctx.channel
        await ctx.message.delete()
        await target.send(message)

    # ─── !announce ────────────────────────────────────────────────────────────
    @commands.command(name="announce", usage="<#channel> <message>")
    @is_owner()
    async def announce(self, ctx, channel: discord.TextChannel, *, message: str):
        """Send an announcement embed to any channel."""
        embed = discord.Embed(
            description=message,
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.set_footer(text="Announcement")
        await channel.send(embed=embed)
        await ctx.message.delete()

    # ─── !setgame ─────────────────────────────────────────────────────────────
    @commands.command(name="setgame", usage="<watching/playing/listening> <text>")
    @is_owner()
    async def setgame(self, ctx, activity_type: str, *, text: str):
        """Change the bot's status/activity."""
        activity_type = activity_type.lower()
        if activity_type == "playing":
            activity = discord.Game(name=text)
        elif activity_type == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=text)
        elif activity_type == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=text)
        else:
            return await ctx.reply("❌ Type must be `playing`, `watching`, or `listening`.")

        await self.bot.change_presence(activity=activity)
        await ctx.reply(embed=discord.Embed(
            title="✅ Status Updated",
            description=f"Now **{activity_type}** {text}",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        ))

    # ─── !servers ─────────────────────────────────────────────────────────────
    @commands.command(name="servers")
    @is_owner()
    async def servers(self, ctx):
        """See every server the bot is in."""
        guilds = self.bot.guilds
        lines = "\n".join(
            f"**{i+1}.** {g.name} — {g.member_count} members (ID: {g.id})"
            for i, g in enumerate(guilds)
        )
        embed = discord.Embed(
            title=f"📡 Servers ({len(guilds)})",
            description=lines[:4096] or "No servers.",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        await ctx.reply(embed=embed)

    # ─── !info ────────────────────────────────────────────────────────────────
    @commands.command(name="info")
    @is_owner()
    async def info(self, ctx):
        """Show the bot's website and Discord server."""
        embed = discord.Embed(
            title="💀 Death Bot",
            description="Discord's premier all-in-one bot for management and engagement.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="🌐 Website",       value="[deathhh.netlify.app](https://deathhh.netlify.app/)",  inline=True)
        embed.add_field(name="💬 Discord Server", value="[Join here](https://discord.gg/kmGn5bh8Kf)",           inline=True)
        embed.add_field(name="➕ Add Bot",        value="[Invite Death](https://discord.com/oauth2/authorize?client_id=1510024097269153843&permissions=8&integration_type=0&scope=bot)", inline=True)
        embed.set_footer(text="Death Bot — Est. 2026")
        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Owner(bot))
