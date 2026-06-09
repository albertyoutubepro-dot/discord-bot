import discord
from discord.ext import commands
import re
import random

class Quote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Regex pattern to match standard Discord message links
        self.msg_link_pattern = re.compile(
            r'https://(?:ptb\.|canary\.)?discord\.com/channels/(\d+)/(\d+)/(\d+)'
        )
        
        # A massive pool of 30 aesthetic nature/scenery/waterfall links to minimize repeats
        self.scenery_pool = [
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80",  # Yosemite Valley
            "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=800&q=80",  # Foggy green hills
            "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?auto=format&fit=crop&w=800&q=80",  # Enchanted forest path
            "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=800&q=80",  # Forest sunbeams
            "https://images.unsplash.com/photo-1501854140801-50d01698950b?auto=format&fit=crop&w=800&q=80",  # Green valley mountains
            "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=800&q=80",  # High mountain peak
            "https://images.unsplash.com/photo-1434725039720-abb26e22cf14?auto=format&fit=crop&w=800&q=80",  # Pristine meadow
            "https://images.unsplash.com/photo-1472214222541-d510753a4707?auto=format&fit=crop&w=800&q=80",  # Sunset lake
            "https://images.unsplash.com/photo-1518173946687-a4c8a383392e?auto=format&fit=crop&w=800&q=80",  # Rainy woods
            "https://images.unsplash.com/photo-1426604966848-d7adac402bff?auto=format&fit=crop&w=800&q=80",  # Clear lake reflection
            "https://images.unsplash.com/photo-1418065460487-3e41a6c84dc5?auto=format&fit=crop&w=800&q=80",  # Misty pine forest
            "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=800&q=80",  # Deep sunset ocean
            "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?auto=format&fit=crop&w=800&q=80",  # Looking up at forest canopy
            "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=800&q=80",  # Warm tree clearing
            "https://images.unsplash.com/photo-1465146344425-f00d5f5c8f07?auto=format&fit=crop&w=800&q=80",  # Wildflower fields
            "https://images.unsplash.com/photo-1510784722466-f2aa9c52fa6c?auto=format&fit=crop&w=800&q=80",  # Golden hour stream
            "https://images.unsplash.com/photo-1513809637208-021202e4e838?auto=format&fit=crop&w=800&q=80",  # Snowy woods
            "https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?auto=format&fit=crop&w=800&q=80",  # Ocean waves at dusk
            "https://images.unsplash.com/photo-1497436072909-60f360e1d4b1?auto=format&fit=crop&w=800&q=80",  # Blue sky lake
            "https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&w=800&q=80",  # Forest floor light
            "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?auto=format&fit=crop&w=800&q=80",  # Snowy peaks
            "https://images.unsplash.com/photo-1475113548554-5a36f1f523d6?auto=format&fit=crop&w=800&q=80",  # Rushing river woods
            "https://images.unsplash.com/photo-1511497584788-876760111969?auto=format&fit=crop&w=800&q=80",  # Dark woodland road
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",  # Tropical beach sunset
            "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?auto=format&fit=crop&w=800&q=80",  # Blooming spring orchard
            "https://images.unsplash.com/photo-1504198453319-5ce911bafcde?auto=format&fit=crop&w=800&q=80",  # Bamboo grove
            "https://images.unsplash.com/photo-1518495973542-4542c06a5843?auto=format&fit=crop&w=800&q=80",  # Leaves sun flare
            "https://i.pinimg.com/originals/fb/96/09/fb9609e7f7b3df82987eb3b60ba94ea6.gif",              # Aesthetic waterfall anime loop 1
            "https://i.pinimg.com/originals/52/63/0e/52630e62a1975b95a896d8b940989f6b.gif",              # Aesthetic nature stream loop 2
            "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3N0aTR6YWV3bW53YmU0ZWhvczFvYmRsZ2NpdWhpZnN5cW5pcnA3diZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oz8xAFtqo0LYIkIwE/giphy.gif" # Scenic waterfall 3
        ]

    # ─── Helper to Build Sleek Bleed/Greed Style Text ──────────────────────────
    def build_quote_text(self, message: discord.Message) -> str:
        """Compiles clean, text-only quote featuring the quote author's custom signature and a random image fallback."""
        # Convert message timestamp to a relative Discord timestamp
        unix_time = int(message.created_at.timestamp())
        time_tag = f"<t:{unix_time}:R>"
        
        # Bleed/Greed header style: **display name first letter** (or clean identifier)
        header = f"**{message.author.display_name[0].lower()}**"
        
        # Blockquote the original message content safely
        content = message.content or ""
        if content:
            blockquote_content = "\n".join(f"> {line}" for line in content.split("\n"))
        else:
            blockquote_content = "> *(No text content)*"
            
        # Dynamically pull the original author's name for the signature line (with ':3' ending, no 'catboy')
        signature_line = f"> \n>  - {message.author.display_name.lower()} :3"
        
        # Combine everything together
        quote_msg = f"{header}\n{blockquote_content}\n{signature_line}"
        
        # If the original message had an image attachment, use that. Otherwise, choose from our 30-image pool
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    quote_msg += f"\n{attachment.url}"
                    return quote_msg
                    
        # Fallback to random aesthetic image to guarantee no boring repeats
        random_image = random.choice(self.scenery_pool)
        quote_msg += f"\n{random_image}"
            
        return quote_msg

    # ─── Command: !quote ──────────────────────────────────────────────────────
    @commands.command(name="quote", aliases=["q"])
    async def quote_message(self, ctx, message_id: int = None, channel: discord.TextChannel = None):
        """Quotes a message. Reply to a message with '!q', or type '!q <message_id>'."""
        target_channel = channel or ctx.channel
        
        # Reply Handling
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

        quote_content = self.build_quote_text(message)
        
        # Delete command call to keep chat clean
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        await ctx.send(quote_content)

    # ─── Automatic Link Quote Listener ───────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        match = self.msg_link_pattern.search(message.content)
        if match:
            guild_id = int(match.group(1))
            channel_id = int(match.group(2))
            message_id = int(match.group(3))

            if guild_id == message.guild.id:
                channel = message.guild.get_channel(channel_id)
                if channel:
                    try:
                        quoted_msg = await channel.fetch_message(message_id)
                        quote_content = self.build_quote_text(quoted_msg)
                        await message.channel.send(quote_content)
                    except (discord.NotFound, discord.Forbidden):
                        pass

async def setup(bot):
    await bot.add_cog(Quote(bot))
