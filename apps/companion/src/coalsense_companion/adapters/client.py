"""Cliente de adaptador: una solicitud por respuesta, sin reintento de acciones inciertas."""

import threading
from dataclasses import asdict

from ..bus.session import SessionRejected, decode_message, encode_message
from ..bus.stop_state import RouteEvidence
from ..bus.windows_pipe import WindowsPipe


class AdapterClient:
    def __init__(self, endpoint: WindowsPipe, credential: str) -> None:
        self._endpoint, self._credential = endpoint, credential
        self._sequence = 0
        self._lock = threading.Lock()

    def _request(self, kind: str, value: object) -> dict[str, object]:
        with self._lock:
            if not self._credential:
                raise SessionRejected()
            self._sequence += 1
            try:
                self._endpoint.write(
                    encode_message(
                        {
                            "version": 1,
                            "credential": self._credential,
                            "sequence": self._sequence,
                            "kind": kind,
                            kind: value,
                        }
                    )
                )
                reply = decode_message(self._endpoint.read())
                status = reply.get("status")
                if (
                    set(reply) != {"version", "sequence", "accepted", "status"}
                    or type(reply["version"]) is not int
                    or reply["version"] != 1
                    or type(reply["sequence"]) is not int
                    or reply["sequence"] != self._sequence
                    or type(reply["accepted"]) is not bool
                    or not isinstance(status, str)
                    or not status.isascii()
                    or len(status) > 64
                ):
                    raise SessionRejected()
                return reply
            except Exception:
                self._credential = ""
                self._endpoint.close()
                raise SessionRejected() from None

    def publish(self, intention: object) -> dict[str, object]:
        return self._request("intent", intention)

    def health(self, evidence: RouteEvidence) -> None:
        if not self._request("health", asdict(evidence))["accepted"]:
            raise SessionRejected()

    def close(self) -> None:
        self._credential = ""
        self._endpoint.close()
