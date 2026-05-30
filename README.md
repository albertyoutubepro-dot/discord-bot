# 🤖 Discord Mod Bot (Python)

A full-featured Discord moderation bot built with **discord.py** using `!` prefix commands.  
Includes **anti-raid protection**, **mod tools**, and **snipe commands**.

---

## ✨ Features

### 🛡️ Anti-Raid
- Auto-detects raids (5+ joins in 10 seconds)
- Auto-kicks new members during lockdown & DMs them an explanation
- Alerts your `#mod-logs` / `#admin` channel with a lockdown embed
- Auto-lifts lockdown after 10 minutes
- Manual `!lockdown` commands for admins

### 🔨 Moderation
| Command | Description | Permission |
|---------|-------------|------------|
| `!ban <@user> [days] [reason]` | Ban a user | Ban Members |
| `!unban <user_id> [reason]` | Unban a user by ID | Ban Members |
| `!kick <@user> [reason]` | Kick a user | Kick Members |
| `!mute <@user> <minutes> [reason]` | Timeout a user | Moderate Members |
| `!unmute <@user>` | Remove timeout | Moderate Members |
| `!warn <@user> <reason>` | Warn a user (DMs them) | Moderate Members |
| `!warnings <@user>` | View all warnings | Moderate Members |
| `!clearwarnings <@user>` | Clear all warnings | Administrator |
| `!purge <amount> [@user]` | Bulk delete up to 100 messages | Manage Messages |
| `!slowmode <seconds>` | Set channel slowmode | Manage Channels |
| `!lock [reason]` | Lock this channel | Manage Channels |
| `!unlock` | Unlock this channel | Manage Channels |

### 🔍 Snipe
| Command | Description |
|---------|-------------|
| `!snipe` | Last **deleted** message in the channel (with attachments) |
| `!editsnipe` | Last **edited** message — before and after |

### ℹ️ Info
| Command | Description |
|---------|-------------|
| `!userinfo [@user]` | Account age, join date, roles, warnings |
| `!serverinfo` | Member count, boosts, channels, owner |
| `!help [command]` | List all commands or get details on one |

---

## 🚀 Setup Guide

### Step 1 — Create a Discord Bot

1. Go to [https://discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application** → give it a name → **Create**
3. Left sidebar → **Bot** → **Add Bot** → confirm
4. Click **Reset Token**, copy and save your token
5. Scroll down — enable these **Privileged Gateway Intents**:
   - ✅ **Server Members Intent**
   - ✅ **Message Content Intent**
6. Click **Save Changes**

### Step 2 — Invite the Bot

1. Left sidebar → **OAuth2** → **URL Generator**
2. Scopes: ✅ `bot`
3. Bot Permissions: ✅ **Administrator** (or manually: Ban Members, Kick Members, Moderate Members, Manage Messages, Manage Channels, View Channel, Send Messages, Embed Links, Read Message History)
4. Copy the URL → open in browser → select your server → **Authorize**

### Step 3 — Install Python & Dependencies

You need **Python 3.10+** — check with:
```bash
python --version
```

Install dependencies:
```bash
pip install -r requirements.txt
```

> On some systems use `pip3` instead of `pip`.

### Step 4 — Configure Environment

1. Rename `.env.example` to `.env`
2. Add your bot token:

```env
DISCORD_TOKEN=your_bot_token_here
```

You only need the token (no Client ID needed — prefix bots don't register slash commands).

### Step 5 — Run the Bot

```bash
python main.py
```

You should see:
```
✅ Loaded cog: antiraid.py
✅ Loaded cog: info.py
✅ Loaded cog: mod.py
✅ Loaded cog: snipe.py

✅ Logged in as YourBot#1234 (ID: 123456789)
📡 Serving 1 guild(s)
🤖 Prefix: !
```

---

## 🔧 Customization

### Change the Prefix

In `main.py`, line 9:
```python
bot = commands.Bot(command_prefix="!", ...)
#                                   ↑ change this
```

You can also use multiple prefixes:
```python
command_prefix=["!", "?", "."]
```

### Change the Raid Threshold

In `main.py`, around line 60:
```python
data["join_timestamps"] = [t for t in data["join_timestamps"] if now - t < 10]
#                                                                              ↑ seconds window

if len(data["join_timestamps"]) >= 5:
#                                  ↑ joins required to trigger
```

### Change Auto-Lift Duration

In `main.py`, the `auto_lift` coroutine:
```python
await asyncio.sleep(600)   # ← seconds (600 = 10 minutes)
```

### Log Channel Detection

The bot searches for a channel with `mod`, `log`, or `admin` in the name:
```python
any(kw in c.name for kw in ("mod", "log", "admin"))
# ↑ add or change keywords to match your server
```

---

## 📁 File Structure

```
discord-modbot-py/
├── main.py              # Bot setup, snipe listeners, anti-raid detection
├── requirements.txt
├── .env                 # Your token (never commit this!)
├── .env.example         # Template
└── cogs/
    ├── mod.py           # ban, unban, kick, mute, unmute, warn, warnings,
    │                    # clearwarnings, purge, slowmode, lock, unlock
    ├── antiraid.py      # !lockdown command
    ├── snipe.py         # !snipe, !editsnipe
    └── info.py          # !userinfo, !serverinfo, !help
```

---

## ⚠️ Notes

- **Warnings & snipe cache are stored in memory** — they reset on restart. For persistence, add SQLite (`aiosqlite`) or another database.
- The bot's role must be **above** the roles of members you want to moderate.
- **Message Content Intent** must be enabled in the Developer Portal for snipe and all prefix commands to work.

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| `discord.errors.LoginFailure` | Token is wrong or has spaces — recheck `.env` |
| Commands not responding | Message Content Intent not enabled in Dev Portal |
| `Missing Permissions` | Bot role is too low in the role hierarchy |
| Anti-raid not triggering | Server Members Intent not enabled in Dev Portal |
| Module not found | Run `pip install -r requirements.txt` again |
| `python` not found | Try `python3 main.py` instead |
