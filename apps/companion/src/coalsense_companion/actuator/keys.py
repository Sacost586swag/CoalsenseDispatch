"""Acordes acotados: validar todo antes de pulsar; liberar incluso si cambia foco."""

from collections.abc import Callable

from .guard import ActuationGate, ActuationTicket
from .windows import NativeInputFailure, _key_code


def press(
    gate: ActuationGate,
    ticket: ActuationTicket,
    keys: list[str],
    check_target: Callable[[], None],
) -> None:
    # [SUPUESTO] máximo 16 teclas por acorde; evita retener una secuencia arbitraria.
    normalized = [key.upper() for key in keys]
    codes = [_key_code(key) for key in normalized]
    if len(codes) > 16 or len(set(codes)) != len(codes):
        raise NativeInputFailure()
    try:
        for key in normalized:

            def down(key: str = key) -> None:
                check_target()
                gate.controller.key_down(ticket.lease, key)

            gate.step(ticket, down)
    finally:
        # Alto invalida el ticket y se encarga de sus recursos; estos pasos no lo eluden.
        for key in reversed(normalized):

            def up(key: str = key) -> None:
                gate.controller.key_up(ticket.lease, key)

            gate.step(ticket, up)
