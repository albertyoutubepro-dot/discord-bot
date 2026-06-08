import discord
from discord.ext import commands

# ─── Configuration ────────────────────────────────────────────────────────────
# Your actual Discord User ID to make sure you never get banned and receive the DM alerts
OWNER_ID = 1446215395358015559  

class Honeypot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # In-memory storage mapping: { guild_id: channel_id }
        self.trap_channels = {}

    # Helper check to ensure only server administrators or the bot owner can configure the trap
    async def is_admin(self, ctx):
        return ctx.author.guild_permissions.administrator or ctx.author.id == OWNER_ID or await self.bot.is_owner(ctx.author)

    @commands.group(name="honeypot", aliases=["trap"], invoke_without_command=True)
    async def honeypot_group(self, ctx):
        """Base command to manage the honeypot security channel."""
        if not await self.is_admin(ctx):
            return
        await ctx.reply("❌ **use: `!honeypot set <#channel>` or `!honeypot clear`**")

    @honeypot_group.command(name="set")
    async def set_honeypot(self, ctx, channel: discord.TextChannel):
        """Sets the trap channel for this server."""
        if not await self.is_admin(ctx):
            return

        self.trap_channels[ctx.guild.id] = channel.id
        await ctx.reply(f"🔒 **honeypot channel has been set to {channel.mention}.**\n⚠️ *any non-admin user who types here will be instantly banned.*")

    @honeypot_group.command(name="clear")
    async def clear_honeypot(self, ctx):
        """Disables the honeypot trap channel for this server."""
        if not await self.is_admin(ctx):
            return

        if ctx.guild.id in self.trap_channels:
            del self.trap_channels[ctx.guild.id]
            await ctx.reply("🔓 **honeypot security channel has been disabled.**")
        else:
            await ctx.reply("❌ **no honeypot channel is currently configured.**")

    # ─── Event Listener ───────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. Ignore direct messages or system messages
        if not message.guild or message.author.bot:
            return

        # 2. Check if this guild has a honeypot channel set up
        trap_channel_id = self.trap_channels.get(message.guild.id)
        if not trap_channel_id or message.channel.id != trap_channel_id:
            return

        # 3. Safe List: Never ban the bot owner, guild owner, or server administrators
        is_bot_owner = message.author.id == OWNER_ID or await self.bot.is_owner(message.author)
        is_guild_owner = message.author.id == message.guild.owner_id
        is_admin = message.author.guild_permissions.administrator

        if is_bot_owner or is_guild_owner or is_admin:
            return  # Safe! Allow them to type/test without consequences

        # 4. Trigger the Trap (Ban, DM owner, & clean up)
        try:
            # Delete the message immediately to hide the spam
            await message.delete()
            
            # Ban the user and delete their message history from the past day
            await message.author.ban(
                reason="Triggered security honeypot channel (Potential self-bot/scam account).",
                delete_message_days=1
            )
            
            # Send a silent DM to the bot owner with the log details
            owner = self.bot.get_user(OWNER_ID) or await self.bot.fetch_user(OWNER_ID)
            if owner:
                embed = discord.Embed(
                    title="💀 **honeypot triggered**",
                    description="*an account triggered the trap and was banished.*",
                    color=discord.Color.from_rgb(17, 2, 33) # Matches death's dark aesthetic
                )
                embed.add_field(name="👤 user", value=f"{message.author}\n`{message.author.id}`", inline=False)
                embed.add_field(name="🏛️ server", value=f"{message.guild.name}\n`{message.guild.id}`", inline=True)
                embed.add_field(name="📺 channel", value=f"#{message.channel.name}", inline=True)
                embed.set_footer(text="death security systems 🌑")
                try:
                    await owner.send(embed=embed)
                except discord.Forbidden:
                    # In case your DMs are closed or bot can't message you
                    pass

            # Send a clean log to the channel to let everyone know the threat was handled
            await message.channel.send(f"🌌 **annihilated:** user `{message.author}` has been banned for triggering the trap.")
        except discord.Forbidden:
            # If the bot lacks permissions to ban or delete messages, print an error to the channel
            try:
                await message.channel.send("⚠️ **security alert:** someone triggered the trap, but i don't have permission to ban them.")
            except discord.HTTPException:
                pass
        except Exception as e:
            print(f"Error executing honeypot ban: {e}")

async def setup(bot):
    await bot.add_cog(Honeypot(bot))
