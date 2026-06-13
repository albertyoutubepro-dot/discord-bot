import discord
from discord.ext import commands, tasks
import asyncio

class VanityRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Dynamic storage per guild: { guild_id: { "vanity": "string", "role_id": int } }
        if not hasattr(bot, "vanity_settings"):
            self.bot.vanity_settings = {}
            
        # Start the background checking loop
        self.check_vanities_loop.start()

    def cog_unload(self):
        self.check_vanities_loop.cancel()

    @property
    def db(self):
        return self.bot.cogs.get("Database")

    # Helper function to evaluate a member's status and update roles
    async def process_member_vanity(self, member: discord.Member):
        if member.bot or not member.guild:
            return

        guild = member.guild
        config = self.bot.vanity_settings.get(guild.id)
        if not config:
            return  # Vanity rewards not configured/enabled for this server

        vanity_string = config.get("vanity")
        role_id = config.get("role_id")
        
        role = guild.get_role(role_id)
        if not role or not vanity_string:
            return

        has_vanity = False

        # Scan all activities for a CustomActivity (Custom Status)
        for activity in member.activities:
            if isinstance(activity, discord.CustomActivity):
                # IMPORTANT: In discord.py, the custom status text is stored in 'state'.
                # 'name' is usually set to "Custom Status".
                text_to_check = []
                if activity.state:
                    text_to_check.append(activity.state.lower())
                if activity.name:
                    text_to_check.append(activity.name.lower())
                
                # Combine state and name to verify matches
                combined_text = " ".join(text_to_check)
                if vanity_string.lower() in combined_text:
                    has_vanity = True
                    break

        try:
            if has_vanity:
                if role not in member.roles:
                    await member.add_roles(role, reason=f"Repping server vanity '{vanity_string}' in status")
            else:
                if role in member.roles:
                    await member.remove_roles(role, reason=f"Removed server vanity '{vanity_string}' from status")
        except discord.Forbidden:
            # Bot lacks permissions or hierarchy is incorrect
            pass
        except discord.HTTPException:
            pass

    # ─── Event Listeners ──────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """Triggers instantly when a user changes their status/activity."""
        await self.process_member_vanity(after)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Checks their status immediately when they join the server."""
        await self.process_member_vanity(member)

    # ─── Configuration Commands ───────────────────────────────────────────────
    @commands.group(name="setvan", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def setvan(self, ctx):
        """Manage vanity reward settings for your server."""
        embed = discord.Embed(
            title="🔮 Vanity Reward Settings",
            description="Reward members with a role for supporting your server vanity in their custom status!",
            color=discord.Color.from_rgb(17, 2, 33)
        )
        embed.add_field(
            name="⚙️ Commands",
            value=(
                "`!setvan set <vanity_text> <@role>` — Configure vanity check & reward role\n"
                "`!setvan disable` — Disable vanity rewards for this server\n"
                "`!setvan status` — View current vanity configuration"
            ),
            inline=False
        )
        embed.set_footer(text="requires Presence and Server Members intents enabled")
        await ctx.reply(embed=embed)

    @setvan.command(name="set")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def setvan_set(self, ctx, vanity_text: str, role: discord.Role):
        """Configure the vanity check requirements and reward role."""
        if role >= ctx.guild.me.top_role:
            return await ctx.reply("❌ **That role is higher than my highest role. Move my role higher in your Server Settings!**")

        # Save config in memory
        self.bot.vanity_settings[ctx.guild.id] = {
            "vanity": vanity_text,
            "role_id": role.id
        }

        # Optional database integration hook
        if self.db and hasattr(self.db, "save_vanity_settings"):
            try:
                await self.db.save_vanity_settings(ctx.guild.id, vanity_text, role.id)
            except Exception:
                pass

        embed = discord.Embed(
            title="✅ Vanity Rewards Enabled",
            description=(
                f"Successfully configured vanity monitoring!\n\n"
                f"• **Vanity to match:** `{vanity_text}`\n"
                f"• **Reward Role:** {role.mention}"
            ),
            color=discord.Color.from_rgb(17, 2, 33),
            timestamp=discord.utils.utcnow()
        )
        await ctx.reply(embed=embed)

    @setvan.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def setvan_disable(self, ctx):
        """Disable vanity monitoring and remove settings."""
        self.bot.vanity_settings.pop(ctx.guild.id, None)

        if self.db and hasattr(self.db, "save_vanity_settings"):
            try:
                await self.db.save_vanity_settings(ctx.guild.id, None, None)
            except Exception:
                pass

        embed = discord.Embed(
            title="🔕 Vanity Rewards Disabled",
            description="Vanity monitoring has been disabled for this server.",
            color=discord.Color.from_rgb(17, 2, 33),
            timestamp=discord.utils.utcnow()
        )
        await ctx.reply(embed=embed)

    @setvan.command(name="status")
    @commands.has_permissions(administrator=True)
    async def setvan_status(self, ctx):
        """View active vanity reward configurations."""
        config = self.bot.vanity_settings.get(ctx.guild.id)
        if not config:
            return await ctx.reply("❌ **Vanity rewards are currently disabled or unconfigured on this server.**")

        vanity_text = config.get("vanity")
        role_id = config.get("role_id")
        role = ctx.guild.get_role(role_id)

        embed = discord.Embed(
            title="📋 Current Vanity Config",
            color=discord.Color.from_rgb(17, 2, 33),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Required String", value=f"`{vanity_text}`", inline=True)
        embed.add_field(name="Assigned Reward", value=role.mention if role else "*(Role not found)*", inline=True)
        await ctx.reply(embed=embed)

    # ─── Background Fail-safe Loop ────────────────────────────────────────────
    @tasks.loop(minutes=15)
    async def check_vanities_loop(self):
        """Sweeps the server every 15 minutes to fix anyone missed by event drops."""
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            # Check if this guild actually has vanity rewards set up
            config = self.bot.vanity_settings.get(guild.id)
            if not config:
                continue
                
            role = guild.get_role(config.get("role_id"))
            if not role:
                continue
                
            for member in guild.members:
                await self.process_member_vanity(member)
                # Avoid hitting local gateway connection rate limits
                await asyncio.sleep(0.05)

async def setup(bot):
    await bot.add_cog(VanityRewards(bot))
