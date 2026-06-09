import discord
from discord.ext import commands
import re
import random
import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

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

    # ─── Dynamic PIL Image Rendering Engine ──────────────────────────────────
    async def generate_quote_card(self, background_url: str, text: str, author_name: str) -> io.BytesIO:
        """Downloads a background image, applies a dark overlay, draws centered text + bottom-right signature, and returns it."""
        async with aiohttp.ClientSession() as session:
            async with session.get(background_url) as resp:
                if resp.status != 200:
                    raise Exception("Failed to download quote background image.")
                image_bytes = await resp.read()

        # Open image using Pillow
        base_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        
        # Standardize canvas size to make text layout predictable
        canvas_width, canvas_height = 800, 500
        base_image = base_image.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
        
        # Apply a subtle semi-transparent dark overlay to make white text highly readable
        overlay = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 110)) # ~43% opacity black
        final_image = Image.alpha_composite(base_image, overlay)
        
        draw = ImageDraw.Draw(final_image)
        
        # Font Configuration - Try to load system fonts, fallback to default
        try:
            # Standard Linux/Unix/Mac sans-serif fonts
            main_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 34)
            sig_font = ImageFont.truetype("DejaVuSans.ttf", 22)
        except IOError:
            try:
                # Standard Windows sans-serif fonts
                main_font = ImageFont.truetype("arial.ttf", 34)
                sig_font = ImageFont.truetype("arial.ttf", 22)
            except IOError:
                # Safe fallback
                main_font = ImageFont.load_default()
                sig_font = ImageFont.load_default()

        # 1. Format and Center the Quoted Message Text
        wrapped_lines = []
        max_chars_per_line = 36
        words = text.split()
        
        current_line = []
        for word in words:
            if len(" ".join(current_line + [word])) <= max_chars_per_line:
                current_line.append(word)
            else:
                wrapped_lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            wrapped_lines.append(" ".join(current_line))

        # Handle drawing multi-line centered text
        line_height = 42
        total_text_height = len(wrapped_lines) * line_height
        start_y = (canvas_height - total_text_height) // 2 - 20
        
        for i, line in enumerate(wrapped_lines):
            try:
                # Modern Pillow text bbox calculations
                left, top, right, bottom = draw.textbbox((0, 0), line, font=main_font)
                text_width = right - left
            except AttributeError:
                # Fallback for old Pillow versions
                text_width = draw.textsize(line, font=main_font)[0]
                
            x_pos = (canvas_width - text_width) // 2
            y_pos = start_y + (i * line_height)
            
            # Subtle drop shadow for perfect visibility
            draw.text((x_pos + 2, y_pos + 2), line, fill=(0, 0, 0, 200), font=main_font)
            draw.text((x_pos, y_pos), line, fill=(255, 255, 255, 255), font=main_font)

        # 2. Format and Draw Signature in bottom-right corner
        signature = f"- {author_name.lower()} :3"
        try:
            left, top, right, bottom = draw.textbbox((0, 0), signature, font=sig_font)
            sig_width = right - left
            sig_height = bottom - top
        except AttributeError:
            sig_width, sig_height = draw.textsize(signature, font=sig_font)

        # 30px padding from right and bottom edges
        sig_x = canvas_width - sig_width - 45
        sig_y = canvas_height - sig_height - 45
        
        # Subtle drop shadow for signature
        draw.text((sig_x + 1, sig_y + 1), signature, fill=(0, 0, 0, 200), font=sig_font)
        draw.text((sig_x, sig_y), signature, fill=(240, 240, 240, 255), font=sig_font)

        # Save resulting image to memory
        output = io.BytesIO()
        final_image.convert("RGB").save(output, format="JPEG", quality=90)
        output.seek(0)
        return output

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

        async with ctx.typing():
            # Choose a random background scenery image
            bg_url = random.choice(self.scenery_pool)
            
            try:
                # Generate custom image containing the quote text and signature
                image_data = await self.generate_quote_card(
                    background_url=bg_url,
                    text=message.content or "*(No text content)*",
                    author_name=message.author.display_name
                )
                
                # Delete command call trigger safely to keep chat clean
                try:
                    await ctx.message.delete()
                except discord.Forbidden:
                    pass

                # Upload directly as a file attachment—meaning NO visible links!
                await ctx.send(file=discord.File(fp=image_data, filename="quote.jpg"))
                
            except Exception as e:
                await ctx.reply(f"❌ **An error occurred generating the image:** `{e}`")

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
                        
                        async with message.channel.typing():
                            bg_url = random.choice(self.scenery_pool)
                            image_data = await self.generate_quote_card(
                                background_url=bg_url,
                                text=quoted_msg.content or "*(No text content)*",
                                author_name=quoted_msg.author.display_name
                            )
                            await message.channel.send(file=discord.File(fp=image_data, filename="quote.jpg"))
                    except (discord.NotFound, discord.Forbidden):
                        pass

async def setup(bot):
    await bot.add_cog(Quote(bot))
