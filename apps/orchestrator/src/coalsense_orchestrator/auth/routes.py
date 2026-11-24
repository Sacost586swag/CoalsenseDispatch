"""Rutas HTTP de autenticación. TLS obligatorio (REQ-00-026); errores en el formato común.

Detrás de un proxy, la confianza en `X-Forwarded-Proto` y `X-Forwarded-For` viene solo de
`trusted_proxies` (IP o rangos CIDR). No ejecutar uvicorn con `--proxy-headers`: reescribiría
el esquema y el cliente con otra lista de confianza (`--forwarded-allow-ips`) y las dos podrían
discrepar. Usar `--no-proxy-headers`.

Sesión: `Authorization: Bearer <credencial>`. Si el pedido toca rotar la credencial, la
respuesta trae la nueva en `X-Credential-Rotated` (con `Cache-Control: no-store`). Ninguna
ruta de contenido se sirve sin `RequireScopes`; `operator` solo recibe alcances `ops:*`.
"""

import logging
from collections.abc import Awaitable, Callable, Iterable
from ipaddress import IPv4Network, IPv6Network, ip_address, ip_network
from typing import Annotated

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from .codes import EmailCodeService
from .errors import AuthError, generic, request_invalid, tls_required
from .pairing import PairingService
from .revocation import RevocationService
from .roles import RequireScopes
from .scopes import DEVICES_MANAGE, PAIRING_CLAIM
from .sessions import Principal, SessionService

HSTS = "max-age=63072000; includeSubDomains"
log = logging.getLogger("coalsense.auth")


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RequestCode(_Body):
    email: str = Field(max_length=254)


class VerifyCode(_Body):
    email: str = Field(max_length=254)
    code: str = Field(max_length=32)
    device_label: str = Field(min_length=1, max_length=80)


# Secreto del companion: alto en entropía (>= 43 caracteres base64url = 256 bits) y seguro en URL.
CLIENT_REF = r"^[A-Za-z0-9_-]{43,128}$"


class StartPairing(_Body):
    client_ref: str = Field(pattern=CLIENT_REF)
    device_label: str = Field(min_length=1, max_length=80)


class CompanionRef(_Body):
    client_ref: str = Field(pattern=CLIENT_REF)


class CompanionDecision(CompanionRef):
    claim_id: str = Field(min_length=1, max_length=64)


class ClaimPairing(_Body):
    code: str = Field(max_length=32)


class TrustedProxies:
    """Proxies de confianza: direcciones, rangos CIDR o (solo pruebas) nombres literales."""

    def __init__(self, entries: Iterable[str]) -> None:
        self._networks: list[IPv4Network | IPv6Network] = []
        self._names: set[str] = set()
        for entry in entries:
            try:
                self._networks.append(ip_network(entry, strict=False))
            except ValueError:
                self._names.add(entry)

    def __contains__(self, host: str) -> bool:
        if host in self._names:
            return True
        try:
            address = ip_address(host)
        except ValueError:
            return False
        return any(
            address in network for network in self._networks if network.version == address.version
        )


def normalize_ip(raw: str) -> str:
    """Una red IPv6 /64 cuenta como un solo cliente; IPv4 mapeada se reduce a IPv4."""
    try:
        address = ip_address(raw)
    except ValueError:
        return raw
    if address.version == 4:
        return str(address)
    if address.ipv4_mapped:
        return str(address.ipv4_mapped)
    return str(ip_network(f"{address}/64", strict=False))


