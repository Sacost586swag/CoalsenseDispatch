"""Revocación inmediata de dispositivos y sesiones (REQ-00-023).

Sin caché: `SessionService.authenticate` consulta el repositorio en cada pedido, así que la
credencial revocada falla en el siguiente. Cada revocación deja un evento de bitácora que la
persona puede ver (se le informa); el cuerpo de la bitácora nunca lleva credenciales.
"""

from .errors import device_not_found, session_not_found
from .ports import AuthDeps


class RevocationService:
    def __init__(self, deps: AuthDeps) -> None:
        self.deps = deps

    def revoke_device(self, account_id: str, device_id: str) -> None:
        """Revoca el dispositivo y, con él, su sesión. Ajeno e inexistente dan el mismo 404."""
        d = self.deps
        with d.lock:
            device = d.repo.get_device(device_id)
            if device is None or device.account_id != account_id or device.revoked_at:
                d.emit("auth.device.revoked", "failed", account_id)
                raise device_not_found()
            now = d.clock.now_iso()
            device.revoked_at = now
            d.repo.update_device(device)
            session = d.repo.session_of_device(device_id)
            if session and not session.revoked_at:
                session.revoked_at = now
                d.repo.update_session(session)
            d.emit("auth.device.revoked", "ok", account_id, device_id)

    def revoke_session(self, account_id: str, session_id: str) -> None:
        """Cierra solo la sesión; el dispositivo sigue vinculado y puede ingresar de nuevo."""
        d = self.deps
        with d.lock:
            session = d.repo.get_session(session_id)
            device = d.repo.get_device(session.device_id) if session else None
            if session is None or device is None or device.account_id != account_id:
                d.emit("auth.session.revoked", "failed", account_id)
                raise session_not_found()
            if session.revoked_at:
                d.emit("auth.session.revoked", "failed", account_id, device.id)
                raise session_not_found()
            session.revoked_at = d.clock.now_iso()
            d.repo.update_session(session)
            d.emit("auth.session.revoked", "ok", account_id, device.id)
