# CovasCast v1.5.0

> ⚠️ **Note:** This plugin was built with AI assistance (Claude). I'm not a Python expert — there may be bugs or rough edges. Feedback welcome!

Real-time Twitch chat integration for [COVAS:NEXT](https://ratherrude.github.io/Elite-Dangerous-AI-Integration/). COVAS listens to your Twitch chat, responds verbally to mentions, and builds passive awareness of what chat is talking about — all without interrupting your stream.

Built for streamers who want their AI to feel like a genuine part of the broadcast.

## What It Does

- **`@covas` mentions** — COVAS responds verbally when chat tags her directly
- **Background chat awareness** — chat is passively fed into COVAS's context so she always knows what's happening, even when not directly addressed
- **Verbal-only responses** — COVAS speaks her replies out loud (audible on stream) rather than posting text to chat
- **On-demand chat status** — ask COVAS to recap recent mentions or chat activity
- **Optional content moderation** — filter chat through OpenAI's moderation API with configurable categories and announce or silent drop behaviour

## How It Works

CovasCast runs a TwitchIO IRC client in a background thread. It connects to your channel's chat, listens for messages, and feeds them into COVAS's context. Direct mentions trigger an immediate verbal response. All other chat is rate-limited and added to context passively — so COVAS can reference what chat has been saying without responding to every message.

COVAS responds verbally rather than posting to chat. Since she's audible on stream, viewers hear her responses naturally without the chat feed being cluttered.

---

## Setup

### Step 1 — Get a Twitch OAuth Token

You need an OAuth token with the following scopes:
- `chat:read`
- `chat:edit`

The easiest way is via [TwitchTokenGenerator](https://twitchtokengenerator.com/) — select the scopes above and generate a token. The site gives you three values — you only need the **Access Token**. Prefix it with `oauth:` so it looks like `oauth:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`. The Refresh Token and Client ID are not needed.

> **Keep your token private.** Treat it like a password.

### Step 2 — Install the Plugin

> ⚠️ **GitHub extraction note:** When downloading a release from GitHub, the zip file will extract to a folder named something like `CovasCast-v1.0.0`. You must rename this folder to just `CovasCast` before placing it in your plugins directory, otherwise COVAS:NEXT may not load it correctly.

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
When chat includes your mention trigger (default `@covas`), COVAS responds verbally. Her response is audible on stream — viewers hear it through your audio.

```
Chat:  lag0matic: @covas what do you think of this build?
COVAS: [responds verbally on stream audio]
```

### Background chat awareness
All other chat messages are passively fed into COVAS's context (rate limited to one update per 10 seconds). COVAS builds up awareness of what chat is discussing without responding to every message. If chat has been talking about something for a few minutes, COVAS will know about it when asked.

### On-demand status
```
"Check Twitch chat"           # Recent mentions and last activity
"Any messages from chat?"     # Same
```

---

## Content Moderation (Optional)

When enabled, chat messages are checked against OpenAI's moderation API before reaching COVAS.

### Settings

| Setting | Description |
|---|---|
| Enable OpenAI Content Moderation | Master on/off switch |
| Announce filtered messages | On = COVAS verbally flags filtered messages. Off = silent drop |
| Categories to filter | Comma-separated list of categories to enforce. Leave blank to enforce all |
| OpenAI API Key | Your OpenAI API key (requires billing set up at platform.openai.com) |

### Category filtering

By default only the following categories are enforced, avoiding false positives from normal gaming chat (e.g. "kill those pirates"):

```
sexual, sexual/minors, self-harm, hate
```

Available categories you can add or remove:
- `harassment` — general harassment
- `harassment/threatening` — threatening language
- `hate` — hate speech
- `hate/threatening` — threatening hate speech
- `sexual` — sexual content
- `sexual/minors` — sexual content involving minors
- `violence` — violent content *(leave off for gaming chat)*
- `violence/graphic` — graphic violence
- `self-harm` — self harm content
- `self-harm/intent` — self harm intent
- `self-harm/instructions` — self harm instructions
- `illicit` — illicit content
- `illicit/violent` — violent illicit content

> **Gaming tip:** Keep `violence` and `harassment` off the list — they generate too many false positives in gaming chat. Stick to `sexual`, `sexual/minors`, `self-harm`, and `hate` for a clean stream.

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

**Moderation not catching anything**
- Check your OpenAI account has a payment method added at platform.openai.com (required even though the moderation API is free)
- Confirm the category you're testing is in your Categories to filter list

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
**v1.5.0** — Added moderation catagory toggles. This lets you allow certain things through the filter
**v1.0.0** — Initial release
- IRC chat connection via TwitchIO
- `@covas` mention detection with verbal response
- Rate-limited background chat context (10 second intervals)
- Optional OpenAI content moderation with configurable category filtering
- Announce or silent drop behaviour for filtered messages
- Verbal-only responses (no chat posting)

---

## Credits

**Author**: Lag0matic  
**Original concept**: [COVAS-Labs/COVAS-NEXT-Twitch-Integration](https://github.com/COVAS-Labs/COVAS-NEXT-Twitch-Integration)  
**COVAS:NEXT**: https://ratherrude.github.io/Elite-Dangerous-AI-Integration/  
**Twitch API**: TwitchIO library

