"""In-process anti-spam middleware for Telegram updates and API actions."""
import asyncio
import os
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from ..core.config import env_float, env_int
from ..helpers import ADMIN_IDS, UNLIMITED_USERS


def _specific_env(action: str, suffix: str) -> str:
    return f"ANTISPAM_{action.upper()}_{suffix}"


def _profile_float(action: str, suffix: str, generic_name: str, default: float) -> float:
    if _specific_env(action, suffix) in os.environ:
        return env_float(_specific_env(action, suffix), default, minimum=0.0)
    return env_float(generic_name, default, minimum=0.0)


def _profile_int(action: str, suffix: str, generic_name: str, default: int) -> int:
    if _specific_env(action, suffix) in os.environ:
        return env_int(_specific_env(action, suffix), default, minimum=1)
    return env_int(generic_name, default, minimum=1)


@dataclass(frozen=True)
class AntiSpamProfile:
    action: str
    min_interval: float
    window_seconds: float
    max_events: int
    cooldown_seconds: float


@dataclass
class AntiSpamDecision:
    allowed: bool
    reason: str = ""
    action: str = "message"
    retry_after: int = 0
    notify: bool = True


class AntiSpamGuard:
    """Protects the app from per-user spam and global update spikes.

    v2 keeps independent per-action limits. A user pressing inline buttons
    should not spend the same burst budget as a user sending AI chat messages.
    """

    DEFAULTS = {
        "message": {
            "min_interval": 0.5,
            "window_seconds": 20.0,
            "max_events": 10,
            "cooldown_seconds": 15.0,
        },
        "command": {
            "min_interval": 0.25,
            "window_seconds": 10.0,
            "max_events": 12,
            "cooldown_seconds": 10.0,
        },
        "callback": {
            "min_interval": 0.2,
            "window_seconds": 10.0,
            "max_events": 20,
            "cooldown_seconds": 8.0,
        },
        "api_chat": {
            "min_interval": 0.8,
            "window_seconds": 20.0,
            "max_events": 8,
            "cooldown_seconds": 20.0,
        },
        "api_practice": {
            "min_interval": 0.4,
            "window_seconds": 20.0,
            "max_events": 14,
            "cooldown_seconds": 15.0,
        },
    }

    def __init__(self) -> None:
        self.notify_interval = env_float("ANTISPAM_NOTIFY_INTERVAL_SECONDS", 10.0, minimum=0.0)
        self.max_concurrent_updates = env_int("MAX_CONCURRENT_UPDATES", 200, minimum=1)
        self.profiles = {
            action: self._load_profile(action, defaults)
            for action, defaults in self.DEFAULTS.items()
        }

        self._counter_lock = asyncio.Lock()
        self._events: dict[tuple[str, int], deque[float]] = defaultdict(deque)
        self._cooldowns: dict[tuple[str, int], float] = {}
        self._last_seen: dict[tuple[str, int], float] = {}
        self._last_notify: dict[int, float] = {}
        self._active_updates = 0
        self._active_by_action: Counter[str] = Counter()
        self._blocked_total = 0
        self._blocked_by_reason: Counter[str] = Counter()
        self._blocked_by_action: Counter[str] = Counter()
        self._allowed_by_action: Counter[str] = Counter()

    def _load_profile(self, action: str, defaults: dict) -> AntiSpamProfile:
        return AntiSpamProfile(
            action=action,
            min_interval=_profile_float(
                action,
                "MIN_INTERVAL_SECONDS",
                "ANTISPAM_MIN_INTERVAL_SECONDS",
                defaults["min_interval"],
            ),
            window_seconds=_profile_float(
                action,
                "WINDOW_SECONDS",
                "ANTISPAM_WINDOW_SECONDS",
                defaults["window_seconds"],
            ),
            max_events=_profile_int(
                action,
                "MAX_EVENTS_PER_WINDOW",
                "ANTISPAM_MAX_EVENTS_PER_WINDOW",
                defaults["max_events"],
            ),
            cooldown_seconds=_profile_float(
                action,
                "COOLDOWN_SECONDS",
                "ANTISPAM_COOLDOWN_SECONDS",
                defaults["cooldown_seconds"],
            ),
        )

    def _profile(self, action: str) -> AntiSpamProfile:
        return self.profiles.get(action, self.profiles["message"])

    def _mark_blocked(self, action: str, reason: str) -> None:
        self._blocked_total += 1
        self._blocked_by_reason[reason] += 1
        self._blocked_by_action[action] += 1

    def _should_notify(self, user_id: int, now: float) -> bool:
        last_notify = self._last_notify.get(user_id, 0.0)
        if now - last_notify < self.notify_interval:
            return False
        self._last_notify[user_id] = now
        return True

    def check_user(self, user_id: int, action: str = "message") -> AntiSpamDecision:
        now = time.monotonic()
        profile = self._profile(action)
        key = (profile.action, user_id)

        cooldown_until = self._cooldowns.get(key, 0.0)
        if cooldown_until > now:
            self._mark_blocked(profile.action, "cooldown")
            return AntiSpamDecision(
                allowed=False,
                reason="cooldown",
                action=profile.action,
                retry_after=max(1, int(cooldown_until - now)),
                notify=self._should_notify(user_id, now),
            )

        last_seen = self._last_seen.get(key, 0.0)
        if profile.min_interval and now - last_seen < profile.min_interval:
            self._mark_blocked(profile.action, "too_fast")
            return AntiSpamDecision(
                allowed=False,
                reason="too_fast",
                action=profile.action,
                retry_after=max(1, int(profile.min_interval - (now - last_seen))),
                notify=self._should_notify(user_id, now),
            )

        events = self._events[key]
        while events and now - events[0] > profile.window_seconds:
            events.popleft()

        if len(events) >= profile.max_events:
            cooldown_until = now + profile.cooldown_seconds
            self._cooldowns[key] = cooldown_until
            self._mark_blocked(profile.action, "burst")
            return AntiSpamDecision(
                allowed=False,
                reason="burst",
                action=profile.action,
                retry_after=max(1, int(profile.cooldown_seconds)),
                notify=self._should_notify(user_id, now),
            )

        events.append(now)
        self._last_seen[key] = now
        self._allowed_by_action[profile.action] += 1
        return AntiSpamDecision(allowed=True, action=profile.action)

    async def acquire_global(self, action: str = "update") -> bool:
        async with self._counter_lock:
            if self._active_updates >= self.max_concurrent_updates:
                self._mark_blocked(action, "busy")
                return False
            self._active_updates += 1
            self._active_by_action[action] += 1
            return True

    def release_global(self, action: str = "update") -> None:
        self._active_updates = max(0, self._active_updates - 1)
        if self._active_by_action[action] > 0:
            self._active_by_action[action] -= 1

    def stats(self) -> dict:
        now = time.monotonic()
        active_cooldowns = sum(1 for until in self._cooldowns.values() if until > now)
        tracked_users = {
            user_id
            for (_action, user_id) in self._events.keys()
        }
        return {
            "active_updates": self._active_updates,
            "active_by_action": dict(self._active_by_action),
            "max_concurrent_updates": self.max_concurrent_updates,
            "tracked_users": len(tracked_users),
            "tracked_action_users": len(self._events),
            "active_cooldowns": active_cooldowns,
            "blocked_total": self._blocked_total,
            "blocked_by_reason": dict(self._blocked_by_reason),
            "blocked_by_action": dict(self._blocked_by_action),
            "allowed_by_action": dict(self._allowed_by_action),
            "profiles": {
                action: {
                    "min_interval": profile.min_interval,
                    "window_seconds": profile.window_seconds,
                    "max_events_per_window": profile.max_events,
                    "cooldown_seconds": profile.cooldown_seconds,
                }
                for action, profile in self.profiles.items()
            },
        }


