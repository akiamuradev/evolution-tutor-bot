"""Guarded entrypoint for expensive AI model calls."""
import asyncio
from dataclasses import dataclass
from time import monotonic

from .ai_client import call_openrouter
from .request_guard import ai_request_guard


AI_BUSY_MESSAGE = (
    "Сейчас много запросов к ИИ. Я не потерял твое сообщение, "
    "но свободный слот не появился вовремя. Попробуй отправить его еще раз через несколько секунд."
)


@dataclass
class GuardedAIResponse:
    text: str = ""
    busy: bool = False
    waited_seconds: float = 0.0


class AIGatewayStats:
    def __init__(self) -> None:
        self.started_total = 0
        self.completed_total = 0
        self.busy_total = 0
        self.cancelled_total = 0
        self.failed_total = 0
        self.inflight_by_kind: dict[str, int] = {}
        self.model_active_by_kind: dict[str, int] = {}
        self.started_by_kind: dict[str, int] = {}
        self.completed_by_kind: dict[str, int] = {}
        self.busy_by_kind: dict[str, int] = {}
        self.cancelled_by_kind: dict[str, int] = {}
        self.failed_by_kind: dict[str, int] = {}
        self.total_waited_seconds_by_kind: dict[str, float] = {}
        self.max_waited_seconds_by_kind: dict[str, float] = {}
        self.total_duration_seconds_by_kind: dict[str, float] = {}
        self.max_duration_seconds_by_kind: dict[str, float] = {}

    def start(self, kind: str) -> None:
        self.started_total += 1
        self.inflight_by_kind[kind] = self.inflight_by_kind.get(kind, 0) + 1
        self.started_by_kind[kind] = self.started_by_kind.get(kind, 0) + 1

    def mark_model_active(self, kind: str) -> None:
        self.model_active_by_kind[kind] = self.model_active_by_kind.get(kind, 0) + 1

    def unmark_model_active(self, kind: str) -> None:
        self.model_active_by_kind[kind] = max(0, self.model_active_by_kind.get(kind, 0) - 1)

    def busy(self, kind: str) -> None:
        self.busy_total += 1
        self.busy_by_kind[kind] = self.busy_by_kind.get(kind, 0) + 1

    def cancel(self, kind: str) -> None:
        self.cancelled_total += 1
        self.cancelled_by_kind[kind] = self.cancelled_by_kind.get(kind, 0) + 1

    def complete(self, kind: str, waited_seconds: float, duration_seconds: float) -> None:
        self.completed_total += 1
        self.completed_by_kind[kind] = self.completed_by_kind.get(kind, 0) + 1
        self.total_waited_seconds_by_kind[kind] = (
            self.total_waited_seconds_by_kind.get(kind, 0.0) + waited_seconds
        )
        self.max_waited_seconds_by_kind[kind] = max(
            self.max_waited_seconds_by_kind.get(kind, 0.0),
            waited_seconds,
        )
        self.total_duration_seconds_by_kind[kind] = (
            self.total_duration_seconds_by_kind.get(kind, 0.0) + duration_seconds
        )
        self.max_duration_seconds_by_kind[kind] = max(
            self.max_duration_seconds_by_kind.get(kind, 0.0),
            duration_seconds,
        )

    def fail(self, kind: str) -> None:
        self.failed_total += 1
        self.failed_by_kind[kind] = self.failed_by_kind.get(kind, 0) + 1

    def finish(self, kind: str) -> None:
        self.inflight_by_kind[kind] = max(0, self.inflight_by_kind.get(kind, 0) - 1)

    def stats(self) -> dict:
        kinds = sorted({
            *self.started_by_kind.keys(),
            *self.completed_by_kind.keys(),
            *self.busy_by_kind.keys(),
            *self.cancelled_by_kind.keys(),
            *self.failed_by_kind.keys(),
            *self.inflight_by_kind.keys(),
            *self.model_active_by_kind.keys(),
        })
        by_kind = {}
        for kind in kinds:
            completed = self.completed_by_kind.get(kind, 0)
            total_waited = self.total_waited_seconds_by_kind.get(kind, 0.0)
            total_duration = self.total_duration_seconds_by_kind.get(kind, 0.0)
            by_kind[kind] = {
                "inflight": self.inflight_by_kind.get(kind, 0),
                "model_active": self.model_active_by_kind.get(kind, 0),
                "started": self.started_by_kind.get(kind, 0),
                "completed": completed,
                "busy": self.busy_by_kind.get(kind, 0),
                "cancelled": self.cancelled_by_kind.get(kind, 0),
                "failed": self.failed_by_kind.get(kind, 0),
                "avg_waited_seconds": round(total_waited / completed, 3) if completed else 0,
                "max_waited_seconds": round(self.max_waited_seconds_by_kind.get(kind, 0.0), 3),
                "avg_duration_seconds": round(total_duration / completed, 3) if completed else 0,
                "max_duration_seconds": round(self.max_duration_seconds_by_kind.get(kind, 0.0), 3),
            }
        return {
            "started_total": self.started_total,
            "completed_total": self.completed_total,
            "busy_total": self.busy_total,
            "cancelled_total": self.cancelled_total,
            "failed_total": self.failed_total,
            "inflight_total": sum(self.inflight_by_kind.values()),
            "model_active_total": sum(self.model_active_by_kind.values()),
            "by_kind": by_kind,
        }


ai_gateway_stats = AIGatewayStats()


async def call_openrouter_guarded(
    user_id: int,
    messages: list,
    *,
    kind: str = "unknown",
    wait_timeout: int | float | None = None,
    busy_message: str = AI_BUSY_MESSAGE,
    **kwargs,
) -> GuardedAIResponse:
    """Call OpenRouter only after acquiring the shared AI request guard."""
    kind = (kind or "unknown").strip() or "unknown"
    started_at = monotonic()
    ai_gateway_stats.start(kind)
    lease = None
    try:
        lease = await ai_request_guard.acquire(user_id, wait_timeout=wait_timeout)
        if lease is None:
            ai_gateway_stats.busy(kind)
            return GuardedAIResponse(text=busy_message, busy=True)

        ai_gateway_stats.mark_model_active(kind)
        async with lease:
            text = await call_openrouter(messages, **kwargs)
        duration_seconds = max(0.0, monotonic() - started_at)
        ai_gateway_stats.complete(kind, lease.waited_seconds, duration_seconds)
        return GuardedAIResponse(
            text=text,
            busy=False,
            waited_seconds=lease.waited_seconds,
        )
    except asyncio.CancelledError:
        ai_gateway_stats.cancel(kind)
        raise
    except BaseException:
        ai_gateway_stats.fail(kind)
        raise
    finally:
        if lease is not None:
            ai_gateway_stats.unmark_model_active(kind)
        ai_gateway_stats.finish(kind)
