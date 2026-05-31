import discord
from discord.ext import commands
import asyncio

OWNER_ID = 1446215395358015559

def is_owner():
    async def predicate(ctx):
        if ctx.author.id != OWNER_ID:
            return False
        return True
    return commands.check(predicate)


class GodMode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'bot_banned'):
            bot.bot_banned = set()  # user_ids banned from using the bot

    # ─── !ownerhelp ───────────────────────────────────────────────────────────
    @commands.command(name="ownerhelp")
    @is_owner()
    async def ownerhelp(self, ctx):
        """Secret owner command list. Deletes after 30 seconds."""
        await ctx.message.delete()
        embed = discord.Embed(
            title="👑 Owner Commands",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="📢 Messaging", inline=False, value="\n".join([
            "`!say [#channel] <msg>` — Make bot say something",
            "`!announce #channel <msg>` — Send announcement embed",
            "`!globalannounce <msg>` — Announce to every server",
            "`!dm <user_id> <msg>` — DM anyone on any server",
            "`!impersonate @user <msg>` — Speak as another user",
            "`!bigtext <msg>` — Send in giant emoji letters",
            "`!banner [#channel] <text>` — Send decorative banner",
        ]))
        embed.add_field(name="🌐 Cross-Server", inline=False, value="\n".join([
            "`!globalban <user_id> [reason]` — Ban from all servers",
            "`!globalkick <user_id> [reason]` — Kick from all servers",
            "`!blacklist <user_id>` — Block user from all servers",
            "`!botban <user_id>` — Ban from using bot entirely",
            "`!botunban <user_id>` — Remove bot ban",
            "`!leave <server_id>` — Make bot leave a server",
            "`!finduser <user_id>` — Find what servers user is in",
            "`!forcenick <server_id> <user_id> <nick>` — Change nick anywhere",
        ]))
        embed.add_field(name="📊 Bot Info", inline=False, value="\n".join([
            "`!servers` — List all servers bot is in",
            "`!botstats` — Detailed stats on all servers",
            "`!lookup <user_id>` — Get info on any user",
            "`!botstatus` — Uptime, ping, memory",
            "`!info` — Bot website and links",
        ]))
        embed.add_field(name="🎭 Fun/Troll", inline=False, value="\n".join([
            "`!fakeban @user [reason]` — Fake ban message",
            "`!copycat @user` — Mimic user for 60s",
            "`!uwumode [#channel]` — Toggle uwu mode",
            "`!echo` — Toggle echo mode",
            "`!autoreact` — Toggle 🐰 autoreact",
            "`!bunny` — Random bunny gif",
        ]))
        embed.add_field(name="⚡ Power Tools", inline=False, value="\n".join([
            "`!freeze [#channel]` — Freeze a channel",
            "`!unfreeze [#channel]` — Unfreeze a channel",
            "`!selfpurge [amount]` — Delete your own messages",
            "`!setgame <type> <text>` — Change bot status",
        ]))
        embed.add_field(name="👑 Flex", inline=False, value="\n".join([
            "`!crown` — Announce your arrival to the server",
            "`!bow` — Make the server bow down",
            "`!royaldecree <message>` — Send a royal decree",
            "`!goat` — Show why you're the GOAT",
            "`!flex` — Flex your owner status",
        ]))
        embed.add_field(name="🤖 ASCII & Special", inline=False, value="\n".join([
            "`!asciibanner <text> [font]` — Generate ASCII art",
            "`!asciibanner fonts` — List all available fonts",
            "`!bunny` — Random bunny gif",
            "`!autoreact` — Toggle 🐰 autoreact",
        ]))
        embed.set_footer(text="This message deletes in 30 seconds.")

        msg = await ctx.send(embed=embed)
        await asyncio.sleep(30)
        await msg.delete()

    # ─── !globalannounce ──────────────────────────────────────────────────────
    @commands.command(name="globalannounce", usage="<message>")
    @is_owner()
    async def globalannounce(self, ctx, *, message: str):
        """Send an announcement to every server the bot is in."""
        success, failed = 0, 0
        for guild in self.bot.guilds:
            channel = discord.utils.find(
                lambda c: isinstance(c, discord.TextChannel) and
                c.permissions_for(guild.me).send_messages,
                sorted(guild.text_channels, key=lambda c: c.position)
            )
            if channel:
                try:
                    embed = discord.Embed(
                        description=message,
                        color=discord.Color.red(),
                        timestamp=discord.utils.utcnow(),
                    )
                    embed.set_author(name="Global Announcement", icon_url=self.bot.user.display_avatar.url)
                    await channel.send(embed=embed)
                    success += 1
                except Exception:
                    failed += 1
            else:
                failed += 1

        await ctx.reply(embed=discord.Embed(
            title="📢 Global Announcement Sent",
            description=f"✅ Sent to **{success}** servers\n❌ Failed in **{failed}** servers",
            color=discord.Color.green(), timestamp=discord.utils.utcnow(),
        ))

    # ─── !globalban ───────────────────────────────────────────────────────────
    @commands.command(name="globalban", usage="<user_id> [reason]")
    @is_owner()
    async def globalban(self, ctx, user_id: int, *, reason: str = "Global ban by bot owner"):
        """Ban a user from every server the bot is in."""
        success, failed = 0, 0
        for guild in self.bot.guilds:
            try:
                await guild.ban(discord.Object(id=user_id), reason=reason)
                success += 1
            except Exception:
                failed += 1

        await ctx.reply(embed=discord.Embed(
            title="🔨 Global Ban",
            color=discord.Color.red(), timestamp=discord.utils.utcnow(),
        ).add_field(name="User ID", value=str(user_id), inline=True
        ).add_field(name="Banned In", value=f"{success} servers", inline=True
        ).add_field(name="Failed", value=f"{failed} servers", inline=True
        ).add_field(name="Reason", value=reason, inline=False))

    # ─── !globalkick ──────────────────────────────────────────────────────────
    @commands.command(name="globalkick", usage="<user_id> [reason]")
    @is_owner()
    async def globalkick(self, ctx, user_id: int, *, reason: str = "Global kick by bot owner"):
        """Kick a user from every server the bot is in."""
        success, failed = 0, 0
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member:
                try:
                    await member.kick(reason=reason)
                    success += 1
                except Exception:
                    failed += 1
            else:
                failed += 1

        await ctx.reply(embed=discord.Embed(
            title="👢 Global Kick",
            color=discord.Color.orange(), timestamp=discord.utils.utcnow(),
        ).add_field(name="User ID", value=str(user_id), inline=True
        ).add_field(name="Kicked From", value=f"{success} servers", inline=True
        ).add_field(name="Failed", value=f"{failed} servers", inline=True))

    # ─── !blacklist ───────────────────────────────────────────────────────────
    @commands.command(name="blacklist", usage="<user_id>")
    @is_owner()
    async def blacklist(self, ctx, user_id: int):
        """Blacklist a user from every server the bot is in (ban + bot ban)."""
        self.bot.bot_banned.add(user_id)
        success, failed = 0, 0
        for guild in self.bot.guilds:
            try:
                await guild.ban(discord.Object(id=user_id), reason="Blacklisted by bot owner")
                success += 1
            except Exception:
                failed += 1

        await ctx.reply(embed=discord.Embed(
            title="⛔ User Blacklisted",
            description=f"User `{user_id}` has been banned from **{success}** servers and blocked from using the bot.",
            color=discord.Color.dark_red(), timestamp=discord.utils.utcnow(),
        ))

    # ─── !botban / !botunban ──────────────────────────────────────────────────
    @commands.command(name="botban", usage="<user_id>")
    @is_owner()
    async def botban(self, ctx, user_id: int):
        """Ban a user from using the bot entirely."""
        self.bot.bot_banned.add(user_id)
        await ctx.reply(embed=discord.Embed(
            title="🚫 Bot Ban",
            description=f"User `{user_id}` can no longer use any bot commands.",
            color=discord.Color.red(), timestamp=discord.utils.utcnow(),
        ))

    @commands.command(name="botunban", usage="<user_id>")
    @is_owner()
    async def botunban(self, ctx, user_id: int):
        """Remove a bot ban."""
        self.bot.bot_banned.discard(user_id)
        await ctx.reply(embed=discord.Embed(
            title="✅ Bot Ban Removed",
            description=f"User `{user_id}` can use the bot again.",
            color=discord.Color.green(), timestamp=discord.utils.utcnow(),
        ))

    # ─── !leave ───────────────────────────────────────────────────────────────
    @commands.command(name="leave", usage="<server_id>")
    @is_owner()
    async def leave(self, ctx, server_id: int):
        """Make the bot leave a specific server."""
        guild = self.bot.get_guild(server_id)
        if not guild:
            return await ctx.reply("❌ Server not found.")
        name = guild.name
        await guild.leave()
        await ctx.reply(embed=discord.Embed(
            title="👋 Left Server",
            description=f"Left **{name}** (`{server_id}`).",
            color=discord.Color.orange(), timestamp=discord.utils.utcnow(),
        ))

    # ─── !finduser ────────────────────────────────────────────────────────────
    @commands.command(name="finduser", usage="<user_id>")
    @is_owner()
    async def finduser(self, ctx, user_id: int):
        """Find what servers a user shares with the bot."""
        found = []
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member:
                found.append(f"**{guild.name}** (`{guild.id}`) — joined {discord.utils.format_dt(member.joined_at, 'R')}")

        if not found:
            return await ctx.reply(f"❌ User `{user_id}` not found in any server.")

        await ctx.reply(embed=discord.Embed(
            title=f"🔍 User Found in {len(found)} Server(s)",
            description="\n".join(found)[:4096],
            color=discord.Color.blurple(), timestamp=discord.utils.utcnow(),
        ))

    # ─── !forcenick ───────────────────────────────────────────────────────────
    @commands.command(name="forcenick", usage="<server_id> <user_id> <nickname>")
    @is_owner()
    async def forcenick(self, ctx, server_id: int, user_id: int, *, nickname: str):
        """Change someone's nickname in any server the bot is in."""
        guild = self.bot.get_guild(server_id)
        if not guild:
            return await ctx.reply("❌ Server not found.")
        member = guild.get_member(user_id)
        if not member:
            return await ctx.reply("❌ Member not found in that server.")
        try:
            await member.edit(nick=nickname)
            await ctx.reply(embed=discord.Embed(
                title="✅ Nickname Changed",
                description=f"Changed **{member}**'s nickname to **{nickname}** in **{guild.name}**.",
                color=discord.Color.green(), timestamp=discord.utils.utcnow(),
            ))
        except discord.Forbidden:
            await ctx.reply("❌ I don't have permission to change that member's nickname.")

    # ─── !botstats ────────────────────────────────────────────────────────────
    @commands.command(name="botstats")
    @is_owner()
    async def botstats(self, ctx):
        """Detailed stats across all servers."""
        total_members = sum(g.member_count for g in self.bot.guilds)
        lines = "\n".join(
            f"**{g.name}** — {g.member_count} members | Owner: <@{g.owner_id}> | ID: `{g.id}`"
            for g in sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)
        )
        embed = discord.Embed(
            title=f"📊 Bot Stats — {len(self.bot.guilds)} Servers",
            description=lines[:4096],
            color=discord.Color.blurple(), timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text=f"Total members across all servers: {total_members}")
        await ctx.reply(embed=embed)

    # ─── Bot ban check ────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.author.id in self.bot.bot_banned:
            ctx = await self.bot.get_context(message)
            if ctx.valid:
                raise commands.CheckFailure("Bot banned")


async def setup(bot):
    await bot.add_cog(GodMode(bot))