anti_spam_guard = AntiSpamGuard()


def action_from_event(event: Any) -> str:
    if isinstance(event, CallbackQuery):
        return "callback"
    if isinstance(event, Message):
        text = (event.text or "").strip()
        if text.startswith("/"):
            return "command"
        return "message"
    return "update"


class AntiSpamMiddleware(BaseMiddleware):
    """Early throttle for messages and callback queries."""

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        user_id = getattr(user, "id", None)
        action = action_from_event(event)
        if not user_id or user_id in ADMIN_IDS or user_id in UNLIMITED_USERS:
            return await handler(event, data)

        decision = anti_spam_guard.check_user(user_id, action=action)
        if not decision.allowed:
            if decision.notify:
                await self._notify(event, decision)
            return None

        acquired = await anti_spam_guard.acquire_global(action=action)
        if not acquired:
            if decision.notify:
                await self._notify(event, AntiSpamDecision(False, "busy", action, 5, True))
            return None

        try:
            return await handler(event, data)
        finally:
            anti_spam_guard.release_global(action=action)

    async def _notify(self, event: Any, decision: AntiSpamDecision) -> None:
        text = (
            "Слишком много действий подряд. Подожди "
            f"{decision.retry_after or 3} сек. и попробуй снова."
        )
        try:
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=False)
        except Exception:
            pass
