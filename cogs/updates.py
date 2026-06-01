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


class Changelog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'changelog_channels'):
            bot.changelog_channels = {}

    @property
    def db(self):
        return self.bot.cogs.get("Database")

    # ─── !setchangelog ────────────────────────────────────────────────────────
    @commands.command(name="setchangelog", usage="[#channel]")
    @is_owner()
    async def setchangelog(self, ctx, channel: discord.TextChannel = None):
        """Set the changelog channel. Leave blank to disable."""
        if channel is None:
            self.bot.changelog_channels.pop(ctx.guild.id, None)
            if self.db:
                await self.db.save_changelog_channel(ctx.guild.id, None)
            return await ctx.reply(embed=discord.Embed(
                title="📋 Changelog Disabled",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow(),
            ))
        self.bot.changelog_channels[ctx.guild.id] = channel.id
        if self.db:
            await self.db.save_changelog_channel(ctx.guild.id, channel.id)
        await ctx.reply(embed=discord.Embed(
            title="✅ Changelog Channel Set",
            description=f"Updates will be posted in {channel.mention}.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        ))

    # ─── !update ──────────────────────────────────────────────────────────────
    @commands.command(name="update", usage="<version> <changes>")
    @is_owner()
    async def update(self, ctx, version: str, *, changes: str):
        """Post a changelog update. Separate multiple changes with |
        Example: !update v2.5 Added !flex | Fixed !ban bug | New !crown command"""
        await ctx.message.delete()
        channel_id = self.bot.changelog_channels.get(ctx.guild.id)
        if not channel_id:
            return await ctx.send("❌ No changelog channel set. Use `!setchangelog #channel` first.", delete_after=5)
        channel = ctx.guild.get_channel(channel_id)
        if not channel:
            return await ctx.send("❌ Changelog channel not found.", delete_after=5)

        change_list = [c.strip() for c in changes.split("|") if c.strip()]

        def format_change(change: str) -> str:
            c = change.lower()
            if any(w in c for w in ["add", "new", "+"]):
                return f"✅ {change}"
            elif any(w in c for w in ["fix", "patch", "bug", "repair"]):
                return f"🔧 {change}"
            elif any(w in c for w in ["remove", "delete", "drop", "-"]):
                return f"❌ {change}"
            elif any(w in c for w in ["update", "improve", "upgrade", "enhance"]):
                return f"⬆️ {change}"
            else:
                return f"• {change}"

        formatted = "\n".join(format_change(c) for c in change_list)
        embed = discord.Embed(
            title=f"🔄 Death Bot — Update {version}",
            description=formatted,
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(
            name=f"Update by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )
        embed.set_footer(text=f"Death Bot • Version {version}")
        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Changelog(bot))
