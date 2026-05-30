import discord
from discord.ext import commands
import random
import asyncio
import aiohttp


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ─── !8ball ───────────────────────────────────────────────────────────────
    @commands.command(name="8ball", usage="<question>")
    async def eightball(self, ctx, *, question: str):
        """Ask the magic 8ball a question."""
        responses = [
            "✅ It is certain.", "✅ It is decidedly so.", "✅ Without a doubt.",
            "✅ Yes, definitely.", "✅ You may rely on it.", "✅ As I see it, yes.",
            "✅ Most likely.", "✅ Outlook good.", "✅ Yes.", "✅ Signs point to yes.",
            "🤷 Reply hazy, try again.", "🤷 Ask again later.", "🤷 Better not tell you now.",
            "🤷 Cannot predict now.", "🤷 Concentrate and ask again.",
            "❌ Don't count on it.", "❌ My reply is no.", "❌ My sources say no.",
            "❌ Outlook not so good.", "❌ Very doubtful.",
        ]
        embed = discord.Embed(color=discord.Color.purple(), timestamp=discord.utils.utcnow())
        embed.add_field(name="❓ Question", value=question, inline=False)
        embed.add_field(name="🎱 Answer", value=random.choice(responses), inline=False)
        embed.set_footer(text=f"Asked by {ctx.author}")
        await ctx.reply(embed=embed)

    # ─── !coinflip ────────────────────────────────────────────────────────────
    @commands.command(name="coinflip", aliases=["flip", "coin"])
    async def coinflip(self, ctx):
        """Flip a coin."""
        result = random.choice(["🪙 Heads!", "🪙 Tails!"])
        await ctx.reply(embed=discord.Embed(
            title="Coin Flip", description=result,
            color=discord.Color.gold(), timestamp=discord.utils.utcnow()
        ))

    # ─── !roll ────────────────────────────────────────────────────────────────
    @commands.command(name="roll", usage="[sides=6]")
    async def roll(self, ctx, sides: int = 6):
        """Roll a dice. Default is 6 sides."""
        if sides < 2 or sides > 1000:
            return await ctx.reply("❌ Sides must be between 2 and 1000.")
        result = random.randint(1, sides)
        await ctx.reply(embed=discord.Embed(
            title=f"🎲 Dice Roll (d{sides})",
            description=f"You rolled a **{result}**!",
            color=discord.Color.blurple(), timestamp=discord.utils.utcnow()
        ))

    # ─── !rps ─────────────────────────────────────────────────────────────────
    @commands.command(name="rps", usage="<rock/paper/scissors>")
    async def rps(self, ctx, choice: str):
        """Play rock paper scissors against the bot."""
        choice = choice.lower()
        options = ["rock", "paper", "scissors"]
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

        if choice not in options:
            return await ctx.reply("❌ Choose `rock`, `paper`, or `scissors`.")

        bot_choice = random.choice(options)

        if choice == bot_choice:
            result, color = "🤝 It's a tie!", discord.Color.yellow()
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result, color = "🎉 You win!", discord.Color.green()
        else:
            result, color = "😔 You lose!", discord.Color.red()

        embed = discord.Embed(title="✂️ Rock Paper Scissors", color=color, timestamp=discord.utils.utcnow())
        embed.add_field(name="Your Choice", value=f"{emojis[choice]} {choice.title()}", inline=True)
        embed.add_field(name="My Choice",   value=f"{emojis[bot_choice]} {bot_choice.title()}", inline=True)
        embed.add_field(name="Result",      value=result, inline=False)
        await ctx.reply(embed=embed)

    # ─── !pp ──────────────────────────────────────────────────────────────────
    @commands.command(name="pp", usage="[@user]")
    async def pp(self, ctx, member: discord.Member = None):
        """Check someone's pp size 👀"""
        member = member or ctx.author
        size = random.randint(0, 15)
        bar = "8" + "=" * size + "D"
        await ctx.reply(embed=discord.Embed(
            title=f"{member.display_name}'s PP",
            description=f"`{bar}`\n**{size} inches**",
            color=discord.Color.pink() if hasattr(discord.Color, 'pink') else discord.Color.magenta(),
            timestamp=discord.utils.utcnow()
        ))

    # ─── !rate ────────────────────────────────────────────────────────────────
    @commands.command(name="rate", usage="<thing>")
    async def rate(self, ctx, *, thing: str):
        """Rate anything out of 10."""
        score = random.randint(0, 10)
        bars = "█" * score + "░" * (10 - score)
        color = discord.Color.green() if score >= 7 else discord.Color.orange() if score >= 4 else discord.Color.red()
        await ctx.reply(embed=discord.Embed(
            title=f"⭐ Rating: {thing[:50]}",
            description=f"`[{bars}]` **{score}/10**",
            color=color, timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Rated by {ctx.author}"))

    # ─── !ship ────────────────────────────────────────────────────────────────
    @commands.command(name="ship", usage="<@user1> <@user2>")
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member):
        """Ship two people together 💕"""
        score = random.randint(0, 100)
        bars = "█" * (score // 10) + "░" * (10 - score // 10)
        if score >= 80:
            verdict = "💍 Soulmates!"
        elif score >= 60:
            verdict = "💕 Great match!"
        elif score >= 40:
            verdict = "🙂 Could work..."
        elif score >= 20:
            verdict = "😬 Rough..."
        else:
            verdict = "💔 Not a chance."
        embed = discord.Embed(
            title="💘 Shipping...",
            description=f"**{user1.display_name}** ❤️ **{user2.display_name}**\n\n`[{bars}]` **{score}%**\n{verdict}",
            color=discord.Color.red(), timestamp=discord.utils.utcnow()
        )
        await ctx.reply(embed=embed)

    # ─── !truth ───────────────────────────────────────────────────────────────
    @commands.command(name="truth")
    async def truth(self, ctx):
        """Get a random truth question."""
        truths = [
            "What's the most embarrassing thing you've ever done?",
            "What's your biggest fear?",
            "Have you ever lied to get out of trouble?",
            "What's the weirdest dream you've ever had?",
            "What's something you've never told anyone?",
            "Who was your first crush?",
            "What's the most childish thing you still do?",
            "Have you ever cheated on a test?",
            "What's your most embarrassing moment in public?",
            "What's a bad habit you have?",
        ]
        await ctx.reply(embed=discord.Embed(
            title="🫦 Truth",
            description=random.choice(truths),
            color=discord.Color.blue(), timestamp=discord.utils.utcnow()
        ).set_footer(text=f"For {ctx.author.display_name}"))

    # ─── !dare ────────────────────────────────────────────────────────────────
    @commands.command(name="dare")
    async def dare(self, ctx):
        """Get a random dare."""
        dares = [
            "Send a voice message saying 'I am a potato'.",
            "Change your nickname to 'Sir Stinksalot' for 10 minutes.",
            "Send the last photo in your camera roll.",
            "Type with your elbows for the next 5 messages.",
            "Speak only in questions for the next 3 minutes.",
            "Send a message entirely in emoji.",
            "DM the 5th person in your friends list 'You are my hero'.",
            "Let the person to your left post a status for you.",
            "Do your best robot impression in a voice message.",
            "Send a selfie making the silliest face you can.",
        ]
        await ctx.reply(embed=discord.Embed(
            title="😈 Dare",
            description=random.choice(dares),
            color=discord.Color.orange(), timestamp=discord.utils.utcnow()
        ).set_footer(text=f"For {ctx.author.display_name}"))

    # ─── !wyr ─────────────────────────────────────────────────────────────────
    @commands.command(name="wyr")
    async def wyr(self, ctx):
        """Would you rather..."""
        questions = [
            ("be able to fly", "be able to be invisible"),
            ("never eat pizza again", "never eat ice cream again"),
            ("live in the past", "live in the future"),
            ("be always hot", "be always cold"),
            ("have no internet for a year", "have no friends for a year"),
            ("be super strong", "be super fast"),
            ("know how you die", "know when you die"),
            ("always have to sing instead of speak", "always have to dance when you walk"),
            ("be famous but hated", "be unknown but loved"),
            ("fight 100 duck-sized horses", "fight 1 horse-sized duck"),
        ]
        a, b = random.choice(questions)
        embed = discord.Embed(
            title="🤔 Would You Rather...",
            description=f"🅰️ **{a.capitalize()}**\n\n**OR**\n\n🅱️ **{b.capitalize()}**",
            color=discord.Color.purple(), timestamp=discord.utils.utcnow()
        )
        msg = await ctx.reply(embed=embed)
        await msg.add_reaction("🅰️")
        await msg.add_reaction("🅱️")

    # ─── !poll ────────────────────────────────────────────────────────────────
    @commands.command(name="poll", usage="<question>")
    async def poll(self, ctx, *, question: str):
        """Create a yes/no poll."""
        embed = discord.Embed(
            title="📊 Poll",
            description=question,
            color=discord.Color.blurple(), timestamp=discord.utils.utcnow()
        ).set_footer(text=f"Poll by {ctx.author}")
        msg = await ctx.reply(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

    # ─── !joke ────────────────────────────────────────────────────────────────
    @commands.command(name="joke")
    async def joke(self, ctx):
        """Get a random joke."""
        jokes = [
            ("Why don't scientists trust atoms?", "Because they make up everything!"),
            ("Why did the scarecrow win an award?", "Because he was outstanding in his field!"),
            ("I told my wife she was drawing her eyebrows too high.", "She looked surprised."),
            ("Why can't you give Elsa a balloon?", "Because she'll let it go!"),
            ("What do you call cheese that isn't yours?", "Nacho cheese!"),
            ("Why did the bicycle fall over?", "Because it was two-tired!"),
            ("What do you call a fish without eyes?", "A fsh!"),
            ("Why can't a nose be 12 inches long?", "Because then it would be a foot!"),
        ]
        setup, punchline = random.choice(jokes)
        embed = discord.Embed(title="😂 Joke", color=discord.Color.yellow(), timestamp=discord.utils.utcnow())
        embed.add_field(name="Setup",     value=setup,     inline=False)
        embed.add_field(name="Punchline", value=punchline, inline=False)
        await ctx.reply(embed=embed)

    # ─── !choose ──────────────────────────────────────────────────────────────
    @commands.command(name="choose", usage="<option1> | <option2> | ...")
    async def choose(self, ctx, *, options: str):
        """Choose between multiple options. Separate with |"""
        choices = [o.strip() for o in options.split("|") if o.strip()]
        if len(choices) < 2:
            return await ctx.reply("❌ Give at least 2 options separated by `|`. Example: `!choose pizza | burgers | tacos`")
        picked = random.choice(choices)
        await ctx.reply(embed=discord.Embed(
            title="🎯 I Choose...",
            description=f"**{picked}**",
            color=discord.Color.green(), timestamp=discord.utils.utcnow()
        ).set_footer(text=f"From {len(choices)} options"))


    # ─── !kiss ────────────────────────────────────────────────────────────────
    @commands.command(name="kiss", usage="[@user]")
    async def kiss(self, ctx, member: discord.Member = None):
        """Send a kiss gif to someone."""
        import random
        gifs = [
            "https://media1.giphy.com/media/G3va31oEEnIkM/giphy.gif",
            "https://media0.giphy.com/media/bGm9FuBCGg4SY/giphy.gif",
            "https://media2.giphy.com/media/zkppEMFvRX5FC/giphy.gif",
            "https://media3.giphy.com/media/11WPtGPPBEfTxC/giphy.gif",
            "https://media1.giphy.com/media/raiDtE5sMuDMI/giphy.gif",
        ]
        target = member.mention if member else "the air 💨"
        embed = discord.Embed(
            title=f"💋 {ctx.author.display_name} kisses {target}",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_image(url=random.choice(gifs))
        await ctx.reply(embed=embed)

    # ─── !hug ─────────────────────────────────────────────────────────────────
    @commands.command(name="hug", usage="[@user]")
    async def hug(self, ctx, member: discord.Member = None):
        """Send a hug gif to someone."""
        import random
        gifs = [
            "https://media2.giphy.com/media/l2QDM9Jnim1YVILXa/giphy.gif",
            "https://media0.giphy.com/media/3M4NpbLCTxBqU/giphy.gif",
            "https://media1.giphy.com/media/od5H3PmEG5EVq/giphy.gif",
            "https://media3.giphy.com/media/ZQN9jsRWp1M76/giphy.gif",
            "https://media2.giphy.com/media/143v0Z4767T15K/giphy.gif",
        ]
        target = member.mention if member else "everyone 🤗"
        embed = discord.Embed(
            title=f"🤗 {ctx.author.display_name} hugs {target}",
            color=discord.Color.pink() if hasattr(discord.Color, 'pink') else discord.Color.magenta(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_image(url=random.choice(gifs))
        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))
