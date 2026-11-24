"""Sesiones efímeras de adaptadores emitidas por el supervisor confiable.

Este registro es interno al núcleo. No expone un endpoint de alta a los adaptadores.
El transporte named pipe con ACL debe autenticar cada publicación con esta credencial.
"""

import hashlib
import secrets
import threading
from dataclasses import dataclass, field

from coalsense_intents.models import ACTOR_ORIGINS, MODALITIES, ActorOrigin, Modality


@dataclass(frozen=True, slots=True)
class AdapterSession:
    adapter: str
    modality: Modality
    actor_origin: ActorOrigin


@dataclass(frozen=True, slots=True)
class AdapterCredential:
    credential: str = field(repr=False)


class AdapterRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, AdapterSession] = {}
        self._lock = threading.RLock()

    def register(
        self, adapter: str, modality: Modality, actor_origin: ActorOrigin
    ) -> AdapterCredential:
        if not adapter.strip() or len(adapter) > 128:
            raise ValueError("Invalid adapter identifier")
        if modality not in MODALITIES or actor_origin not in ACTOR_ORIGINS:
            raise ValueError("Invalid adapter session")
        credential = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[self._fingerprint(credential)] = AdapterSession(
                adapter, modality, actor_origin
            )
        return AdapterCredential(credential)

    @staticmethod
    def _fingerprint(credential: str) -> str:
        return hashlib.sha256(credential.encode()).hexdigest()

    def authenticate(self, credential: str) -> AdapterSession | None:
        if not isinstance(credential, str) or len(credential) != 43 or not credential.isascii():
            return None
        with self._lock:
            return self._sessions.get(self._fingerprint(credential))

    def revoke(self, credential: str) -> None:
        with self._lock:
            self._sessions.pop(self._fingerprint(credential), None)
