"""REQ-00-022: persistencia segura, rotación y aislamiento de sesiones del companion."""

import logging
import sys
from uuid import uuid4

import pytest
from coalsense_companion.auth.credential_store import (
    CredentialStore,
    CredentialStoreError,
    DeviceCredential,
    WindowsCredentialBackend,
)


class MemoryBackend:
    def __init__(self) -> None:
        self.items: dict[str, bytes] = {}

    def read(self, target: str) -> bytes | None:
        return self.items.get(target)

    def write(self, target: str, value: bytes) -> None:
        self.items[target] = value

    def delete(self, target: str) -> None:
        self.items.pop(target, None)


def test_session_survives_a_new_store_and_rotation_replaces_the_secret() -> None:
    backend = MemoryBackend()
    store = CredentialStore("https://example.org", "device-1", backend=backend)
    assert store.load() is None
    old = DeviceCredential("session-1", "A" * 43)
    store.save(old)
    restarted = CredentialStore("https://example.org", "device-1", backend=backend)
    assert restarted.load() == old
    new = DeviceCredential("session-1", "B" * 43)
    restarted.save(new)
    assert store.load() == new
    assert all(old.value.encode() not in blob for blob in backend.items.values())
    store.clear()
    assert restarted.load() is None
    store.clear()  # cerrar una sesión ya borrada es seguro


def test_credentials_are_isolated_by_service_and_device() -> None:
    backend = MemoryBackend()
    original = CredentialStore("https://example.org", "device-1", backend=backend)
    original.save(DeviceCredential("session-1", "A" * 43))
    for origin, device in (
        ("https://other.example.org", "device-1"),
        ("https://example.org:8443", "device-1"),
        ("https://example.org", "device-2"),
    ):
        assert CredentialStore(origin, device, backend=backend).load() is None
    equivalent = CredentialStore("https://EXAMPLE.org:443/", "device-1", backend=backend)
    assert equivalent.load() == original.load()
    assert not any("device-1" in target for target in backend.items)


@pytest.mark.parametrize(
    "origin",
    [
        "http://example.org",
        "https://user:xxx@example.org",
        "https://example.org/path",
        "https://example.org?secret=value",
        "https://example.org#fragment",
        "https://",
    ],
)
def test_rejects_unsafe_service_origins(origin: str) -> None:
    with pytest.raises(ValueError):
        CredentialStore(origin, "device-1", backend=MemoryBackend())


@pytest.mark.parametrize("value", ["", "short", "é" * 43, "A" * 43 + "\n"])
def test_rejects_malformed_credentials(value: str) -> None:
    with pytest.raises(ValueError):
        DeviceCredential("session-1", value)


def test_secret_is_not_in_representations_or_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    credential = DeviceCredential("session-1", "A" * 43)
    backend = MemoryBackend()
    store = CredentialStore("https://example.org", "device-1", backend=backend)
    store.save(credential)
    store.load()
    assert credential.value not in repr(credential) + repr(store) + caplog.text


@pytest.mark.parametrize("operation", ["read", "write", "delete"])
def test_backend_errors_do_not_expose_secrets(operation: str) -> None:
    class BrokenBackend(MemoryBackend):
        def read(self, target: str) -> bytes | None:
            if operation == "read":
                raise OSError("private secret")
            return super().read(target)

        def write(self, target: str, value: bytes) -> None:
            if operation == "write":
                raise OSError("private secret")
            super().write(target, value)

        def delete(self, target: str) -> None:
            if operation == "delete":
                raise OSError("private secret")
            super().delete(target)

    store = CredentialStore("https://example.org", "device-1", backend=BrokenBackend())
    with pytest.raises(CredentialStoreError) as caught:
        if operation == "read":
            store.load()
        elif operation == "write":
            store.save(DeviceCredential("session-1", "A" * 43))
        else:
            store.clear()
    assert "private secret" not in str(caught.value)
    assert caught.value.__suppress_context__


@pytest.mark.parametrize(
    "blob",
    [
        b"private secret",
        b"{}",
        b"[]",
        b"\xff",
        b'{"version":2,"session_id":"s","value":"private secret"}',
    ],
)
def test_corruption_is_reported_without_exposing_the_blob(blob: bytes) -> None:
    backend = MemoryBackend()
    store = CredentialStore("https://example.org", "device-1", backend=backend)
    store.save(DeviceCredential("session-1", "A" * 43))
    backend.items[next(iter(backend.items))] = blob
    with pytest.raises(CredentialStoreError) as caught:
        store.load()
    assert "private secret" not in str(caught.value)


@pytest.mark.skipif(sys.platform != "win32", reason="Requiere Windows Credential Manager")
def test_windows_vault_round_trip_and_rotation() -> None:
    # Destino aleatorio exclusivo de la prueba; no toca credenciales existentes.
    device = f"test-{uuid4()}"
    store = CredentialStore("https://credential-test.invalid", device)
    try:
        assert store.load() is None
        store.save(DeviceCredential("session-test", "A" * 43))
        restarted = CredentialStore("https://credential-test.invalid", device)
        assert restarted.load() == DeviceCredential("session-test", "A" * 43)
        restarted.save(DeviceCredential("session-test", "B" * 43))
        assert store.load() == DeviceCredential("session-test", "B" * 43)
    finally:
        store.clear()
    assert store.load() is None


def test_non_windows_never_falls_back_to_a_plaintext_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    with pytest.raises(CredentialStoreError):
        WindowsCredentialBackend()
