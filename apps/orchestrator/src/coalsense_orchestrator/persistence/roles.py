"""La identidad viene de la sesión, nunca de un person_id enviado en el cuerpo."""

from collections.abc import Mapping
from uuid import UUID

from coalsense_orchestrator.auth.sessions import Principal


class PersistenceError(ValueError):
    """Código de dominio sin DSN, consulta, parámetros ni errores del controlador."""


def person_scope(principal: Principal, scope: str) -> UUID:
    if (
        type(principal) is not Principal
        or principal.role != "person"
        or scope not in principal.scopes
    ):
        raise PersistenceError("persistence.access.denied")
    person_id: UUID | None = None
    try:
        person_id = UUID(principal.account_id)
    except (ValueError, TypeError, AttributeError):
        pass
    if person_id is None:
        raise PersistenceError("persistence.access.denied")
    return person_id


def agent_environment(environment: Mapping[str, str]) -> dict[str, str]:
    """Base para el futuro lanzador; no acredita aislamiento de red del proceso.

    No se heredan DSN, PG*, claves, tokens, PYTHONPATH ni configuración de proxies.
    El ejecutable del agente debe indicarse por una ruta absoluta.
    """
    allowed = {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG", "LC_ALL"}
    return {name: value for name, value in environment.items() if name.upper() in allowed}
