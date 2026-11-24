"""Host real y Job Object de Windows; el adaptador idle no declara salud física."""

import ctypes
import sys
import threading
import time
from types import SimpleNamespace

import pytest
from coalsense_companion.bus.session import HealthReceipt
from coalsense_companion.bus.stop_state import StopState
from coalsense_companion.process_host import WindowsAdapterProcess, windows_process_factory
from coalsense_companion.process_launch import python_launch
from coalsense_companion.supervisor import AdapterSpec, Supervisor
from coalsense_companion.windows_job import _ExtendedLimits

from ..bus.test_core import setup_bus

native = pytest.mark.skipif(sys.platform != "win32", reason="Procesos y job de Windows")


def test_job_limits_abi() -> None:
    assert ctypes.sizeof(_ExtendedLimits) == (144 if ctypes.sizeof(ctypes.c_void_p) == 8 else 112)


def test_dead_child_is_not_reported_alive_while_channel_worker_is_cleaning_up() -> None:
    host = object.__new__(WindowsAdapterProcess)
    cancellations = []
    host._process = SimpleNamespace(poll=lambda: 0)
    host._worker = SimpleNamespace(is_alive=lambda: True)
    host._server = SimpleNamespace(cancel=lambda: cancellations.append(True))
    assert not host.is_alive() and cancellations == [True]


@native
def test_child_environment_does_not_inherit_secrets_or_python_injection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "private provider secret")
    monkeypatch.setenv("COALSENSE_DEVICE_CREDENTIAL", "private token")
    monkeypatch.setenv("PYTHONPATH", "private Python path")
    monkeypatch.setenv("PYTHONHOME", "private Python home")
    executable, environment = python_launch()
    assert executable and "OPENAI_API_KEY" not in environment
    assert "COALSENSE_DEVICE_CREDENTIAL" not in environment
    assert "PYTHONPATH" not in environment and "PYTHONHOME" not in environment
    assert "private" not in repr(environment)


@native
def test_real_host_connects_receives_once_and_revokes_on_stop_without_console_or_device_input() -> (
    None
):
    bus, registry, credential, _, _ = setup_bus()
    from coalsense_companion.bus.auth import AdapterCredential

    process = WindowsAdapterProcess(
        AdapterSpec("voice@1.0.0", "voice", "person"),
        AdapterCredential(credential),
        bus,
        registry,
    )
    try:
        deadline = time.monotonic() + 10
        receipt = None
        wait = threading.Event()
        while time.monotonic() < deadline and process.is_alive():
            receipt = process.poll_health()
            if receipt is not None:
                break
            wait.wait(0.02)
        assert isinstance(receipt, HealthReceipt)
        assert receipt.evidence.adapter_responding and not receipt.evidence.device_streaming
        assert not receipt.evidence.stop_bound and not receipt.evidence.model_loaded
        assert process.poll_health() is None
        assert registry.authenticate(credential) is not None
        assert credential not in repr(process)
        assert process._process is not None and credential not in repr(process._process.args)
    finally:
        process.stop()
        assert process.wait_closed(5)
    assert registry.authenticate(credential) is None and process.cleanup_failures == 0


@native
def test_supervisor_uses_real_process_and_keeps_unverified_device_unreachable() -> None:
    bus, registry, _, _, _ = setup_bus()
    state = StopState(on_unreachable=lambda _: bus.halt())
    supervisor = Supervisor(registry, state)
    hosts = []
    factory = windows_process_factory(bus, registry)

    def launch(spec, credential):
        host = factory(spec, credential)
        hosts.append(host)
        return host

    supervisor.add(AdapterSpec("keyboard@1", "keyboard_mouse", "person"), launch)
    try:
        deadline = time.monotonic() + 10
        wait = threading.Event()
        while time.monotonic() < deadline:
            supervisor.tick()
            if supervisor.snapshot()[0].phase == "running":
                break
            wait.wait(0.02)
        assert supervisor.snapshot()[0].phase == "running"
        assert not state.snapshot().stop_reachable
        assert state.snapshot().routes[0].reason == "device_unavailable"
    finally:
        supervisor.stop("keyboard@1")
        for host in hosts:
            assert host.wait_closed(5)


@native
def test_closing_job_terminates_child_even_without_cooperative_shutdown() -> None:
    bus, registry, credential, _, _ = setup_bus()
    from coalsense_companion.bus.auth import AdapterCredential

    process = WindowsAdapterProcess(
        AdapterSpec("voice@1.0.0", "voice", "person"),
        AdapterCredential(credential),
        bus,
        registry,
    )
    try:
        assert process._job is not None
        process._job.close()
        assert process.wait_closed(5)
    finally:
        process.stop()
        assert process.wait_closed(5)


@native
def test_real_supervisor_restarts_one_crashed_child_while_another_process_survives() -> None:
    bus, registry, _, _, _ = setup_bus()
    state = StopState(on_unreachable=lambda _: bus.halt())
    supervisor = Supervisor(registry, state, retry_base_ns=10_000_000, retry_cap_ns=100_000_000)
    hosts, credentials = {"voice@1": [], "keyboard@1": []}, {"voice@1": [], "keyboard@1": []}

    def launch(spec, credential):
        host = WindowsAdapterProcess(spec, credential, bus, registry)
        hosts[spec.identifier].append(host)
        credentials[spec.identifier].append(credential)
        return host

    supervisor.add(AdapterSpec("voice@1", "voice", "person"), launch)
    supervisor.add(AdapterSpec("keyboard@1", "keyboard_mouse", "person"), launch)
    wait = threading.Event()
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            supervisor.tick()
            if all(status.phase == "running" for status in supervisor.snapshot()):
                break
            wait.wait(0.02)
        assert all(status.phase == "running" for status in supervisor.snapshot())
        keyboard_pid = hosts["keyboard@1"][0].pid
        voice = hosts["voice@1"][0]
        voice._job.close()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            supervisor.tick()
            if len(hosts["voice@1"]) == 2 and all(
                status.phase == "running" for status in supervisor.snapshot()
            ):
                break
            wait.wait(0.02)
        assert len(hosts["voice@1"]) == 2 and hosts["voice@1"][-1].pid != voice.pid
        assert registry.authenticate(credentials["voice@1"][0].credential) is None
        assert hosts["keyboard@1"][0].pid == keyboard_pid and len(hosts["keyboard@1"]) == 1
        assert hosts["keyboard@1"][0].is_alive() and not state.snapshot().stop_reachable
    finally:
        for identifier in hosts:
            supervisor.stop(identifier)
        for instances in hosts.values():
            for host in instances:
                assert host.wait_closed(5)
