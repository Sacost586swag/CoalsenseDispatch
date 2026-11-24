"""Roles y alcances (REQ-00-024): la tabla explícita; lo que no está aquí no se puede.

`operator` solo tiene alcances técnicos `ops:*` (métricas, salud): ninguno de lectura de
contenido (V-11, P-00-4). El caregiver no aprueba por la persona (V-12): `approval:decide`
llega con un permiso delegado y revocable que existe en otra tarea.

[SUPUESTO] Los alcances de `caregiver` y `company` (fase 2) son los mínimos de cada rol.
"""

from collections.abc import Mapping

CONTENT_READ = "content:read"
CONTENT_WRITE = "content:write"
APPROVAL_DECIDE = "approval:decide"
DEVICES_MANAGE = "devices:manage"
PAIRING_CLAIM = "pairing:claim"
COMPANY_MANAGE = "company:manage"
OPS_METRICS = "ops:metrics"
OPS_HEALTH = "ops:health"

# Quien alcance alguno de estos ve o decide sobre contenido privado.
CONTENT_SCOPES = frozenset({CONTENT_READ, CONTENT_WRITE, APPROVAL_DECIDE})

_ACCOUNT = frozenset({DEVICES_MANAGE, PAIRING_CLAIM})

ROLE_SCOPES: Mapping[str, frozenset[str]] = {
    "person": _ACCOUNT | {CONTENT_READ, CONTENT_WRITE, APPROVAL_DECIDE},
    "caregiver": _ACCOUNT | {CONTENT_READ, CONTENT_WRITE},
    "operator": frozenset({OPS_METRICS, OPS_HEALTH}),
    "company": _ACCOUNT | {COMPANY_MANAGE},  # fase 2
}


def scopes_for(role: str) -> frozenset[str]:
    """Un rol desconocido no tiene ningún alcance."""
    return ROLE_SCOPES.get(role, frozenset())
