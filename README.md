# CovasCast v1.0.0

> ⚠️ **Note:** This plugin was built with AI assistance (Claude). I'm not a Python expert — there may be bugs or rough edges. Feedback welcome!

Real-time Twitch chat integration for [COVAS:NEXT](https://ratherrude.github.io/Elite-Dangerous-AI-Integration/). COVAS listens to your Twitch chat, responds verbally to mentions, and builds passive awareness of what chat is talking about — all without interrupting your stream.

Built for streamers who want their AI to feel like a genuine part of the broadcast.

## What It Does

- **`@covas` mentions** — COVAS responds verbally when chat tags her directly
- **Background chat awareness** — chat is passively fed into COVAS's context so she always knows what's happening, even when not directly addressed
- **Verbal-only responses** — COVAS speaks her replies out loud (audible on stream) rather than posting text to chat
- **On-demand chat status** — ask COVAS to recap recent mentions or chat activity
- **Optional content moderation** — filter chat through OpenAI's moderation API before it reaches COVAS

## How It Works

CovasCast runs a TwitchIO IRC client in a background thread. It connects to your channel's chat, listens for messages, and feeds them into COVAS's context. Direct mentions trigger an immediate verbal response. All other chat is rate-limited and added to context passively — so COVAS can reference what chat has been saying without responding to every message.

COVAS responds verbally rather than posting to chat. Since she's audible on stream, viewers hear her responses naturally without the chat feed being cluttered.

---

## Setup

### Step 1 — Get a Twitch OAuth Token

You need an OAuth token with the following scopes:
- `chat:read`
- `chat:edit`

The easiest way is via [TwitchTokenGenerator](https://twitchtokengenerator.com/) — select the scopes above and generate a token. The site gives you three values — you only need the **Access Token**. 
> **Keep your token private.** Treat it like a password.

### Step 2 — Install the Plugin

1. Place the `CovasCast` folder in:
   ```
   %appdata%\com.covas-next.ui\plugins\
   ```

2. Restart COVAS:NEXT
3. Open the COVAS:NEXT menu → navigate to **CovasCast** settings
4. Fill in your settings:
   - **Twitch Channel Name**: your channel name without `#` (e.g. `lag0matic`)
   - **OAuth Token**: your Access Token prefixed with `oauth:`
   - **Mention Trigger**: the text that triggers a verbal response (default: `@covas`)
5. Start your COVAS chat session — the bot connects automatically

---

## How COVAS Responds

### Direct mentions
When chat includes your mention trigger (default `@covas`), COVAS responds verbally. Her response is audible on stream — viewers hear it through your audio.

```
Chat:  lag0matic: @covas what do you think of this build?
COVAS: [responds verbally on stream audio]
```

### Background chat awareness
All other chat messages are passively fed into COVAS's context (rate limited to one update per 10 seconds). This means COVAS builds up awareness of what chat is discussing without responding to every message. If chat has been talking about something for a few minutes, COVAS will know about it when asked.

### On-demand status
```
"Check Twitch chat"           # Recent mentions and last activity
"Any messages from chat?"     # Same
```

---

## Content Moderation (Optional)

When enabled, chat messages are checked against OpenAI's moderation API before reaching COVAS. Flagged messages are silently dropped. To enable:

1. Check **Enable OpenAI Content Moderation** in plugin settings
2. Enter your OpenAI API key

Adds a small latency and OpenAI API cost per message. Recommended only if your chat is particularly rowdy.

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
- Check your OAuth token is correctly pasted 
- Make sure your channel name has no `#` prefix in settings
- Restart COVAS:NEXT after saving settings

**`@covas` mentions not triggering a response**
- Check the Mention Trigger field in settings matches what chatters are typing (default `@covas`, case insensitive)
- Confirm COVAS chat session is active — the bot only works while a session is running

**"Not connected to Twitch"**
- Your OAuth token may have expired — generate a new one and update settings

---

## Files

```
CovasCast/
  CovasCast.py         # Main plugin
  manifest.json        # Plugin metadata
  requirements.txt     # Python dependencies
  deps/                # Bundled Python dependencies 
```

---

## Version History

**v1.0.0** — Initial release
- IRC chat connection via TwitchIO
- `@covas` mention detection with verbal response
- Rate-limited background chat context
- Optional OpenAI content moderation
- Verbal-only responses (no chat posting)

---

## Credits

**Author**: Lag0matic  
**Original concept**: [COVAS-Labs/COVAS-NEXT-Twitch-Integration](https://github.com/COVAS-Labs/COVAS-NEXT-Twitch-Integration)  
**COVAS:NEXT**: https://ratherrude.github.io/Elite-Dangerous-AI-Integration/  
**Twitch API**: TwitchIO library
