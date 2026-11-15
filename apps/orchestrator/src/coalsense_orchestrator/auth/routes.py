"""Rutas HTTP de autenticación. TLS obligatorio (REQ-00-026); errores en el formato común."""

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from .codes import EmailCodeService
from .errors import AuthError, generic, request_invalid, session_required, tls_required
from .pairing import PairingService

HSTS = "max-age=63072000; includeSubDomains"


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RequestCode(_Body):
    email: str = Field(max_length=254)


class VerifyCode(_Body):
    email: str = Field(max_length=254)
    code: str = Field(max_length=32)
    device_label: str = Field(min_length=1, max_length=80)


class StartPairing(_Body):
    client_ref: str = Field(min_length=16, max_length=128)
    device_label: str = Field(min_length=1, max_length=80)


class ClaimPairing(_Body):
    code: str = Field(max_length=32)


def _no_session(request: Request) -> str:
    raise session_required()


def _peer(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def client_ip(request: Request, trusted: frozenset[str]) -> str:
    """IP real: recorre `X-Forwarded-For` de derecha a izquierda solo por proxies de confianza."""
    ip = _peer(request)
    if ip in trusted:
        for hop in reversed(request.headers.get("x-forwarded-for", "").split(",")):
            ip = hop.strip() or ip
            if ip not in trusted:
                break
    return ip


def _is_https(request: Request, trusted: frozenset[str]) -> bool:
    if request.url.scheme == "https":
        return True
    forwarded = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    return _peer(request) in trusted and forwarded == "https"


def _json(error: AuthError) -> JSONResponse:
    headers = {"Retry-After": str(error.retry_after_s)} if error.retry_after_s else None
    return JSONResponse(error.to_dict(), status_code=error.status, headers=headers)


def create_app(
    emails: EmailCodeService,
    pairing: PairingService,
    *,
    trusted_proxies: frozenset[str] = frozenset(),
    current_account: Callable[[Request], str] = _no_session,
) -> FastAPI:
    """`current_account` devuelve el id de la cuenta con sesión abierta; la sesión es T-00-011."""
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    account = Annotated[str, Depends(current_account)]

    @app.middleware("http")
    async def require_tls(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not _is_https(request, trusted_proxies):
            return _json(tls_required())
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = HSTS
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
        return _json(generic(500))

    @app.post("/auth/code/request", status_code=202)
    def request_code(body: RequestCode, request: Request) -> dict[str, bool]:
        emails.request(body.email, client_ip(request, trusted_proxies))
        return {"requested": True}

    @app.post("/auth/code/verify")
    def verify_code(body: VerifyCode, request: Request) -> dict[str, str | bool]:
        who, device, created = emails.verify(
            body.email, body.code, body.device_label, client_ip(request, trusted_proxies)
        )
        return {"account_id": who.id, "device_id": device.id, "created": created}

    @app.post("/auth/pairing/start", status_code=201)
    def start_pairing(body: StartPairing, request: Request) -> dict[str, str]:
        ip = client_ip(request, trusted_proxies)
        code = pairing.start(body.client_ref, body.device_label, ip)
        return {"code": code}

    @app.post("/auth/pairing/claim")
    def claim_pairing(body: ClaimPairing, request: Request, account_id: account) -> dict[str, str]:
        device = pairing.claim(account_id, body.code, client_ip(request, trusted_proxies))
        return {"device_id": device.id}

    @app.post("/auth/devices/{device_id}/revoke")
    def revoke_device(device_id: str, account_id: account) -> dict[str, bool]:
        pairing.revoke(account_id, device_id)
        return {"revoked": True}

    return app
