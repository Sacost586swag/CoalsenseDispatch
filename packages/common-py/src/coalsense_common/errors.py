"""Formato compartido para errores de APIs y pantallas."""

from dataclasses import dataclass


@dataclass(eq=False)
class AppError(Exception):
    code: str
    message_es: str
    recoverable: bool
    next_actions: list[str]

    def __post_init__(self) -> None:
        super().__init__(self.message_es)

    def to_dict(self) -> dict[str, str | bool | list[str]]:
        return {
            "code": self.code,
            "message_es": self.message_es,
            "recoverable": self.recoverable,
            "next_actions": list(self.next_actions),
        }
