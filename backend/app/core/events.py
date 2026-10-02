"""Real-time event streaming bus for live investigation updates."""

import asyncio
from typing import Dict, Set, Any, AsyncGenerator
import json
import logging

logger = logging.getLogger("apex.events")


class EventBus:
    """In-memory pub/sub broker for real-time investigation streaming."""

    def __init__(self):
        # Maps investigation_id -> set of asyncio.Queue listeners
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, investigation_id: str) -> asyncio.Queue:
        """Register a subscriber queue for a specific investigation."""
        async with self._lock:
            if investigation_id not in self._subscribers:
                self._subscribers[investigation_id] = set()
            queue = asyncio.Queue(maxsize=100)
            self._subscribers[investigation_id].add(queue)
            return queue

    async def unsubscribe(self, investigation_id: str, queue: asyncio.Queue) -> None:
        """Unregister a subscriber queue."""
        async with self._lock:
            if investigation_id in self._subscribers:
                self._subscribers[investigation_id].discard(queue)
                if not self._subscribers[investigation_id]:
                    del self._subscribers[investigation_id]

    async def publish(self, investigation_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast an event to all active listeners of an investigation."""
        async with self._lock:
            queues = list(self._subscribers.get(investigation_id, []))

        payload = {
            "type": event_type,
            "investigation_id": investigation_id,
            "data": data,
        }

        for queue in queues:
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("Event queue full for investigation %s, skipping event", investigation_id)


event_bus = EventBus()
