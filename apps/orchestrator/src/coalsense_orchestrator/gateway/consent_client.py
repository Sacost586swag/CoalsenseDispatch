"""Puerto de consent.check (spec 05), sin concesiones ni almacenamiento local.

El gateway debe consultarlo justo antes de cada salida. Una comprobación anterior
del constructor de prompts no es un sello ni una autorización reutilizable.
"""

from typing import Protocol


class ConsentError(ValueError):
    """Código sin contenido, identificadores ni errores del servicio remoto."""


class ConsentChecker(Protocol):
    async def check(self, person_id: str, category: str, provider: str) -> bool:
        """Consulta vigente; la identidad llega del contexto autenticado."""
        ...


class DenyConsentChecker:
    """Hasta integrar T-05-011, no existe consentimiento concedido implícitamente."""

    async def check(self, person_id: str, category: str, provider: str) -> bool:
        return False


async def require_consent(
    checker: ConsentChecker, person_id: str, category: str, provider: str
) -> None:
    if any(
        type(value) is not str or not value.strip() for value in (person_id, category, provider)
    ):
        raise ConsentError("consent.context.invalid")
    decision: object = None
    try:
        decision = await checker.check(person_id, category, provider)
    except Exception:
        # Fuera del manejador se eleva sin encadenar el error del servicio.
        pass
    if type(decision) is not bool:
        raise ConsentError("consent.unavailable")
    if decision is not True:
        raise ConsentError("consent.denied")
