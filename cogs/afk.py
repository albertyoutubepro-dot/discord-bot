import discord
from discord.ext import commands
import time


class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
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
        ).set_footer(text="Send any message to remove AFK"))

    # ─── Listener ─────────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # ── Remove AFK if the user sends any message ──
        if message.author.id in self.bot.afk_users:
            # Ignore the !afk command itself
            if message.content.lower().startswith("!afk"):
                return

            data = self.bot.afk_users.pop(message.author.id)
            duration = int(time.time() - data["timestamp"])
            hrs, remainder = divmod(duration, 3600)
            mins, secs = divmod(remainder, 60)

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
            return  # Don't check mentions if they just came back

        # ── Notify if a mentioned user is AFK ──
        if message.mentions:
            notified = set()  # avoid double notifying same user
            for mentioned in message.mentions:
                if mentioned.id in notified:
                    continue
                if mentioned.id in self.bot.afk_users and mentioned.id != message.author.id:
                    notified.add(mentioned.id)
                    data = self.bot.afk_users[mentioned.id]
                    duration = int(time.time() - data["timestamp"])
                    hrs, remainder = divmod(duration, 3600)
                    mins, secs = divmod(remainder, 60)

                    if hrs > 0:
                        dur_str = f"{hrs}h {mins}m {secs}s"
                    elif mins > 0:
                        dur_str = f"{mins}m {secs}s"
                    else:
                        dur_str = f"{secs}s"

                    try:
                        await message.reply(embed=discord.Embed(
                            title="💤 User is AFK",
                            description=f"**{mentioned.display_name}** is AFK: **{data['reason']}**\n*Been AFK for {dur_str}*",
                            color=discord.Color.light_gray(),
                            timestamp=discord.utils.utcnow(),
                        ), delete_after=10)
                    except discord.Forbidden:
                        pass


async def setup(bot):
    await bot.add_cog(AFK(bot))
