"""Etapa de integración real: Docker ausente o una imagen ausente hacen fallar la prueba."""

import os
from pathlib import Path

import pytest

if __name__ == "__main__":
    os.environ["COALSENSE_TEST_POSTGRES"] = "1"
    tests = Path(__file__).resolve().parents[1] / "tests/persistence"
    raise SystemExit(pytest.main([str(tests), "-q", "-rs"]))
