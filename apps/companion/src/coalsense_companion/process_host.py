"""Host Windows real: proceso sin consola, job privado y named pipe autenticado."""

from __future__ import annotations

import os
import subprocess
import threading
import time
from collections.abc import Callable
from typing import Any, cast

from coalsense_common.ids import monotonic_ns

from .adapters import ADAPTER_MODULES
from .bus.auth import AdapterCredential, AdapterRegistry, AdapterSession
from .bus.core import IntentBus
from .bus.pipe_server import serve_connection
from .bus.session import HealthReceipt, PipeSession, encode_message
from .bus.windows_pipe import WindowsPipe
from .process_launch import ProcessLaunchFailure, python_launch
from .supervisor import AdapterSpec, ProcessFactory
from .windows_job import WindowsJob


class WindowsAdapterProcess:
    def __init__(
        self,
        spec: AdapterSpec,
        credential: AdapterCredential,
        bus: IntentBus,
        registry: AdapterRegistry,
        *,
        module: str = "coalsense_companion.adapters.idle",
        clock: Callable[[], int] = monotonic_ns,
    ) -> None:
        if not isinstance(module, str) or module not in ADAPTER_MODULES:
            raise ProcessLaunchFailure()
        expected = AdapterSession(spec.identifier, spec.modality, spec.actor_origin)
        if registry.authenticate(credential.credential) != expected or bus.registry is not registry:
            raise ProcessLaunchFailure()
        executable, environment = python_launch()
        self._clock, self._registry = clock, registry
        self._credential: AdapterCredential | None = credential
        self._server = WindowsPipe.create()
        self._session = PipeSession(bus, registry, credential.credential, expected)
        self._stopped = threading.Event()
        self._finished = threading.Event()
        self.protocol_failures = 0
        self.cleanup_failures = 0
        self._process: subprocess.Popen[bytes] | None = None
        self._worker: threading.Thread | None = None
        self._job: WindowsJob | None = None
        self._assigned = False
        try:
            self._job = WindowsJob()
            self._process = subprocess.Popen(
                [executable, "-I", "-m", "coalsense_companion.adapters.worker"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                creationflags=0x08000000,  # CREATE_NO_WINDOW; solo Windows
                env=environment,
            )
            # Windows CPython 3.12: el handle de Popen es el proceso real, sin redirector venv.
            self._job.assign(int(cast(Any, self._process)._handle))
            self._assigned = True
            assert self._process.stdin is not None
            self._process.stdin.write(
                encode_message(
                    {
                        "version": 1,
                        "pipe": self._server.name,
                        "server_pid": os.getpid(),
                        "credential": credential.credential,
                        "module": module,
                    }
                )
                + b"\n"
            )
            self._process.stdin.flush()
            self._process.stdin.close()
            self._worker = threading.Thread(
                target=self._serve, name="coalsense-adapter-channel", daemon=True
            )
            self._worker.start()
        except Exception:
            self._cleanup()
            if self._process is not None:
                self._process.wait(timeout=5)
            raise ProcessLaunchFailure() from None

    @property
    def pid(self) -> int:
        assert self._process is not None
        return self._process.pid

    def _revoke(self) -> None:
        credential, self._credential = self._credential, None
        if credential is not None:
            self._registry.revoke(credential.credential)

    def _terminate(self) -> None:
        failed = False
        try:
            if self._job is not None:
                self._job.close()
        except Exception:
            failed = True
        if (
            (not self._assigned or failed)
            and self._process is not None
            and self._process.poll() is None
        ):
            self._process.terminate()
        if failed:
            raise ProcessLaunchFailure()

    def _cleanup(self) -> None:
        self._stopped.set()
        self._revoke()
        try:
            self._terminate()
        except Exception:
            self.cleanup_failures += 1
        try:
            self._server.close()
        except Exception:
            self.cleanup_failures += 1
        self._session.close()
        self._finished.set()

    def _serve(self) -> None:
        try:
            serve_connection(
                self._server,
                self._session,
                expected_client_pid=self.pid,
                stopped=self._stopped,
                clock=self._clock,
            )
        except Exception:
            if not self._stopped.is_set():
                self.protocol_failures += 1
        finally:
            self._cleanup()

    def is_alive(self) -> bool:
        running = self._process is not None and self._process.poll() is None
        if not running:
            self._server.cancel()
        return running

    def poll_health(self) -> HealthReceipt | None:
        return self._session.take_health()

    def stop(self) -> None:
        # Señalar y cancelar sin join; el supervisor no espera a los trabajadores.
        self._stopped.set()
        self._revoke()
        self._server.cancel()
        try:
            self._terminate()
        except Exception:
            raise ProcessLaunchFailure() from None

    def wait_closed(self, timeout: float = 5) -> bool:
        # [SUPUESTO] espera técnica opcional de 5 s para el cierre, fuera de stop().
        deadline = time.monotonic() + timeout
        if self._process is not None:
            try:
                self._process.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                return False
        self._server.cancel()
        if self._worker is not None:
            self._worker.join(max(0, deadline - time.monotonic()))
        return not self.is_alive() and (self._worker is None or not self._worker.is_alive())


def windows_process_factory(
    bus: IntentBus,
    registry: AdapterRegistry,
    *,
    module: str = "coalsense_companion.adapters.idle",
    clock: Callable[[], int] = monotonic_ns,
) -> ProcessFactory:
    return lambda spec, credential: WindowsAdapterProcess(
        spec,
        credential,
        bus,
        registry,
        module=module,
        clock=clock,
    )
