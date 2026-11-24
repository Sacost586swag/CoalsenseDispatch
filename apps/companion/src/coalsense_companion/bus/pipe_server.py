"""Entrega del canal local al bus; no ejecuta consumidores ni acepta órdenes remotas."""

import threading
from collections.abc import Callable

from coalsense_common.ids import monotonic_ns

from .session import PipeSession
from .windows_pipe import PipeTimeout, WindowsPipe


def serve_connection(
    endpoint: WindowsPipe,
    session: PipeSession,
    *,
    expected_client_pid: int,
    stopped: threading.Event,
    clock: Callable[[], int] = monotonic_ns,
) -> None:
    # [SUPUESTO] conexión inicial hasta 30 s; consulta cancelable cada 250 ms.
    endpoint.accept(expected_client_pid=expected_client_pid, timeout_ms=30000)
    while not stopped.is_set():
        try:
            raw = endpoint.read(timeout_ms=250)
        except PipeTimeout:
            continue
        reply = session.handle(raw, received_ns=clock())
        endpoint.write(reply)
