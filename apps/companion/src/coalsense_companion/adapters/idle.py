"""Adaptador de diagnóstico sin dispositivo. Nunca declara una ruta de Alto sana."""

import time

from ..bus.stop_state import RouteEvidence
from .client import AdapterClient


def run(client: AdapterClient) -> None:
    while True:
        client.health(RouteEvidence(False, False, True, False))
        time.sleep(0.25)  # [SUPUESTO] informe técnico de diagnóstico, no espera de la persona
