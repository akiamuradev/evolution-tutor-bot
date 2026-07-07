"""In-process tracking for cancellable AI generation tasks."""
import asyncio
from dataclasses import dataclass


@dataclass
class GenerationState:
    task: asyncio.Task
    chat_id: int | None = None
    message_id: int | None = None


class GenerationRegistry:
    """Tracks one active cancellable generation per user in this process."""

    def __init__(self) -> None:
        self._items: dict[int, GenerationState] = {}
        self._lock = asyncio.Lock()
        self.cancelled_total = 0
        self.replaced_total = 0

    async def register(
        self,
        user_id: int,
        task: asyncio.Task,
        *,
        chat_id: int | None = None,
        message_id: int | None = None,
    ) -> None:
        async with self._lock:
            old = self._items.get(user_id)
            if old and not old.task.done():
                old.task.cancel()
                self.replaced_total += 1
            self._items[user_id] = GenerationState(
                task=task,
                chat_id=chat_id,
                message_id=message_id,
            )

    async def unregister(self, user_id: int, task: asyncio.Task | None = None) -> None:
        async with self._lock:
            current = self._items.get(user_id)
            if not current:
                return
            if task is None or current.task is task:
                self._items.pop(user_id, None)

    async def cancel(self, user_id: int) -> bool:
        async with self._lock:
            current = self._items.pop(user_id, None)

        if not current or current.task.done():
            return False

        current.task.cancel()
        self.cancelled_total += 1
        return True

    def stats(self) -> dict:
        active = sum(1 for item in self._items.values() if not item.task.done())
        return {
            "active_generations": active,
            "tracked_users": len(self._items),
            "cancelled_total": self.cancelled_total,
            "replaced_total": self.replaced_total,
        }


generation_registry = GenerationRegistry()
