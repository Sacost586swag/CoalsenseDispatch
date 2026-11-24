"""Borde ctypes disponible solo en Windows, importable para pruebas en otras plataformas."""

import ctypes


def last_error() -> int:
    reader = getattr(ctypes, "get_last_error", None)
    if reader is None:
        raise OSError("Windows native error state is unavailable")
    return int(reader())
