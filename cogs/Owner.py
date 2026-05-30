import discord
from discord.ext import commands
import random

OWNER_ID = 1446215395358015559
AUTOREACT_USERS = {1446215395358015559, 1430807402688548876}  # owner + extra user

def is_owner():
    async def predicate(ctx):
        if ctx.author.id != OWNER_ID:
            await ctx.reply("❌ This command is restricted to the bot owner.")
            return False
        return True
    return commands.check(predicate)

def is_autoreact_user():
    async def predicate(ctx):
        if ctx.author.id not in AUTOREACT_USERS:
            await ctx.reply("❌ You don't have permission to use this command.")
            return False
        return True
    return commands.check(predicate)

def uwuify(text: str) -> str:
    text = text.replace('r', 'w').replace('R', 'W').replace('l', 'w').replace('L', 'W')
    text = text.replace('no', 'nyo').replace('No', 'Nyo').replace('NO', 'NYO')
    text = text.replace('you', 'chu').replace('You', 'Chu')
    text = text.replace('the', 'da').replace('The', 'Da')
    endings = [' uwu', ' owo', ' >w<', ' :3', ' ~', ' nya~', '']
    if text and text[-1] in '.!?':
        text = text[:-1] + random.choice(endings)
    return text


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'autoreact_channels'): bot.autoreact_channels = set()
        if not hasattr(bot, 'echo_channels'):      bot.echo_channels = set()
        if not hasattr(bot, 'uwu_channels'):       bot.uwu_channels = set()

    # ─── !say ─────────────────────────────────────────────────────────────────
    @commands.command(name="say", usage="[#channel] <message>")
    @is_owner()
    async def say(self, ctx, channel: discord.TextChannel = None, *, message: str):
        """Make the bot send a message in a channel."""
        await ctx.message.delete()
        await (channel or ctx.channel).send(message)

    # ─── !announce ────────────────────────────────────────────────────────────
    @commands.command(name="announce", usage="<#channel> <message>")
    @is_owner()
    async def announce(self, ctx, channel: discord.TextChannel, *, message: str):
        """Send an announcement embed to any channel."""
        embed = discord.Embed(description=message, color=discord.Color.red(), timestamp=discord.utils.utcnow())
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.set_footer(text="Announcement")
        await channel.send(embed=embed)
        await ctx.message.delete()

    # ─── !setgame ─────────────────────────────────────────────────────────────
    @commands.command(name="setgame", usage="<watching/playing/listening> <text>")
    @is_owner()
    async def setgame(self, ctx, activity_type: str, *, text: str):
        """Change the bot's status/activity."""
        t = activity_type.lower()
        if t == "playing":       activity = discord.Game(name=text)
        elif t == "watching":    activity = discord.Activity(type=discord.ActivityType.watching,  name=text)
        elif t == "listening":   activity = discord.Activity(type=discord.ActivityType.listening, name=text)
        else: return await ctx.reply("❌ Type must be `playing`, `watching`, or `listening`.")
        await self.bot.change_presence(activity=activity)
        await ctx.reply(embed=discord.Embed(title="✅ Status Updated", description=f"Now **{t}** {text}",
            color=discord.Color.green(), timestamp=discord.utils.utcnow()))

    # ─── !servers ─────────────────────────────────────────────────────────────
    @commands.command(name="servers")
    @is_owner()
    async def servers(self, ctx):
        """See every server the bot is in."""
        lines = "\n".join(f"**{i+1}.** {g.name} — {g.member_count} members (ID: {g.id})"
                          for i, g in enumerate(self.bot.guilds))
        await ctx.reply(embed=discord.Embed(title=f"📡 Servers ({len(self.bot.guilds)})",
            description=lines[:4096] or "No servers.", color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()))

    # ─── !info ────────────────────────────────────────────────────────────────
    @commands.command(name="info")
    @is_owner()
    async def info(self, ctx):
        """Show the bot's website and Discord server."""
        embed = discord.Embed(title="💀 Death Bot",
            description="Discord's premier all-in-one bot for management and engagement.",
            color=discord.Color.red(), timestamp=discord.utils.utcnow())
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
        embed = discord.Embed(title="📈 CRYPTO GO BRRR", color=discord.Color.gold(), timestamp=discord.utils.utcnow())
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
            embed = discord.Embed(title="🔍 User Lookup", color=discord.Color.blurple(), timestamp=discord.utils.utcnow())
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="Username",        value=str(user), inline=True)
            embed.add_field(name="ID",              value=user.id,   inline=True)
            embed.add_field(name="Bot",             value="Yes" if user.bot else "No", inline=True)
            embed.add_field(name="Account Created", value=discord.utils.format_dt(user.created_at, "R"), inline=True)
            embed.add_field(name="Avatar URL",      value=f"[Click here]({user.display_avatar.url})", inline=True)
            await ctx.reply(embed=embed)
        except discord.NotFound:
            await ctx.reply("❌ User not found.")

    # ─── !impersonate ─────────────────────────────────────────────────────────
    @commands.command(name="impersonate", usage="<@user> <message>")
    @is_owner()
    async def impersonate(self, ctx, member: discord.Member, *, message: str):
        """Send a message as a webhook that looks like another user."""
        await ctx.message.delete()
        try:
            wh = await ctx.channel.create_webhook(name=member.display_name)
            await wh.send(content=message, username=member.display_name, avatar_url=member.display_avatar.url)
            await wh.delete()
        except discord.Forbidden:
            await ctx.reply("❌ I need **Manage Webhooks** permission.")

    # ─── !autoreact ───────────────────────────────────────────────────────────
    @commands.command(name="autoreact")
    @is_autoreact_user()
    async def autoreact(self, ctx):
        """Toggle 🐰 auto-react on your messages and one other user's messages in this channel."""
        if ctx.channel.id in self.bot.autoreact_channels:
            self.bot.autoreact_channels.discard(ctx.channel.id)
            await ctx.reply(embed=discord.Embed(title="🐰 Auto-React Disabled",
                description=f"Disabled in {ctx.channel.mention}.", color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()))
        else:
            self.bot.autoreact_channels.add(ctx.channel.id)
            await ctx.reply(embed=discord.Embed(title="🐰 Auto-React Enabled",
                description=f"Reacting 🐰 to messages in {ctx.channel.mention}.",
                color=discord.Color.green(), timestamp=discord.utils.utcnow()))

    # ─── !echo ────────────────────────────────────────────────────────────────
    @commands.command(name="echo")
    @is_owner()
    async def echo(self, ctx):
        """Toggle echo mode — bot repeats everything you say in this channel."""
        if ctx.channel.id in self.bot.echo_channels:
            self.bot.echo_channels.discard(ctx.channel.id)
            await ctx.reply(embed=discord.Embed(title="🔇 Echo Disabled",
                description=f"No longer echoing your messages in {ctx.channel.mention}.",
                color=discord.Color.orange(), timestamp=discord.utils.utcnow()))
        else:
            self.bot.echo_channels.add(ctx.channel.id)
            await ctx.reply(embed=discord.Embed(title="🔊 Echo Enabled",
                description=f"Now echoing your messages in {ctx.channel.mention}.",
                color=discord.Color.green(), timestamp=discord.utils.utcnow()))

    # ─── !bigtext ─────────────────────────────────────────────────────────────
    @commands.command(name="bigtext", usage="<message>")
    @is_owner()
    async def bigtext(self, ctx, *, message: str):
        """Send a message in giant regional indicator letters."""
        await ctx.message.delete()
        lookup = {
            'a':'🇦','b':'🇧','c':'🇨','d':'🇩','e':'🇪','f':'🇫','g':'🇬','h':'🇭',
            'i':'🇮','j':'🇯','k':'🇰','l':'🇱','m':'🇲','n':'🇳','o':'🇴','p':'🇵',
            'q':'🇶','r':'🇷','s':'🇸','t':'🇹','u':'🇺','v':'🇻','w':'🇼','x':'🇽',
            'y':'🇾','z':'🇿',' ':'   ','0':'0️⃣','1':'1️⃣','2':'2️⃣','3':'3️⃣',
            '4':'4️⃣','5':'5️⃣','6':'6️⃣','7':'7️⃣','8':'8️⃣','9':'9️⃣','!':'❗','?':'❓',
        }
        result = ' '.join(lookup.get(c.lower(), c) for c in message)
        await ctx.send(result[:2000])

    # ─── !banner ──────────────────────────────────────────────────────────────
    @commands.command(name="banner", usage="[#channel] <text>")
    @is_owner()
    async def banner(self, ctx, channel: discord.TextChannel = None, *, text: str = ""):
        """Send a decorative banner embed in any channel."""
        await ctx.message.delete()
        target = channel or ctx.channel
        embed = discord.Embed(
            description=f"```\n{'━' * 30}\n   {text.upper()}\n{'━' * 30}\n```",
            color=discord.Color.red(), timestamp=discord.utils.utcnow(),
        )
        await target.send(embed=embed)

    # ─── !uwumode ─────────────────────────────────────────────────────────────
    @commands.command(name="uwumode")
    @is_owner()
    async def uwumode(self, ctx, channel: discord.TextChannel = None):
        """Toggle uwu mode in a channel."""
        target = channel or ctx.channel
        if target.id in self.bot.uwu_channels:
            self.bot.uwu_channels.discard(target.id)
            await ctx.reply(embed=discord.Embed(title="UwU Mode Disabled",
                description=f"UwU mode turned off in {target.mention}.",
                color=discord.Color.orange(), timestamp=discord.utils.utcnow()))
        else:
            self.bot.uwu_channels.add(target.id)
            await ctx.reply(embed=discord.Embed(title="UwU Mode Enabled OwO",
                description=f"UwU mode on in {target.mention}~ evewything is uwu now >w<",
                color=discord.Color.magenta(), timestamp=discord.utils.utcnow()))

    # ─── Listeners ────────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Auto-react — both owner and extra user get 🐰
        if message.author.id in AUTOREACT_USERS and message.channel.id in self.bot.autoreact_channels:
            try:
                await message.add_reaction("🐰")
            except discord.Forbidden:
                pass

        # Echo — owner only
        if message.author.id == OWNER_ID and message.channel.id in self.bot.echo_channels:
            if not message.content.startswith('!'):
                try:
                    await message.channel.send(f"> {message.content}")
                except discord.Forbidden:
                    pass


async def setup(bot):
    await bot.add_cog(Owner(bot))
