import discord
from discord.ext import commands
import asyncio
import random

OWNER_ID = 1446215395358015559

def is_owner():
    async def predicate(ctx):
        if ctx.author.id != OWNER_ID:
            return False
        return True
    return commands.check(predicate)


class Extras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'marriages'):
            bot.marriages = {}
        if not hasattr(bot, 'copycat_targets'):
            bot.copycat_targets = {}

    @property
    def db(self):
        return self.bot.cogs.get("Database")

    # ─── !steal ───────────────────────────────────────────────────────────────
    @commands.command(name="steal", usage="<emoji>")
    @commands.has_permissions(manage_emojis=True)
    async def steal(self, ctx, emoji: str):
        """Steal an emoji from another server and add it to yours."""
        import re
        match = re.match(r"<a?:(\w+):(\d+)>", emoji)
        if not match:
            return await ctx.reply("❌ That's not a custom emoji. Only custom emojis can be stolen.")
        animated = emoji.startswith("<a:")
        name = match.group(1)
        emoji_id = match.group(2)
        ext = "gif" if animated else "png"
        url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}"
        async with self.bot.http._HTTPClient__session.get(url) as resp:
            if resp.status != 200:
                return await ctx.reply("❌ Couldn't fetch that emoji.")
            image_data = await resp.read()
        try:
            new_emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data,
                reason=f"Stolen by {ctx.author}")
            await ctx.reply(embed=discord.Embed(
                title="✅ Emoji Stolen!",
                description=f"Added {new_emoji} **:{name}:** to the server!",
                color=discord.Color.green(), timestamp=discord.utils.utcnow(),
            ))
        except discord.Forbidden:
            await ctx.reply("❌ I need **Manage Emojis** permission.")
        except discord.HTTPException as e:
            await ctx.reply(f"❌ Failed to add emoji: {e}")

    # ─── !fakeban ─────────────────────────────────────────────────────────────
    @commands.command(name="fakeban", usage="<@user> [reason]")
    @is_owner()
    async def fakeban(self, ctx, member: discord.Member, *, reason: str = "Violating server rules"):
        """Send a fake ban message that looks real (owner only)."""
        await ctx.message.delete()
        embed = discord.Embed(title="🔨 Member Banned", color=discord.Color.red(), timestamp=discord.utils.utcnow())
        embed.add_field(name="User",      value=f"{member} ({member.id})", inline=True)
        embed.add_field(name="Moderator", value=str(ctx.author),           inline=True)
        embed.add_field(name="Reason",    value=reason,                    inline=False)
        embed.set_footer(text="Death Bot Moderation")
        await ctx.send(embed=embed)

    # ─── !marry ───────────────────────────────────────────────────────────────
    @commands.command(name="marry", usage="<@user>")
    async def marry(self, ctx, member: discord.Member):
        """Propose to someone 💍"""
        if member == ctx.author:
            return await ctx.reply("❌ You can't marry yourself!")
        if member.bot:
            return await ctx.reply("❌ You can't marry a bot!")
        if ctx.author.id in self.bot.marriages:
            partner_id = self.bot.marriages[ctx.author.id]
            partner = ctx.guild.get_member(partner_id)
            return await ctx.reply(f"❌ You're already married to {partner.mention if partner else f'<@{partner_id}>'}! Use `!divorce` first.")
        if member.id in self.bot.marriages:
            partner_id = self.bot.marriages[member.id]
            partner = ctx.guild.get_member(partner_id)
            return await ctx.reply(f"❌ {member.mention} is already married to {partner.mention if partner else f'<@{partner_id}>'}!")

        embed = discord.Embed(
            title="💍 Marriage Proposal!",
            description=f"{ctx.author.mention} is proposing to {member.mention}!\n\nDo you accept?",
            color=discord.Color.magenta(),
            timestamp=discord.utils.utcnow(),
        )

        view = discord.ui.View(timeout=60)
        accept_btn = discord.ui.Button(label="Accept 💍", style=discord.ButtonStyle.success)
        deny_btn   = discord.ui.Button(label="Deny 💔",   style=discord.ButtonStyle.danger)

        async def accept_callback(interaction: discord.Interaction):
            if interaction.user.id != member.id:
                return await interaction.response.send_message("❌ Only the proposed person can respond!", ephemeral=True)
            self.bot.marriages[ctx.author.id] = member.id
            self.bot.marriages[member.id] = ctx.author.id
            if self.db:
                await self.db.save_marriage(ctx.author.id, member.id)
            view.stop()
            await interaction.response.edit_message(embed=discord.Embed(
                title="💒 Just Married!",
                description=f"🎉 {ctx.author.mention} and {member.mention} are now married! 💍",
                color=discord.Color.magenta(),
                timestamp=discord.utils.utcnow(),
            ), view=None)

        async def deny_callback(interaction: discord.Interaction):
            if interaction.user.id != member.id:
                return await interaction.response.send_message("❌ Only the proposed person can respond!", ephemeral=True)
            view.stop()
            await interaction.response.edit_message(embed=discord.Embed(
                title="💔 Proposal Rejected",
                description=f"{member.mention} rejected {ctx.author.mention}'s proposal. Ouch.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow(),
            ), view=None)

        accept_btn.callback = accept_callback
        deny_btn.callback   = deny_callback
        view.add_item(accept_btn)
        view.add_item(deny_btn)
        await ctx.reply(embed=embed, view=view)

    # ─── !divorce ─────────────────────────────────────────────────────────────
    @commands.command(name="divorce", usage="<@user>")
    async def divorce(self, ctx, member: discord.Member = None):
        """Divorce your partner 💔"""
        if ctx.author.id not in self.bot.marriages:
            return await ctx.reply("❌ You're not married to anyone!")
        partner_id = self.bot.marriages[ctx.author.id]
        if member and member.id != partner_id:
            return await ctx.reply(f"❌ You're not married to {member.mention}!")
        partner = ctx.guild.get_member(partner_id)
        self.bot.marriages.pop(ctx.author.id, None)
        self.bot.marriages.pop(partner_id, None)
        if self.db:
            await self.db.delete_marriage(ctx.author.id, partner_id)
        await ctx.reply(embed=discord.Embed(
            title="💔 Divorced",
            description=f"{ctx.author.mention} and {partner.mention if partner else f'<@{partner_id}>'} are no longer married.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        ))

    # ─── !copycat ─────────────────────────────────────────────────────────────
    @commands.command(name="copycat", usage="<@user>")
    @is_owner()
    async def copycat(self, ctx, member: discord.Member):
        """Mimic everything a user says in this channel for 60 seconds (owner only)."""
        if member.bot:
            return await ctx.reply("❌ Can't copycat a bot.")
        self.bot.copycat_targets[ctx.channel.id] = member.id
        await ctx.message.delete()
        await ctx.send(embed=discord.Embed(
            title="🎭 Copycat Active",
            description=f"Mimicking {member.mention} for **60 seconds**.",
            color=discord.Color.blurple(), timestamp=discord.utils.utcnow(),
        ))
        await asyncio.sleep(60)
        if self.bot.copycat_targets.get(ctx.channel.id) == member.id:
            self.bot.copycat_targets.pop(ctx.channel.id, None)
            await ctx.send(embed=discord.Embed(
                title="🎭 Copycat Stopped",
                description=f"No longer mimicking {member.mention}.",
                color=discord.Color.orange(), timestamp=discord.utils.utcnow(),
            ))

    # ─── Copycat listener ─────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        target_id = self.bot.copycat_targets.get(message.channel.id)
        if target_id and message.author.id == target_id:
            if not message.content.startswith("!"):
                try:
                    await message.channel.send(message.content)
                except discord.Forbidden:
                    pass


async def setup(bot):
    await bot.add_cog(Extras(bot))
