"""Interfaces y registros de autenticación. Los códigos no tienen campo de vencimiento (P-00-3)."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Protocol

from coalsense_common import wall_clock_iso
from coalsense_common.ids import monotonic_ns

from .errors import throttled

if TYPE_CHECKING:
    from .rate_limit import RateLimiter

log = logging.getLogger("coalsense.auth")

Kind = Literal["email", "device"]


class Clock(Protocol):
    def monotonic_s(self) -> float: ...

    def now_iso(self) -> str: ...


class SystemClock:
    def monotonic_s(self) -> float:
        return monotonic_ns() / 1_000_000_000

    def now_iso(self) -> str:
        return wall_clock_iso()


@dataclass(frozen=True)
class AuthEvent:
    """Evento de bitácora: nunca lleva código, hash, correo ni su `lookup`."""

    event: str
    result: str  # ok | failed | throttled | error
    at: str
    account_id: str | None = None
    device_id: str | None = None


class AuditSink(Protocol):
    def emit(self, event: AuthEvent) -> None: ...


class CodeSender(Protocol):
    """Envía el código por correo. La implementación real llega por el gateway (V-08, H2)."""

    def send_code(self, email: str, code: str) -> None: ...


class EmailVault(Protocol):
    """Cifra el correo para `account.email_ciphertext` (spec 07)."""

    def seal(self, email: str) -> bytes: ...


@dataclass
class Account:
    id: str
    role: str
    email_ciphertext: bytes
    email_lookup: str
    # Pista del correo (p***@e***) que ve quien confirma un emparejamiento. Es un dato derivado
    # del correo: se borra junto con la cuenta (exportación y borrado, spec 07).
    email_hint: str
    language: str
    created_at: str


@dataclass
class Device:
    id: str
    account_id: str
    label: str
    paired_at: str
    revoked_at: str | None = None


@dataclass
class CodeRecord:
    """Fila de `pairing_code`. Activo = sin `used_at` ni `invalidated_at`."""

    id: str
    kind: Kind
    subject_lookup: str
    code_hash: str
    created_at: str
    attempts: int = 0
    claims: int = 0  # reclamos recibidos de un código de emparejamiento (gastan su cupo)
    claim_id: str | None = None  # id del reclamo pendiente: solo el companion lo conoce
    used_at: str | None = None
    invalidated_at: str | None = None
    account_id: str | None = None
    device_label: str | None = None


class AuthRepository(Protocol):
    def get_account_by_lookup(self, lookup: str) -> Account | None: ...

    def get_account(self, account_id: str) -> Account | None: ...

    def add_account(self, account: Account) -> None: ...

    def add_device(self, device: Device) -> None: ...

    def get_device(self, device_id: str) -> Device | None: ...

    def update_device(self, device: Device) -> None: ...

    def save_code(self, record: CodeRecord) -> None:
        """Guarda el código e invalida el activo anterior del mismo (kind, subject_lookup)."""
        ...

    def active_code(self, kind: Kind, subject_lookup: str) -> CodeRecord | None: ...

    def find_active_code(self, kind: Kind, code_hash: str) -> CodeRecord | None: ...

    def update_code(self, record: CodeRecord) -> None: ...


@dataclass(frozen=True)
class AuthDeps:
    repo: AuthRepository
    audit: AuditSink
    clock: Clock
    limiter: RateLimiter
    key: bytes = field(repr=False)
    # Un solo candado para los servicios en memoria; con PostgreSQL lo reemplaza la transacción.
    lock: threading.RLock = field(default_factory=threading.RLock)

    def emit(
        self,
        event: str,
        result: str,
        account_id: str | None = None,
        device_id: str | None = None,
    ) -> None:
        self.audit.emit(AuthEvent(event, result, self.clock.now_iso(), account_id, device_id))
        log.info("evento=%s resultado=%s", event, result)

    def guard(self, event: str, *keys: str) -> None:
        self._raise_if(event, self.limiter.retry_after(*keys))

    def guard_window(self, event: str, key: str, limit: int, window_s: int) -> None:
        self._raise_if(event, self.limiter.window_wait(key, limit, window_s))

    def _raise_if(self, event: str, wait: int) -> None:
        if wait:
            self.emit(event, "throttled")
            raise throttled(wait)
