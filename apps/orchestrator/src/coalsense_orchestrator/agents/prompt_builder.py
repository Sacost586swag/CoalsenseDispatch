"""Lista permitida y selección explícita; nunca recibe perfiles ni estado clínico.

Solo produce datos de solicitud. No llama modelos, decide herramientas, persiste
prompts ni convierte el contenido de la tarea en instrucciones del sistema.
"""

from dataclasses import dataclass, field
from typing import Literal, cast

from coalsense_orchestrator.gateway.consent_client import (
    ConsentChecker,
    DenyConsentChecker,
    require_consent,
)

PreferenceName = Literal["tone", "language", "format"]
Tone = Literal["professional", "neutral", "warm"]
Language = Literal["es-EC"]
TextFormat = Literal["paragraph", "bullets", "sections"]


class PromptError(ValueError):
    """Código estable; no incorpora campos, valores ni excepciones de entrada."""


@dataclass(frozen=True)
class MemoryPreferences:
    """[SUPUESTO] Vocabulario inicial cerrado para preferencias relevantes al texto.

    No admite resúmenes, estructuras arbitrarias ni campos del perfil. Ampliarlo
    requiere ampliar explícitamente el contrato y sus pruebas de minimización.
    """

    tone: Tone | None = None
    language: Language | None = None
    format: TextFormat | None = None

    def __post_init__(self) -> None:
        if any(
            value is not None and type(value) is not str
            for value in (self.tone, self.language, self.format)
        ):
            raise PromptError("prompt.input.invalid")
        if (
            self.tone not in (None, "professional", "neutral", "warm")
            or self.language not in (None, "es-EC")
            or self.format not in (None, "paragraph", "bullets", "sections")
        ):
            raise PromptError("prompt.input.invalid")

    @classmethod
    def from_payload(cls, value: object) -> "MemoryPreferences":
        if type(value) is not dict or set(value) - {"tone", "language", "format"}:
            raise PromptError("prompt.input.invalid")
        # Ausencia y null no son intercambiables en el contrato de entrada.
        if any(type(item) is not str for item in value.values()):
            raise PromptError("prompt.input.invalid")
        return cls(
            tone=cast(Tone | None, value.get("tone")),
            language=cast(Language | None, value.get("language")),
            format=cast(TextFormat | None, value.get("format")),
        )


@dataclass(frozen=True)
class PromptInput:
    step_instruction: str = field(repr=False)
    task_text: str = field(repr=False)
    memory_preferences: MemoryPreferences = field(default_factory=MemoryPreferences, repr=False)

    def __post_init__(self) -> None:
        if (
            type(self.step_instruction) is not str
            or not self.step_instruction.strip()
            or type(self.task_text) is not str
            or not self.task_text.strip()
            or type(self.memory_preferences) is not MemoryPreferences
        ):
            raise PromptError("prompt.input.invalid")

    @classmethod
    def from_payload(cls, value: object) -> "PromptInput":
        allowed = {"step_instruction", "task_text", "memory_preferences"}
        if (
            type(value) is not dict
            or set(value) - allowed
            or not {"step_instruction", "task_text"} <= set(value)
        ):
            raise PromptError("prompt.input.invalid")
        return cls(
            step_instruction=value["step_instruction"],
            task_text=value["task_text"],
            memory_preferences=MemoryPreferences.from_payload(value.get("memory_preferences", {})),
        )


@dataclass(frozen=True)
class TextSelection:
    """Rango semiabierto en puntos de código Python, no offsets UTF-16 del navegador."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if (
            type(self.start) is not int
            or type(self.end) is not int
            or self.start < 0
            or self.end <= self.start
        ):
            raise PromptError("prompt.selection.invalid")


@dataclass(frozen=True)
class PreparedPrompt:
    """Datos mínimos ligados al contexto; no acredita consentimiento futuro."""

    person_id: str
    provider: str
    step_instruction: str = field(repr=False)
    task_text: str = field(repr=False)
    preferences: tuple[tuple[PreferenceName, str], ...] = field(repr=False)

    def to_payload(self) -> dict[str, object]:
        result: dict[str, object] = {
            "step_instruction": self.step_instruction,
            "task_text": self.task_text,
        }
        if self.preferences:
            result["memory_preferences"] = dict(self.preferences)
        return result


async def build_prompt(
    source: PromptInput,
    *,
    person_id: str,
    provider: str,
    selection: TextSelection,
    preference_names: tuple[PreferenceName, ...] = (),
    checker: ConsentChecker | None = None,
) -> PreparedPrompt:
    if type(source) is not PromptInput:
        raise PromptError("prompt.input.invalid")
    if type(selection) is not TextSelection or selection.end > len(source.task_text):
        raise PromptError("prompt.selection.invalid")
    text = source.task_text[selection.start : selection.end]
    if not text.strip():
        raise PromptError("prompt.selection.invalid")
    if (
        type(preference_names) is not tuple
        or any(
            type(name) is not str or name not in ("tone", "language", "format")
            for name in preference_names
        )
        or len(set(preference_names)) != len(preference_names)
    ):
        raise PromptError("prompt.selection.invalid")
    chosen: list[tuple[PreferenceName, str]] = []
    for name in preference_names:
        value = getattr(source.memory_preferences, name)
        if value is not None:
            chosen.append((name, value))
    await require_consent(
        checker if checker is not None else DenyConsentChecker(),
        person_id,
        "llm_content",
        provider,
    )
    return PreparedPrompt(person_id, provider, source.step_instruction, text, tuple(chosen))
