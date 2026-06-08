import discord
from discord.ext import commands

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # In-memory storage for reaction roles
        # Format: { message_id: { emoji_name_or_id: role_id } }
        self.reaction_data = {}

    @commands.group(name="reactionrole", aliases=["rr"], invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def reaction_role_group(self, ctx):
        """Base command for managing reaction roles."""
        await ctx.reply("❌ **use: `!rr embed <title> <description>` to make a post, or `!rr add <message_id> <emoji> <@role>` to bind a role.**")

    @reaction_role_group.command(name="embed")
    @commands.has_permissions(manage_roles=True)
    async def send_rr_embed(self, ctx, title: str, *, description: str):
        """Creates a sleek, themed embed to use for your reaction roles setup."""
        embed = discord.Embed(
            title=f"🔮 **{title.lower()}**",
            description=f"*{description}*",
            color=discord.Color.from_rgb(17, 2, 33)  # Deep dark purple/black theme
        )
        
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            
        embed.set_footer(text="tap a reaction below to claim your role")
        
        # Send the embed message
        msg = await ctx.send(embed=embed)
        
        # Reply with the message ID to make binding roles extremely easy
        await ctx.reply(
            f"✅ **embed created successfully.**\n"
            f"📝 **message id:** `{msg.id}`\n"
            f"👉 *use `!rr add {msg.id} <emoji> <@role>` in this channel to add your buttons!*"
        )

    @reaction_role_group.command(name="add")
    @commands.has_permissions(manage_roles=True)
    async def add_reaction_role(self, ctx, message_id: int, emoji: str, role: discord.Role):
        """Binds an emoji and a role to a specific message."""
        # Check if the bot's role is high enough to manage this role
        if ctx.guild.me.top_role.position <= role.position:
            return await ctx.reply("❌ **my top role is not high enough to manage this role.**")

        # Try to find the message in the channel to add the initial reaction
        try:
            message = await ctx.channel.fetch_message(message_id)
            await message.add_reaction(emoji)
        except discord.NotFound:
            return await ctx.reply("❌ **message not found in this channel. make sure you run this command in the same channel as the message.**")
        except discord.HTTPException:
            return await ctx.reply("❌ **invalid emoji or failed to add reaction.**")

        # Initialize the message ID key if it doesn't exist
        if message_id not in self.reaction_data:
            self.reaction_data[message_id] = {}

        # Save the emoji to role mapping
        self.reaction_data[message_id][str(emoji)] = role.id
        await ctx.reply(f"✅ **bound {emoji} to {role.name} on message `{message_id}`.**")

    @reaction_role_group.command(name="clear")
    @commands.has_permissions(manage_roles=True)
    async def clear_reaction_roles(self, ctx, message_id: int):
        """Clears all bound reaction roles from a specific message."""
        if message_id in self.reaction_data:
            del self.reaction_data[message_id]
            await ctx.reply(f"🗑️ **cleared all reaction roles for message `{message_id}`.**")
        else:
            await ctx.reply("❌ **no reaction roles are set up on that message.**")

    # ─── Event Listeners for Handling Reactions ───────────────────────────────
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # Ignore reactions from the bot itself
        if payload.user_id == self.bot.user.id:
            return

        # Check if the reacted message has reaction roles set up
        if payload.message_id in self.reaction_data:
            emoji_str = str(payload.emoji)
            mappings = self.reaction_data[payload.message_id]

            if emoji_str in mappings:
                guild = self.bot.get_guild(payload.guild_id)
                if not guild:
                    return

                member = guild.get_member(payload.user_id)
                role = guild.get_role(mappings[emoji_str])

                if member and role:
                    try:
                        await member.add_roles(role, reason="reaction role claim")
                    except discord.Forbidden:
                        pass # Bot lacks permission or role hierarchy is blocked

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        # Check if the unreacted message has reaction roles set up
        if payload.message_id in self.reaction_data:
            emoji_str = str(payload.emoji)
            mappings = self.reaction_data[payload.message_id]

            if emoji_str in mappings:
                guild = self.bot.get_guild(payload.guild_id)
                if not guild:
                    return

                # Fetch member since they might not be cached when removing reactions
                try:
                    member = await guild.fetch_member(payload.user_id)
                except discord.NotFound:
                    return

                role = guild.get_role(mappings[emoji_str])

                if member and role:
                    try:
                        await member.remove_roles(role, reason="reaction role forfeit")
                    except discord.Forbidden:
                        pass # Bot lacks permission or role hierarchy is blocked

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
