"""Lightweight in-process guards for expensive AI requests."""
import asyncio
import time
from dataclasses import dataclass

from ..core.config import env_int


@dataclass
class RequestLease:
    guard: "AIRequestGuard"
    user_id: int
    user_lock: asyncio.Lock
    waited_seconds: float = 0.0
    released: bool = False

    async def __aenter__(self) -> "RequestLease":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.release()

    def release(self) -> None:
        if self.released:
            return
        self.released = True
        if self.user_lock.locked():
            self.user_lock.release()
        self.guard.release_global()


class AIRequestGuard:
    """Limits simultaneous AI work per user and globally in one bot process.

    This is the first queue layer: requests may wait for a free global AI slot,
    but duplicate AI work from the same user is still rejected immediately.
    """

    def __init__(self) -> None:
        self.max_global = env_int("MAX_CONCURRENT_AI_REQUESTS", 20, minimum=1)
        self.queue_wait_seconds = env_int("AI_QUEUE_WAIT_SECONDS", 45, minimum=1)
        self.max_waiting = env_int("MAX_WAITING_AI_REQUESTS", 200, minimum=1)
        self._global_semaphore = asyncio.Semaphore(self.max_global)
        self._user_locks: dict[int, asyncio.Lock] = {}
        self._active_global = 0
        self._waiting_global = 0
        self._queued_total = 0
        self._queue_timeout_total = 0
        self._duplicate_user_total = 0

    async def acquire(self, user_id: int, wait_timeout: int | float | None = None) -> RequestLease | None:
        """Acquire an AI lease.

        Args:
            user_id: logical platform user id.
            wait_timeout: seconds to wait for a global slot. Use 0 for old
                fail-fast behavior. None uses AI_QUEUE_WAIT_SECONDS.
        """
        started_at = time.monotonic()
        if wait_timeout is None:
            wait_timeout = self.queue_wait_seconds

        user_lock = self._user_locks.setdefault(user_id, asyncio.Lock())
        if user_lock.locked():
            self._duplicate_user_total += 1
            return None

        global_acquired = False
        await user_lock.acquire()
        try:
            if self._global_semaphore.locked() and wait_timeout <= 0:
                user_lock.release()
                return None

            if self._global_semaphore.locked():
                if self._waiting_global >= self.max_waiting:
                    user_lock.release()
                    return None

                self._waiting_global += 1
                self._queued_total += 1
                try:
                    await asyncio.wait_for(
                        self._global_semaphore.acquire(),
                        timeout=wait_timeout,
                    )
                    global_acquired = True
                except asyncio.TimeoutError:
                    self._queue_timeout_total += 1
                    user_lock.release()
                    return None
                finally:
                    self._waiting_global = max(0, self._waiting_global - 1)
            else:
                await self._global_semaphore.acquire()
                global_acquired = True

            self._active_global += 1
            global_acquired = False
        except BaseException:
            if global_acquired:
                self._global_semaphore.release()
            if user_lock.locked():
                user_lock.release()
            raise

        waited_seconds = max(0.0, time.monotonic() - started_at)
        return RequestLease(self, user_id, user_lock, waited_seconds=waited_seconds)

    def release_global(self) -> None:
        self._active_global = max(0, self._active_global - 1)
        self._global_semaphore.release()

    def stats(self) -> dict:
        active_users = sum(1 for lock in self._user_locks.values() if lock.locked())
        return {
            "active_ai_requests": self._active_global,
            "waiting_ai_requests": self._waiting_global,
            "active_users": active_users,
            "max_concurrent_ai_requests": self.max_global,
            "max_waiting_ai_requests": self.max_waiting,
            "queue_wait_seconds": self.queue_wait_seconds,
            "queued_total": self._queued_total,
            "queue_timeout_total": self._queue_timeout_total,
            "duplicate_user_total": self._duplicate_user_total,
            "known_user_locks": len(self._user_locks),
        }


ai_request_guard = AIRequestGuard()
