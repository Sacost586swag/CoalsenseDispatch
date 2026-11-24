"""Sello interno sin plazo humano, vinculado a identidad, política y contenido."""

import hashlib
import hmac
import json
from dataclasses import dataclass, field, replace
from uuid import UUID

from .rules import PolicyError


@dataclass(frozen=True)
class ApprovalGrant:
    pending_action_id: UUID
    person_id: UUID
    session_id: UUID
    content_digest: str = field(repr=False)
    policy_digest: str
    context_revision: int
    signature: str = field(default="", repr=False)

    def message(self) -> bytes:
        return json.dumps(
            [
                "coalsense.approval.v1",
                str(self.pending_action_id),
                str(self.person_id),
                str(self.session_id),
                "person",
                self.content_digest,
                self.policy_digest,
                self.context_revision,
            ],
            separators=(",", ":"),
        ).encode("ascii")


class GrantSigner:
    def __init__(self, key: bytes) -> None:
        if type(key) is not bytes or len(key) < 32:
            raise PolicyError("approval.key.invalid")
        self._key = key

    def sign(self, grant: ApprovalGrant) -> ApprovalGrant:
        signature = hmac.new(self._key, grant.message(), hashlib.sha256).hexdigest()
        return replace(grant, signature=signature)

    def verify(self, grant: ApprovalGrant) -> bool:
        if type(grant) is not ApprovalGrant or type(grant.signature) is not str:
            return False
        try:
            return hmac.compare_digest(self.sign(grant).signature, grant.signature)
        except (ValueError, TypeError, OverflowError):
            return False
