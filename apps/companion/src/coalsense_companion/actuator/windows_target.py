"""Inspección Win32 de destino e integridad. Solo consulta identificadores y tokens."""

import ctypes
import sys
from typing import Any

from .target import Target, TargetBlocked

_DWORD = ctypes.c_uint32
_HANDLE = ctypes.c_void_p


class _Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int32), ("y", ctypes.c_int32)]


class _Rect(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int32) for name in ("left", "top", "right", "bottom")]


class _GuiInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", _DWORD),
        ("flags", _DWORD),
        *(
            (name, _HANDLE)
            for name in (
                "hwndActive",
                "hwndFocus",
                "hwndCapture",
                "hwndMenuOwner",
                "hwndMoveSize",
                "hwndCaret",
            )
        ),
        ("rcCaret", _Rect),
    ]


def _function(dll: Any, name: str, args: list[Any], result: Any) -> Any:
    function = getattr(dll, name)
    function.argtypes, function.restype = args, result
    return function


class WindowsTargetProbe:
    _foreground: Any
    _cursor: Any
    _at_point: Any
    _root: Any
    _thread: Any
    _gui: Any
    _open_process: Any
    _current: Any
    _close: Any
    _open_token: Any
    _token_info: Any
    _sid_count: Any
    _sid_authority: Any

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise TargetBlocked()
        user = ctypes.WinDLL("user32", use_last_error=True)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        security = ctypes.WinDLL("advapi32", use_last_error=True)
        self._foreground = _function(user, "GetForegroundWindow", [], _HANDLE)
        self._cursor = _function(user, "GetCursorPos", [ctypes.POINTER(_Point)], ctypes.c_int32)
        self._at_point = _function(user, "WindowFromPoint", [_Point], _HANDLE)
        self._root = _function(user, "GetAncestor", [_HANDLE, ctypes.c_uint32], _HANDLE)
        self._thread = _function(
            user,
            "GetWindowThreadProcessId",
            [_HANDLE, ctypes.POINTER(_DWORD)],
            _DWORD,
        )
        self._gui = _function(
            user,
            "GetGUIThreadInfo",
            [_DWORD, ctypes.POINTER(_GuiInfo)],
            ctypes.c_int32,
        )
        self._open_process = _function(
            kernel,
            "OpenProcess",
            [_DWORD, ctypes.c_int32, _DWORD],
            _HANDLE,
        )
        self._current = _function(kernel, "GetCurrentProcess", [], _HANDLE)
        self._close = _function(kernel, "CloseHandle", [_HANDLE], ctypes.c_int32)
        self._open_token = _function(
            security,
            "OpenProcessToken",
            [_HANDLE, _DWORD, ctypes.POINTER(_HANDLE)],
            ctypes.c_int32,
        )
        self._token_info = _function(
            security,
            "GetTokenInformation",
            [_HANDLE, ctypes.c_uint32, ctypes.c_void_p, _DWORD, ctypes.POINTER(_DWORD)],
            ctypes.c_int32,
        )
        self._sid_count = _function(
            security,
            "GetSidSubAuthorityCount",
            [ctypes.c_void_p],
            ctypes.POINTER(ctypes.c_uint8),
        )
        self._sid_authority = _function(
            security,
            "GetSidSubAuthority",
            [ctypes.c_void_p, _DWORD],
            ctypes.POINTER(_DWORD),
        )

    def _integrity(self, process: int) -> int:
        token = _HANDLE()
        if not self._open_token(process, 0x0008, ctypes.byref(token)):  # TOKEN_QUERY
            raise TargetBlocked()
        try:
            size = _DWORD()
            self._token_info(token, 25, None, 0, ctypes.byref(size))  # TokenIntegrityLevel
            if not 0 < size.value <= 65536:
                raise TargetBlocked()
            buffer = ctypes.create_string_buffer(size.value)
            if not self._token_info(token, 25, buffer, size.value, ctypes.byref(size)):
                raise TargetBlocked()
            sid = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
            if not sid:
                raise TargetBlocked()
            count = self._sid_count(sid)
            if not count or not count[0]:
                raise TargetBlocked()
            authority = self._sid_authority(sid, count[0] - 1)
            if not authority:
                raise TargetBlocked()
            return int(authority[0])
        finally:
            self._close(token)

    def capture(self, *, pointer: bool) -> Target:
        window = self._foreground()
        foreground = window
        focus = 0
        if pointer:
            point = _Point()
            if not self._cursor(ctypes.byref(point)):
                raise TargetBlocked()
            window = self._root(self._at_point(point), 2)  # GA_ROOT
        if not window:
            raise TargetBlocked()
        process = _DWORD()
        thread = self._thread(window, ctypes.byref(process))
        if not thread or not process.value:
            raise TargetBlocked()
        foreground_process = _DWORD()
        if pointer and (
            not foreground or not self._thread(foreground, ctypes.byref(foreground_process))
        ):
            raise TargetBlocked()
        if not pointer:
            gui = _GuiInfo()
            gui.cbSize = ctypes.sizeof(_GuiInfo)
            if not self._gui(thread, ctypes.byref(gui)):
                raise TargetBlocked()
            focus = gui.hwndFocus or 0
            if not focus:
                raise TargetBlocked()
            if self._root(focus, 2) != window:
                raise TargetBlocked()
        handle = self._open_process(0x1000, False, process.value)  # QUERY_LIMITED_INFORMATION
        if not handle:
            raise TargetBlocked()
        try:
            allowed = self._integrity(handle) <= self._integrity(self._current())
        finally:
            self._close(handle)
        if pointer and foreground_process.value != process.value:
            # El destino de la rueda depende de la configuración de Windows: verificar
            # tanto el primer plano como la ventana bajo el puntero antes de inyectar.
            other = self._open_process(0x1000, False, foreground_process.value)
            if not other:
                raise TargetBlocked()
            try:
                allowed = allowed and self._integrity(other) <= self._integrity(self._current())
            finally:
                self._close(other)
        # UIAccess no permite eludir esta restricción conservadora.
        return Target(
            int(window),
            int(focus),
            process.value,
            allowed,
            "elevated" if not allowed else "",
            int(foreground) if pointer else 0,
            foreground_process.value,
        )
