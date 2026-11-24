"""Backend Win32 SendInput. Ninguna llamada ocurre al importar el módulo.

El actuador debe envolver cada llamada con ActuationGate. `api` solo permite probar
el ABI sin enviar entradas al escritorio de la persona. No existe alternativa que
simule éxito cuando Windows o SendInput no están disponibles.
"""

import ctypes
import math
import sys
import threading
from typing import Any

WORD = ctypes.c_uint16
DWORD = ctypes.c_uint32
LONG = ctypes.c_int32
ULONG_PTR = ctypes.c_size_t
INJECTION_TAG = 0x434F414C  # [SUPUESTO] marca COAL para evitar eco en el adaptador de teclado


class _MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", LONG),
        ("dy", LONG),
        ("mouseData", DWORD),
        ("dwFlags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _KeyboardInput(ctypes.Structure):
    _fields_ = [
        ("wVk", WORD),
        ("wScan", WORD),
        ("dwFlags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", DWORD), ("wParamL", WORD), ("wParamH", WORD)]


class _InputUnion(ctypes.Union):
    _fields_ = [("mi", _MouseInput), ("ki", _KeyboardInput), ("hi", _HardwareInput)]


class _Input(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", DWORD), ("data", _InputUnion)]


_KEYS = {
    "BACKSPACE": 0x08,
    "TAB": 0x09,
    "ENTER": 0x0D,
    "SHIFT": 0x10,
    "CONTROL": 0x11,
    "CTRL": 0x11,
    "ALT": 0x12,
    "ESCAPE": 0x1B,
    "SPACE": 0x20,
    "PAGEUP": 0x21,
    "PAGEDOWN": 0x22,
    "END": 0x23,
    "HOME": 0x24,
    "LEFT": 0x25,
    "UP": 0x26,
    "RIGHT": 0x27,
    "DOWN": 0x28,
    "INSERT": 0x2D,
    "DELETE": 0x2E,
    "WIN": 0x5B,
}
_BUTTONS = {
    "left": (0x01, 0x0002, 0x0004),
    "right": (0x02, 0x0008, 0x0010),
    "middle": (0x04, 0x0020, 0x0040),
}
_EXTENDED = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, 0x5B}


class NativeInputFailure(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Windows could not complete the local input operation")


def _key_code(key: str) -> int:
    name = key.upper()
    if name in _KEYS:
        return _KEYS[name]
    if len(name) == 1 and name.isascii() and name.isalnum():
        return ord(name)
    if name.startswith("F") and name[1:].isdigit() and 1 <= int(name[1:]) <= 24:
        return 0x70 + int(name[1:]) - 1
    raise NativeInputFailure()


def _keyboard(vk: int, scan: int = 0, flags: int = 0) -> _Input:
    event = _Input()
    event.type = 1
    event.ki = _KeyboardInput(vk, scan, flags, 0, INJECTION_TAG)
    return event


def _mouse(flags: int, x: int = 0, y: int = 0, data: int = 0) -> _Input:
    event = _Input()
    event.type = 0
    event.mi = _MouseInput(x, y, data & 0xFFFFFFFF, flags, 0, INJECTION_TAG)
    return event


def _integer(value: float) -> int:
    try:
        if not math.isfinite(value):
            raise NativeInputFailure()
        converted = round(value)
        if not -(2**31) <= converted < 2**31:
            raise NativeInputFailure()
        return converted
    except (OverflowError, ValueError):
        raise NativeInputFailure() from None


class WindowsInputBackend:
    def __init__(self, *, api: Any = None) -> None:
        if api is None:
            if sys.platform != "win32":
                raise NativeInputFailure()
            try:
                api = ctypes.WinDLL("user32", use_last_error=True)
            except OSError:
                raise NativeInputFailure() from None
        self._api = api
        self._send = api.SendInput
        self._send.argtypes = [ctypes.c_uint32, ctypes.POINTER(_Input), ctypes.c_int]
        self._send.restype = ctypes.c_uint32
        self._async = api.GetAsyncKeyState
        self._async.argtypes = [ctypes.c_int]
        self._async.restype = ctypes.c_int16
        self._metrics = api.GetSystemMetrics
        self._metrics.argtypes = [ctypes.c_int]
        self._metrics.restype = ctypes.c_int
        self._lock = threading.RLock()
        self._pending_unicode: set[int] = set()

    def _write(self, events: list[_Input]) -> None:
        if not events:
            return
        data = (_Input * len(events))(*events)
        try:
            written = self._send(len(events), data, ctypes.sizeof(_Input))
        except Exception:
            raise NativeInputFailure() from None
        if written != len(events):
            raise NativeInputFailure()

    def key_down(self, key: str) -> bool:
        code = _key_code(key)
        with self._lock:
            if self._async(code) & 0x8000:
                return False
            self._write([_keyboard(code, flags=1 if code in _EXTENDED else 0)])
            return True

    def key_up(self, key: str) -> None:
        code = _key_code(key)
        with self._lock:
            self._write([_keyboard(code, flags=2 | (1 if code in _EXTENDED else 0))])

    def button_down(self, button: str) -> bool:
        if button not in _BUTTONS:
            raise NativeInputFailure()
        vk, down, _ = _BUTTONS[button]
        with self._lock:
            if self._async(vk) & 0x8000:
                return False
            self._write([_mouse(down)])
            return True

    def button_up(self, button: str) -> None:
        if button not in _BUTTONS:
            raise NativeInputFailure()
        with self._lock:
            self._write([_mouse(_BUTTONS[button][2])])

    def move(self, x: float, y: float, *, absolute: bool = False) -> None:
        with self._lock:
            if not absolute:
                self._write([_mouse(0x0001, _integer(x), _integer(y))])
                return
            left, top = self._metrics(76), self._metrics(77)
            width, height = self._metrics(78), self._metrics(79)
            if width < 2 or height < 2:
                raise NativeInputFailure()
            px, py = _integer(x), _integer(y)
            nx = round(min(max(px - left, 0), width - 1) * 65535 / (width - 1))
            ny = round(min(max(py - top, 0), height - 1) * 65535 / (height - 1))
            self._write([_mouse(0x0001 | 0x8000 | 0x4000, nx, ny)])

    def scroll(self, dx: float, dy: float) -> None:
        events = []
        if dy:
            events.append(_mouse(0x0800, data=_integer(dy * 120)))
        if dx:
            events.append(_mouse(0x1000, data=_integer(dx * 120)))
        with self._lock:
            self._write(events)

    def write_character(self, character: str) -> None:
        try:
            if len(character) != 1:
                raise NativeInputFailure()
            raw = character.encode("utf-16-le")
        except UnicodeEncodeError:
            raise NativeInputFailure() from None
        units = [
            int.from_bytes(raw[index : index + 2], "little") for index in range(0, len(raw), 2)
        ]
        events = [
            event for unit in units for event in (_keyboard(0, unit, 4), _keyboard(0, unit, 6))
        ]
        with self._lock:
            self._pending_unicode.update(units)
            try:
                self._write(events)
            except Exception:
                # La inserción parcial es incierta: se intenta soltar toda unidad iniciada.
                try:
                    self.release_text()
                except NativeInputFailure:
                    pass
                raise NativeInputFailure() from None
            self._pending_unicode.difference_update(units)

    def release_text(self) -> None:
        with self._lock:
            for unit in tuple(self._pending_unicode):
                try:
                    self._write([_keyboard(0, unit, 6)])
                except NativeInputFailure:
                    continue
                self._pending_unicode.remove(unit)
            if self._pending_unicode:
                raise NativeInputFailure()
