import discord
from discord.ext import commands

OWNER_ID = 1446215395358015559

def is_owner():
    async def predicate(ctx):
        if ctx.author.id != OWNER_ID:
            return False
        return True
    return commands.check(predicate)


class WhoIs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="whois", usage="<user_id>")
    @is_owner()
    async def whois(self, ctx, user_id: int):
        """Deep lookup on any user across all servers. Owner only."""
        # Fetch the user globally
        try:
            user = await self.bot.fetch_user(user_id)
        except discord.NotFound:
            return await ctx.reply("❌ User not found.")

        # Find all shared servers
        shared_guilds = []
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member:
                shared_guilds.append((guild, member))

        # Build embed
        embed = discord.Embed(
            title=f"🔍 Who Is — {user}",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        # Basic info
        account_age = (discord.utils.utcnow() - user.created_at).days
        embed.add_field(name="🪪 Username",      value=str(user),                                          inline=True)
        embed.add_field(name="🆔 ID",            value=str(user.id),                                       inline=True)
        embed.add_field(name="🤖 Bot",           value="Yes" if user.bot else "No",                        inline=True)
        embed.add_field(name="📅 Account Created", value=discord.utils.format_dt(user.created_at, "F"),   inline=True)
        embed.add_field(name="🗓️ Account Age",   value=f"{account_age} days old",                          inline=True)
        embed.add_field(name="🌐 Shared Servers", value=str(len(shared_guilds)),                           inline=True)

        # Avatar URL
        embed.add_field(name="🖼️ Avatar", value=f"[Click here]({user.display_avatar.url})", inline=True)

        # Warn count across all servers
        total_warns = sum(
            len(self.bot.warn_data.get(f"{user_id}:{guild.id}", []))
            for guild in self.bot.guilds
        )
        embed.add_field(name="⚠️ Total Warns (all servers)", value=str(total_warns), inline=True)

        # Bot ban status
        is_banned = user_id in self.bot.bot_banned
        embed.add_field(name="🚫 Bot Banned", value="Yes 🔴" if is_banned else "No 🟢", inline=True)

        # Shared servers details
        if shared_guilds:
            server_lines = []
            for guild, member in shared_guilds[:8]:  # max 8 to avoid embed limit
                roles = [r.name for r in member.roles if r.name != "@everyone"][:3]
                roles_str = ", ".join(roles) if roles else "No roles"
                days_in = (discord.utils.utcnow() - member.joined_at).days
                server_lines.append(
                    f"**{guild.name}** — joined {days_in}d ago\n"
                    f"└ Roles: {roles_str}"
                )
            embed.add_field(
                name=f"🏠 Shared Servers ({len(shared_guilds)})",
                value="\n".join(server_lines)[:1024],
                inline=False,
            )
        else:
            embed.add_field(name="🏠 Shared Servers", value="None — user is not in any server the bot is in", inline=False)

        embed.set_footer(text=f"Requested by {ctx.author} • Death Bot")
        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(WhoIs(bot))
