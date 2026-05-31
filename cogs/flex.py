import discord
from discord.ext import commands
import asyncio
import time

OWNER_ID = 1446215395358015559

def is_owner():
    async def predicate(ctx):
        if ctx.author.id != OWNER_ID:
            return False
        return True
    return commands.check(predicate)


class Flex(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ─── !crown ───────────────────────────────────────────────────────────────
    @commands.command(name="crown")
    @is_owner()
    async def crown(self, ctx):
        """Announce your arrival to the entire server. Owner only."""
        await ctx.message.delete()

        embed = discord.Embed(
            title="👑 THE OWNER HAS ARRIVED",
            description=(
                f"**{ctx.author.display_name}** has entered the chat.\n\n"
                "╔══════════════════════════╗\n"
                f"║  👑  **{ctx.author.display_name.upper()}**  👑  ║\n"
                "║   Owner • God • Legend   ║\n"
                "╚══════════════════════════╝\n\n"
                "*Bow down. The king is here.*"
            ),
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="Death Bot • Owner Flex")

        # @ everyone
        await ctx.channel.send("@everyone", embed=embed)

    # ─── !bow ─────────────────────────────────────────────────────────────────
    @commands.command(name="bow")
    @is_owner()
    async def bow(self, ctx):
        """Make the server bow down. Owner only."""
        await ctx.message.delete()

        embed = discord.Embed(
            title="🫅 BOW DOWN",
            description=(
                f"@everyone\n\n"
                f"The owner **{ctx.author.display_name}** has graced us with their presence.\n\n"
                "🙇 🙇 🙇 🙇 🙇 🙇 🙇 🙇\n\n"
                "*Show some respect.*"
            ),
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.channel.send("@everyone", embed=embed)

    # ─── !royaldecree ─────────────────────────────────────────────────────────
    @commands.command(name="royaldecree", usage="<message>")
    @is_owner()
    async def royaldecree(self, ctx, *, message: str):
        """Send a royal decree to the server. Owner only."""
        await ctx.message.delete()

        embed = discord.Embed(
            title="📜 ROYAL DECREE",
            description=(
                "```\n"
                "════════════════════════════\n"
                "     ✦ OFFICIAL DECREE ✦    \n"
                "════════════════════════════\n"
                "```\n"
                f"*By order of **{ctx.author.display_name}**, Owner of {ctx.guild.name}:*\n\n"
                f"**{message}**\n\n"
                "*So it is written. So it shall be done.*\n\n"
                "🔱 ❖ 🔱"
            ),
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text=f"Decreed by {ctx.author.display_name} • {ctx.guild.name}")
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.channel.send("@everyone", embed=embed)

    # ─── !goat ────────────────────────────────────────────────────────────────
    @commands.command(name="goat")
    @is_owner()
    async def goat(self, ctx):
        """Show why you're the GOAT. Owner only."""
        await ctx.message.delete()

        # Get owner's stats
        import aiosqlite
        try:
            async with aiosqlite.connect("death_bot.db") as db:
                async with db.execute(
                    "SELECT xp, messages, vc_minutes FROM levels WHERE user_id=? AND guild_id=?",
                    (ctx.author.id, ctx.guild.id)
                ) as cursor:
                    row = await cursor.fetchone()
                    owner_xp = row[0] if row else 0
                    owner_msgs = row[1] if row else 0
                    owner_vc = row[2] if row else 0

                # Get server averages
                async with db.execute(
                    "SELECT AVG(xp), AVG(messages), AVG(vc_minutes) FROM levels WHERE guild_id=?",
                    (ctx.guild.id,)
                ) as cursor:
                    avg = await cursor.fetchone()
                    avg_xp = int(avg[0]) if avg and avg[0] else 0
                    avg_msgs = int(avg[1]) if avg and avg[1] else 0
                    avg_vc = int(avg[2]) if avg and avg[2] else 0
        except Exception:
            owner_xp, owner_msgs, owner_vc = 0, 0, 0
            avg_xp, avg_msgs, avg_vc = 0, 0, 0

        hours, mins = divmod(owner_vc, 60)
        avg_hours, avg_mins = divmod(avg_vc, 60)

        # Warn count
        key = f"{ctx.author.id}:{ctx.guild.id}"
        warns = len(self.bot.warn_data.get(key, []))

        embed = discord.Embed(
            title=f"🐐 {ctx.author.display_name} — THE GOAT",
            description="*Can't compete. Don't even try.*",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="✨ XP",            value=f"**{owner_xp}** vs server avg {avg_xp}", inline=True)
        embed.add_field(name="💬 Messages",      value=f"**{owner_msgs}** vs server avg {avg_msgs}", inline=True)
        embed.add_field(name="🎙️ VC Time",       value=f"**{hours}h {mins}m** vs server avg {avg_hours}h {avg_mins}m", inline=True)
        embed.add_field(name="⚠️ Warnings",      value=f"**{warns}** (clean)", inline=True)
        embed.add_field(name="📅 In Server Since", value=discord.utils.format_dt(ctx.author.joined_at, "R"), inline=True)
        embed.add_field(name="👑 Status",         value="**Owner • Untouchable**", inline=True)
        embed.set_footer(text="Greatest Of All Time • No contest")
        await ctx.channel.send(embed=embed)

    # ─── !flex ────────────────────────────────────────────────────────────────
    @commands.command(name="flex")
    @is_owner()
    async def flex(self, ctx):
        """Flex your owner status. Owner only."""
        await ctx.message.delete()

        key = f"{ctx.author.id}:{ctx.guild.id}"
        warns = len(self.bot.warn_data.get(key, []))
        roles = [r.mention for r in reversed(ctx.author.roles) if r != ctx.guild.default_role][:8]
        days_in_server = (discord.utils.utcnow() - ctx.author.joined_at).days
        account_age = (discord.utils.utcnow() - ctx.author.created_at).days

        embed = discord.Embed(
            title=f"💪 {ctx.author.display_name} — YOU CAN'T COMPETE",
            description=(
                "```\n"
                "╔═══════════════════════════╗\n"
                "║     OWNER FLEX CARD 💀     ║\n"
                "╚═══════════════════════════╝\n"
                "```"
            ),
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="👑 Rank",           value="**#1 — Owner**",                    inline=True)
        embed.add_field(name="⚠️ Warnings",       value=f"**{warns}** — untouchable",        inline=True)
        embed.add_field(name="📅 Days Here",       value=f"**{days_in_server}** days",        inline=True)
        embed.add_field(name="🗓️ Account Age",    value=f"**{account_age}** days old",       inline=True)
        embed.add_field(name="🔒 Can Be Banned",   value="**No.**",                           inline=True)
        embed.add_field(name="🤝 Can Be Kicked",   value="**Absolutely not.**",               inline=True)
        if roles:
            embed.add_field(name=f"🎭 Roles ({len(roles)})", value=" ".join(roles), inline=False)
        embed.set_footer(text="Sit down. • Death Bot")
        await ctx.channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Flex(bot))
