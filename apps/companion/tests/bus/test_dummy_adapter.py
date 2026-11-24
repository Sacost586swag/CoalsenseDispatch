from copy import deepcopy

from coalsense_intents import Intent

from .test_core import message, setup_bus


def test_unsubscribe_and_dummy_adapter_do_not_require_consumer_changes() -> None:
    bus, registry, _, _, _ = setup_bus()
    seen: list[Intent] = []
    unsubscribe = bus.subscribe(["nav.next"], seen.append)
    dummy = registry.register("dummy@1", "switch_scan", "person")
    bus.publish(deepcopy(message("nav.next")), dummy.credential)
    bus.drain()
    assert seen[0]["modality"] == "switch_scan"
    unsubscribe()
    bus.publish(message("nav.next"), dummy.credential)
    bus.drain()
    assert len(seen) == 1
