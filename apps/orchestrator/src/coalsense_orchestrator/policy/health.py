"""Adaptador del receptor de latidos enlazado por una conexión autenticada."""

from collections.abc import Callable
from typing import Protocol

from coalsense_intents.heartbeat import HeartbeatReceiver

from coalsense_orchestrator.auth.sessions import Principal


class StopHealth(Protocol):
    async def reachable(self, principal: Principal) -> bool: ...


class DenyStopHealth:
    async def reachable(self, principal: Principal) -> bool:
        return False


class HeartbeatStopHealth:
    def __init__(self, lookup: Callable[[Principal], HeartbeatReceiver | None]) -> None:
        self._lookup = lookup

    async def reachable(self, principal: Principal) -> bool:
        receiver = self._lookup(principal)
        return type(receiver) is HeartbeatReceiver and receiver.stop_reachable is True
