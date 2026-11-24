from email.message import Message
from types import SimpleNamespace

import pytest
from coalsense_audit.licenses import python_license


@pytest.mark.parametrize(
    "legacy,expected",
    [
        ("MIT license", "MIT"),
        ("Apache 2.0", "Apache-2.0"),
        ("MIT license AND GPL-3.0-only", "MIT license AND GPL-3.0-only"),
        ("MIT license custom", "MIT license custom"),
    ],
)
def test_legacy_license_aliases_are_exact(
    monkeypatch: pytest.MonkeyPatch, legacy: str, expected: str
) -> None:
    metadata = Message()
    metadata["License"] = legacy
    monkeypatch.setattr(
        "importlib.metadata.distribution",
        lambda _: SimpleNamespace(
            version="1.0",
            metadata=metadata,
        ),
    )
    assert python_license("fixture", "1.0") == expected
    metadata["License-Expression"] = "GPL-3.0-only"
    assert python_license("fixture", "1.0") == "GPL-3.0-only"  # SPDX siempre manda
