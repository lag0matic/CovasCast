# CovasCast v2.0.0

> ⚠️ **Note:** This plugin was built with AI assistance (Claude). I'm not a Python expert — there may be bugs or rough edges. Feedback welcome!

Real-time Twitch chat integration for [COVAS:NEXT](https://ratherrude.github.io/Elite-Dangerous-AI-Integration/). COVAS listens to your Twitch chat, responds verbally to mentions, and builds passive awareness of what chat is talking about — all without interrupting your stream.

Built for streamers who want their AI to feel like a genuine part of the broadcast.

## What It Does

- **`@covas` mentions** — COVAS responds verbally when chat tags it directly
- **Background chat awareness** — chat is passively fed into COVAS's context so it always knows what's happening, even when not directly addressed
- **Verbal-only responses** — COVAS speaks its replies out loud (audible on stream) rather than posting text to chat
- **Bot chat posting** — optionally allow COVAS to post messages directly to chat (toggle)
- **Moderation actions** — optionally allow COVAS to timeout, ban, unban, or delete messages (individual toggles, all off by default)
- **On-demand chat status** — ask COVAS to recap recent mentions or chat activity
- **Optional content moderation** — filter chat through OpenAI's moderation API with per-category toggles and announce or silent drop behaviour

## How It Works

CovasCast runs a TwitchIO IRC client in a background thread. It connects to your channel's chat, listens for messages, and feeds them into COVAS's context. Direct mentions trigger an immediate verbal response. All other chat is rate-limited and added to context passively — so COVAS can reference what chat has been saying without responding to every message.

By default COVAS responds verbally only. Bot chat posting and moderation actions are opt-in via individual toggles in settings.

> ### ⚠️ Designed for a Dedicated Bot Account
> CovasCast is intended to run on a **separate Twitch account**, not your personal broadcaster account. Create a second Twitch account for your bot (e.g. `MyBotName`), generate an OAuth token for that account, and enter it in the plugin settings. Then mod the bot in your channel with `/mod MyBotName`.
>
> This is the standard approach used by all legitimate Twitch bots (Nightbot, StreamElements, etc.) and is **fully ToS compliant**. Running it on your personal broadcaster account will work for read-only listening, but is not recommended if you enable chat posting or moderation actions.

---

## Setup

### Step 1 — Get a Twitch OAuth Token

You need an OAuth token with the following scopes:

**For chat reading and posting:**
- `chat:read`
- `chat:edit`

**If enabling moderation actions (requires a modded bot account):**
- `moderator:manage:banned_users`
- `moderator:manage:chat_messages`

The easiest way is via [TwitchTokenGenerator](https://twitchtokengenerator.com/) — select the scopes you need and generate a token. The site gives you three values — you only need the **Access Token**. Prefix it with `oauth:` so it looks like `oauth:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`. The Refresh Token and Client ID are not needed.

> **Keep your token private.** Treat it like a password.

### Step 2 — Install the Plugin

> ⚠️ **GitHub extraction note:** When downloading a release from GitHub, the zip file will extract to a folder named something like `CovasCast-v2.0.0`. You must rename this folder to just `CovasCast` before placing it in your plugins directory, otherwise COVAS:NEXT may not load it correctly.

1. Download the latest release and extract it
2. Rename the folder to `CovasCast` (strip the version suffix)
3. Place the `CovasCast` folder in:
   ```
   %appdata%\com.covas-next.ui\plugins\
   ```
4. Dependencies are bundled — no installation step needed
5. Restart COVAS:NEXT
6. Open the COVAS:NEXT menu → navigate to **CovasCast** settings
7. Fill in your settings:
   - **Twitch Channel Name**: your channel name without `#` (e.g. `lag0matic`)
   - **OAuth Token**: your Access Token prefixed with `oauth:`
   - **Mention Trigger**: the text that triggers a verbal response (default: `@covas`)
8. Start your COVAS chat session — the bot connects automatically

---

## How COVAS Responds

### Direct mentions
When chat includes your mention trigger (default `@covas`), COVAS responds verbally. Its response is audible on stream — viewers hear it through your audio. If chat posting is enabled, it may also respond in chat.

```
Chat:  viewer: @covas what do you think of this build?
COVAS: [responds verbally on stream audio]
```

### Background chat awareness
All other chat messages are passively fed into COVAS's context (rate limited to one update per 10 seconds). COVAS builds up awareness of what chat is discussing without responding to every message.

### On-demand status
```
"Check Twitch chat"           # Recent mentions and last activity
"Any messages from chat?"     # Same
```

---

## Bot Capabilities (Optional)

All bot actions are **off by default**. Enable only what you're comfortable with. Moderation actions require the bot account to be modded in your channel.

| Toggle | What it enables | Requires mod |
|---|---|---|
| Allow: Post messages to chat | COVAS can send messages to chat | No |
| Allow: Delete messages | COVAS can delete specific messages | Yes |
| Allow: Timeout users | COVAS can temporarily mute users | Yes |
| Allow: Ban users | COVAS can permanently ban users | Yes |
| Allow: Unban / untimeout users | COVAS can lift bans and timeouts | Yes |

> **Recommendation:** Think carefully before enabling ban — that's a permanent action. Timeout is safer for AI moderation since it's reversible. If you enable moderation actions, use a dedicated bot account rather than your broadcaster token.

---

## Bot Voice Commands

These commands are spoken by **you** (the streamer) during your COVAS session. COVAS understands natural language so you don't need exact phrasing — these are just examples.

> **Important:** Bot capability toggles must be enabled in settings before these commands will work. Moderation commands also require the bot account to be modded in your channel first.

### Posting to Chat
```
"Tell chat we're taking a short break"
"Say hello to everyone in chat"
"Post in chat that the giveaway is starting"
```

### Timeout (Temporary Mute)
```
"Timeout SomeBadActor for 10 minutes"
"Mute SomeBadActor for 2 hours"
"Give SomeBadActor a 5 minute timeout for spamming"
```
Timeouts can be lifted early using the unban/untimeout command. Maximum duration is 14 days.

### Ban (Permanent)
```
"Ban SomeBadActor"
"Permanently ban SomeBadActor for hate speech"
```
> ⚠️ Bans are permanent. Use timeout for anything you might want to reverse.

### Unban / Untimeout
```
"Unban SomeBadActor"
"Untimeout SomeBadActor, they've calmed down"
"Lift the ban on SomeBadActor"
```

### Delete a Message
```
"Delete that last message from SomeBadActor"
```
> **Note:** Message deletion requires COVAS to know the message ID, which isn't always available from context. This command may not work reliably in all situations. Timeout is a more dependable way to deal with a problematic message after the fact.

---

## Content Moderation (Optional)

When enabled, chat messages are checked against OpenAI's moderation API before reaching COVAS.

### Settings

| Setting | Description |
|---|---|
| Enable OpenAI Content Moderation | Master on/off switch |
| Announce filtered messages | On = the AI verbally flags filtered messages. Off = silent drop |
| OpenAI API Key | Your OpenAI API key (requires billing set up at platform.openai.com) |

### Category toggles

Each moderation category has its own toggle. The defaults are tuned for gaming chat — categories that generate too many false positives (violence, harassment) are off by default.

| Toggle | Category | Default | Notes |
|---|---|---|---|
| Filter: Harassment | General harassment | Off | High false positive rate in gaming chat |
| Filter: Harassment / Threatening | Threatening language | Off | High false positive rate in gaming chat |
| Filter: Hate | Hate speech | **On** | |
| Filter: Hate / Threatening | Threatening hate speech | **On** | |
| Filter: Sexual | Sexual content | **On** | |
| Filter: Sexual / Minors | Sexual content involving minors | **On** | |
| Filter: Violence | Violent content | Off | Will catch "kill those pirates" — leave off for gaming |
| Filter: Violence / Graphic | Graphic violence | Off | |
| Filter: Self-harm | Self-harm content | **On** | |
| Filter: Self-harm / Intent | Self-harm intent | **On** | |
| Filter: Self-harm / Instructions | Self-harm instructions | **On** | |
| Filter: Illicit | Illicit content | Off | |
| Filter: Illicit / Violent | Violent illicit content | Off | |

> **Note:** If no category toggles are enabled, moderation will not filter anything even if the master switch is on.

---

## Token Usage

Background chat is rate-limited to one context update every 10 seconds. On a quiet channel this is negligible. On a busier channel the rate limiter keeps costs manageable even during raids.

Rough estimates per stream:
- **Quiet channel** (~10 chatters): ~50–100 tokens
- **Active channel** (~100 chatters): ~500–1,000 tokens
- **Raid scenario** (500+ messages in 30s): rate limiter caps this to the same as active channel

---

## Troubleshooting

**Bot doesn't connect**
- Check your OAuth token is correctly pasted with the `oauth:` prefix
- Make sure your channel name has no `#` prefix in settings
- Restart COVAS:NEXT after saving settings

**`@covas` mentions not triggering a response**
- Check the Mention Trigger field in settings matches what chatters are typing (default `@covas`, case insensitive)
- Confirm COVAS chat session is active — the bot only works while a session is running

**"Not connected to Twitch"**
- Your OAuth token may have expired — generate a new one and update settings

**Moderation actions not working**
- The bot account must be modded in your channel — run `/mod BotName` in your chat
- Make sure the relevant OAuth token scopes are included when generating your token
- Confirm the relevant capability toggle is enabled in settings

**Moderation not catching anything**
- Check your OpenAI account has a payment method added at platform.openai.com (required even though the moderation API is free)
- Confirm at least one category toggle is enabled in settings

---

## Files

```
CovasCast/
  CovasCast.py         # Main plugin
  manifest.json        # Plugin metadata
  requirements.txt     # Python dependencies (reference only — deps are bundled)
  deps/                # Bundled Python dependencies
```

---

## Version History

**v2.0.0** — Bot capabilities and moderation actions
- Added optional chat posting — COVAS can now post messages to Twitch chat (toggle)
- Added moderation actions — timeout, ban, unban, delete message (individual toggles, all off by default)
- All capabilities are opt-in with sensible off defaults — nothing fires without explicit permission
- Added dedicated bot account guidance — use a separate Twitch account for full bot functionality

**v1.5.0** — Added per-category moderation toggles. Each of OpenAI's 13 moderation categories now has its own on/off switch in the settings panel, with sensible gaming-friendly defaults.

**v1.0.0** — Initial release
- IRC chat connection via TwitchIO
- `@covas` mention detection with verbal response
- Rate-limited background chat context (10 second intervals)
- Optional OpenAI content moderation
- Announce or silent drop behaviour for filtered messages
- Verbal-only responses (no chat posting)

---

## Credits

**Author**: Lag0matic  
**Original concept**: [COVAS-Labs/COVAS-NEXT-Twitch-Integration](https://github.com/COVAS-Labs/COVAS-NEXT-Twitch-Integration)  
**COVAS:NEXT**: https://ratherrude.github.io/Elite-Dangerous-AI-Integration/  
**Twitch API**: TwitchIO library
