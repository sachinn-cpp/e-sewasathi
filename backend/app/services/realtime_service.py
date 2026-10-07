"""Realtime event hub for WebSocket updates (in-process broadcaster)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


class ApplicationHub:
    """Fan-out of JSON events to WebSocket subscribers per application.

    DEMO_MODE note: MongoDB change streams would require a replica set, so the
    demo uses this in-process broadcaster. Swap ``publish`` for a change-stream
    tailer in production without touching subscribers.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}

    def subscribe(self, application_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=200)
        self._subscribers.setdefault(application_id, []).append(queue)
        return queue

    def unsubscribe(self, application_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        subscribers = self._subscribers.get(application_id, [])
        if queue in subscribers:
            subscribers.remove(queue)
        if not subscribers:
            self._subscribers.pop(application_id, None)

    async def publish(self, application_id: str, event: dict[str, Any]) -> None:
        if not get_settings().realtime_enabled:
            return
        payload = {
            **event,
            "application_id": application_id,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        for queue in list(self._subscribers.get(application_id, [])):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("WebSocket queue full for %s", application_id)


hub = ApplicationHub()


async def publish_event(application_id: str, event: dict[str, Any]) -> None:
    """Publish one event to every live subscriber of an application."""
    await hub.publish(application_id, event)
