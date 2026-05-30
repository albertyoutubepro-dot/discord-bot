import discord
from discord.ext import commands
import time


class History(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="history", usage="<@user>")
    @commands.has_permissions(moderate_members=True)
    async def history(self, ctx, member: discord.Member):
        """View full mod action history for a user."""
        key = f"{member.id}:{ctx.guild.id}"
        warns = self.bot.warn_data.get(key, [])

        # Fetch audit log entries for this user
        bans    = []
        kicks   = []
        mutes   = []

        try:
            async for entry in ctx.guild.audit_logs(limit=50, action=discord.AuditLogAction.ban):
                if entry.target and entry.target.id == member.id:
                    bans.append(entry)

            async for entry in ctx.guild.audit_logs(limit=50, action=discord.AuditLogAction.kick):
                if entry.target and entry.target.id == member.id:
                    kicks.append(entry)

            async for entry in ctx.guild.audit_logs(limit=50, action=discord.AuditLogAction.member_update):
                if entry.target and entry.target.id == member.id:
                    if hasattr(entry.after, 'timed_out_until') and entry.after.timed_out_until:
                        mutes.append(entry)
        except discord.Forbidden:
            pass

        embed = discord.Embed(
            title=f"📋 Mod History — {member}",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id} • {len(warns)} warning(s) • {len(bans)} ban(s) • {len(kicks)} kick(s) • {len(mutes)} mute(s)")

        # ── Warnings ──
        if warns:
            warn_lines = "\n".join(
                f"**#{i+1}** <t:{int(w['timestamp'])}:R> — {w['reason']} *(by {w['moderator']})*"
                for i, w in enumerate(warns)
            )
            embed.add_field(name=f"⚠️ Warnings ({len(warns)})", value=warn_lines[:1024], inline=False)
        else:
            embed.add_field(name="⚠️ Warnings", value="None", inline=False)

        # ── Bans ──
        if bans:
            ban_lines = "\n".join(
                f"<t:{int(e.created_at.timestamp())}:R> — {e.reason or 'No reason'} *(by {e.user})*"
                for e in bans[:5]
            )
            embed.add_field(name=f"🔨 Bans ({len(bans)})", value=ban_lines[:1024], inline=False)
        else:
            embed.add_field(name="🔨 Bans", value="None", inline=False)

        # ── Kicks ──
        if kicks:
            kick_lines = "\n".join(
                f"<t:{int(e.created_at.timestamp())}:R> — {e.reason or 'No reason'} *(by {e.user})*"
                for e in kicks[:5]
            )
            embed.add_field(name=f"👢 Kicks ({len(kicks)})", value=kick_lines[:1024], inline=False)
        else:
            embed.add_field(name="👢 Kicks", value="None", inline=False)

        # ── Mutes ──
        if mutes:
            mute_lines = "\n".join(
                f"<t:{int(e.created_at.timestamp())}:R> — {e.reason or 'No reason'} *(by {e.user})*"
                for e in mutes[:5]
            )
            embed.add_field(name=f"🔇 Mutes ({len(mutes)})", value=mute_lines[:1024], inline=False)
        else:
            embed.add_field(name="🔇 Mutes", value="None", inline=False)

        # ── Account age warning ──
        account_age_days = (discord.utils.utcnow() - member.created_at).days
        if account_age_days < 30:
            embed.add_field(
                name="⚠️ New Account",
                value=f"Account is only **{account_age_days} day(s)** old.",
                inline=False
            )

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(History(bot))
