from typing_extensions import override
import asyncio
import threading
import re
import time
import requests
import os
import sys
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

# Set up deps path before importing twitchio
current_dir = os.path.dirname(os.path.abspath(__file__))
deps_path = os.path.join(current_dir, 'deps')
if deps_path not in sys.path:
    sys.path.insert(0, deps_path)

import twitchio

from lib.PluginHelper import PluginHelper
from lib.PluginSettingDefinitions import PluginSettings, SettingsGrid, TextSetting, ToggleSetting
from lib.Logger import log
from lib.PluginBase import PluginBase, PluginManifest
from lib.Event import PluginEvent

# ============================================================================
# PARAM MODELS
# ============================================================================

class EmptyParams(BaseModel):
    pass

class ChatStatusParams(BaseModel):
    limit: Optional[int] = 5           # Number of recent mentions to retrieve

# ============================================================================
# RATE LIMITER
# Prevents background chat flooding the context window during raids or hype.
# Allows one background chat event per interval (default 10 seconds).
# ============================================================================

class RateLimiter:
    def __init__(self, interval_seconds: float = 10.0):
        self.interval = interval_seconds
        self.last_allowed = 0.0
        self.lock = threading.Lock()

    def allow(self) -> bool:
        with self.lock:
            now = time.time()
            if now - self.last_allowed >= self.interval:
                self.last_allowed = now
                return True
            return False

# ============================================================================
# TWITCHIO BOT CLIENT
# Handles IRC chat connection and EventSub WebSocket for channel alerts.
# Runs in a background thread with its own asyncio event loop.
# ============================================================================

