import discord
from discord.ext import commands
import sys
import io
import traceback

# Your actual Discord User ID
OWNER_ID = 1446215395358015559  

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'bot_banned'):
            bot.bot_banned = set()

    async def cog_check(self, ctx):
        # Strict security check: only the bot developer can run these commands
        return ctx.author.id == OWNER_ID or await self.bot.is_owner(ctx.author)

    # ─── 1. Invite Finder (Existing Invites Only) ────────────────────────────
    @commands.command(name="fetchinvite")
    async def fetch_existing_invite(self, ctx, guild_id: int):
        """Attempts to find an already created, active invite for a server the bot is in."""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return await ctx.reply("❌ **i am not in a server with that id.**")

        # Fallback 1: Try to read the server's existing invite list (requires Manage Server permission)
        if guild.me.guild_permissions.manage_guild:
            try:
                invites = await guild.invites()
                # Find the first active, unexpired invite link
                active_invites = [inv for inv in invites if not inv.revoked]
                if active_invites:
                    best_invite = active_invites[0]
                    return await ctx.reply(f"🔮 **found existing invite for '{guild.name}':**\n{best_invite.url}")
            except discord.Forbidden:
                pass
            except Exception as e:
                print(f"Error fetching invites: {e}")

        # Fallback 2: Check if the server has an active public widget invite enabled
        try:
            widget = await guild.widget()
            if widget and widget.invite_url:
                return await ctx.reply(f"🔮 **found public widget invite for '{guild.name}':**\n{widget.invite_url}")
        except discord.Forbidden:
            pass
        except Exception:
            pass

        await ctx.reply(
            f"❌ **could not find any active public invites for '{guild.name}'.**\n"
            f"*the bot does not have 'Manage Server' permissions to read the invite list, and the widget is turned off.*"
        )

    # ─── 2. Server Management ─────────────────────────────────────────────────
    @commands.command(name="servers")
    async def list_servers(self, ctx):
        """Lists all servers the bot is currently in."""
        msg = "```\n"
        for guild in self.bot.guilds:
            msg += f"{guild.name} (ID: {guild.id}) - Members: {guild.member_count}\n"
        msg += "```"
        
        if len(msg) > 2000:
            try:
                await ctx.author.send(msg)
                await ctx.reply("📬 **sent the server list to your DMs since it's too long.**")
            except discord.Forbidden:
                await ctx.reply("❌ **your DMs are locked. i couldn't send the full list.**")
        else:
            await ctx.reply(msg)

    @commands.command(name="leaveserver")
    async def leave_server(self, ctx, guild_id: int):
        """Forces the bot to leave a specific server."""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return await ctx.reply("❌ **i am not in a server with that id.**")
            
        await guild.leave()
        await ctx.reply(f"🚪 **successfully left server:** `{guild.name}` ({guild_id})")

    # ─── 3. Global Blacklist ──────────────────────────────────────────────────
    @commands.command(name="botban")
    async def blacklist_user(self, ctx, user: discord.User):
        """Globally blacklists a user from using any bot commands."""
        if user.id == OWNER_ID or await self.bot.is_owner(user):
            return await ctx.reply("❌ **you cannot blacklist a bot developer!**")
            
        self.bot.bot_banned.add(user.id)
        await ctx.reply(f"🔒 **{user}** has been globally blacklisted from using the bot.")

    @commands.command(name="botunban")
    async def unblacklist_user(self, ctx, user: discord.User):
        """Removes a user from the global blacklist."""
        if user.id in self.bot.bot_banned:
            self.bot.bot_banned.remove(user.id)
            await ctx.reply(f"🔓 **{user}** has been removed from the global blacklist.")
        else:
            await ctx.reply("❌ **that user is not blacklisted.**")

    # ─── 4. Developer Evaluation ──────────────────────────────────────────────
    @commands.command(name="eval")
    async def evaluate_code(self, ctx, *, body: str):
        """Evaluates arbitrary python code. Use with caution."""
        # Clean up any markdown code blocks from the input
        if body.startswith("```"):
            body = "\n".join(body.split("\n")[1:-1]) if "\n" in body else body.strip("`")

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': None
        }

        env.update(globals())
        stdout = io.StringIO()

        to_compile = f'async def func():\n' + '\n'.join(f'    {line}' for line in body.split('\n'))

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.reply(f"
