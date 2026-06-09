import discord
from discord.ext import commands
import re

class Quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Regex pattern to match standard Discord message links
        self.msg_link_pattern = re.compile(
            r'https://(?:ptb\.|canary\.)?discord\.com/channels/(\d+)/(\d+)/(\d+)'
        )

    # ─── Helper to Build Quote Embed ──────────────────────────────────────────
    def build_quote_embed(self, message: discord.Message, quoted_by: discord.Member) -> discord.Embed:
        """Compiles a premium dark velvet quote layout."""
        embed = discord.Embed(
            description=message.content or "*(No text content)*",
            color=discord.Color.from_rgb(17, 2, 33), # Deep dark velvet purple
            timestamp=message.created_at
        )
        
        # Set author info to the person who originally sent the message
        embed.set_author(
            name=message.author.display_name, 
            icon_url=message.author.display_avatar.url
        )
        
        # Add system details about context
        embed.set_footer(
            text=f"Quoted by {quoted_by.display_name} • Sent in #{message.channel.name}",
            icon_url=quoted_by.display_avatar.url
        )

        # Handle attachment images if present
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    embed.set_image(url=attachment.url)
                    break
                    
        return embed

    # ─── Command: !quote ──────────────────────────────────────────────────────
    @commands.command(name="quote", aliases=["q"])
    async def quote_message(self, ctx, message_id: int = None, channel: discord.TextChannel = None):
        """Quotes a message. Reply to a message with '!q', or type '!q <message_id>'."""
        target_channel = channel or ctx.channel
        
        # ─── If no ID is passed, check if the user is replying to a message ───
        if message_id is None:
            if ctx.message.reference and ctx.message.reference.message_id:
                message_id = ctx.message.reference.message_id
                # Pull the channel where the referenced message lives
                if ctx.message.reference.channel_id:
                    target_channel = ctx.guild.get_channel(ctx.message.reference.channel_id) or target_channel
            else:
                return await ctx.reply(
                    "❌ **How to use:**\n"
                    "• **Reply** to someone's message and type `!q`\n"
                    "• Or type `!q <message_id>`"
                )
        
        try:
            message = await target_channel.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.reply("❌ **Message not found.** Make sure the ID is correct and I have access to that channel.")
        except discord.Forbidden:
            return await ctx.reply("❌ **Access Denied.** I don't have permissions to read that channel.")

        embed = self.build_quote_embed(message, ctx.author)
        
        # Delete command call to keep chat super clean
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        await ctx.send(embed=embed)

    # ─── Automatic Link Quote Listener ───────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bot messages
        if message.author.bot or not message.guild:
            return

        # Check if message contains a valid Discord message link
        match = self.msg_link_pattern.search(message.content)
        if match:
            guild_id = int(match.group(1))
            channel_id = int(match.group(2))
            message_id = int(match.group(3))

            # Only quote if it's from the same server
            if guild_id == message.guild.id:
                channel = message.guild.get_channel(channel_id)
                if channel:
                    try:
                        quoted_msg = await channel.fetch_message(message_id)
                        embed = self.build_quote_embed(quoted_msg, message.author)
                        
                        # Send the gorgeous quote card directly
                        await message.channel.send(embed=embed)
                    except (discord.NotFound, discord.Forbidden):
                        pass # Silently pass if permission missing or missing link

async def setup(bot):
    await bot.add_cog(Quote(bot))
