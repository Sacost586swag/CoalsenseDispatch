"""Named pipe Win32 local, ACL del usuario y E/S solapada cancelable.

Una instancia aleatoria por adaptador, sin herencia de handles. La ACL protegida
contiene únicamente el SID del usuario actual. Se comprueba además el PID del par
antes de transferir credenciales. Los errores son fijos y no incluyen el mensaje.
"""

from __future__ import annotations

import ctypes
import re
import sys
import threading
from typing import Any
from uuid import uuid4

from ..win32 import last_error
from .session import MAX_MESSAGE_BYTES

_DWORD = ctypes.c_uint32
_BOOL = ctypes.c_int32
_HANDLE = ctypes.c_void_p
_INVALID = ctypes.c_void_p(-1).value
_PREFIX = "\\\\.\\pipe\\CoalsenseDispatch."
_NAME = re.compile(re.escape(_PREFIX) + r"[a-f0-9]{32}")


class PipeFailure(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Windows could not complete the local adapter channel operation")


class PipeTimeout(PipeFailure):
    pass


class PipeClosed(PipeFailure):
    pass


class _SecurityAttributes(ctypes.Structure):
    _fields_ = [("length", _DWORD), ("descriptor", ctypes.c_void_p), ("inherit", _BOOL)]


class _Overlapped(ctypes.Structure):
    _fields_ = [
        ("internal", ctypes.c_size_t),
        ("internal_high", ctypes.c_size_t),
        ("offset", _DWORD),
        ("offset_high", _DWORD),
        ("event", _HANDLE),
    ]


def _function(dll: Any, name: str, args: list[Any], result: Any) -> Any:
    function = getattr(dll, name)
    function.argtypes, function.restype = args, result
    return function


class _Api:
    close: Any
    free: Any
    current: Any
    open_token: Any
    token_info: Any
    sid_string: Any
    sddl_descriptor: Any
    create_pipe: Any
    open_pipe: Any
    set_mode: Any
    connect: Any
    disconnect: Any
    client_pid: Any
    server_pid: Any
    create_event: Any
    wait: Any
    cancel: Any
    result: Any
    read: Any
    write: Any

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise PipeFailure()
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        security = ctypes.WinDLL("advapi32", use_last_error=True)
        pointer = ctypes.c_void_p
        dword_p = ctypes.POINTER(_DWORD)
        overlapped_p = ctypes.POINTER(_Overlapped)
        self.close = _function(kernel, "CloseHandle", [_HANDLE], _BOOL)
        self.free = _function(kernel, "LocalFree", [pointer], pointer)
        self.current = _function(kernel, "GetCurrentProcess", [], _HANDLE)
        self.open_token = _function(
            security, "OpenProcessToken", [_HANDLE, _DWORD, ctypes.POINTER(_HANDLE)], _BOOL
        )
        self.token_info = _function(
            security,
            "GetTokenInformation",
            [_HANDLE, ctypes.c_uint32, pointer, _DWORD, dword_p],
            _BOOL,
        )
        self.sid_string = _function(
            security, "ConvertSidToStringSidW", [pointer, ctypes.POINTER(ctypes.c_wchar_p)], _BOOL
        )
        self.sddl_descriptor = _function(
            security,
            "ConvertStringSecurityDescriptorToSecurityDescriptorW",
            [ctypes.c_wchar_p, _DWORD, ctypes.POINTER(pointer), dword_p],
            _BOOL,
        )
        self.create_pipe = _function(
            kernel,
            "CreateNamedPipeW",
            [
                ctypes.c_wchar_p,
                _DWORD,
                _DWORD,
                _DWORD,
                _DWORD,
                _DWORD,
                _DWORD,
                ctypes.POINTER(_SecurityAttributes),
            ],
            _HANDLE,
        )
        self.open_pipe = _function(
            kernel,
            "CreateFileW",
            [ctypes.c_wchar_p, _DWORD, _DWORD, pointer, _DWORD, _DWORD, _HANDLE],
            _HANDLE,
        )
        self.set_mode = _function(
            kernel, "SetNamedPipeHandleState", [_HANDLE, dword_p, pointer, pointer], _BOOL
        )
        self.connect = _function(kernel, "ConnectNamedPipe", [_HANDLE, overlapped_p], _BOOL)
        self.disconnect = _function(kernel, "DisconnectNamedPipe", [_HANDLE], _BOOL)
        self.client_pid = _function(
            kernel, "GetNamedPipeClientProcessId", [_HANDLE, dword_p], _BOOL
        )
        self.server_pid = _function(
            kernel, "GetNamedPipeServerProcessId", [_HANDLE, dword_p], _BOOL
        )
        self.create_event = _function(
            kernel, "CreateEventW", [pointer, _BOOL, _BOOL, ctypes.c_wchar_p], _HANDLE
        )
        self.wait = _function(kernel, "WaitForSingleObject", [_HANDLE, _DWORD], _DWORD)
        self.cancel = _function(kernel, "CancelIoEx", [_HANDLE, overlapped_p], _BOOL)
        self.result = _function(
            kernel, "GetOverlappedResult", [_HANDLE, overlapped_p, dword_p, _BOOL], _BOOL
        )
        self.read = _function(
            kernel, "ReadFile", [_HANDLE, pointer, _DWORD, dword_p, overlapped_p], _BOOL
        )
        self.write = _function(
            kernel, "WriteFile", [_HANDLE, pointer, _DWORD, dword_p, overlapped_p], _BOOL
        )

    def user_sid(self) -> str:
        token, text = _HANDLE(), ctypes.c_wchar_p()
        if not self.open_token(self.current(), 8, ctypes.byref(token)):
            raise PipeFailure()
        try:
            size = _DWORD()
            self.token_info(token, 1, None, 0, ctypes.byref(size))  # TokenUser
            if not 0 < size.value <= 65536:
                raise PipeFailure()
            buffer = ctypes.create_string_buffer(size.value)
            if not self.token_info(token, 1, buffer, size, ctypes.byref(size)):
                raise PipeFailure()
            sid = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
            if not sid or not self.sid_string(sid, ctypes.byref(text)) or not text.value:
                raise PipeFailure()
            return text.value
        finally:
            if text:
                self.free(text)
            self.close(token)


def _name(name: str) -> str:
    if not isinstance(name, str) or not _NAME.fullmatch(name):
        raise PipeFailure()
    return name


class WindowsPipe:
    # [SUPUESTO] E/S local 1 s por defecto; rango configurable 0–60 s. No es un plazo de decisión.
    def __init__(self, api: Any, handle: int, name: str, *, server: bool) -> None:
        self._api, self._handle, self.name, self.server = api, handle, name, server
        self._io = threading.Lock()
        self._submit = threading.Lock()
        self._closed = threading.Event()

    @classmethod
    def create(cls) -> WindowsPipe:
        api = _Api()
        name = _PREFIX + uuid4().hex
        descriptor = ctypes.c_void_p()
        # FA solo para la cuenta actual. No heredar ACE de Everyone/Authenticated Users.
        sddl = f"D:P(A;;FA;;;{api.user_sid()})"
        if not api.sddl_descriptor(sddl, 1, ctypes.byref(descriptor), None):
            raise PipeFailure()
        try:
            attributes = _SecurityAttributes(ctypes.sizeof(_SecurityAttributes), descriptor, False)
            handle = api.create_pipe(
                name,
                0x00000003 | 0x40000000 | 0x00080000,
                0x00000004 | 0x00000002 | 0x00000008,
                1,
                MAX_MESSAGE_BYTES,
                MAX_MESSAGE_BYTES,
                0,
                ctypes.byref(attributes),
            )  # DUPLEX | OVERLAPPED | FIRST_INSTANCE; MESSAGE | READMODE_MESSAGE | REJECT_REMOTE
            if handle in (None, 0, _INVALID):
                raise PipeFailure()
            return cls(api, handle, name, server=True)
        finally:
            api.free(descriptor)

    @classmethod
    def connect(cls, name: str, *, expected_server_pid: int) -> WindowsPipe:
        _name(name)
        if type(expected_server_pid) is not int or expected_server_pid <= 0:
            raise PipeFailure()
        api = _Api()
        handle = api.open_pipe(
            name,
            0x80000000 | 0x40000000,
            0,
            None,
            3,
            0x40000000 | 0x00100000 | 0x00010000,
            None,
        )  # OVERLAPPED | SECURITY_SQOS_PRESENT | SECURITY_IDENTIFICATION
        if handle in (None, 0, _INVALID):
            raise PipeFailure()
        endpoint = cls(api, handle, name, server=False)
        try:
            mode = _DWORD(2)  # READMODE_MESSAGE
            peer = _DWORD()
            if (
                not api.set_mode(handle, ctypes.byref(mode), None, None)
                or not api.server_pid(handle, ctypes.byref(peer))
                or peer.value != expected_server_pid
            ):
                raise PipeFailure()
            return endpoint
        except Exception:
            endpoint.close()
            raise PipeFailure() from None

    def _operate(self, kind: str, buffer: Any, size: int, timeout_ms: int) -> int:
        if type(timeout_ms) is not int or not 0 <= timeout_ms <= 60000:
            raise PipeFailure()
        with self._io:
            if self._closed.is_set():
                raise PipeClosed()
            event = self._api.create_event(None, True, False, None)
            if not event:
                raise PipeFailure()
            operation = _Overlapped()
            operation.event = event
            transferred = _DWORD()
            try:
                with self._submit:
                    if self._closed.is_set():
                        raise PipeClosed()
                    if kind == "connect":
                        success = self._api.connect(self._handle, ctypes.byref(operation))
                    else:
                        function = self._api.read if kind == "read" else self._api.write
                        success = function(
                            self._handle, buffer, size, None, ctypes.byref(operation)
                        )
                    error = last_error() if not success else 0
                if kind == "connect" and error == 535:  # PIPE_CONNECTED: cliente llegó antes
                    return 0
                if not success and error != 997:  # IO_PENDING
                    raise PipeClosed() if error in {109, 232, 995} else PipeFailure()
                timed_out = False
                if not success:
                    wait = self._api.wait(event, timeout_ms)
                    if wait != 0:
                        timed_out = wait == 258
                        self._api.cancel(self._handle, ctypes.byref(operation))
                        # Conservar OVERLAPPED y buffer hasta que termine la cancelación.
                if not self._api.result(
                    self._handle, ctypes.byref(operation), ctypes.byref(transferred), True
                ):
                    error = last_error()
                    if timed_out and error == 995:
                        raise PipeTimeout()
                    raise PipeClosed() if error in {109, 232, 995} else PipeFailure()
                # Si completó al vencer la espera, entregar el mensaje: no perderlo.
                return transferred.value
            finally:
                self._api.close(event)

    def accept(self, *, expected_client_pid: int, timeout_ms: int = 1000) -> None:
        if not self.server or type(expected_client_pid) is not int or expected_client_pid <= 0:
            raise PipeFailure()
        self._operate("connect", None, 0, timeout_ms)
        peer = _DWORD()
        if (
            not self._api.client_pid(self._handle, ctypes.byref(peer))
            or peer.value != expected_client_pid
        ):
            raise PipeFailure()

    def read(self, *, timeout_ms: int = 1000) -> bytes:
        buffer = ctypes.create_string_buffer(MAX_MESSAGE_BYTES)
        size = self._operate("read", buffer, MAX_MESSAGE_BYTES, timeout_ms)
        if not 0 < size <= MAX_MESSAGE_BYTES:
            raise PipeClosed()
        return bytes(buffer.raw[:size])

    def write(self, message: bytes, *, timeout_ms: int = 1000) -> None:
        if not isinstance(message, bytes) or not 0 < len(message) <= MAX_MESSAGE_BYTES:
            raise PipeFailure()
        buffer = ctypes.create_string_buffer(message)
        if self._operate("write", buffer, len(message), timeout_ms) != len(message):
            raise PipeFailure()

    def cancel(self) -> None:
        with self._submit:
            self._closed.set()
            self._api.cancel(self._handle, None)

    def close(self) -> None:
        self.cancel()
        with self._io:
            if self._handle:
                if self.server:
                    self._api.disconnect(self._handle)
                self._api.close(self._handle)
                self._handle = 0
