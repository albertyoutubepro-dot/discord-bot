import discord
from discord.ext import commands

# ─── Configuration ────────────────────────────────────────────────────────────
# Your actual Discord User ID
OWNER_ID = 1446215395358015559  

# Custom check that only allows you (the owner) to run specific admin commands
def is_suite_owner():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID or await ctx.bot.is_owner(ctx.author)
    return commands.check(predicate)

class AdminSuite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'maintenance_mode'):
            bot.maintenance_mode = False

    # ─── 1. Maintenance Mode (Owner Only) ─────────────────────────────────────
    @commands.command(name="maintenance")
    @is_suite_owner()
    async def toggle_maintenance(self, ctx):
        """Toggles global maintenance mode, restricting bot commands to developers only."""
        self.bot.maintenance_mode = not self.bot.maintenance_mode
        status = "enabled" if self.bot.maintenance_mode else "disabled"
        
        # Update presence to reflect status
        if self.bot.maintenance_mode:
            await self.bot.change_presence(activity=discord.Game(name="🌑 offline"))
        else:
            await self.bot.change_presence(activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="the server | !help"
            ))
            
        await ctx.reply(f"🌑 **system status changed to {status}.**")

    # ─── 2. Public Commands (Anyone Can Use!) ─────────────────────────────────
    @commands.command(name="socials", aliases=["links", "developer"])
    async def show_socials(self, ctx):
        """Displays the developer's social media links in a fancy, highly styled embed."""
        embed = discord.Embed(
            title="💀 **death**",
            description="*socials & links. tap in below.*",
            color=discord.Color.from_rgb(17, 2, 33) # Deep velvet dark purple/almost black
        )
        
        # Minimalist, clean fields without robotic template descriptions
        embed.add_field(
            name="🌑 **server**", 
            value="[join up](https://discord.gg/kmGn5bh8Kf)", 
            inline=False
        )
        embed.add_field(
            name="⛓️ **tiktok**", 
            value="[@userovcnavdryh](https://www.tiktok.com/@userovcnavdryh)", 
            inline=True
        )
        embed.add_field(
            name="🔮 **instagram**", 
            value="[@ihateloveloloxd](https://www.instagram.com/ihateloveloloxd/)", 
            inline=True
        )
        embed.add_field(
            name="📄 **guns.lol**", 
            value="[guns.lol/6syj](https://guns.lol/6syj)", 
            inline=False
        )
        
        # Add the bot's avatar as a thumbnail if it exists
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            
        embed.set_footer(
            text="made by 6syj", 
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(AdminSuite(bot))

    # Global check to enforce maintenance mode if enabled
    @bot.check
    async def check_maintenance(ctx):
        if getattr(bot, 'maintenance_mode', False):
            is_owner = ctx.author.id == OWNER_ID or await bot.is_owner(ctx.author)
            if not is_owner:
                await ctx.reply("🌑 **the system is currently undergoing deep maintenance. check back later.**")
                return False
        return True
