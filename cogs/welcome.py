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
            return await ctx.reply("❌ That role is higher than my highest role.")
            
        self.bot.autorole[ctx.guild.id] = role.id
        if self.db:
            await self.db.save_autorole(ctx.guild.id, role.id)
            
        await ctx.reply(embed=discord.Embed(
            title="✅ Autorole Set",
            description=f"New members will automatically receive {role.mention}.",
            color=discord.Color.from_rgb(17, 2, 33),
            timestamp=discord.utils.utcnow(),
        ))

    @autorole.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def autorole_disable(self, ctx):
        """Disable autorole."""
        self.bot.autorole.pop(ctx.guild.id, None)
        if self.db:
            await self.db.save_autorole(ctx.guild.id, None)
            
        await ctx.reply(embed=discord.Embed(
            title="🔕 Autorole Disabled",
            color=discord.Color.from_rgb(17, 2, 33),
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
            color=discord.Color.from_rgb(17, 2, 33),
            timestamp=discord.utils.utcnow(),
        ))


async def setup(bot):
    await bot.add_cog(Welcome(bot))
```
eof

### Ready to set it up:
1. Replace your current `cogs/welcome.py` code with this updated file.
2. Go to your Discord channel and run this exact command to configure your fancy new setup:
   ```text
   !setwelcome set #welcome {user} welcome to /preserved we hope you enjoy your stay 

   https://i.pinimg.com/originals/36/19/8b/36198b95d50aab4db748e61b2bf28a6d.gif
