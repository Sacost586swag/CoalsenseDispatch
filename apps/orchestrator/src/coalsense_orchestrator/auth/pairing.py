"""Emparejamiento de un dispositivo con un código corto (REQ-00-021), en dos pasos.

1. `start`: el companion genera un `client_ref` secreto (alta entropía, solo viaja a esta API;
   aquí se guarda únicamente su HMAC) y pide un código, que muestra en pantalla.
2. `claim`: la persona o su cuidador/a dicta el código en la web, con la cuenta abierta. Solo
   marca el código como reclamado por esa cuenta; no crea ningún dispositivo.
3. `status` / `confirm` / `reject`: el companion, con su `client_ref`, ve a qué cuenta se
   le pide vincularlo (pista: el correo enmascarado, p. ej. p***@e***) y el `claim_id` del
   reclamo pendiente. Confirma o rechaza en el propio equipo enviando ese `claim_id`; si no
   coincide, falla con 409. Solo `confirm` crea la fila `device`; `reject` invalida el código.
   El primer reclamo gana: mientras hay uno pendiente, los demás se rechazan (sin tiempo límite
   para que la persona decida) y gastan espera y cupo del código.

Así adivinar un código no basta para atar un equipo ajeno a otra cuenta. Sin vencimiento por
tiempo: el código se invalida por uso, por rechazo, por pedir otro desde el mismo companion o
por agotar `MAX_CLAIMS` reclamos.
"""

import hmac

from coalsense_common import new_id

from .codes import hash_code, lookup, new_pairing_code, normalize_pairing_code
from .errors import (
    claim_mismatch,
    code_gone,
    device_not_found,
    pairing_busy,
    pairing_not_claimed,
)
from .ports import AuthDeps, CodeRecord, Device

MAX_CLAIMS = 3  # [SUPUESTO] reclamos válidos por código antes de invalidarlo


class PairingService:
    def __init__(self, deps: AuthDeps) -> None:
        self.deps = deps

    def start(self, client_ref: str, device_label: str, ip: str) -> str:
        """Genera un código para el companion.

        Pedir otro desde el mismo `client_ref` invalida el anterior.
        """
        d = self.deps
        keys = (f"start:ip:{ip}",)
        with d.lock:
            d.guard("auth.pairing.started", *keys)
            d.limiter.fail(*keys)
            code = new_pairing_code()
            while d.repo.find_active_code("device", hash_code(d.key, "device", "", code)):
                code = new_pairing_code()  # choque con otro código activo: improbable
            d.repo.save_code(
                CodeRecord(
                    id=new_id(),
                    kind="device",
                    subject_lookup=lookup(d.key, "client", client_ref),
                    code_hash=hash_code(d.key, "device", "", code),
                    created_at=d.clock.now_iso(),
                    device_label=device_label,
                )
            )
            d.emit("auth.pairing.started", "ok")
            return code

    def claim(self, account_id: str, code: str, ip: str) -> None:
        """La cuenta con sesión reclama el código; el dispositivo aún no existe.

        Un intento fallido no se puede atribuir a un código concreto (se busca por hash): lo frena
        la espera creciente por cuenta y por IP. Cada código admite `MAX_CLAIMS` reclamos.
        """
        d = self.deps
        keys = (f"pair:acct:{account_id}", f"pair:ip:{ip}")
        with d.lock:
            d.guard("auth.pairing.claimed", *keys)
            record = d.repo.find_active_code(
                "device", hash_code(d.key, "device", "", normalize_pairing_code(code))
            )
            if record is None:
                d.limiter.fail(*keys)
                d.emit("auth.pairing.claimed", "failed", account_id)
                raise code_gone()
            record.claims += 1
            if record.claims > MAX_CLAIMS:
                record.invalidated_at = d.clock.now_iso()
                d.repo.update_code(record)
                d.emit("auth.pairing.claimed", "failed", account_id)
                raise code_gone()
            if record.account_id is not None:
                # El primer reclamo gana: sin límite de tiempo, nadie se cuela mientras la
                # persona decide en el companion. El intento cuesta espera y cupo del código.
                d.repo.update_code(record)
                d.limiter.fail(*keys)
                d.emit("auth.pairing.claimed", "failed", account_id)
                raise pairing_busy()
            record.account_id = account_id
            record.claim_id = new_id()
            d.repo.update_code(record)
            d.limiter.reset(keys[0])
            d.emit("auth.pairing.claimed", "ok", account_id)

    def status(self, client_ref: str, ip: str) -> tuple[str, str | None, str | None]:
        """Estado para el companion: (estado, pista de la cuenta, claim_id).

        Consultar un código ya terminado no cuenta como fallo: el companion puede seguir
        preguntando sin dar espera a otros equipos que comparten su IP.
        """
        d = self.deps
        with d.lock:
            record = self._companion_code("auth.pairing.status", client_ref, ip, count=False)
            if record.account_id is None:
                return "waiting", None, None
            account = d.repo.get_account(record.account_id)
            return "claimed", account.email_hint if account else "", record.claim_id

    def confirm(self, client_ref: str, claim_id: str, ip: str) -> Device:
        """El companion acepta vincularse a la cuenta del reclamo pendiente (`claim_id`)."""
        d = self.deps
        with d.lock:
            record = self._companion_code("auth.device.paired", client_ref, ip)
            self._check_claim(record, claim_id)
            assert record.account_id is not None
            now = d.clock.now_iso()
            device = Device(new_id(), record.account_id, record.device_label or "", now)
            d.repo.add_device(device)
            record.used_at = now
            d.repo.update_code(record)
            d.emit("auth.device.paired", "ok", record.account_id, device.id)
            return device

    def reject(self, client_ref: str, claim_id: str, ip: str) -> None:
        """La persona dice que no en el companion: el código se invalida y no hay dispositivo.

        Decisión: rechazar siempre invalida el código (no hay "probar con otra cuenta" sobre el
        mismo código). Para vincular con otra cuenta, el companion pide un código nuevo.
        """
        d = self.deps
        with d.lock:
            record = self._companion_code("auth.pairing.rejected", client_ref, ip)
            self._check_claim(record, claim_id)
            record.invalidated_at = d.clock.now_iso()
            d.repo.update_code(record)
            d.emit("auth.pairing.rejected", "ok", record.account_id)

    def revoke(self, account_id: str, device_id: str) -> None:
        d = self.deps
        with d.lock:
            device = d.repo.get_device(device_id)
            if device is None or device.account_id != account_id or device.revoked_at:
                d.emit("auth.device.revoked", "failed", account_id)
                raise device_not_found()  # igual para ajeno e inexistente
            device.revoked_at = d.clock.now_iso()
            d.repo.update_device(device)
            d.emit("auth.device.revoked", "ok", account_id, device_id)

    def _companion_code(
        self, event: str, client_ref: str, ip: str, *, count: bool = True
    ) -> CodeRecord:
        d = self.deps
        key = f"companion:ip:{ip}"
        d.guard(event, key)
        record = d.repo.active_code("device", lookup(d.key, "client", client_ref))
        if record is None:
            if count:
                d.limiter.fail(key)
            d.emit(event, "failed")
            raise code_gone()
        return record

    def _check_claim(self, record: CodeRecord, claim_id: str) -> None:
        if record.account_id is None or record.claim_id is None:
            raise pairing_not_claimed()
        if not hmac.compare_digest(record.claim_id, claim_id):
            raise claim_mismatch()  # reclamo viejo o ajeno: no se vincula nada
