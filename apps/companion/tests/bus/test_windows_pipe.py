"""Named pipe real de Windows: ACL, identidad del par y cancelación sin entrada OS."""

import ctypes
import json
import os
import secrets
import subprocess
import sys
import threading
from types import SimpleNamespace

import pytest
from coalsense_companion.adapters.client import AdapterClient
from coalsense_companion.bus.pipe_server import serve_connection
from coalsense_companion.bus.session import SessionRejected, decode_message, encode_message
from coalsense_companion.bus.windows_pipe import (
    PipeClosed,
    PipeFailure,
    PipeTimeout,
    WindowsPipe,
    _Api,
    _function,
    _Overlapped,
    _SecurityAttributes,
)
from coalsense_companion.process_launch import python_launch

from .test_auth import session
from .test_core import message

native = pytest.mark.skipif(sys.platform != "win32", reason="Named pipe nativo de Windows")


def test_native_structures_have_correct_pointer_sized_abi() -> None:
    wide = ctypes.sizeof(ctypes.c_void_p) == 8
    assert ctypes.sizeof(_Overlapped) == (32 if wide else 20)
    assert ctypes.sizeof(_SecurityAttributes) == (24 if wide else 12)


def test_other_platforms_have_no_success_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    with pytest.raises(PipeFailure):
        WindowsPipe.create()


@pytest.mark.parametrize(
    "name", ["server", "\\\\remote\\pipe\\CoalsenseDispatch." + "a" * 32, "../private"]
)
def test_client_never_opens_remote_or_arbitrary_path(name: str) -> None:
    with pytest.raises(PipeFailure) as caught:
        WindowsPipe.connect(name, expected_server_pid=1)
    assert "private" not in str(caught.value)


@pytest.mark.parametrize("completed_at_deadline", [True, False])
def test_cancel_race_does_not_drop_a_message_that_already_completed(
    monkeypatch: pytest.MonkeyPatch,
    completed_at_deadline: bool,
) -> None:
    error = [997]
    closed, cancelled = [], []
    monkeypatch.setattr(ctypes, "get_last_error", lambda: error[0], raising=False)

    def read(_, buffer, size, __, operation):
        ctypes.memmove(buffer, b"{}", 2)
        return False

    def result(_, operation, count, wait):
        if completed_at_deadline:
            count._obj.value = 2
            return True
        error[0] = 995
        return False

    api = SimpleNamespace(
        create_event=lambda *_: 9,
        read=read,
        wait=lambda *_: 258,
        cancel=lambda *_: cancelled.append(True),
        result=result,
        close=closed.append,
    )
    endpoint = WindowsPipe(api, 1, "test", server=False)
    if completed_at_deadline:
        assert endpoint.read(timeout_ms=1) == b"{}"
    else:
        with pytest.raises(PipeTimeout):
            endpoint.read(timeout_ms=1)
    assert cancelled == [True] and closed == [9]


@native
def test_native_exchange_pins_both_pids_and_preserves_message_boundaries() -> None:
    server = WindowsPipe.create()
    client = WindowsPipe.connect(server.name, expected_server_pid=os.getpid())
    try:
        server.accept(expected_client_pid=os.getpid())
        client.write(b'{"one":1}')
        client.write(b'{"two":2}')
        assert server.read() == b'{"one":1}'
        assert server.read() == b'{"two":2}'
        server.write(b'{"accepted":true}')
        assert client.read() == b'{"accepted":true}'
    finally:
        client.close()
        server.close()


@native
def test_wrong_server_pid_is_rejected_before_any_credential_transfer() -> None:
    server = WindowsPipe.create()
    try:
        with pytest.raises(PipeFailure):
            WindowsPipe.connect(server.name, expected_server_pid=os.getpid() + 1)
    finally:
        server.close()


@native
def test_unregistered_client_process_pid_is_rejected() -> None:
    server = WindowsPipe.create()
    client = WindowsPipe.connect(server.name, expected_server_pid=os.getpid())
    try:
        with pytest.raises(PipeFailure):
            server.accept(expected_client_pid=os.getpid() + 1)
    finally:
        client.close()
        server.close()


