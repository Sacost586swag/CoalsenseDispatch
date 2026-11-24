"""ABI y secuencias Win32; nunca envía entradas al escritorio real."""

import ctypes
from collections import deque
from typing import Any

import pytest
from coalsense_companion.actuator.windows import (
    INJECTION_TAG,
    NativeInputFailure,
    WindowsInputBackend,
    _Input,
)


class Function:
    def __init__(self, call: Any) -> None:
        self.call = call

    def __call__(self, *args: Any) -> Any:
        return self.call(*args)


class API:
    def __init__(self) -> None:
        self.events: list[dict[str, int]] = []
        self.results: deque[int] = deque()
        self.down: set[int] = set()
        self.SendInput = Function(self.send)
        self.GetAsyncKeyState = Function(lambda key: -32768 if key in self.down else 0)
        self.GetSystemMetrics = Function(lambda key: {76: -1920, 77: 0, 78: 3840, 79: 1080}[key])

    def send(self, count: int, events: Any, size: int) -> int:
        assert size == ctypes.sizeof(_Input)
        for event in events:
            if event.type == 1:
                self.events.append(
                    {
                        "type": 1,
                        "vk": event.ki.wVk,
                        "scan": event.ki.wScan,
                        "flags": event.ki.dwFlags,
                        "tag": event.ki.dwExtraInfo,
                    }
                )
            else:
                self.events.append(
                    {
                        "type": 0,
                        "x": event.mi.dx,
                        "y": event.mi.dy,
                        "data": event.mi.mouseData,
                        "flags": event.mi.dwFlags,
                        "tag": event.mi.dwExtraInfo,
                    }
                )
        return self.results.popleft() if self.results else count


def test_windows_input_abi_and_extended_key_release() -> None:
    assert ctypes.sizeof(_Input) == (40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28)
    api = API()
    backend = WindowsInputBackend(api=api)
    assert backend.key_down("Left")
    backend.key_up("Left")
    assert [event["flags"] for event in api.events] == [1, 3]
    assert all(event["tag"] == INJECTION_TAG for event in api.events)
    api.down.add(0x11)
    assert backend.key_down("Control") is False
    assert len(api.events) == 2


def test_pointer_coordinates_use_virtual_desktop_and_signed_wheel_data() -> None:
    api = API()
    backend = WindowsInputBackend(api=api)
    backend.move(-1920, 0, absolute=True)
    assert api.events[-1]["x"] == api.events[-1]["y"] == 0
    backend.move(1919, 1079, absolute=True)
    assert api.events[-1]["x"] == api.events[-1]["y"] == 65535
    assert api.events[-1]["flags"] == 0xC001
    backend.move(-3, 2)
    assert api.events[-1]["x"] == -3 and api.events[-1]["flags"] == 1
    backend.scroll(1, -1)
    assert [event["data"] for event in api.events[-2:]] == [(-120) & 0xFFFFFFFF, 120]


def test_unicode_surrogates_are_one_batch_and_partial_injection_is_cleaned_up() -> None:
    api = API()
    backend = WindowsInputBackend(api=api)
    backend.write_character("😀")
    assert [event["scan"] for event in api.events] == [0xD83D, 0xD83D, 0xDE00, 0xDE00]
    assert [event["flags"] for event in api.events] == [4, 6, 4, 6]
    api.results.extend([1, 0])  # inserción parcial; primer intento de soltar también falla
    with pytest.raises(NativeInputFailure):
        backend.write_character("ñ")
    backend.release_text()
    assert api.events[-1]["scan"] == ord("ñ") and api.events[-1]["flags"] == 6


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), 2**40, 2**31 - 0.1])
def test_invalid_movement_never_wraps_into_another_native_coordinate(bad: float) -> None:
    api = API()
    with pytest.raises(NativeInputFailure):
        WindowsInputBackend(api=api).move(bad, 0)
    assert api.events == []


def test_unavailable_platform_or_rejected_write_never_reports_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    with pytest.raises(NativeInputFailure):
        WindowsInputBackend()
    api = API()
    api.results.append(0)
    with pytest.raises(NativeInputFailure):
        WindowsInputBackend(api=api).key_down("Enter")
