import discord
from discord.ext import commands
import aiosqlite
import json
import time
from collections import defaultdict

DB_PATH = "death_bot.db"


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.setup_and_load())

    # ─── Schema ───────────────────────────────────────────────────────────────
    async def setup_and_load(self):
        await self.create_tables()
        await self.load_all()

    async def create_tables(self):
        async with aiosqlite.connect(DB_PATH) as db:
            # Levels (already existed — keep as-is)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS levels (
                    user_id    INTEGER,
                    guild_id   INTEGER,
                    xp         INTEGER DEFAULT 0,
                    messages   INTEGER DEFAULT 0,
                    vc_minutes INTEGER DEFAULT 0,
                    last_seen  INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS message_log (
                    user_id   INTEGER,
                    guild_id  INTEGER,
                    timestamp INTEGER
                )
            """)

            # Guild settings (one row per guild)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id          INTEGER PRIMARY KEY,
                    log_channel       INTEGER,
                    welcome_channel   INTEGER,
                    welcome_message   TEXT,
                    autorole          INTEGER,
                    level_channel     INTEGER,
                    changelog_channel INTEGER,
                    antinuke_enabled  INTEGER DEFAULT 0
                )
            """)

            # Warns
            await db.execute("""
                CREATE TABLE IF NOT EXISTS warns (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id    INTEGER,
                    guild_id   INTEGER,
                    reason     TEXT,
                    moderator  TEXT,
                    timestamp  REAL
                )
            """)

            # Level roles
            await db.execute("""
                CREATE TABLE IF NOT EXISTS level_roles (
                    guild_id INTEGER,
                    level    INTEGER,
                    role_id  INTEGER,
                    PRIMARY KEY (guild_id, level)
                )
            """)

            # Antinuke whitelist
            await db.execute("""
                CREATE TABLE IF NOT EXISTS antinuke_whitelist (
                    guild_id INTEGER,
                    user_id  INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)

            # Bot bans (global)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_banned (
                    user_id INTEGER PRIMARY KEY
                )
            """)

            # Marriages
            await db.execute("""
                CREATE TABLE IF NOT EXISTS marriages (
                    user_id    INTEGER PRIMARY KEY,
                    partner_id INTEGER
                )
            """)

            await db.commit()

    # ─── Load everything into memory on startup ───────────────────────────────
    async def load_all(self):
        async with aiosqlite.connect(DB_PATH) as db:

            # guild_settings
            async with db.execute("SELECT * FROM guild_settings") as cursor:
                async for row in cursor:
                    (guild_id, log_ch, wel_ch, wel_msg,
                     autorole, lvl_ch, changelog_ch, antinuke) = row

                    if log_ch:
                        self.bot.log_channels[guild_id] = log_ch
                    if wel_ch and wel_msg:
                        self.bot.welcome_config[guild_id] = {
                            "channel_id": wel_ch,
                            "message": wel_msg,
                        }
                    if autorole:
                        self.bot.autorole[guild_id] = autorole
                    if lvl_ch:
                        self.bot.level_channels[guild_id] = lvl_ch
                    if changelog_ch:
                        self.bot.changelog_channels[guild_id] = changelog_ch
                    if antinuke:
                        self.bot.antinuke_enabled.add(guild_id)

            # warns
            async with db.execute("SELECT user_id, guild_id, reason, moderator, timestamp FROM warns") as cursor:
                async for row in cursor:
                    user_id, guild_id, reason, moderator, timestamp = row
                    key = f"{user_id}:{guild_id}"
                    self.bot.warn_data[key].append({
                        "reason": reason,
                        "moderator": moderator,
                        "timestamp": timestamp,
                    })

            # level_roles
            async with db.execute("SELECT guild_id, level, role_id FROM level_roles") as cursor:
                async for row in cursor:
                    guild_id, level, role_id = row
                    if guild_id not in self.bot.level_roles:
                        self.bot.level_roles[guild_id] = {}
                    self.bot.level_roles[guild_id][level] = role_id

            # antinuke whitelist
            async with db.execute("SELECT guild_id, user_id FROM antinuke_whitelist") as cursor:
                async for row in cursor:
                    guild_id, user_id = row
                    self.bot.antinuke_whitelist[guild_id].add(user_id)

            # bot_banned
            async with db.execute("SELECT user_id FROM bot_banned") as cursor:
                async for row in cursor:
                    self.bot.bot_banned.add(row[0])

            # marriages
            async with db.execute("SELECT user_id, partner_id FROM marriages") as cursor:
                async for row in cursor:
                    self.bot.marriages[row[0]] = row[1]

    # ─── Save helpers (called from other cogs) ────────────────────────────────

    async def save_log_channel(self, guild_id: int, channel_id: int | None):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, log_channel)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET log_channel = ?
            """, (guild_id, channel_id, channel_id))
            await db.commit()

    async def save_welcome(self, guild_id: int, channel_id: int | None, message: str | None):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, welcome_channel, welcome_message)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    welcome_channel = ?,
                    welcome_message = ?
            """, (guild_id, channel_id, message, channel_id, message))
            await db.commit()

    async def save_autorole(self, guild_id: int, role_id: int | None):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, autorole)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET autorole = ?
            """, (guild_id, role_id, role_id))
            await db.commit()

    async def save_level_channel(self, guild_id: int, channel_id: int | None):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, level_channel)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET level_channel = ?
            """, (guild_id, channel_id, channel_id))
            await db.commit()

    async def save_changelog_channel(self, guild_id: int, channel_id: int | None):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, changelog_channel)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET changelog_channel = ?
            """, (guild_id, channel_id, channel_id))
            await db.commit()

    async def save_antinuke_enabled(self, guild_id: int, enabled: bool):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, antinuke_enabled)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET antinuke_enabled = ?
            """, (guild_id, int(enabled), int(enabled)))
            await db.commit()

    async def save_warn(self, user_id: int, guild_id: int, reason: str, moderator: str, timestamp: float):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO warns (user_id, guild_id, reason, moderator, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, guild_id, reason, moderator, timestamp))
            await db.commit()

    async def clear_warns(self, user_id: int, guild_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "DELETE FROM warns WHERE user_id=? AND guild_id=?",
                (user_id, guild_id)
            )
            await db.commit()

    async def save_level_role(self, guild_id: int, level: int, role_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO level_roles (guild_id, level, role_id)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id, level) DO UPDATE SET role_id = ?
            """, (guild_id, level, role_id, role_id))
            await db.commit()

    async def save_antinuke_whitelist_add(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT OR IGNORE INTO antinuke_whitelist (guild_id, user_id) VALUES (?, ?)
            """, (guild_id, user_id))
            await db.commit()

    async def save_antinuke_whitelist_remove(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "DELETE FROM antinuke_whitelist WHERE guild_id=? AND user_id=?",
                (guild_id, user_id)
            )
            await db.commit()

    async def save_bot_ban(self, user_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO bot_banned (user_id) VALUES (?)", (user_id,))
            await db.commit()

    async def save_bot_unban(self, user_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM bot_banned WHERE user_id=?", (user_id,))
            await db.commit()

    async def save_marriage(self, user1_id: int, user2_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT OR REPLACE INTO marriages (user_id, partner_id) VALUES (?, ?)
            """, (user1_id, user2_id))
            await db.execute("""
                INSERT OR REPLACE INTO marriages (user_id, partner_id) VALUES (?, ?)
            """, (user2_id, user1_id))
            await db.commit()

    async def delete_marriage(self, user1_id: int, user2_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM marriages WHERE user_id=? OR user_id=?", (user1_id, user2_id))
            await db.commit()


async def setup(bot):
    await bot.add_cog(Database(bot))
