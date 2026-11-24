"""Dependencia FastAPI `RequireScopes`: sesión real + alcances (REQ-00-024).

Toda ruta que no sea de entrada (código, emparejamiento del companion) declara sus alcances
aquí. Sin sesión válida: 401. Con sesión pero sin el alcance: 403, también para `operator` en
cualquier ruta de contenido (V-11, P-00-4).
"""

from fastapi import Request

from .errors import forbidden
from .sessions import Principal, SessionService


def bearer(request: Request) -> str | None:
    scheme, _, value = request.headers.get("authorization", "").partition(" ")
    return value.strip() if scheme.lower() == "bearer" else None


class RequireScopes:
    """Se usa como `Depends(RequireScopes(CONTENT_READ))`; `scopes` permite auditar las rutas."""

    def __init__(self, *scopes: str) -> None:
        self.scopes = frozenset(scopes)

    def __call__(self, request: Request) -> Principal:
        sessions: SessionService = request.app.state.sessions
        principal, rotated = sessions.authenticate(bearer(request))
        if rotated:
            request.state.rotated_credential = rotated  # lo agrega a la respuesta el middleware
        if not self.scopes <= principal.scopes:
            sessions.deps.emit(
                "auth.scope.denied", "failed", principal.account_id, principal.device_id
            )
            raise forbidden()
        return principal

