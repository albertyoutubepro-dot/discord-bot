import discord
from discord.ext import commands
import time
import psutil
import os

class BotStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.command(name="botstatus")
    async def botstatus(self, ctx):
        """Show the bot's current status, uptime, and stats."""
        # Uptime
        uptime_seconds = int(time.time() - self.start_time)
        days    = uptime_seconds // 86400
        hours   = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

        # Ping
        ping = round(self.bot.latency * 1000)
        ping_status = "🟢" if ping < 100 else "🟡" if ping < 200 else "🔴"

        # Memory usage
        try:
            process = psutil.Process(os.getpid())
            memory = process.memory_info().rss / 1024 / 1024
            mem_str = f"{memory:.1f} MB"
        except Exception:
            mem_str = "N/A"

        # Stats
        total_members = sum(g.member_count for g in self.bot.guilds)
        total_commands = len(self.bot.commands)

        embed = discord.Embed(
            title="💀 Death Bot — Status",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="🟢 Status",     value="Online",       inline=True)
        embed.add_field(name=f"{ping_status} Ping", value=f"{ping}ms", inline=True)
        embed.add_field(name="⏱️ Uptime",     value=uptime_str,     inline=True)
        embed.add_field(name="🖥️ Memory",     value=mem_str,        inline=True)
        embed.add_field(name="📡 Servers",    value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="👥 Members",    value=str(total_members),        inline=True)
        embed.add_field(name="⌨️ Commands",   value=str(total_commands),       inline=True)
        embed.add_field(name="🐍 Library",    value="discord.py",              inline=True)
        embed.set_footer(text="Death Bot — Est. 2026")

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(BotStatus(bot))