class TwitchBot(twitchio.Client):
    def __init__(self, plugin_instance, token: str, channel: str, *args, **kwargs):
        super().__init__(token=token, *args, **kwargs)
        self.plugin = plugin_instance
        self.channel_name = channel.lower().lstrip('#')
        self.eventsub_client = None

    async def event_ready(self):
        log('info', f'COVASCAST: Connected to Twitch IRC as {self.nick}')
        self.plugin.connected = True

        # Join the channel
        await self.join_channels([self.channel_name])
        log('info', f'COVASCAST: Joined channel #{self.channel_name}')

    async def event_message(self, message: twitchio.Message):
        # Ignore our own messages
        if message.echo:
            return

        author = message.author.name if message.author else 'unknown'
        content = message.content
        mention_trigger = self.plugin.mention_trigger.lower()

        log('info', f'COVASCAST: CHAT - {author}: {content}')

        # Update recent chat cache
        self.plugin.recent_chat.append({
            'author': author,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        if len(self.plugin.recent_chat) > 100:
            self.plugin.recent_chat.pop(0)

        # OpenAI moderation check if enabled
        if self.plugin.moderation_enabled and self.plugin.openai_api_key:
            flagged, categories = self.plugin._check_moderation(content)
            if flagged:
                log('info', f'COVASCAST: Message from {author} flagged by moderation, skipping')
                if self.plugin.moderation_announce and self.plugin.helper:
                    try:
                        flagged_cats = [c for c, v in categories.items() if v]
                        self.plugin.helper.dispatch_event(PluginEvent(
                            plugin_event_name='twitch_moderated',
                            plugin_event_content={
                                'author': author,
                                'categories': ', '.join(flagged_cats) if flagged_cats else 'policy violation'
                            }
                        ))
                    except Exception as e:
                        log('info', f'COVASCAST: moderation dispatch failed: {str(e)}')
                return

        # Check for @COVAS mention — immediate reply event
        if mention_trigger and mention_trigger in content.lower():
            log('info', f'COVASCAST: Mention detected from {author}')
            self.plugin.recent_mentions.append({
                'author': author,
                'content': content,
                'timestamp': datetime.now().isoformat()
            })
            if len(self.plugin.recent_mentions) > 20:
                self.plugin.recent_mentions.pop(0)

            if self.plugin.helper:
                try:
                    self.plugin.helper.dispatch_event(PluginEvent(
                        plugin_event_name='twitch_mention',
                        plugin_event_content={
                            'author': author,
                            'message': content
                        }
                    ))
                except Exception as e:
                    log('info', f'COVASCAST: dispatch_event failed: {str(e)}')
        else:
            # Background chat — rate limited to avoid flooding context
            if self.plugin.chat_rate_limiter.allow():
                if self.plugin.helper:
                    try:
                        self.plugin.helper.dispatch_event(PluginEvent(
                            plugin_event_name='twitch_chat',
                            plugin_event_content={
                                'author': author,
                                'message': content
                            }
                        ))
                    except Exception as e:
                        log('info', f'COVASCAST: dispatch_event failed: {str(e)}')

    async def event_error(self, error: Exception, data=None):
        log('info', f'COVASCAST: IRC error: {str(error)}')


# ============================================================================
# MAIN PLUGIN CLASS
# ============================================================================

class CovasCastPlugin(PluginBase):

    def __init__(self, plugin_manifest: PluginManifest):
        super().__init__(plugin_manifest)

        self.bot = None
        self.bot_thread = None
        self.bot_loop = None
        self.connected = False
        self.helper = None

        # Local state cache
        self.recent_chat = []           # Rolling buffer of last 100 chat messages
        self.recent_mentions = []       # Rolling buffer of last 20 @COVAS mentions
        self.last_alert = None          # Most recent channel alert (follow/sub/raid etc.)
        self.viewer_count = 0

        # Rate limiter for background chat — 1 context update per 10 seconds
        self.chat_rate_limiter = RateLimiter(interval_seconds=10.0)

        # Settings cache
        self.channel = ''
        self.mention_trigger = '@covas'
        self.moderation_enabled = False
        self.moderation_announce = False
        self.moderation_categories = set()
        self.openai_api_key = ''

    settings_config = PluginSettings(
        key="CovasCastPlugin",
        label="CovasCast",
        icon="live_tv",
        grids=[
            SettingsGrid(
                key="twitch_settings",
                label="Twitch Settings",
                fields=[
                    TextSetting(
                        key="channel",
                        label="Twitch Channel Name",
                        type="text",
                        readonly=False,
                        placeholder="your_channel_name",
                        default_value=""
                    ),
                    TextSetting(
                        key="oauth_token",
                        label="OAuth Token (Access Token only)",
                        type="text",
                        readonly=False,
                        placeholder="oauth:xxxxxxxx  (Access Token from TwitchTokenGenerator)",
                        default_value=""
                    ),
                    TextSetting(
                        key="mention_trigger",
                        label="Mention Trigger",
                        type="text",
                        readonly=False,
                        placeholder="@covas",
                        default_value="@covas"
                    ),
                ]
            ),
            SettingsGrid(
                key="moderation_settings",
                label="OpenAI Moderation (Optional)",
                fields=[
                    ToggleSetting(
                        key="moderation_enabled",
                        label="Enable OpenAI Content Moderation",
                        type="toggle",
                        readonly=False,
                        placeholder=None,
                        default_value=False
                    ),
                    ToggleSetting(
                        key="moderation_announce",
                        label="Announce filtered messages (off = silent drop)",
                        type="toggle",
                        readonly=False,
                        placeholder=None,
                        default_value=False
                    ),
                    TextSetting(
                        key="moderation_categories",
                        label="Categories to filter (comma-separated, leave blank for all)",
                        type="text",
                        readonly=False,
                        placeholder="sexual, sexual/minors, self-harm, hate",
                        default_value="sexual, sexual/minors, self-harm, hate"
                    ),
                    TextSetting(
                        key="openai_api_key",
                        label="OpenAI API Key",
                        type="text",
                        readonly=False,
                        placeholder="sk-...",
                        default_value=""
                    ),
                ]
            )
        ]
    )

    @override
    def get_settings_config(self):
        return self.settings_config

    def on_settings_changed(self, settings: dict):
        self.settings = settings
        self.channel = settings.get('channel', '').strip().lstrip('#')
        self.mention_trigger = settings.get('mention_trigger', '@covas').strip()
        self.moderation_enabled = settings.get('moderation_enabled', False)
        self.moderation_announce = settings.get('moderation_announce', False)
        self.openai_api_key = settings.get('openai_api_key', '').strip()

        # Parse category filter — empty means all categories enforced
        raw_cats = settings.get('moderation_categories', '').strip()
        if raw_cats:
            self.moderation_categories = {c.strip().lower() for c in raw_cats.split(',') if c.strip()}
        else:
            self.moderation_categories = set()  # empty = enforce all

    # -------------------------------------------------------------------------
    # LIFECYCLE
    # -------------------------------------------------------------------------

    @override
    def on_chat_start(self, helper: PluginHelper):
        self.helper = helper
        log('info', 'COVASCAST: Chat started')

        try:
            # Register events
            helper.register_event(
                name='twitch_mention',
                should_reply_check=lambda e: True,
                prompt_generator=self._mention_prompt
            )
            helper.register_event(
                name='twitch_alert',
                should_reply_check=lambda e: True,
                prompt_generator=self._alert_prompt
            )
            helper.register_event(
                name='twitch_chat',
                should_reply_check=lambda e: False,  # Background context only
                prompt_generator=self._chat_background_prompt
            )
            helper.register_event(
                name='twitch_moderated',
                should_reply_check=lambda e: True,
                prompt_generator=self._moderated_prompt
            )

            # Register tools
            helper.register_action(
                'twitch_status',
                "Get recent Twitch chat mentions and channel status on demand.",
                ChatStatusParams, self.twitch_status, 'global'
            )

            # Register status generator
            helper.register_status_generator(self.generate_twitch_status)

            # Start bot
            token = self.settings.get('oauth_token', '').strip()
            channel = self.settings.get('channel', '').strip().lstrip('#')

            if token and channel:
                self._start_bot(token, channel)
            else:
                log('info', 'COVASCAST: Missing OAuth token or channel name. Configure in plugin settings.')

            log('info', 'COVASCAST: Setup complete')

        except Exception as e:
            log('info', f'COVASCAST: Failed during chat start: {str(e)}')

    @override
    def on_chat_stop(self, helper: PluginHelper):
        log('info', 'COVASCAST: Chat stopped — disconnecting')
        self._stop_bot()
        self.helper = None

    # -------------------------------------------------------------------------
    # BOT THREAD MANAGEMENT
    # -------------------------------------------------------------------------

    def _start_bot(self, token: str, channel: str):
        """Start TwitchIO bot in a dedicated background thread."""
        try:
            self.bot_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.bot_loop)
            self.bot = TwitchBot(
                plugin_instance=self,
                token=token,
                channel=channel
            )

            def run_bot():
                asyncio.set_event_loop(self.bot_loop)
                try:
                    self.bot_loop.run_until_complete(self.bot.start())
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    log('info', f'COVASCAST: Bot error: {str(e)}')
                finally:
                    self.connected = False
                    log('info', 'COVASCAST: Bot stopped')

            self.bot_thread = threading.Thread(target=run_bot, daemon=True)
            self.bot_thread.start()
            log('info', 'COVASCAST: Bot thread started')

        except Exception as e:
            log('info', f'COVASCAST: Failed to start bot: {str(e)}')

    def _stop_bot(self):
        """Gracefully shut down the TwitchIO bot."""
        try:
            if self.bot and self.bot_loop and not self.bot_loop.is_closed():
                future = asyncio.run_coroutine_threadsafe(
                    self.bot.close(),
                    self.bot_loop
                )
                future.result(timeout=5)
        except Exception as e:
            log('info', f'COVASCAST: Error stopping bot: {str(e)}')
        finally:
            self.connected = False
            self.bot = None

    def _run_async(self, coro):
        """Run a coroutine on the bot's event loop from a sync context."""
        if not self.bot_loop or self.bot_loop.is_closed():
            raise RuntimeError("Bot event loop is not running.")
        future = asyncio.run_coroutine_threadsafe(coro, self.bot_loop)
        return future.result(timeout=10)

    # -------------------------------------------------------------------------
    # ALERT DISPATCHER
    # Called by TwitchBot EventSub handlers
    # -------------------------------------------------------------------------

    def _fire_alert(self, alert_type: str, **kwargs):
        """Fire a channel alert event into COVAS context."""
        self.last_alert = {
            'type': alert_type,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }

        if self.helper:
            self.helper.dispatch_event(PluginEvent(
                plugin_event_name='twitch_alert',
                plugin_event_content={
                    'type': alert_type,
                    **kwargs
                }
            ))

    # -------------------------------------------------------------------------
    # EVENT PROMPT GENERATORS
    # -------------------------------------------------------------------------

    def _mention_prompt(self, event: PluginEvent) -> str:
        author = event.plugin_event_content.get('author', 'Someone')
        message = event.plugin_event_content.get('message', '')
        return (
            f"Twitch chatter {author} mentioned you in chat: \"{message}\". "
            f"Respond verbally to their message."
        )

    def _alert_prompt(self, event: PluginEvent) -> str:
        content = event.plugin_event_content
        alert_type = content.get('type', '')
        user = content.get('user', 'Someone')

        prompts = {
            'follow': f"{user} just followed the channel! Welcome them warmly.",
            'sub': f"{user} just subscribed ({content.get('tier', 'Tier 1')})! Celebrate their subscription.",
            'resub': (
                f"{user} resubscribed for {content.get('months', 1)} months!"
                + (f" They said: \"{content.get('message')}\"" if content.get('message') else '')
                + " Acknowledge their loyalty."
            ),
            'giftsub': f"{user} gifted {content.get('total', 1)} subscription(s) to the community! Thank them for their generosity.",
            'bits': (
                f"{user} cheered {content.get('amount', 0)} bits!"
                + (f" They said: \"{content.get('message')}\"" if content.get('message') else '')
                + " Thank them enthusiastically."
            ),
            'raid': f"{user} is raiding with {content.get('viewers', 0)} viewers! Welcome the raiding party.",
            'redeem': f"{user} redeemed the channel point reward \"{content.get('reward', 'a reward')}\". Acknowledge their redemption.",
        }

        return prompts.get(alert_type, f"A Twitch event occurred: {alert_type} from {user}.")

    def _chat_background_prompt(self, event: PluginEvent) -> str:
        """Background chat — added to context but no reply triggered."""
        author = event.plugin_event_content.get('author', 'unknown')
        message = event.plugin_event_content.get('message', '')
        return f"Twitch chat — {author}: {message}"

    def _moderated_prompt(self, event: PluginEvent) -> str:
        """Fired when a message is filtered by content moderation."""
        author = event.plugin_event_content.get('author', 'unknown')
        categories = event.plugin_event_content.get('categories', 'policy violation')
        return (
            f"A message from Twitch chatter {author} was filtered by content moderation "
            f"({categories}). Briefly acknowledge that a message was filtered if appropriate."
        )

    # -------------------------------------------------------------------------
    # STATUS GENERATOR
    # Reads from local cache only — no API calls per turn.
    # -------------------------------------------------------------------------

    def generate_twitch_status(self, projected_states: dict) -> list[tuple[str, str]]:
        """Push Twitch connection state into context each turn."""
        try:
            if not self.connected:
                return [("Twitch", "Not connected")]

            channel = self.channel or 'unknown'
            parts = [f"Live on #{channel}"]

            if self.last_alert:
                alert_type = self.last_alert.get('type', '')
                user = self.last_alert.get('user', '')
                time_str = self._relative_time(self.last_alert.get('timestamp', ''))
                parts.append(f"Last alert: {alert_type} from {user}{time_str}")

            return [("Twitch", " | ".join(parts))]

        except Exception as e:
            log('info', f'COVASCAST: Status generator error: {str(e)}')
            return [("Twitch", "Connected")]

    def _relative_time(self, timestamp: str) -> str:
        if not timestamp:
            return ''
        try:
            dt = datetime.fromisoformat(timestamp)
            mins = int((datetime.now() - dt).total_seconds() // 60)
            if mins < 1:
                return ' (just now)'
            elif mins < 60:
                return f' ({mins}m ago)'
            else:
                return f' ({mins // 60}h ago)'
        except:
            return ''

    # -------------------------------------------------------------------------
    # TOOLS
    # -------------------------------------------------------------------------

    def twitch_send_chat(self, args, projected_states) -> str:
        """Send a message to Twitch chat."""
        try:
            if not self.connected or not self.bot:
                return "COVASCAST: Not connected to Twitch."

            if not args.message:
                return "COVASCAST: No message provided."

            channel = self.channel

            async def send():
                ch = self.bot.get_channel(channel)
                if not ch:
                    ch = await self.bot.fetch_channel(channel)
                await ch.send(args.message)

            self._run_async(send())
            log('info', f'COVASCAST: Sent to chat: {args.message[:50]}')
            return f"COVASCAST: Sent to chat: {args.message}"

        except Exception as e:
            log('info', f'COVASCAST: Send chat failed: {str(e)}')
            return f"COVASCAST: Failed to send message — {str(e)}"

    def twitch_status(self, args, projected_states) -> str:
        """Return recent mentions and channel status from local cache."""
        try:
            if not self.connected:
                return "COVASCAST: Not connected to Twitch."

            limit = min(args.limit or 5, 20)
            lines = [f"COVASCAST: Channel #{self.channel}"]

            if self.recent_mentions:
                recent = self.recent_mentions[-limit:]
                lines.append(f"\nRecent mentions ({len(recent)}):")
                for m in recent:
                    time_str = self._relative_time(m.get('timestamp', ''))
                    lines.append(f"  {m['author']}{time_str}: {m['content']}")
            else:
                lines.append("\nNo recent mentions.")

            if self.last_alert:
                alert_type = self.last_alert.get('type', '')
                user = self.last_alert.get('user', '')
                time_str = self._relative_time(self.last_alert.get('timestamp', ''))
                lines.append(f"\nLast alert: {alert_type} from {user}{time_str}")

            return "\n".join(lines)

        except Exception as e:
            log('info', f'COVASCAST: Status check failed: {str(e)}')
            return f"COVASCAST: Failed to get status — {str(e)}"

    # -------------------------------------------------------------------------
    # OPENAI MODERATION
    # -------------------------------------------------------------------------

    def _check_moderation(self, text: str) -> tuple:
        """Check text against OpenAI moderation API. Returns (is_flagged, categories).
        Only flags if one of the configured categories is triggered."""
        if not self.openai_api_key:
            return False, {}
        try:
            response = requests.post(
                "https://api.openai.com/v1/moderations",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_api_key}"
                },
                json={"input": text},
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()["results"][0]
                categories = result["categories"]

                # Determine which categories triggered
                flagged_cats = {c for c, v in categories.items() if v}

                # If a category filter is configured, only care about those categories
                if self.moderation_categories:
                    flagged_cats = flagged_cats & self.moderation_categories

                is_flagged = len(flagged_cats) > 0

                if is_flagged:
                    log('info', f'COVASCAST: Message flagged — {", ".join(flagged_cats)}')

                return is_flagged, {c: (c in flagged_cats) for c in categories}
            return False, {}
        except Exception as e:
            log('info', f'COVASCAST: Moderation check failed: {str(e)}')
            return False, {}
