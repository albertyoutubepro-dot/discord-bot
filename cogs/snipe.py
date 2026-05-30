import discord
from discord.ext import commands
import time


class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ─── !snipe ───────────────────────────────────────────────────────────────
    @commands.command(name="snipe", usage="")
    async def snipe(self, ctx):
        """Show the last deleted message in this channel."""
        cached = self.bot.snipe_cache.get(ctx.channel.id)

        if not cached:
            return await ctx.reply("🕳️ Nothing to snipe — no deleted messages cached here.")

        age = int(time.time() - cached["timestamp"])
        author: discord.User = cached["author"]

        embed = discord.Embed(
            title="🗑️ Sniped Message",
            description=cached["content"][:4096],
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(name=str(author), icon_url=author.display_avatar.url)
        embed.set_footer(text=f"Deleted {age}s ago • #{ctx.channel.name}")

        if cached["attachments"]:
            embed.add_field(name="📎 Attachments", value="\n".join(cached["attachments"][:5]))
            embed.set_image(url=cached["attachments"][0])

        await ctx.reply(embed=embed)

    # ─── !editsnipe ───────────────────────────────────────────────────────────
    @commands.command(name="editsnipe", usage="")
    async def editsnipe(self, ctx):
        """Show the last edited message in this channel."""
        cached = self.bot.editsnipe_cache.get(ctx.channel.id)

        if not cached:
            return await ctx.reply("🕳️ Nothing to editsnipe — no edited messages cached here.")

        age = int(time.time() - cached["timestamp"])
        author: discord.User = cached["author"]

        embed = discord.Embed(
            title="✏️ Edit Sniped Message",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(name=str(author), icon_url=author.display_avatar.url)
        embed.add_field(name="Before", value=cached["before"][:1024], inline=False)
        embed.add_field(name="After",  value=cached["after"][:1024],  inline=False)
        embed.set_footer(text=f"Edited {age}s ago • #{ctx.channel.name}")

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Snipe(bot))
