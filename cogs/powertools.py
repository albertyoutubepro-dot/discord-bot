import discord
from discord.ext import commands

OWNER_ID = 1446215395358015559

def is_owner():
    async def predicate(ctx):
        if ctx.author.id != OWNER_ID:
            await ctx.reply("❌ This command is restricted to the bot owner.")
            return False
        return True
    return commands.check(predicate)


class PowerTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'frozen_channels'):
            bot.frozen_channels = {}  # channel_id -> { overwrites before freeze }

    # ─── !freeze ──────────────────────────────────────────────────────────────
    @commands.command(name="freeze", usage="[#channel]")
    @is_owner()
    async def freeze(self, ctx, channel: discord.TextChannel = None):
        """Freeze a channel — nobody can send messages except you. Owner only."""
        target = channel or ctx.channel

        if target.id in self.bot.frozen_channels:
            return await ctx.reply(f"❌ {target.mention} is already frozen. Use `!unfreeze` to unfreeze it.")

        # Save all current overwrites so we can restore them later
        saved = {}
        for target_role_or_member, overwrite in target.overwrites.items():
            saved[target_role_or_member.id] = {
                "type": "role" if isinstance(target_role_or_member, discord.Role) else "member",
                "pairs": list(iter(overwrite)),
            }
        self.bot.frozen_channels[target.id] = saved

        # Lock everyone out
        for role in ctx.guild.roles:
            overwrite = target.overwrites_for(role)
            overwrite.send_messages = False
            await target.set_permissions(role, overwrite=overwrite)

        # Make sure the bot can still send
        await target.set_permissions(ctx.guild.me, send_messages=True)

        await target.send(embed=discord.Embed(
            title="🧊 Channel Frozen",
            description="This channel has been frozen. Nobody can send messages until it's unfrozen.",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        ))

        if target != ctx.channel:
            await ctx.reply(f"🧊 {target.mention} has been frozen.")

    # ─── !unfreeze ────────────────────────────────────────────────────────────
    @commands.command(name="unfreeze", usage="[#channel]")
    @is_owner()
    async def unfreeze(self, ctx, channel: discord.TextChannel = None):
        """Unfreeze a frozen channel. Owner only."""
        target = channel or ctx.channel

        if target.id not in self.bot.frozen_channels:
            return await ctx.reply(f"❌ {target.mention} is not frozen.")

        saved = self.bot.frozen_channels.pop(target.id)

        # Restore original overwrites
        for target_id, data in saved.items():
            if data["type"] == "role":
                obj = ctx.guild.get_role(target_id)
            else:
                obj = ctx.guild.get_member(target_id)
            if obj:
                overwrite = discord.PermissionOverwrite(**dict(data["pairs"]))
                await target.set_permissions(obj, overwrite=overwrite)

        await target.send(embed=discord.Embed(
            title="🔥 Channel Unfrozen",
            description="This channel has been unfrozen. You can send messages again.",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        ))

        if target != ctx.channel:
            await ctx.reply(f"🔥 {target.mention} has been unfrozen.")

    # ─── !selfpurge ───────────────────────────────────────────────────────────
    @commands.command(name="selfpurge", usage="[amount]")
    @is_owner()
    async def selfpurge(self, ctx, amount: int = 100):
        """Delete all of your own messages in this channel. Owner only."""
        if amount < 1 or amount > 500:
            return await ctx.reply("❌ Amount must be between 1 and 500.")

        await ctx.message.delete()

        deleted = 0
        async for message in ctx.channel.history(limit=500):
            if message.author.id == ctx.author.id:
                try:
                    await message.delete()
                    deleted += 1
                    if deleted >= amount:
                        break
                except discord.Forbidden:
                    break
                except discord.NotFound:
                    pass

        msg = await ctx.send(embed=discord.Embed(
            title="🧹 Self Purge Complete",
            description=f"Deleted **{deleted}** of your messages.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        ))

        import asyncio
        await asyncio.sleep(5)
        await msg.delete()


async def setup(bot):
    await bot.add_cog(PowerTools(bot))
