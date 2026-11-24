"""Arranque fijo del hijo. La credencial llega exclusivamente por stdin heredado."""

import re
import sys

from ..bus.session import MAX_MESSAGE_BYTES, SessionRejected, decode_message
from ..bus.windows_pipe import WindowsPipe
from . import ADAPTER_MODULES
from .client import AdapterClient
from .idle import run as run_idle


def main() -> int:
    client: AdapterClient | None = None
    try:
        bootstrap = decode_message(sys.stdin.buffer.readline(MAX_MESSAGE_BYTES + 1))
        sys.stdin.close()
        if (
            set(bootstrap) != {"version", "pipe", "server_pid", "credential", "module"}
            or type(bootstrap["version"]) is not int
            or bootstrap["version"] != 1
            or not isinstance(bootstrap["pipe"], str)
            or type(bootstrap["server_pid"]) is not int
            or bootstrap["server_pid"] <= 0
            or not isinstance(bootstrap["credential"], str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{43}", bootstrap["credential"])
            or not isinstance(bootstrap["module"], str)
            or bootstrap["module"] not in ADAPTER_MODULES
        ):
            raise SessionRejected()
        endpoint = WindowsPipe.connect(
            bootstrap["pipe"], expected_server_pid=bootstrap["server_pid"]
        )
        client = AdapterClient(endpoint, bootstrap["credential"])
        bootstrap.clear()
        run_idle(client)
        return 0
    except Exception:
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
