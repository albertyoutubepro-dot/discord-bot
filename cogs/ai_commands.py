import discord
from discord.ext import commands
import aiohttp
import random
import os

GROK_API_KEY = os.getenv("GROK_API_KEY")


async def ask_grok(prompt: str, system: str = "You are a helpful assistant.") -> str:
    """Send a prompt to Grok and return the response."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "grok-3-latest",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1024,
            }
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                error = await resp.text()
                return f"❌ API error {resp.status}: {error[:200]}"


class AICommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ─── !ask ─────────────────────────────────────────────────────────────────
    @commands.command(name="ask", usage="<question>")
    async def ask(self, ctx, *, question: str):
        """Ask Grok AI any question. Owner only."""
        async with ctx.typing():
            response = await ask_grok(question)

        if len(response) <= 4096:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(name="❓ Question", value=question[:1024], inline=False)
            embed.add_field(name="🤖 Answer",   value=response[:1024], inline=False)
            embed.set_footer(text="Powered by Grok AI")
            await ctx.reply(embed=embed)
        else:
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            await ctx.reply(f"**❓ {question}**\n\n{chunks[0]}")
            for chunk in chunks[1:]:
                await ctx.send(chunk)

    # ─── !roastai ─────────────────────────────────────────────────────────────
    @commands.command(name="roastai", usage="<@user>")
    async def roastai(self, ctx, member: discord.Member):
        """Grok AI generates a savage custom roast. Owner only."""
        if member == ctx.author:
            return await ctx.reply("❌ You can't roast yourself!")

        roles = [r.name for r in member.roles if r.name != "@everyone"][:5]
        join_days = (discord.utils.utcnow() - member.joined_at).days
        account_days = (discord.utils.utcnow() - member.created_at).days

        prompt = f"""Roast this Discord user in 2-3 sentences. Be savage, funny and creative.
        Use their info to make it personal:
        - Username: {member.display_name}
        - Roles: {', '.join(roles) if roles else 'no roles (literally nobody)'}
        - Days in server: {join_days}
        - Account age: {account_days} days

        Make it funny and cutting but not actually mean spirited. No slurs."""

        async with ctx.typing():
            roast = await ask_grok(prompt, system="You are a savage but funny roast comedian. Keep it under 3 sentences.")

        embed = discord.Embed(
            title=f"🔥 AI Roast — {member.display_name}",
            description=roast,
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Powered by Grok AI")
        await ctx.reply(embed=embed)

    # ─── !storytime ───────────────────────────────────────────────────────────
    @commands.command(name="storytime")
    async def storytime(self, ctx):
        """Grok AI generates a short story starring random server members. Owner only."""
        members = [m for m in ctx.guild.members if not m.bot]
        cast = random.sample(members, min(4, len(members)))
        cast_names = [m.display_name for m in cast]

        genres = ["fantasy adventure", "horror", "comedy", "mystery", "sci-fi", "romance"]
        genre = random.choice(genres)

        prompt = f"""Write a short, funny {genre} story (about 150 words) set in a Discord server called '{ctx.guild.name}'.
        The main characters are: {', '.join(cast_names)}.
        Make it entertaining, reference their names naturally. Keep it fun and appropriate."""

        async with ctx.typing():
            story = await ask_grok(prompt, system="You are a creative storyteller who writes fun short stories. Keep it under 200 words.")

        embed = discord.Embed(
            title=f"📖 Story Time — {genre.title()}",
            description=story,
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name="🎭 Starring",
            value=" • ".join(m.mention for m in cast),
            inline=False
        )
        embed.set_footer(text="Powered by Grok AI")
        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(AICommands(bot))
