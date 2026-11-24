"""Sesión por dispositivo (REQ-00-022, REQ-00-023): credencial opaca con rotación.

- Credencial: `secrets.token_urlsafe(32)`. Se entrega una sola vez (al emparejar o ingresar) y
  solo se guarda su HMAC con la clave de autenticación. Nunca va a logs ni a la bitácora.
- Rotación: la primera vez que se usa pasada `ROTATE_AFTER_S` desde la emisión, la respuesta
  trae una credencial nueva (cabecera `X-Credential-Rotated`). La anterior vale un único uso más,
  para no perder la sesión si la respuesta se pierde o dos pedidos se cruzan; ese uso rota otra
  vez, así que la persona siempre sale con una credencial vigente.
- Sin inactividad: la sesión no tiene vencimiento ni por tiempo ni por inactividad. Una persona
  puede dejar trabajo pendiente semanas y volver. La única forma de cerrarla es revocarla
  (`revocation.py`) o que la rotación falle (la respuesta se pierde dos veces seguidas).
- Revocar es inmediato: cada pedido consulta el repositorio, no hay caché que lo retrase.

shortcut: la gracia no detecta robo de una credencial vieja; la revocación es el remedio.
"""

import hmac
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime

from coalsense_common import new_id

from .errors import session_required
from .ports import Account, AuthDeps, Device, Session
from .scopes import scopes_for

ROTATE_AFTER_S = 60 * 60  # [SUPUESTO] 60 minutos desde la emisión
CREDENTIAL = re.compile(r"[A-Za-z0-9_-]{43}")  # token_urlsafe(32)


def new_credential() -> str:
    return secrets.token_urlsafe(32)


def credential_hash(key: bytes, credential: str) -> str:
    return hmac.new(key, f"session|{credential}".encode(), "sha256").hexdigest()


@dataclass(frozen=True)
class IssuedCredential:
    session_id: str
    value: str = field(repr=False)


@dataclass(frozen=True)
class Principal:
    """Quien hace el pedido: alcances efectivos = los de la sesión que su rol todavía permite."""

    account_id: str
    device_id: str
    session_id: str
    role: str
    scopes: frozenset[str]


class SessionService:
    def __init__(self, deps: AuthDeps) -> None:
        self.deps = deps

    def issue(self, account: Account, device: Device) -> IssuedCredential:
        """Crea la sesión del dispositivo. Quien llama ya tiene `deps.lock`."""
        d = self.deps
        value = new_credential()
        session = Session(
            id=new_id(),
            device_id=device.id,
            scopes=scopes_for(account.role),
            credential_hash=credential_hash(d.key, value),
            rotated_at=d.clock.now_iso(),
        )
        d.repo.add_session(session)
        d.emit("auth.session.issued", "ok", account.id, device.id)
        return IssuedCredential(session.id, value)

    def authenticate(self, credential: str | None) -> tuple[Principal, str | None]:
        """(quién es, credencial nueva si tocó rotar). 401 igual para todo caso inválido."""
        d = self.deps
        if credential is None or not CREDENTIAL.fullmatch(credential):
            raise session_required()
        presented = credential_hash(d.key, credential)
        with d.lock:
            session = d.repo.find_session(presented)
            if session is None:
                raise session_required()
            device = d.repo.get_device(session.device_id)
            account = d.repo.get_account(device.account_id) if device else None
            if session.revoked_at or device is None or device.revoked_at or account is None:
                owner = device.account_id if device else None
                d.emit("auth.session.rejected", "failed", owner, session.device_id)
                raise session_required()
            current = hmac.compare_digest(session.credential_hash, presented)
            rotated = None
            if not current or self._due(session):
                rotated = self._rotate(session, account.id)
            principal = Principal(
                account_id=account.id,
                device_id=device.id,
                session_id=session.id,
                role=account.role,
                scopes=session.scopes & scopes_for(account.role),
            )
            return principal, rotated

    def _due(self, session: Session) -> bool:
        now = datetime.fromisoformat(self.deps.clock.now_iso())
        return (now - datetime.fromisoformat(session.rotated_at)).total_seconds() >= ROTATE_AFTER_S

    def _rotate(self, session: Session, account_id: str) -> str:
        d = self.deps
        value = new_credential()
        # La vigente pasa a ser la de gracia; la de gracia usada (si se presentó) queda fuera.
        session.previous_hash = session.credential_hash
        session.credential_hash = credential_hash(d.key, value)
        session.rotated_at = d.clock.now_iso()
        d.repo.update_session(session)
        d.emit("auth.session.rotated", "ok", account_id, session.device_id)
        return value
