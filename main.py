import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from collections import defaultdict
import time

load_dotenv()

# ─── Bot Setup ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ─── Shared State ─────────────────────────────────────────────────────────────
bot.snipe_cache     = {}   # channel_id -> { content, author, timestamp, attachments }
bot.editsnipe_cache = {}   # channel_id -> { before, after, author, timestamp }
bot.raid_data       = defaultdict(lambda: {"join_timestamps": [], "lockdown": False})
bot.warn_data       = defaultdict(list)   # "user_id:guild_id" -> [{ reason, timestamp, moderator }]
bot.log_channels    = {}                   # guild_id -> channel_id
bot.welcome_config  = {}                   # guild_id -> { channel_id, message }
bot.autorole        = {}                   # guild_id -> role_id
bot.bot_banned      = set()               # user_ids banned from using the bot
bot.uwu_channels    = set()               # channel_ids with uwu mode on

# ─── UwU Mode Hook ────────────────────────────────────────────────────────────
original_send = discord.TextChannel.send

async def uwu_send(self, content=None, **kwargs):
    if content and self.id in bot.uwu_channels:
        import random
        text = str(content)
        text = text.replace('r','w').replace('R','W').replace('l','w').replace('L','W')
        text = text.replace('you','chu').replace('You','Chu').replace('the','da').replace('The','Da')
        endings = [' uwu', ' owo', ' >w<', ' :3', ' ~', ' nya~', '']
        if text and text[-1] in '.!?':
            text = text[:-1] + random.choice(endings)
        content = text
    return await original_send(self, content, **kwargs)

discord.TextChannel.send = uwu_send

# ─── Load Cogs ────────────────────────────────────────────────────────────────
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"  ✅ Loaded cog: {filename}")

# ─── Snipe Listeners ──────────────────────────────────────────────────────────
@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot:
        return
    bot.snipe_cache[message.channel.id] = {
        "content":     message.content or "*[No text content]*",
        "author":      message.author,
        "timestamp":   time.time(),
        "attachments": [a.url for a in message.attachments],
    }

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author.bot or before.content == after.content:
        return
    bot.editsnipe_cache[before.channel.id] = {
        "before":    before.content or "*[No text content]*",
        "after":     after.content  or "*[No text content]*",
        "author":    before.author,
        "timestamp": time.time(),
    }

# ─── Anti-Raid Listener ───────────────────────────────────────────────────────
@bot.event
async def on_member_join(member: discord.Member):
    guild_id = member.guild.id
    data = bot.raid_data[guild_id]

    # Lockdown: kick newcomers immediately
    if data["lockdown"]:
        try:
            await member.send(
                embed=discord.Embed(
                    title="🔒 Server Lockdown",
                    description=f"**{member.guild.name}** is currently in lockdown due to a detected raid. Please try again later.",
                    color=discord.Color.red(),
                )
            )
        except discord.Forbidden:
            pass
        try:
            await member.kick(reason="Anti-raid lockdown active")
        except discord.Forbidden:
            pass
        return

    # Track joins in a 10-second sliding window
    now = time.time()
    data["join_timestamps"].append(now)
    data["join_timestamps"] = [t for t in data["join_timestamps"] if now - t < 10]

    # Trigger lockdown at 5+ joins in 10 seconds
    if len(data["join_timestamps"]) >= 5:
        data["lockdown"] = True
        print(f"[ANTI-RAID] Lockdown triggered in {member.guild.name}")

        # Find a mod/log channel to alert
        log_channel = discord.utils.find(
            lambda c: isinstance(c, discord.TextChannel) and
                      any(kw in c.name for kw in ("mod", "log", "admin")),
            member.guild.channels,
        )

        if log_channel:
            embed = discord.Embed(
                title="⚠️ RAID DETECTED — Lockdown Activated",
                description=(
                    f"Detected **{len(data['join_timestamps'])}** joins in the last 10 seconds.\n\n"
                    "🔒 New members are being **auto-kicked** until lockdown is lifted.\n\n"
                    "Use `!lockdown lift` to lift lockdown."
                ),
                color=discord.Color.red(),
            )
            embed.set_footer(text="Auto-lifts in 10 minutes")
            try:
                await log_channel.send(embed=embed)
            except discord.Forbidden:
                pass

        # Auto-lift after 10 minutes
        async def auto_lift():
            import asyncio
            await asyncio.sleep(600)
            bot.raid_data[guild_id]["lockdown"] = False
            print(f"[ANTI-RAID] Lockdown auto-lifted in {member.guild.name}")

        bot.loop.create_task(auto_lift())

# ─── Events ───────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"\n✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"📡 Serving {len(bot.guilds)} guild(s)")
    print(f"🤖 Prefix: !")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="the server | !help"
    ))

@bot.check
async def bot_ban_check(ctx: commands.Context):
    if ctx.author.id in bot.bot_banned:
        return False
    return True

@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(f"❌ You don't have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.reply(f"❌ I don't have the required permissions to do that.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.reply(f"❌ Member not found. Please mention them or use their ID.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(f"❌ Missing argument: `{error.param.name}`. Use `!help {ctx.command}` for usage.")
    elif isinstance(error, commands.BadArgument):
        await ctx.reply(f"❌ Invalid argument. Use `!help {ctx.command}` for usage.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Silently ignore unknown commands
    elif isinstance(error, commands.CheckFailure):
        pass  # Silently ignore unauthorized command attempts
    else:
        await ctx.reply(f"❌ An unexpected error occurred: `{error}`")
        raise error

# ─── Run ──────────────────────────────────────────────────────────────────────
async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))

import asyncio
asyncio.run(main())
