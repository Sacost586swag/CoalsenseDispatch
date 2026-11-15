"""Códigos de un solo uso: generación, hash y el servicio de ingreso por correo.

Ningún código vence por tiempo (REQ-00-021, P-00-3): solo se invalidan por uso, por generar
otro o por exceder `MAX_ATTEMPTS` intentos. Solo se guarda el HMAC-SHA256 del código.
"""

import hmac
import re
import secrets

from coalsense_common import new_id

from .errors import code_gone, code_invalid, request_invalid, send_failed
from .ports import Account, AuthDeps, CodeRecord, CodeSender, Device, EmailVault

MAX_ATTEMPTS = 5  # [SUPUESTO] por código
EMAIL_CODE_DIGITS = 6  # [SUPUESTO]
PAIRING_CODE_LENGTH = 6  # [SUPUESTO]
# Sin 0, O, 1 ni I: se dictan por voz sin ambigüedad.
PAIRING_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def new_email_code() -> str:
    return f"{secrets.randbelow(10**EMAIL_CODE_DIGITS):0{EMAIL_CODE_DIGITS}d}"


def new_pairing_code() -> str:
    return "".join(secrets.choice(PAIRING_ALPHABET) for _ in range(PAIRING_CODE_LENGTH))


def normalize_email_code(raw: str) -> str:
    """Acepta "123 456" y "123-456" (dictado). Devuelve "" si no son 6 dígitos."""
    digits = re.sub(r"[\s.-]", "", raw)
    return digits if re.fullmatch(rf"\d{{{EMAIL_CODE_DIGITS}}}", digits) else ""


def normalize_pairing_code(raw: str) -> str:
    return re.sub(r"[\s-]", "", raw).upper()


def normalize_email(raw: str) -> str | None:
    email = raw.strip().lower()
    return email if len(email) <= 254 and _EMAIL.fullmatch(email) else None


def lookup(key: bytes, domain: str, value: str) -> str:
    """Identificador estable y no reversible (HMAC) para buscar sin guardar el valor."""
    return hmac.new(key, f"lookup|{domain}|{value}".encode(), "sha256").hexdigest()


def email_lookup(key: bytes, email: str) -> str:
    return lookup(key, "email", normalize_email(email) or email)


def hash_code(key: bytes, kind: str, subject: str, code: str) -> str:
    return hmac.new(key, f"code|{kind}|{subject}|{code}".encode(), "sha256").hexdigest()


class EmailCodeService:
    """Solicitar y verificar el código por correo (alta e ingreso, REQ-00-020)."""

    def __init__(self, deps: AuthDeps, sender: CodeSender, vault: EmailVault) -> None:
        self.deps = deps
        self.sender = sender
        self.vault = vault

    def request(self, email: str, ip: str) -> None:
        """Responde igual para correos nuevos y conocidos: no revela qué cuentas existen."""
        d = self.deps
        normalized = normalize_email(email)
        if normalized is None:
            raise request_invalid()
        subject = email_lookup(d.key, normalized)
        keys = (f"req:email:{subject}", f"req:ip:{ip}")
        with d.lock:
            d.guard("auth.code.requested", *keys)
            d.limiter.fail(*keys)  # cada pedido cuenta: evita saturar el correo de alguien
            code = new_email_code()
            d.repo.save_code(
                CodeRecord(
                    id=new_id(),
                    kind="email",
                    subject_lookup=subject,
                    code_hash=hash_code(d.key, "email", subject, code),
                    created_at=d.clock.now_iso(),
                )
            )
        try:
            self.sender.send_code(normalized, code)
        except Exception:
            d.emit("auth.code.requested", "error")
            raise send_failed() from None  # sin detalle: podría traer el correo o el código
        d.emit("auth.code.requested", "ok")

    def verify(
        self, email: str, code: str, device_label: str, ip: str
    ) -> tuple[Account, Device, bool]:
        d = self.deps
        normalized = normalize_email(email)
        if normalized is None:
            raise request_invalid()
        subject = email_lookup(d.key, normalized)
        keys = (f"ver:email:{subject}", f"ver:ip:{ip}")
        with d.lock:
            d.guard("auth.login", *keys)
            record = d.repo.active_code("email", subject)
            candidate = hash_code(d.key, "email", subject, normalize_email_code(code))
            if record is None or not hmac.compare_digest(record.code_hash, candidate):
                d.limiter.fail(*keys)
                d.emit("auth.login", "failed")
                if record is None:
                    raise code_gone()
                record.attempts += 1
                if record.attempts >= MAX_ATTEMPTS:
                    record.invalidated_at = d.clock.now_iso()  # el código, no la cuenta
                d.repo.update_code(record)
                raise code_gone() if record.invalidated_at else code_invalid()
            now = d.clock.now_iso()
            record.used_at = now
            d.limiter.reset(keys[0])  # la IP no se limpia: otra persona podría compartirla
            account = d.repo.get_account_by_lookup(subject)
            created = account is None
            if account is None:
                account = Account(
                    id=new_id(),
                    role="person",
                    email_ciphertext=self.vault.seal(normalized),
                    email_lookup=subject,
                    language="es",
                    created_at=now,
                )
                d.repo.add_account(account)
                d.emit("auth.account.created", "ok", account.id)
            record.account_id = account.id
            d.repo.update_code(record)
            device = Device(new_id(), account.id, device_label, now)
            d.repo.add_device(device)
            d.emit("auth.login", "ok", account.id, device.id)
            return account, device, created
