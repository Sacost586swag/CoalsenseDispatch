"""Credencial por dispositivo en Windows Credential Manager (REQ-00-022).

Usa la API nativa, sin dependencias ni alternativa en texto plano. El destino separa
servicios y dispositivos sin revelar sus identificadores. Cada escritura reemplaza
la credencial anterior: el cliente debe guardarla antes del siguiente pedido.
El almacén no aplica vencimiento ni cierre por inactividad.
"""

import ctypes
import hashlib
import json
import re
import sys
from ctypes import wintypes
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlsplit

from ..win32 import last_error

_TOKEN = re.compile(r"[A-Za-z0-9_-]{43}")
_NOT_FOUND = 1168
_GENERIC = 1
_LOCAL_MACHINE = 2  # persiste para este usuario en este equipo, no en otros equipos


class CredentialStoreError(Exception):
    """Error local sin contenido del almacén ni detalles del sistema operativo."""


class CredentialBackend(Protocol):
    def read(self, target: str) -> bytes | None: ...

    def write(self, target: str, value: bytes) -> None: ...

    def delete(self, target: str) -> None: ...


@dataclass(frozen=True)
class DeviceCredential:
    session_id: str
    value: str = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.session_id, str) or not 1 <= len(self.session_id) <= 128:
            raise ValueError("Invalid session identifier")
        if not isinstance(self.value, str) or not _TOKEN.fullmatch(self.value):
            raise ValueError("Invalid device credential")


def _origin(service_origin: str) -> str:
    try:
        parsed = urlsplit(service_origin)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError
        port = parsed.port or 443
        return f"https://{parsed.hostname.lower()}:{port}"
    except ValueError:
        raise ValueError("Expected an HTTPS service origin without credentials or path") from None


class CredentialStore:
    def __init__(
        self, service_origin: str, device_id: str, *, backend: CredentialBackend | None = None
    ) -> None:
        if not isinstance(device_id, str) or not 1 <= len(device_id) <= 128:
            raise ValueError("Invalid device identifier")
        identity = json.dumps([_origin(service_origin), device_id], separators=(",", ":"))
        self._target = "CoalsenseDispatch/session/" + hashlib.sha256(identity.encode()).hexdigest()
        self._backend = backend if backend is not None else WindowsCredentialBackend()

    def load(self) -> DeviceCredential | None:
        try:
            blob = self._backend.read(self._target)
            if blob is None:
                return None
            record = json.loads(blob)
            if not isinstance(record, dict) or set(record) != {"version", "session_id", "value"}:
                raise ValueError
            if type(record["version"]) is not int or record["version"] != 1:
                raise ValueError
            return DeviceCredential(record["session_id"], record["value"])
        except (OSError, ValueError, TypeError, CredentialStoreError):
            raise CredentialStoreError("Could not read the device credential") from None

    def save(self, credential: DeviceCredential) -> None:
        blob = json.dumps(
            {
                "version": 1,
                "session_id": credential.session_id,
                "value": credential.value,
            },
            separators=(",", ":"),
        ).encode()
        try:
            self._backend.write(self._target, blob)
        except (OSError, CredentialStoreError):
            raise CredentialStoreError("Could not save the device credential") from None

    def clear(self) -> None:
        try:
            self._backend.delete(self._target)
        except (OSError, CredentialStoreError):
            raise CredentialStoreError("Could not remove the device credential") from None


class _CredentialAttribute(ctypes.Structure):
    _fields_ = [
        ("Keyword", wintypes.LPWSTR),
        ("Flags", wintypes.DWORD),
        ("ValueSize", wintypes.DWORD),
        ("Value", ctypes.POINTER(wintypes.BYTE)),
    ]


class _Credential(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(wintypes.BYTE)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.POINTER(_CredentialAttribute)),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class WindowsCredentialBackend:
    """Credenciales genéricas del usuario actual; `CredFree` libera cada lectura."""

    _read: Any
    _write: Any
    _delete: Any
    _free: Any

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise CredentialStoreError("Windows Credential Manager is required")
        try:
            api = ctypes.WinDLL("advapi32", use_last_error=True)
        except OSError:
            raise CredentialStoreError("Windows Credential Manager is unavailable") from None
        self._read = api.CredReadW
        self._read.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.POINTER(_Credential)),
        ]
        self._read.restype = wintypes.BOOL
        self._write = api.CredWriteW
        self._write.argtypes = [ctypes.POINTER(_Credential), wintypes.DWORD]
        self._write.restype = wintypes.BOOL
        self._delete = api.CredDeleteW
        self._delete.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self._delete.restype = wintypes.BOOL
        self._free = api.CredFree
        self._free.argtypes = [ctypes.c_void_p]
        self._free.restype = None

    def read(self, target: str) -> bytes | None:
        pointer = ctypes.POINTER(_Credential)()
        if not self._read(target, _GENERIC, 0, ctypes.byref(pointer)):
            if last_error() == _NOT_FOUND:
                return None
            raise CredentialStoreError("Windows credential read failed")
        try:
            record = pointer.contents
            return ctypes.string_at(record.CredentialBlob, record.CredentialBlobSize)
        finally:
            self._free(pointer)

    def write(self, target: str, value: bytes) -> None:
        if not 0 < len(value) <= 2560:
            raise CredentialStoreError("Invalid Windows credential size")
        buffer = (wintypes.BYTE * len(value)).from_buffer_copy(value)
        record = _Credential()
        record.Type = _GENERIC
        record.TargetName = target
        record.CredentialBlobSize = len(value)
        record.CredentialBlob = ctypes.cast(buffer, ctypes.POINTER(wintypes.BYTE))
        record.Persist = _LOCAL_MACHINE
        record.UserName = "CoalsenseDispatch"
        try:
            if not self._write(ctypes.byref(record), 0):
                raise CredentialStoreError("Windows credential write failed")
        finally:
            ctypes.memset(buffer, 0, len(value))

    def delete(self, target: str) -> None:
        if not self._delete(target, _GENERIC, 0) and last_error() != _NOT_FOUND:
            raise CredentialStoreError("Windows credential delete failed")