@native
def test_native_timeout_is_reusable_and_close_cancels_pending_read() -> None:
    server = WindowsPipe.create()
    client = WindowsPipe.connect(server.name, expected_server_pid=os.getpid())
    errors, started = [], threading.Event()
    try:
        server.accept(expected_client_pid=os.getpid())
        with pytest.raises(PipeTimeout):
            server.read(timeout_ms=1)
        client.write(b"still alive")
        assert server.read() == b"still alive"

        def wait() -> None:
            started.set()
            try:
                server.read(timeout_ms=30000)
            except PipeClosed:
                errors.append("closed")

        worker = threading.Thread(target=wait)
        worker.start()
        assert started.wait(3)
        server.close()
        worker.join(3)
        assert not worker.is_alive() and errors == ["closed"]
    finally:
        client.close()
        server.close()


@native
def test_native_acl_is_protected_and_contains_only_current_user() -> None:
    server = WindowsPipe.create()
    security = ctypes.WinDLL("advapi32", use_last_error=True)
    pointer = ctypes.c_void_p
    get_info = _function(
        security,
        "GetSecurityInfo",
        [pointer, ctypes.c_int32, ctypes.c_uint32, *([ctypes.POINTER(pointer)] * 5)],
        ctypes.c_uint32,
    )
    to_string = _function(
        security,
        "ConvertSecurityDescriptorToStringSecurityDescriptorW",
        [
            pointer,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_wchar_p),
            ctypes.POINTER(ctypes.c_uint32),
        ],
        ctypes.c_int32,
    )
    descriptor, text = pointer(), ctypes.c_wchar_p()
    try:
        assert get_info(server._handle, 6, 4, None, None, None, None, ctypes.byref(descriptor)) == 0
        assert to_string(descriptor, 1, 4, ctypes.byref(text), None)
        assert text.value == f"D:P(A;;FA;;;{_Api().user_sid()})"
    finally:
        if text:
            server._api.free(text)
        if descriptor:
            server._api.free(descriptor)
        server.close()


@native
@pytest.mark.parametrize("registered", [True, False])
def test_native_session_reaches_bus_only_with_bound_credential_and_keeps_stop_synchronous(
    registered: bool,
) -> None:
    channel, bus, _, credential = session()
    server = WindowsPipe.create()
    stopped, errors = threading.Event(), []
    stops = []
    bus.on_stop = lambda: stops.append("halt")

    def serve() -> None:
        try:
            serve_connection(server, channel, expected_client_pid=os.getpid(), stopped=stopped)
        except (PipeClosed, SessionRejected) as error:
            errors.append(type(error).__name__)
        finally:
            channel.close()
            server.close()

    worker = threading.Thread(target=serve)
    worker.start()
    endpoint = WindowsPipe.connect(server.name, expected_server_pid=os.getpid())
    client = AdapterClient(endpoint, credential if registered else "a" * 43)
    try:
        intention = message("control.stop") | {"actor_origin": "caregiver"}
        if registered:
            assert client.publish(intention)["accepted"] is True
            assert stops == ["halt"]
            assert bus.drain()[0]["actor_origin"] == "person"
        else:
            with pytest.raises(SessionRejected):
                client.publish(intention)
            assert not stops and not bus.drain()
    finally:
        stopped.set()
        client.close()
        server.cancel()
        worker.join(3)
        server.close()
    assert not worker.is_alive()


@native
def test_real_child_uses_stdin_bootstrap_and_not_argv_for_private_token() -> None:
    server = WindowsPipe.create()
    source = (
        "import json,sys; "
        "from coalsense_companion.bus.windows_pipe import WindowsPipe; "
        "config=json.loads(sys.stdin.readline()); "
        "endpoint=WindowsPipe.connect(config['name'],expected_server_pid=config['pid']); "
        "endpoint.write(json.dumps({'token':config['token']}).encode()); "
        "reply=endpoint.read(); endpoint.close(); "
        "print(json.dumps({'accepted':json.loads(reply)['accepted']}))"
    )
    token = secrets.token_urlsafe(32)
    executable, environment = python_launch()
    child = subprocess.Popen(
        [executable, "-I", "-c", source],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
        env=environment,
    )
    try:
        assert child.stdin is not None
        child.stdin.write(
            encode_message({"name": server.name, "pid": os.getpid(), "token": token}) + b"\n"
        )
        child.stdin.flush()
        server.accept(expected_client_pid=child.pid, timeout_ms=10000)
        assert decode_message(server.read(timeout_ms=10000)) == {"token": token}
        server.write(encode_message({"accepted": True}))
        output, _ = child.communicate(timeout=10)
        assert child.returncode == 0 and json.loads(output) == {"accepted": True}
        assert token not in repr(child.args) and token.encode() not in output
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)
        server.close()
