"""Mensajes JSON del adaptador autenticado; sin pickle, contenido ni secretos en errores."""

import hmac
import json
import threading
from dataclasses import dataclass, field

from .auth import AdapterRegistry, AdapterSession
from .core import IntentBus
from .stop_state import RouteEvidence

MAX_MESSAGE_BYTES = 65536  # [SUPUESTO] límite de transporte local por mensaje


class SessionRejected(RuntimeError):
    def __init__(self) -> None:
        super().__init__("The local adapter session was rejected")


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SessionRejected()
        result[key] = value
    return result


def _constant(_: str) -> None:
    raise SessionRejected()


def decode_message(raw: bytes) -> dict[str, object]:
    try:
        if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_MESSAGE_BYTES:
            raise SessionRejected()
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
        if not isinstance(value, dict):
            raise SessionRejected()
        return value
    except Exception:
        raise SessionRejected() from None


def encode_message(value: object) -> bytes:
    try:
        raw = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode(
            "utf-8"
        )
        if not 0 < len(raw) <= MAX_MESSAGE_BYTES:
            raise SessionRejected()
        return raw
    except Exception:
        raise SessionRejected() from None


@dataclass(frozen=True, slots=True)
class HealthReceipt:
    evidence: RouteEvidence
    received_ns: int


@dataclass(slots=True)
class PipeSession:
    bus: IntentBus = field(repr=False)
    registry: AdapterRegistry = field(repr=False)
    credential: str = field(repr=False)
    expected: AdapterSession
    _sequence: int = field(default=0, init=False)
    _closed: bool = field(default=False, init=False)
    _health: HealthReceipt | None = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def handle(self, raw: bytes, *, received_ns: int) -> bytes:
        with self._lock:
            if self._closed:
                raise SessionRejected()
            try:
                message = decode_message(raw)
                credential = message.get("credential")
                sequence = message.get("sequence")
                if (
                    type(message.get("version")) is not int
                    or message["version"] != 1
                    or type(sequence) is not int
                    or sequence != self._sequence + 1
                    or not isinstance(credential, str)
                    or not credential.isascii()
                    or not hmac.compare_digest(credential, self.credential)
                    or self.registry.authenticate(credential) != self.expected
                    or type(received_ns) is not int
                    or received_ns < 0
                ):
                    raise SessionRejected()
                kind = message.get("kind")
                if kind == "intent" and set(message) == {
                    "version",
                    "credential",
                    "sequence",
                    "kind",
                    "intent",
                }:
                    published = self.bus.publish(message["intent"], credential)
                    response = {
                        "version": 1,
                        "sequence": sequence,
                        "accepted": published.accepted,
                        "status": published.status,
                    }
                elif kind == "health" and set(message) == {
                    "version",
                    "credential",
                    "sequence",
                    "kind",
                    "health",
                }:
                    health = message["health"]
                    if not isinstance(health, dict) or set(health) != {
                        "device_streaming",
                        "model_loaded",
                        "adapter_responding",
                        "stop_bound",
                    }:
                        raise SessionRejected()
                    evidence = RouteEvidence(**health)
                    self._health = HealthReceipt(evidence, received_ns)
                    response = {
                        "version": 1,
                        "sequence": sequence,
                        "accepted": True,
                        "status": "health_received",
                    }
                else:
                    raise SessionRejected()
                self._sequence = sequence
                return encode_message(response)
            except Exception:
                self._closed, self._health = True, None
                raise SessionRejected() from None

    def take_health(self) -> HealthReceipt | None:
        with self._lock:
            value, self._health = self._health, None
            return value

    def close(self) -> None:
        with self._lock:
            self._closed, self._health = True, None
            self.credential = ""
