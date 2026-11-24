"""Job privado: al cerrar el núcleo se terminan también sus adaptadores y descendientes."""

import ctypes
import sys
import threading
from typing import Any

from .bus.windows_pipe import _function
from .process_launch import ProcessLaunchFailure

_DWORD = ctypes.c_uint32
_SIZE = ctypes.c_size_t
_HANDLE = ctypes.c_void_p


class _BasicLimits(ctypes.Structure):
    _fields_ = [
        ("process_time", ctypes.c_int64),
        ("job_time", ctypes.c_int64),
        ("flags", _DWORD),
        ("minimum_working_set", _SIZE),
        ("maximum_working_set", _SIZE),
        ("active_processes", _DWORD),
        ("affinity", _SIZE),
        ("priority", _DWORD),
        ("scheduling", _DWORD),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_uint64)
        for name in (
            "read_operations",
            "write_operations",
            "other_operations",
            "read_bytes",
            "write_bytes",
            "other_bytes",
        )
    ]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("basic", _BasicLimits),
        ("io", _IoCounters),
        ("process_memory", _SIZE),
        ("job_memory", _SIZE),
        ("peak_process_memory", _SIZE),
        ("peak_job_memory", _SIZE),
    ]


class WindowsJob:
    _assign: Any
    _close: Any
    _lock: threading.Lock
    _handle: int

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise ProcessLaunchFailure()
        api = ctypes.WinDLL("kernel32", use_last_error=True)
        create = _function(api, "CreateJobObjectW", [ctypes.c_void_p, ctypes.c_wchar_p], _HANDLE)
        configure = _function(
            api,
            "SetInformationJobObject",
            [_HANDLE, ctypes.c_int32, ctypes.c_void_p, _DWORD],
            ctypes.c_int32,
        )
        self._assign = _function(
            api, "AssignProcessToJobObject", [_HANDLE, _HANDLE], ctypes.c_int32
        )
        self._close = _function(api, "CloseHandle", [_HANDLE], ctypes.c_int32)
        self._lock = threading.Lock()
        self._handle = create(None, None)
        if not self._handle:
            raise ProcessLaunchFailure()
        limits = _ExtendedLimits()
        limits.basic.flags = 0x00002000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not configure(self._handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            self.close()
            raise ProcessLaunchFailure()

    def assign(self, process_handle: int) -> None:
        with self._lock:
            if not self._handle or not self._assign(self._handle, process_handle):
                raise ProcessLaunchFailure()

    def close(self) -> None:
        with self._lock:
            if self._handle:
                if not self._close(self._handle):
                    raise ProcessLaunchFailure()
                self._handle = 0
