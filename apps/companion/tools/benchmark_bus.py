"""Medición local reproducible del bus; no certifica el hardware de referencia de T-01-047."""

import argparse
import json
import math
from time import perf_counter_ns

from coalsense_common import monotonic_ns, new_id, wall_clock_iso
from coalsense_companion.bus.auth import AdapterRegistry
from coalsense_companion.bus.core import IntentBus


def measure(samples: int, warmup: int) -> dict[str, int | float | bool]:
    if samples < 1 or warmup < 0:
        raise ValueError("Invalid benchmark sample count")
    registry = AdapterRegistry()
    adapter = registry.register("benchmark@1", "keyboard_mouse", "person")
    bus = IntentBus(registry, lambda _: None, on_stop=lambda: None, approval_min_confidence=0.85)
    delivered = 0

    def consume(_: object) -> None:
        nonlocal delivered
        delivered += 1

    bus.subscribe(["nav.next"], consume)
    durations = []
    for index in range(warmup + samples):
        intention = {
            "id": new_id(),
            "type": "nav.next",
            "monotonic_ts": monotonic_ns() // 1000,
            "wall_ts": wall_clock_iso(),
            "payload": {},
        }
        start = perf_counter_ns()
        result = bus.publish(intention, adapter.credential)
        bus.drain_one()
        elapsed = (perf_counter_ns() - start) / 1_000_000
        if not result.accepted:
            raise RuntimeError("Benchmark intention rejected")
        if index >= warmup:
            durations.append(elapsed)
    durations.sort()
    return {
        "samples": samples,
        "warmup": warmup,
        "delivered": delivered,
        "p50_ms": durations[math.ceil(samples * 0.50) - 1],
        "p95_ms": durations[math.ceil(samples * 0.95) - 1],
        "max_ms": durations[-1],
        "reference_hardware_verified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Medir validación y entrega local del bus")
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--warmup", type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(measure(args.samples, args.warmup), indent=2))


if __name__ == "__main__":
    main()
