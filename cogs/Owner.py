import discord
from discord.ext import commands
import random

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
        if not hasattr(bot, 'autoreact_channels'):
            bot.autoreact_channels = set()

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
        embed.add_field(name="🌐 Website",        value="[deathhh.netlify.app](https://deathhh.netlify.app/)", inline=True)
        embed.add_field(name="💬 Discord Server", value="[Join here](https://discord.gg/kmGn5bh8Kf)",          inline=True)
        embed.add_field(name="➕ Add Bot",         value="[Invite Death](https://discord.com/oauth2/authorize?client_id=1510024097269153843&permissions=8&integration_type=0&scope=bot)", inline=True)
        embed.set_footer(text="Death Bot — Est. 2026")
        await ctx.reply(embed=embed)

    # ─── !crypto ──────────────────────────────────────────────────────────────
    @commands.command(name="crypto")
    async def crypto(self, ctx):
        """Sends a random crypto meme gif."""
        gifs = [
            "https://media0.giphy.com/media/JtcYnMRbgCdbNjbJMT/giphy.gif",
            "https://media2.giphy.com/media/26n6WywJyh39n1pBu/giphy.gif",
            "https://media1.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif",
            "https://media3.giphy.com/media/3o7TKSha51ATTx9KzC/giphy.gif",
            "https://media0.giphy.com/media/Qss6PkjFMLd3n89kk7/giphy.gif",
        ]
        embed = discord.Embed(
            title="📈 CRYPTO GO BRRR",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_image(url=random.choice(gifs))
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.reply(embed=embed)

    # ─── !lookup ──────────────────────────────────────────────────────────────
    @commands.command(name="lookup", usage="<user_id>")
    @is_owner()
    async def lookup(self, ctx, user_id: int):
        """Get info on any Discord user by ID."""
        try:
            user = await self.bot.fetch_user(user_id)
            embed = discord.Embed(
                title="🔍 User Lookup",
                color=discord.Color.blurple(),
                timestamp=discord.utils.utcnow(),
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="Username",       value=str(user),  inline=True)
            embed.add_field(name="ID",             value=user.id,    inline=True)
            embed.add_field(name="Bot",            value="Yes" if user.bot else "No", inline=True)
            embed.add_field(name="Account Created", value=discord.utils.format_dt(user.created_at, "R"), inline=True)
            embed.add_field(name="Avatar URL",     value=f"[Click here]({user.display_avatar.url})", inline=True)
            await ctx.reply(embed=embed)
        except discord.NotFound:
            await ctx.reply("❌ User not found. Make sure the ID is correct.")

    # ─── !impersonate ─────────────────────────────────────────────────────────
    @commands.command(name="impersonate", usage="<@user> <message>")
    @is_owner()
    async def impersonate(self, ctx, member: discord.Member, *, message: str):
        """Send a message as a webhook that looks like another user."""
        await ctx.message.delete()
        try:
            webhook = await ctx.channel.create_webhook(name=member.display_name)
            await webhook.send(
                content=message,
                username=member.display_name,
                avatar_url=member.display_avatar.url,
            )
            await webhook.delete()
        except discord.Forbidden:
            await ctx.reply("❌ I need **Manage Webhooks** permission to do that.")

    # ─── !autoreact ───────────────────────────────────────────────────────────
    @commands.command(name="autoreact")
    @is_owner()
    async def autoreact(self, ctx):
        """Toggle 🎃 auto-react to your messages in this channel."""
        if ctx.channel.id in self.bot.autoreact_channels:
            self.bot.autoreact_channels.discard(ctx.channel.id)
            await ctx.reply(embed=discord.Embed(
                title="🎃 Auto-React Disabled",
                description=f"No longer reacting to your messages in {ctx.channel.mention}.",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow(),
            ))
        else:
            self.bot.autoreact_channels.add(ctx.channel.id)
            await ctx.reply(embed=discord.Embed(
                title="🎃 Auto-React Enabled",
                description=f"Now reacting 🎃 to your messages in {ctx.channel.mention}.",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow(),
            ))

    # ─── Auto-react listener ──────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.author.id != OWNER_ID:
            return
        if message.channel.id in self.bot.autoreact_channels:
            try:
                await message.add_reaction("🎃")
            except discord.Forbidden:
                pass


async def setup(bot):
    await bot.add_cog(Owner(bot))
