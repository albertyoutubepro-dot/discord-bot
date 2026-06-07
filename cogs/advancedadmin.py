import discord
from discord.ext import commands

# ─── Configuration ────────────────────────────────────────────────────────────
# Your actual Discord User ID
OWNER_ID = 1446215395358015559  

class AdminSuite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'maintenance_mode'):
            bot.maintenance_mode = False

    async def cog_check(self, ctx):
        # Strictly limits these tools to your Discord ID or the official application owner
        return ctx.author.id == OWNER_ID or await self.bot.is_owner(ctx.author)

    # ─── 1. Maintenance Mode ──────────────────────────────────────────────────
    @commands.command(name="maintenance")
    async def toggle_maintenance(self, ctx):
        """Toggles global maintenance mode, restricting bot commands to developers only."""
        self.bot.maintenance_mode = not self.bot.maintenance_mode
        status = "enabled" if self.bot.maintenance_mode else "disabled"
        
        # Update presence to reflect status
        if self.bot.maintenance_mode:
            await self.bot.change_presence(activity=discord.Game(name="⚠️ Maintenance Mode"))
        else:
            await self.bot.change_presence(activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="the server | !help"
            ))
            
        await ctx.reply(f"🔧 **Maintenance mode has been {status}.**")

async def setup(bot):
    await bot.add_cog(AdminSuite(bot))

    # Global check to enforce maintenance mode if enabled
    @bot.check
    async def check_maintenance(ctx):
        if getattr(bot, 'maintenance_mode', False):
            is_owner = ctx.author.id == OWNER_ID or await bot.is_owner(ctx.author)
            if not is_owner:
                await ctx.reply("⚙️ The bot is currently undergoing developer maintenance. Please try again later.")
                return False
        return True
