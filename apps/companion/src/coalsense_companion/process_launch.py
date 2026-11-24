"""Intérprete CPython real y entorno mínimo para procesos de adaptadores Windows.

El redirector venv de Windows crea otro PID. CPython 3.12 permite conservar el venv
al ejecutar el intérprete base con __PYVENV_LAUNCHER__ (Modules/getpath.py). No se
heredan variables de proveedores, secretos, PYTHONPATH ni PYTHONHOME del núcleo.
"""

import os
import sys
from pathlib import Path
from typing import cast


class ProcessLaunchFailure(RuntimeError):
    def __init__(self) -> None:
        super().__init__("The isolated local adapter process could not be started")


def python_launch() -> tuple[str, dict[str, str]]:
    if sys.platform != "win32" or getattr(sys, "frozen", False):
        raise ProcessLaunchFailure()
    executable = Path(cast(str, getattr(sys, "_base_executable", sys.executable)))
    if not executable.is_absolute() or not executable.is_file():
        raise ProcessLaunchFailure()
    allowed = {
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMDATA",
        "COMSPEC",
        "NUMBER_OF_PROCESSORS",
        "PROCESSOR_ARCHITECTURE",
    }
    environment = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    environment["__PYVENV_LAUNCHER__"] = sys.executable
    return str(executable), environment
