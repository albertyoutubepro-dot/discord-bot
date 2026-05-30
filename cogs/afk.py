import discord
from discord.ext import commands
import time


class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # afk_users: { user_id: { "reason": str, "timestamp": float, "guild_id": int } }
        if not hasattr(bot, 'afk_users'):
            bot.afk_users = {}

    # ─── !afk ─────────────────────────────────────────────────────────────────
    @commands.command(name="afk", usage="[reason]")
    async def afk(self, ctx, *, reason: str = "AFK"):
        """Set your AFK status. Anyone who pings you will be notified."""
        self.bot.afk_users[ctx.author.id] = {
            "reason": reason,
            "timestamp": time.time(),
            "guild_id": ctx.guild.id,
        }

        # Try to add [AFK] to nickname
        try:
            if not ctx.author.display_name.startswith("[AFK]"):
                await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}"[:32])
        except discord.Forbidden:
            pass

        await ctx.reply(embed=discord.Embed(
            title="💤 AFK Set",
            description=f"You are now AFK: **{reason}**\nI'll notify anyone who pings you.",
            color=discord.Color.light_gray(),
            timestamp=discord.utils.utcnow(),
        ).set_footer(text="You will be removed from AFK when you send a message"))

    # ─── Listener: notify on ping, remove AFK on message ─────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Remove AFK if the user sends a message
        if message.author.id in self.bot.afk_users:
            data = self.bot.afk_users.pop(message.author.id)
            duration = int(time.time() - data["timestamp"])
            mins, secs = divmod(duration, 60)
            hrs, mins = divmod(mins, 60)

            if hrs > 0:
                dur_str = f"{hrs}h {mins}m {secs}s"
            elif mins > 0:
                dur_str = f"{mins}m {secs}s"
            else:
                dur_str = f"{secs}s"

            # Remove [AFK] from nickname
            try:
                if message.author.display_name.startswith("[AFK] "):
                    original = message.author.display_name[6:]
                    await message.author.edit(nick=original if original != message.author.name else None)
            except discord.Forbidden:
                pass

            try:
                await message.reply(embed=discord.Embed(
                    title="✅ Welcome Back!",
                    description=f"Your AFK has been removed. You were AFK for **{dur_str}**.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow(),
                ), delete_after=5)
            except discord.Forbidden:
                pass
            return

        # Notify if a pinged user is AFK
        if message.mentions:
            for mentioned in message.mentions:
                if mentioned.id in self.bot.afk_users and mentioned.id != message.author.id:
                    data = self.bot.afk_users[mentioned.id]
                    duration = int(time.time() - data["timestamp"])
                    mins, secs = divmod(duration, 60)
                    hrs, mins = divmod(mins, 60)

                    if hrs > 0:
                        dur_str = f"{hrs}h {mins}m {secs}s"
                    elif mins > 0:
                        dur_str = f"{mins}m {secs}s"
                    else:
                        dur_str = f"{secs}s"

                    await message.reply(embed=discord.Embed(
                        title="💤 User is AFK",
                        description=f"**{mentioned.display_name}** is AFK: **{data['reason']}**\n*Been AFK for {dur_str}*",
                        color=discord.Color.light_gray(),
                        timestamp=discord.utils.utcnow(),
                    ), delete_after=10)


async def setup(bot):
    await bot.add_cog(AFK(bot))
