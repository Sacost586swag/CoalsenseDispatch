"""Configuración privada de PostgreSQL; TLS salvo pruebas explícitas en loopback."""

import re
import ssl
from dataclasses import dataclass, field
from urllib.parse import parse_qsl, quote, urlsplit, urlunsplit

from pydantic import SecretStr

from .roles import PersistenceError


@dataclass(frozen=True)
class DatabaseSettings:
    dsn: SecretStr = field(repr=False)
    testing_local: bool = False

    @classmethod
    def from_connection(
        cls,
        *,
        username: str,
        password: SecretStr,
        host: str,
        database: str,
        port: int = 5432,
        testing_local: bool = False,
    ) -> "DatabaseSettings":
        """Codifica componentes; contraseñas con @, : o / no alteran la dirección."""
        valid = (
            type(username) is str
            and bool(username)
            and type(password) is SecretStr
            and bool(password.get_secret_value())
            and type(host) is str
            and re.fullmatch(r"[a-zA-Z0-9.:-]+", host) is not None
            and type(database) is str
            and bool(database)
            and type(port) is int
            and 0 < port < 65536
        )
        if not valid:
            raise PersistenceError("persistence.configuration.invalid")
        dsn: str | None = None
        try:
            address = "[" + host + "]" if ":" in host else host
            userinfo = quote(username, safe="") + ":" + quote(password.get_secret_value(), safe="")
            dsn = urlunsplit(
                (
                    "postgresql",
                    userinfo + "@" + address + ":" + str(port),
                    "/" + quote(database, safe=""),
                    "",
                    "",
                )
            )
        except (UnicodeError, ValueError):
            pass
        if dsn is None:
            raise PersistenceError("persistence.configuration.invalid")
        return cls.from_dsn(dsn, testing_local=testing_local)

    @classmethod
    def from_dsn(cls, dsn: str, *, testing_local: bool = False) -> "DatabaseSettings":
        valid = False
        try:
            if type(dsn) is not str or type(testing_local) is not bool:
                raise ValueError
            parsed = urlsplit(dsn)
            query = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
            valid = bool(
                parsed.scheme in ("postgres", "postgresql")
                and parsed.username
                and parsed.password
                and parsed.hostname
                and parsed.path.startswith("/")
                and len(parsed.path) > 1
                and "/" not in parsed.path[1:]
                and not parsed.fragment
                and (parsed.port is None or 0 < parsed.port < 65536)
                and (not query or query == [("sslmode", "verify-full")])
                and (not testing_local or parsed.hostname in {"127.0.0.1", "::1", "localhost"})
            )
        except Exception:
            pass
        if not valid:
            raise PersistenceError("persistence.configuration.invalid")
        return cls(SecretStr(dsn), testing_local)

    def tls(self) -> ssl.SSLContext | bool:
        return False if self.testing_local else ssl.create_default_context()
