import discord
from discord.ext import commands
import pyfiglet
import random

OWNER_ID = 1446215395358015559

def is_owner():
    async def predicate(ctx):
        if ctx.author.id != OWNER_ID:
            return False
        return True
    return commands.check(predicate)

FONTS = [
    "big", "block", "banner3", "doom", "epic",
    "graffiti", "isometric1", "larry3d", "lean",
    "ogre", "shadow", "slant", "speed", "standard",
    "starwars", "stop", "thin", "univers",
]


class ASCIIBanner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ─── !asciibanner ─────────────────────────────────────────────────────────
    @commands.command(name="asciibanner", usage="<text> [font]", aliases=["ascii"])
    @is_owner()
    async def asciibanner(self, ctx, *, args: str):
        """Generate an ASCII art banner. Owner only.
        Usage: !asciibanner <text> [font]
        Example: !asciibanner Death doom
        Use !asciibanner fonts to see all available fonts."""

        await ctx.message.delete()

        # Check if listing fonts
        if args.strip().lower() == "fonts":
            font_list = "\n".join(f"`{f}`" for f in FONTS)
            embed = discord.Embed(
                title="🔤 Available Fonts",
                description=font_list,
                color=discord.Color.blurple(),
                timestamp=discord.utils.utcnow(),
            )
            msg = await ctx.send(embed=embed)
            import asyncio
            await asyncio.sleep(30)
            await msg.delete()
            return

        # Parse font from last word if it's a known font
        parts = args.rsplit(" ", 1)
        if len(parts) == 2 and parts[1].lower() in FONTS:
            text = parts[0]
            font = parts[1].lower()
        else:
            text = args
            font = random.choice(FONTS)

        # Generate ASCII art
        try:
            result = pyfiglet.figlet_format(text, font=font)
        except pyfiglet.FontNotFound:
            result = pyfiglet.figlet_format(text, font="standard")
            font = "standard"

        # Trim if too long
        if len(result) > 1900:
            result = result[:1900] + "..."

        await ctx.send(f"```\n{result}\n```\n*Font: `{font}`*")


async def setup(bot):
    await bot.add_cog(ASCIIBanner(bot))
