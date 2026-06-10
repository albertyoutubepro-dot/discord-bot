import discord
from discord.ext import commands
import asyncio

class Sticky(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # In-memory storage: { channel_id: { "text": str, "last_message_id": int } }
        self.sticky_messages = {}
        # Thread locks to prevent duplicate sticky postings during fast chats
        self.locks = {}

    # Check helper: Only administrators can configure sticky messages
    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator or await self.bot.is_owner(ctx.author)

    # ─── !sticky Group Command ────────────────────────────────────────────────
    @commands.group(name="sticky", invoke_without_command=True)
    async def sticky_group(self, ctx):
        """Manage sticky messages in your server channels."""
        embed = discord.Embed(
            title="📌 Sticky Messages Setup",
            description="Sticky messages remain permanently at the bottom of a channel.",
            color=discord.Color.from_rgb(17, 2, 33)
        )
        embed.add_field(name="⚙️ Commands", value=(
            "`!sticky add <message>` — Create a sticky message in this channel\n"
            "`!sticky remove` — Remove the sticky message from this channel\n"
            "`!sticky list` — Show all active sticky messages on this server"
        ), inline=False)
        await ctx.reply(embed=embed)

    @sticky_group.command(name="add")
    async def sticky_add(self, ctx, *, text: str):
        """Add or update a sticky message in the current channel."""
        channel_id = ctx.channel.id
        
        # Check if there was an old sticky we should delete first
        if channel_id in self.sticky_messages:
            old_msg_id = self.sticky_messages[channel_id].get("last_message_id")
            if old_msg_id:
                try:
                    old_msg = await ctx.channel.fetch_message(old_msg_id)
                    await old_msg.delete()
                except Exception:
                    pass

        # Send the fresh sticky message using our clean aesthetic embed styling
        embed = discord.Embed(
            description=text,
            color=discord.Color.from_rgb(17, 2, 33)
        )
        embed.set_footer(text="📌 Sticky Message — Please read carefully")
        
        # Delete trigger command to keep layout clean
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        sticky_msg = await ctx.send(embed=embed)
        
        self.sticky_messages[channel_id] = {
            "text": text,
            "last_message_id": sticky_msg.id
        }
        
        # Send confirmation (deletes after 3 seconds to keep chat clean)
        await ctx.send("✅ **Sticky message set successfully.**", delete_after=3)

    @sticky_group.command(name="remove")
    async def sticky_remove(self, ctx):
        """Removes the sticky message from this channel."""
        channel_id = ctx.channel.id
        if channel_id not in self.sticky_messages:
            return await ctx.reply("❌ **There is no active sticky message in this channel.**", delete_after=5)

        data = self.sticky_messages.pop(channel_id, None)
        if data and data.get("last_message_id"):
            try:
                old_msg = await ctx.channel.fetch_message(data["last_message_id"])
                await old_msg.delete()
            except Exception:
                pass

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
            
        await ctx.send("🗑️ **Sticky message removed.**", delete_after=3)

    @sticky_group.command(name="list")
    async def sticky_list(self, ctx):
        """Lists all active sticky messages configured on the server."""
        active_stickies = []
        for ch_id, data in self.sticky_messages.items():
            channel = ctx.guild.get_channel(ch_id)
            if channel:
                # Truncate content preview safely
                preview = data["text"] if len(data["text"]) <= 40 else f"{data['text'][:37]}..."
                active_stickies.append(f"{channel.mention}: `{preview}`")

        embed = discord.Embed(
            title="📌 Active Sticky Messages",
            description="\n".join(active_stickies) if active_stickies else "No active sticky messages found.",
            color=discord.Color.from_rgb(17, 2, 33)
        )
        await ctx.reply(embed=embed)

    # ─── Event Listener ───────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bots, DMs, or empty messages
        if message.author.bot or not message.guild or not message.content:
            return

        channel_id = message.channel.id
        if channel_id not in self.sticky_messages:
            return

        # Initialize lock for this channel if it doesn't exist
        if channel_id not in self.locks:
            self.locks[channel_id] = asyncio.Lock()

        # Execute using a sequential lock queue to prevent rate limit overrides
        async with self.locks[channel_id]:
            data = self.sticky_messages[channel_id]
            old_msg_id = data.get("last_message_id")
            
            # Delete old sticky
            if old_msg_id:
                try:
                    # Fetching from cache if possible, fallback to API
                    old_msg = message.channel.get_partial_message(old_msg_id)
                    await old_msg.delete()
                except Exception:
                    pass

            # Build and send the new sticky embed
            embed = discord.Embed(
                description=data["text"],
                color=discord.Color.from_rgb(17, 2, 33)
            )
            embed.set_footer(text="📌 Sticky Message — Please read carefully")

            try:
                new_sticky = await message.channel.send(embed=embed)
                # Update pointer in memory
                self.sticky_messages[channel_id]["last_message_id"] = new_sticky.id
            except discord.Forbidden:
                # Remove if we lost send permissions
                self.sticky_messages.pop(channel_id, None)

async def setup(bot):
    await bot.add_cog(Sticky(bot))
