import discord
from discord.ext import commands


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ─── Auto-role on join ────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id

        # Give auto-role if set
        role_id = self.bot.autorole.get(guild_id)
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Auto-role on join")
                except discord.Forbidden:
                    pass

        # Send welcome message if set
        config = self.bot.welcome_config.get(guild_id)
        if config:
            channel = member.guild.get_channel(config["channel_id"])
            if channel:
                # Build the message, replacing placeholders
                msg = config["message"] \
                    .replace("{user}", member.mention) \
                    .replace("{username}", member.display_name) \
                    .replace("{server}", member.guild.name) \
                    .replace("{count}", str(member.guild.member_count))

                embed = discord.Embed(
                    description=msg,
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow(),
                )
                embed.set_author(name=f"Welcome to {member.guild.name}!", icon_url=member.guild.icon.url if member.guild.icon else None)
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Member #{member.guild.member_count}")

                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

    # ─── !setwelcome ──────────────────────────────────────────────────────────
    @commands.group(name="setwelcome", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def setwelcome(self, ctx):
        """Manage the welcome message. Subcommands: set, disable, test, status"""
        await ctx.reply("\n".join([
            "**Welcome Commands:**",
            "`!setwelcome set <#channel> <message>` — Set welcome channel and message",
            "`!setwelcome disable` — Disable welcome messages",
            "`!setwelcome test` — Send a test welcome message",
            "`!setwelcome status` — Show current welcome config",
            "",
            "**Placeholders you can use in your message:**",
            "`{user}` — Mentions the new member",
            "`{username}` — Their display name",
            "`{server}` — Server name",
            "`{count}` — Current member count",
            "",
            "**Example:**",
            "`!setwelcome set #welcome Hey {user}, welcome to {server}! You're member #{count} 🎉`",
        ]))

    @setwelcome.command(name="set")
    @commands.has_permissions(administrator=True)
    async def setwelcome_set(self, ctx, channel: discord.TextChannel, *, message: str):
        """Set the welcome channel and message."""
        self.bot.welcome_config[ctx.guild.id] = {
            "channel_id": channel.id,
            "message": message,
        }
        await ctx.reply(embed=discord.Embed(
            title="✅ Welcome Message Set",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        ).add_field(name="Channel", value=channel.mention, inline=True
        ).add_field(name="Message Preview", value=message[:500], inline=False))

    @setwelcome.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def setwelcome_disable(self, ctx):
        """Disable welcome messages."""
        self.bot.welcome_config.pop(ctx.guild.id, None)
        await ctx.reply(embed=discord.Embed(
            title="🔕 Welcome Messages Disabled",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        ))

    @setwelcome.command(name="test")
    @commands.has_permissions(administrator=True)
    async def setwelcome_test(self, ctx):
        """Send a test welcome message for yourself."""
        config = self.bot.welcome_config.get(ctx.guild.id)
        if not config:
            return await ctx.reply("❌ No welcome message set. Use `!setwelcome set` first.")

        channel = ctx.guild.get_channel(config["channel_id"])
        if not channel:
            return await ctx.reply("❌ Welcome channel not found. Please set it again.")

        msg = config["message"] \
            .replace("{user}", ctx.author.mention) \
            .replace("{username}", ctx.author.display_name) \
            .replace("{server}", ctx.guild.name) \
            .replace("{count}", str(ctx.guild.member_count))

        embed = discord.Embed(
            description=msg,
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(name=f"Welcome to {ctx.guild.name}!", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Member #{ctx.guild.member_count} • This is a test")

        await channel.send(embed=embed)
        await ctx.reply(f"✅ Test welcome message sent to {channel.mention}!")

    @setwelcome.command(name="status")
    @commands.has_permissions(administrator=True)
    async def setwelcome_status(self, ctx):
        """Show current welcome config."""
        config = self.bot.welcome_config.get(ctx.guild.id)
        if not config:
            return await ctx.reply("❌ Welcome messages are currently **disabled**.")

        channel = ctx.guild.get_channel(config["channel_id"])
        await ctx.reply(embed=discord.Embed(
            title="📋 Welcome Config",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        ).add_field(name="Channel", value=channel.mention if channel else "Not found", inline=True
        ).add_field(name="Message", value=config["message"][:500], inline=False))

    # ─── !autorole ────────────────────────────────────────────────────────────
    @commands.group(name="autorole", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def autorole(self, ctx):
        """Manage the auto-role given to new members."""
        await ctx.reply("\n".join([
            "**Autorole Commands:**",
            "`!autorole set <@role>` — Set the role to give new members",
            "`!autorole disable`     — Disable autorole",
            "`!autorole status`      — Show current autorole",
        ]))

    @autorole.command(name="set")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def autorole_set(self, ctx, role: discord.Role):
        """Set the role to give new members automatically."""
        if role >= ctx.guild.me.top_role:
            return await ctx.reply("❌ That role is higher than my highest role. Please move my role above it.")
        self.bot.autorole[ctx.guild.id] = role.id
        await ctx.reply(embed=discord.Embed(
            title="✅ Autorole Set",
            description=f"New members will automatically receive {role.mention}.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        ))

    @autorole.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def autorole_disable(self, ctx):
        """Disable autorole."""
        self.bot.autorole.pop(ctx.guild.id, None)
        await ctx.reply(embed=discord.Embed(
            title="🔕 Autorole Disabled",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        ))

    @autorole.command(name="status")
    @commands.has_permissions(administrator=True)
    async def autorole_status(self, ctx):
        """Show current autorole setting."""
        role_id = self.bot.autorole.get(ctx.guild.id)
        if not role_id:
            return await ctx.reply("❌ Autorole is currently **disabled**.")
        role = ctx.guild.get_role(role_id)
        await ctx.reply(embed=discord.Embed(
            title="📋 Autorole Config",
            description=f"New members receive: {role.mention if role else 'Role not found'}",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        ))


async def setup(bot):
    await bot.add_cog(Welcome(bot))
