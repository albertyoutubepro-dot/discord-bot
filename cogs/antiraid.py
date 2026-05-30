import discord
from discord.ext import commands


class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ─── !lockdown ────────────────────────────────────────────────────────────
    @commands.group(name="lockdown", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def lockdown(self, ctx):
        """Manage server lockdown. Subcommands: enable, lift, status"""
        await ctx.reply(
            "Usage: `!lockdown enable` | `!lockdown lift` | `!lockdown status`"
        )

    @lockdown.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def lockdown_enable(self, ctx):
        """Activate lockdown — new members will be auto-kicked."""
        self.bot.raid_data[ctx.guild.id]["lockdown"] = True
        await ctx.reply(embed=discord.Embed(
            title="🔒 Lockdown Enabled",
            description="Server is now in lockdown. New members will be **auto-kicked**.\nUse `!lockdown lift` to disable.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        ).add_field(name="Enabled by", value=str(ctx.author)))

    @lockdown.command(name="lift")
    @commands.has_permissions(administrator=True)
    async def lockdown_lift(self, ctx):
        """Lift lockdown — new members can join normally."""
        self.bot.raid_data[ctx.guild.id]["lockdown"] = False
        self.bot.raid_data[ctx.guild.id]["join_timestamps"] = []
        await ctx.reply(embed=discord.Embed(
            title="✅ Lockdown Lifted",
            description="Server is back to normal. New members can join freely.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        ).add_field(name="Lifted by", value=str(ctx.author)))

    @lockdown.command(name="status")
    @commands.has_permissions(administrator=True)
    async def lockdown_status(self, ctx):
        """Check current lockdown and raid detection status."""
        import time
        data = self.bot.raid_data[ctx.guild.id]
        recent = [t for t in data["join_timestamps"] if time.time() - t < 10]
        active = data["lockdown"]

        embed = discord.Embed(
            title="🛡️ Anti-Raid Status",
            color=discord.Color.red() if active else discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Lockdown Active",         value="🔴 YES" if active else "🟢 NO", inline=True)
        embed.add_field(name="Recent Joins (10s)",      value=str(len(recent)),                inline=True)
        embed.add_field(name="Raid Threshold",          value="5 joins / 10 seconds",          inline=True)
        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(AntiRaid(bot))
