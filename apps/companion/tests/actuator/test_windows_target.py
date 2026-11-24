"""Consultas de destino y liberación de handles; ninguna prueba usa SendInput."""

import ctypes
import sys

import pytest
from coalsense_companion.actuator.target import Target, TargetBlocked, TargetGuard
from coalsense_companion.actuator.windows_target import WindowsTargetProbe, _GuiInfo


def probe(*, target_integrity: int = 8192, own_integrity: int = 8192):
    target = object.__new__(WindowsTargetProbe)
    closed: list[object] = []
    target._foreground = lambda: 10
    target._cursor = lambda _: True
    target._at_point = lambda _: 20
    target._root = lambda window, _: 10 if window == 11 else window

    def thread(window, process):
        process._obj.value = window * 100
        return 100

    def gui(_, info):
        info._obj.hwndFocus = 11
        return True

    target._thread = thread
    target._gui = gui
    target._open_process = lambda *_: 500
    target._close = closed.append
    target._current = lambda: 600
    target._integrity = lambda handle: target_integrity if handle == 500 else own_integrity
    return target, closed


def test_target_abi_and_keyboard_focus_are_pointer_size_correct() -> None:
    assert ctypes.sizeof(_GuiInfo) == (72 if ctypes.sizeof(ctypes.c_void_p) == 8 else 48)
    target, closed = probe()
    assert target.capture(pointer=False) == Target(10, 11, 1000, True, "")
    assert closed == [500]


def test_pointer_checks_window_under_cursor_and_elevated_target_is_denied() -> None:
    target, closed = probe(target_integrity=12288)
    outcome = target.capture(pointer=True)
    assert outcome == Target(20, 0, 2000, False, "elevated", 10, 1000)
    with pytest.raises(TargetBlocked, match="not controllable") as caught:
        TargetGuard(target).capture(pointer=True)
    assert caught.value.reason == "elevated" and closed == [500, 500, 500, 500]


def test_foreign_focus_from_attached_input_threads_is_denied() -> None:
    target, closed = probe()
    target._root = lambda *_: 50
    with pytest.raises(TargetBlocked):
        target.capture(pointer=False)
    assert closed == []


def test_pointer_checks_foreground_privileges_too_for_windows_wheel_routing() -> None:
    target, closed = probe()
    target._open_process = lambda _, __, pid: pid
    target._integrity = lambda handle: 12288 if handle == 1000 else 8192
    outcome = target.capture(pointer=True)
    assert not outcome.allowed and outcome.reason == "elevated"
    assert closed == [2000, 1000]


def test_changed_foreground_is_detected_even_if_pointer_stays_over_same_window() -> None:
    target, _ = probe()
    guard = TargetGuard(target)
    before = guard.capture(pointer=True)
    target._foreground = lambda: 20
    with pytest.raises(TargetBlocked) as caught:
        guard.check(before, pointer=True)
    assert caught.value.reason == "changed"


@pytest.mark.parametrize("fault", ["foreground", "cursor", "process", "focus", "open", "integrity"])
def test_failed_native_query_denies_input_and_closes_acquired_process(fault: str) -> None:
    target, closed = probe()
    if fault == "foreground":
        target._foreground = lambda: 0
    elif fault == "cursor":
        target._cursor = lambda _: False
    elif fault == "process":
        target._thread = lambda *_: 0
    elif fault == "focus":
        target._gui = lambda *_: False
    elif fault == "open":
        target._open_process = lambda *_: None
    elif fault == "integrity":

        def fail(_):
            raise RuntimeError("private system details")

        target._integrity = fail
    with pytest.raises(TargetBlocked) as caught:
        TargetGuard(target).capture(pointer=fault == "cursor")
    assert "private" not in str(caught.value)
    assert closed == ([500] if fault == "integrity" else [])


@pytest.mark.parametrize("fail_read", [False, True])
def test_integrity_query_closes_token_even_when_read_fails(fail_read: bool) -> None:
    target = object.__new__(WindowsTargetProbe)
    closed = []
    count = (ctypes.c_uint8 * 1)(1)
    authority = (ctypes.c_uint32 * 1)(8192)

    def open_token(_, access, handle):
        assert access == 8
        handle._obj.value = 700
        return True

    def info(_, category, buffer, size, needed):
        assert category == 25
        needed._obj.value = 32
        if buffer is None:
            return False
        ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0] = ctypes.addressof(authority)
        return not fail_read

    target._open_token = open_token
    target._token_info = info
    target._sid_count = lambda _: count
    target._sid_authority = lambda *_: authority
    target._close = lambda handle: closed.append(handle.value)
    if fail_read:
        with pytest.raises(TargetBlocked):
            target._integrity(500)
    else:
        assert target._integrity(500) == 8192
    assert closed == [700]


@pytest.mark.skipif(sys.platform != "win32", reason="Consulta de solo lectura Win32")
def test_native_probe_can_query_or_fail_closed_without_sending_input() -> None:
    target = WindowsTargetProbe()
    for pointer in (False, True):
        try:
            outcome = TargetGuard(target).capture(pointer=pointer)
        except TargetBlocked:
            continue
        assert outcome.allowed and outcome.process > 0 and outcome.window > 0


def test_no_success_fallback_on_other_platforms(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    with pytest.raises(TargetBlocked):
        WindowsTargetProbe()
