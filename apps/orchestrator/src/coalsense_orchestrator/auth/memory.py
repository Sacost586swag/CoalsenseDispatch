"""Implementaciones en memoria para pruebas y desarrollo. La BD real llega en H2."""

from .ports import Account, AuthEvent, CodeRecord, Device, Kind, Session


class InMemoryAuditSink:
    def __init__(self) -> None:
        self.events: list[AuthEvent] = []

    def emit(self, event: AuthEvent) -> None:
        self.events.append(event)


class InMemoryAuthRepository:
    def __init__(self) -> None:
        self.accounts: dict[str, Account] = {}
        self.devices: dict[str, Device] = {}
        self.sessions: dict[str, Session] = {}
        self.codes: list[CodeRecord] = []

    def get_account_by_lookup(self, lookup: str) -> Account | None:
        return next((a for a in self.accounts.values() if a.email_lookup == lookup), None)

    def get_account(self, account_id: str) -> Account | None:
        return self.accounts.get(account_id)

    def add_account(self, account: Account) -> None:
        self.accounts[account.id] = account

    def add_device(self, device: Device) -> None:
        self.devices[device.id] = device

    def get_device(self, device_id: str) -> Device | None:
        return self.devices.get(device_id)

    def update_device(self, device: Device) -> None:
        self.devices[device.id] = device

    def add_session(self, session: Session) -> None:
        self.sessions[session.id] = session

    def get_session(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    def find_session(self, credential_hash: str) -> Session | None:
        return next(
            (
                s
                for s in self.sessions.values()
                if credential_hash in (s.credential_hash, s.previous_hash)
            ),
            None,
        )

    def session_of_device(self, device_id: str) -> Session | None:
        return next((s for s in self.sessions.values() if s.device_id == device_id), None)

    def update_session(self, session: Session) -> None:
        self.sessions[session.id] = session

    def save_code(self, record: CodeRecord) -> None:
        for old in self.codes:
            if _active(old) and _subject(old) == _subject(record):
                old.invalidated_at = record.created_at
        self.codes.append(record)

    def active_code(self, kind: Kind, subject_lookup: str) -> CodeRecord | None:
        subject = (kind, subject_lookup)
        return next((c for c in self.codes if _active(c) and _subject(c) == subject), None)

    def find_active_code(self, kind: Kind, code_hash: str) -> CodeRecord | None:
        return next(
            (c for c in self.codes if _active(c) and c.kind == kind and c.code_hash == code_hash),
            None,
        )

    def update_code(self, record: CodeRecord) -> None:
        pass  # los registros se modifican en su lugar


def _subject(code: CodeRecord) -> tuple[str, str]:
    return code.kind, code.subject_lookup


def _active(code: CodeRecord) -> bool:
    return code.used_at is None and code.invalidated_at is None
