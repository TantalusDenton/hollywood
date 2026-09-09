from __future__ import annotations

import asyncio
from collections import defaultdict
from uuid import UUID

from ..models.schemas import ProjectEvent


class ProjectEventBus:
    def __init__(self) -> None:
        self._subscribers: dict[UUID, set[asyncio.Queue[ProjectEvent]]] = defaultdict(set)

    async def publish(self, event: ProjectEvent) -> None:
        for queue in list(self._subscribers[event.project_id]):
            if queue.full():
                continue
            queue.put_nowait(event)

    def subscribe(self, project_id: UUID) -> asyncio.Queue[ProjectEvent]:
        queue: asyncio.Queue[ProjectEvent] = asyncio.Queue(maxsize=100)
        self._subscribers[project_id].add(queue)
        return queue

    def unsubscribe(self, project_id: UUID, queue: asyncio.Queue[ProjectEvent]) -> None:
        self._subscribers[project_id].discard(queue)
