"""Emparejamiento de un dispositivo con un código corto (REQ-00-021).

El companion pide un código y lo muestra; la persona o su cuidador/a lo dicta o lo escribe en
la web, ya con la cuenta abierta. Sin vencimiento por tiempo: se invalida por uso, por pedir
otro desde el mismo companion o por el límite de intentos de quien lo reclama.
"""

from coalsense_common import new_id

from .codes import hash_code, lookup, new_pairing_code, normalize_pairing_code
from .errors import code_gone, device_not_found
from .ports import AuthDeps, CodeRecord, Device


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

    def claim(self, account_id: str, code: str, ip: str) -> Device:
        """Une el companion con la cuenta que dicta el código (el código se busca por su hash).

        Un intento fallido no se puede atribuir a un código concreto: lo frena la espera creciente
        por cuenta y por IP (`attempts` de la fila solo cuenta en los códigos de correo).
        """
        d = self.deps
        keys = (f"pair:acct:{account_id}", f"pair:ip:{ip}")
        with d.lock:
            d.guard("auth.device.paired", *keys)
            record = d.repo.find_active_code(
                "device", hash_code(d.key, "device", "", normalize_pairing_code(code))
            )
            if record is None:
                d.limiter.fail(*keys)
                d.emit("auth.device.paired", "failed", account_id)
                raise code_gone()
            now = d.clock.now_iso()
            record.used_at = now
            record.account_id = account_id
            d.repo.update_code(record)
            d.limiter.reset(keys[0])
            device = Device(new_id(), account_id, record.device_label or "", now)
            d.repo.add_device(device)
            d.emit("auth.device.paired", "ok", account_id, device.id)
            return device

    def revoke(self, account_id: str, device_id: str) -> None:
        d = self.deps
        with d.lock:
            device = d.repo.get_device(device_id)
            if device is None or device.account_id != account_id or device.revoked_at:
                raise device_not_found()  # igual para ajeno e inexistente
            device.revoked_at = d.clock.now_iso()
            d.repo.update_device(device)
            d.emit("auth.device.revoked", "ok", account_id, device_id)
