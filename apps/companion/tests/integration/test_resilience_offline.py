"""Supervisión con puertos de proceso controlados; sin red, cámara ni entrada real."""

import pytest
from coalsense_companion.actuator.runtime import create_runtime
from coalsense_companion.bus.auth import AdapterRegistry
from coalsense_companion.bus.session import HealthReceipt
from coalsense_companion.bus.stop_state import RouteEvidence, StopState
from coalsense_companion.supervisor import AdapterSpec, Supervisor

from ..actuator.test_actuator import Hardware, Probe
from ..bus.test_core import message
from ..bus.test_stop_state import Clock, healthy


class Process:
    def __init__(self) -> None:
        self.alive = True
        self.evidence: RouteEvidence | None = healthy()
        self.fail_poll = False
        self.fail_stop = False
        self.delayed_stop = False
        self.stops = 0

    def is_alive(self) -> bool:
        return self.alive

    def poll_health(self) -> RouteEvidence | None:
        if self.fail_poll:
            raise RuntimeError("private device details")
        return self.evidence

    def stop(self) -> None:
        self.stops += 1
        if self.fail_stop:
            raise RuntimeError("private process details")
        if not self.delayed_stop:
            self.alive = False


def setup(**kwargs):
    clock = Clock()
    registry = AdapterRegistry()
    state = StopState(on_unreachable=lambda _: None, clock=clock, max_age_ns=100)
    statuses = []
    supervisor = Supervisor(
        registry,
        state,
        clock=clock,
        on_status=statuses.append,
        retry_base_ns=10,
        retry_cap_ns=40,
        startup_timeout_ns=200,
        stable_ns=50,
        **kwargs,
    )
    return supervisor, registry, state, clock, statuses


def test_crash_revokes_old_credential_waits_and_restarts_with_new_credential_and_health() -> None:
    supervisor, registry, state, clock, statuses = setup()
    processes, credentials = [], []

    def launch(spec, credential):
        process = Process()
        processes.append(process)
        credentials.append(credential)
        return process

    supervisor.add(AdapterSpec("voice@1", "voice", "person"), launch)
    assert not state.snapshot().stop_reachable
    supervisor.tick()
    assert state.snapshot().stop_reachable and registry.authenticate(credentials[0].credential)
    processes[0].alive = False
    supervisor.tick()
    assert not state.snapshot().stop_reachable
    assert registry.authenticate(credentials[0].credential) is None
    assert statuses[-1].phase == "backoff" and statuses[-1].consecutive_failures == 1
    clock.now = 9
    supervisor.tick()
    assert len(processes) == 1
    clock.now = 10
    supervisor.tick()
    assert len(processes) == 2 and credentials[0] != credentials[1]
    assert state.snapshot().stop_reachable and statuses[-1].phase == "running"
    assert credentials[-1].credential not in repr(statuses)


def test_backoff_grows_caps_and_only_resets_after_stable_health() -> None:
    supervisor, _, _, clock, _ = setup()
    processes = []

    def launch(*_):
        process = Process()
        processes.append(process)
        return process

    supervisor.add(AdapterSpec("voice@1", "voice", "person"), launch)
    supervisor.tick()
    for delay in (10, 20, 40, 40):
        processes[-1].alive = False
        supervisor.tick()
        count = len(processes)
        clock.now += delay - 1
        supervisor.tick()
        assert len(processes) == count
        clock.now += 1
        supervisor.tick()
        assert len(processes) == count + 1
    clock.now += 50
    supervisor.tick()
    assert supervisor.snapshot()[0].consecutive_failures == 0
    processes[-1].alive = False
    supervisor.tick()
    assert supervisor.snapshot()[0].consecutive_failures == 1


def test_startup_without_health_is_not_true_and_response_timeout_restarts_process() -> None:
    supervisor, _, state, clock, _ = setup()
    process = Process()
    process.evidence = None
    supervisor.add(AdapterSpec("voice@1", "voice", "person"), lambda *_: process)
    supervisor.tick()
    assert not state.snapshot().stop_reachable
    clock.now = 199
    supervisor.tick()
    assert supervisor.snapshot()[0].phase == "starting"
    clock.now = 200
    supervisor.tick()
    assert supervisor.snapshot()[0].phase == "backoff" and process.stops == 1


def test_missing_reports_after_first_health_use_short_freshness_deadline() -> None:
    supervisor, _, state, clock, _ = setup()
    process = Process()
    supervisor.add(AdapterSpec("voice@1", "voice", "person"), lambda *_: process)
    supervisor.tick()
    process.evidence = None
    clock.now = 100
    supervisor.tick()
    assert not state.snapshot().stop_reachable
    assert supervisor.snapshot()[0].phase == "backoff"