def _peer(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def client_ip(request: Request, trusted: TrustedProxies) -> str:
    """IP real: recorre `X-Forwarded-For` de derecha a izquierda solo por proxies de confianza."""
    ip = _peer(request)
    if ip in trusted:
        for hop in reversed(",".join(request.headers.getlist("x-forwarded-for")).split(",")):
            ip = hop.strip() or ip
            if ip not in trusted:
                break
    return normalize_ip(ip)


def _is_https(request: Request, trusted: TrustedProxies) -> bool:
    if request.url.scheme == "https":
        return True
    if _peer(request) not in trusted:
        return False
    # Vale el último valor: lo añadió el proxy de confianza; el cliente solo controla los previos.
    values = ",".join(request.headers.getlist("x-forwarded-proto")).split(",")
    return values[-1].strip().lower() == "https"


def _json(error: AuthError) -> JSONResponse:
    headers = {"Retry-After": str(error.retry_after_s)} if error.retry_after_s else None
    return JSONResponse(error.to_dict(), status_code=error.status, headers=headers)


def _log_error(request: Request, event: str, status: int) -> None:
    # Clave `route` (plantilla), nunca `path`: el depurador de registros descarta `path`.
    route = getattr(request.scope.get("route"), "path", "-")
    log.warning(event, extra={"route": route, "status": status})


def create_app(
    emails: EmailCodeService,
    pairing: PairingService,
    sessions: SessionService,
    revocation: RevocationService,
    *,
    trusted_proxies: Iterable[str] = frozenset(),
) -> FastAPI:
    trusted = TrustedProxies(trusted_proxies)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.sessions = sessions
    manager = Annotated[Principal, Depends(RequireScopes(DEVICES_MANAGE))]
    claimer = Annotated[Principal, Depends(RequireScopes(PAIRING_CLAIM))]
    authenticated = Annotated[Principal, Depends(RequireScopes())]

    @app.middleware("http")
    async def require_tls(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not _is_https(request, trusted):
            return _json(tls_required())
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = HSTS
        rotated = getattr(request.state, "rotated_credential", None)
        if rotated:
            response.headers["X-Credential-Rotated"] = rotated
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(AuthError)
    async def auth_error(request: Request, error: AuthError) -> JSONResponse:
        return _json(error)

    @app.exception_handler(RequestValidationError)
    async def invalid(request: Request, error: RequestValidationError) -> JSONResponse:
        return _json(request_invalid())  # el cuerpo no se repite: puede traer correo o código

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
        return _json(generic(error.status_code))

    @app.exception_handler(Exception)
    async def unexpected(request: Request, error: Exception) -> JSONResponse:
        _log_error(request, "auth.http.unexpected", 500)  # sin el error: podría traer datos
        return _json(generic(500))

    @app.get("/auth/session")
    def session_summary(who: authenticated, response: Response) -> dict[str, str]:
        response.headers["Cache-Control"] = "no-store"
        return {
            "account_id": who.account_id,
            "device_id": who.device_id,
            "session_id": who.session_id,
            "role": who.role,
        }

    @app.post("/auth/code/request", status_code=202)
    def request_code(body: RequestCode, request: Request) -> dict[str, bool]:
        emails.request(body.email, client_ip(request, trusted))
        return {"requested": True}

    @app.post("/auth/code/verify")
    def verify_code(
        body: VerifyCode, request: Request, response: Response
    ) -> dict[str, str | bool]:
        who, device, created, issued = emails.verify(
            body.email, body.code, body.device_label, client_ip(request, trusted)
        )
        response.headers["Cache-Control"] = "no-store"  # lleva la credencial, solo esta vez
        return {
            "account_id": who.id,
            "device_id": device.id,
            "session_id": issued.session_id,
            "credential": issued.value,
            "created": created,
        }

    @app.post("/auth/pairing/start", status_code=201)
    def start_pairing(body: StartPairing, request: Request) -> dict[str, str]:
        code = pairing.start(body.client_ref, body.device_label, client_ip(request, trusted))
        return {"code": code}

    @app.post("/auth/pairing/claim", status_code=202)
    def claim_pairing(body: ClaimPairing, request: Request, who: claimer) -> dict[str, str]:
        pairing.claim(who.account_id, body.code, client_ip(request, trusted))
        return {"status": "pending"}

    @app.post("/auth/pairing/status")
    def pairing_status(body: CompanionRef, request: Request) -> dict[str, str | None]:
        state, hint, claim_id = pairing.status(body.client_ref, client_ip(request, trusted))
        return {"state": state, "hint": hint, "claim_id": claim_id}

    @app.post("/auth/pairing/confirm")
    def confirm_pairing(
        body: CompanionDecision, request: Request, response: Response
    ) -> dict[str, str]:
        ip = client_ip(request, trusted)
        device, issued = pairing.confirm(body.client_ref, body.claim_id, ip)
        response.headers["Cache-Control"] = "no-store"  # lleva la credencial, solo esta vez
        return {
            "device_id": device.id,
            "session_id": issued.session_id,
            "credential": issued.value,
        }

    @app.post("/auth/pairing/reject")
    def reject_pairing(body: CompanionDecision, request: Request) -> dict[str, bool]:
        pairing.reject(body.client_ref, body.claim_id, client_ip(request, trusted))
        return {"rejected": True}

    @app.post("/auth/devices/{device_id}/revoke")
    def revoke_device(device_id: str, who: manager) -> dict[str, bool]:
        revocation.revoke_device(who.account_id, device_id)
        return {"revoked": True}

    @app.post("/auth/sessions/{session_id}/revoke")
    def revoke_session(session_id: str, who: manager) -> dict[str, bool]:
        revocation.revoke_session(who.account_id, session_id)
        return {"revoked": True}

    return app
