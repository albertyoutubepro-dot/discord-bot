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

    # ─── Helper to Build Sleek Bleed/Greed Style Text ──────────────────────────
    def build_quote_text(self, message: discord.Message) -> str:
        """Compiles a clean, text-only quote matching the Bleed/Greed style."""
        # Convert message timestamp to a relative Discord timestamp
        unix_time = int(message.created_at.timestamp())
        time_tag = f"<t:{unix_time}:R>"
        
        # Bleed/Greed clean header format: **Username** in #channel (timestamp)
        header = f"**{message.author.display_name}** in {message.channel.mention} ({time_tag})"
        
        # Blockquote the original message content safely
        content = message.content or ""
        if content:
            # Ensure every single line of a multiline message is blockquoted correctly
            blockquote_content = "\n".join(f"> {line}" for line in content.split("\n"))
        else:
            blockquote_content = "> *(No text content)*"
            
        # Combine the header and blockquoted message
        quote_msg = f"{header}\n{blockquote_content}"
        
        # Let attachments render natively by appending the URL at the bottom
        if message.attachments:
            attachment_urls = "\n".join(attachment.url for attachment in message.attachments)
            quote_msg += f"\n{attachment_urls}"
            
        return quote_msg

    # ─── Command: !quote ──────────────────────────────────────────────────────
    @commands.command(name="quote", aliases=["q"])
    async def quote_message(self, ctx, message_id: int = None, channel: discord.TextChannel = None):
        """Quotes a message. Reply to a message with '!q', or type '!q <message_id>'."""
        target_channel = channel or ctx.channel
        
        # ─── Reply Handling ───
        if message_id is None:
            if ctx.message.reference and ctx.message.reference.message_id:
                message_id = ctx.message.reference.message_id
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

        # Build the clean text quote
        quote_content = self.build_quote_text(message)
        
        # Delete the trigger command (like !q) to make it look completely seamless
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        await ctx.send(quote_content)

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
                        quote_content = self.build_quote_text(quoted_msg)
                        
                        # Send the clean quote text directly
                        await message.channel.send(quote_content)
                    except (discord.NotFound, discord.Forbidden):
                        pass # Silently ignore errors

async def setup(bot):
    await bot.add_cog(Quote(bot))
