import discord
from discord.ext import commands
import re

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.cogs.get("Database")

    # ─── Helper to Build Premium Embed ────────────────────────────────────────
    def build_welcome_embed(self, member: discord.Member, guild: discord.Guild, raw_message: str) -> discord.Embed:
        """Parses placeholders, strips raw media URLs, and compiles a premium dark welcome embed."""
        # Clean spacing and replace placeholders
        msg = raw_message \
            .replace("{user}", member.mention) \
            .replace("{username}", member.display_name) \
            .replace("{server}", guild.name) \
            .replace("{count}", str(guild.member_count)) \
            .replace("\\n", "\n")

        # Automatically extract any image/GIF url to use as the embed's primary image
        url_pattern = re.compile(r'(https?://\S+)')
        urls = url_pattern.findall(msg)
        image_url = None
        
        if urls:
            for url in reversed(urls):
                if any(ext in url.lower() for ext in [".gif", ".png", ".jpg", ".jpeg", "pinterest", "giphy", "tenor"]):
                    image_url = url
                    msg = msg.replace(url, "").strip() # Strip out raw link from description text
                    break

        # Create a premium dark velvet themed welcome card
        embed = discord.Embed(
            description=msg,
            color=discord.Color.from_rgb(17, 2, 33), # Deep dark velvet purple
            timestamp=discord.utils.utcnow()
        )
        embed.set_author(name=f"Welcome to {guild.name}!", icon_url=guild.icon.url if guild.icon else None)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        if image_url:
            embed.set_image(url=image_url)
            
        embed.set_footer(text=f"Member #{guild.member_count}")
        return embed

    # ─── Auto-role & Welcome Event ────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id

        # 1. Process Auto-role on join
        role_id = self.bot.autorole.get(guild_id)
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Auto-role on join")
                except discord.Forbidden:
                    pass

        # 2. Process Welcome Message embed
        config = self.bot.welcome_config.get(guild_id)
        if config:
            channel = member.guild.get_channel(config["channel_id"])
            if channel:
                try:
                    embed = self.build_welcome_embed(member, member.guild, config["message"])
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
            "`!setwelcome set <#channel> <message>` — Set welcome channel and message. Use `{user}` `{server}` `{count}`",
            "`!setwelcome disable` — Disable welcome messages",
            "`!setwelcome test` — Send a test welcome message",
            "`!setwelcome status` — View current welcome config",
            "",
            "**Placeholders:**",
            "`{user}` — Mentions the new member",
            "`{username}` — Their display name",
            "`{server}` — Server name",
            "`{count}` — Current member count",
        ]))

    @setwelcome.command(name="set")
    @commands.has_permissions(administrator=True)
    async def setwelcome_set(self, ctx, channel: discord.TextChannel, *, message: str):
        """Set the welcome channel and message."""
        self.bot.welcome_config[ctx.guild.id] = {
            "channel_id": channel.id,
            "message": message,
        }
        if self.db:
            await self.db.save_welcome(ctx.guild.id, channel.id, message)
        
        # Build clean confirmation preview
        preview_embed = self.build_welcome_embed(ctx.author, ctx.guild, message)
        preview_embed.set_footer(text="Configuration Preview")
        
        await ctx.reply(
            content=f"✅ **welcome message successfully saved for {channel.mention}!**\n*here is a preview of how it will look:*",
            embed=preview_embed
        )

    @setwelcome.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def setwelcome_disable(self, ctx):
        """Disable welcome messages."""
        self.bot.welcome_config.pop(ctx.guild.id, None)
        if self.db:
            await self.db.save_welcome(ctx.guild.id, None, None)
        
        await ctx.reply(embed=discord.Embed(
            title="🔕 Welcome Messages Disabled",
            color=discord.Color.from_rgb(17, 2, 33),
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
            
        # Build the premium styled embed
        embed = self.build_welcome_embed(ctx.author, ctx.guild, config["message"])
        embed.set_footer(text=f"Member #{ctx.guild.member_count} • Test Run")
        
        await channel.send(embed=embed)
        await ctx.reply(f"✅ **test welcome card sent directly to {channel.mention}!**")

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
            color=discord.Color.from_rgb(17, 2, 33),
            timestamp=discord.utils.utcnow(),
        ).add_field(name="Channel", value=channel.mention if channel else "Not found", inline=True
        ).add_field(name="Message", value=f"
http://googleusercontent.com/immersive_entry_chip/0

***


http://googleusercontent.com/immersive_entry_chip/1
http://googleusercontent.com/immersive_entry_chip/2
eof