def test_delayed_health_receipt_does_not_rejuvenate_a_dead_route() -> None:
    supervisor, _, state, clock, _ = setup()
    process = Process()
    process.evidence = HealthReceipt(healthy(), 0)
    clock.now = 100
    supervisor.add(AdapterSpec("voice@1", "voice", "person"), lambda *_: process)
    supervisor.tick()
    assert not state.snapshot().stop_reachable
    assert supervisor.snapshot()[0].phase == "backoff" and process.stops == 1


def test_failed_termination_never_spawns_a_duplicate_and_retries_cleanup() -> None:
    supervisor, registry, _, clock, _ = setup()
    process = Process()
    credentials = []

    def launch(_, credential):
        credentials.append(credential)
        return process

    supervisor.add(AdapterSpec("vision@1", "head_gesture", "person"), launch)
    supervisor.tick()
    process.fail_poll = process.fail_stop = True
    supervisor.tick()
    assert supervisor.snapshot()[0].phase == "stopping"
    assert registry.authenticate(credentials[0].credential) is None
    clock.now = 1000
    supervisor.tick()
    assert len(credentials) == 1 and supervisor.cleanup_failures == 2
    process.fail_stop = False
    supervisor.tick()
    assert len(credentials) == 2  # se permite iniciar solo después de confirmar salida


def test_factory_failure_isolated_and_never_leaves_a_usable_credential() -> None:
    supervisor, registry, state, _, statuses = setup()
    credentials = []

    def fail(_, credential):
        credentials.append(credential)
        raise RuntimeError("private paths and credential")

    supervisor.add(AdapterSpec("vision@1", "head_gesture", "person"), fail)
    supervisor.add(AdapterSpec("keyboard@1", "keyboard_mouse", "person"), lambda *_: Process())
    supervisor.tick()
    assert registry.authenticate(credentials[0].credential) is None
    assert state.snapshot().stop_reachable
    assert "private" not in repr(statuses)


def test_offline_other_modality_and_bus_remain_live_when_vision_process_crashes() -> None:
    clock, registry, hardware = Clock(), AdapterRegistry(), Hardware()
    outcomes = []
    runtime = create_runtime(
        registry,
        hardware,
        Probe(),
        lambda _: None,
        outcomes.append,
        approval_min_confidence=0.85,
        clock=clock,
    )
    supervisor = Supervisor(registry, runtime.state, clock=clock)
    credentials, processes = {}, {}

    def launch(spec, credential):
        credentials[spec.identifier] = credential
        processes[spec.identifier] = Process()
        return processes[spec.identifier]

    supervisor.add(AdapterSpec("vision@1", "head_gesture", "person"), launch)
    supervisor.add(AdapterSpec("keyboard@1", "keyboard_mouse", "person"), launch)
    supervisor.tick()
    keyboard = credentials["keyboard@1"].credential
    runtime.bus.publish(message("input.resume"), keyboard)
    runtime.bus.drain()
    processes["vision@1"].alive = False
    supervisor.tick()
    assert runtime.state.snapshot().stop_reachable
    runtime.bus.publish(message("pointer.click", {"button": "left"}), keyboard)
    runtime.bus.drain()
    assert outcomes[-1].code.endswith("done") and len(hardware.events) == 2
    assert runtime.bus.publish(message("control.stop"), keyboard).accepted
    assert runtime.controller.paused


def test_explicit_stop_keeps_adapter_off_until_explicit_start_and_old_messages_are_rejected() -> (
    None
):
    supervisor, registry, state, clock, _ = setup()
    credentials = []

    def launch(_, credential):
        credentials.append(credential)
        return Process()

    supervisor.add(AdapterSpec("keyboard@1", "keyboard_mouse", "person"), launch)
    supervisor.tick()
    supervisor.stop("keyboard@1")
    clock.now = 1000
    supervisor.tick()
    assert supervisor.snapshot()[0].phase == "stopped" and len(credentials) == 1
    assert (
        not state.snapshot().stop_reachable
        and registry.authenticate(credentials[0].credential) is None
    )
    supervisor.start("keyboard@1")
    supervisor.tick()
    assert len(credentials) == 2 and state.snapshot().stop_reachable


@pytest.mark.parametrize("timing", [0, -1, True, 0.5])
def test_invalid_backoff_is_rejected(timing: object) -> None:
    with pytest.raises(ValueError):
        Supervisor(
            AdapterRegistry(), StopState(on_unreachable=lambda _: None), retry_base_ns=timing
        )
