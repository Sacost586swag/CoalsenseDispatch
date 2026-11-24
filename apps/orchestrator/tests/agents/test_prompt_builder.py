"""REQ-02-005/006: lista permitida, minimización y consentimiento sin caché."""

import asyncio
from dataclasses import FrozenInstanceError

import pytest
from coalsense_orchestrator.agents.prompt_builder import (
    MemoryPreferences,
    PromptError,
    PromptInput,
    TextSelection,
    build_prompt,
)
from coalsense_orchestrator.gateway.consent_client import (
    ConsentError,
    DenyConsentChecker,
    require_consent,
)
from hypothesis import given
from hypothesis import strategies as st


class ConsentFake:
    def __init__(self, allowed: bool = True) -> None:
        self.allowed = allowed
        self.calls: list[tuple[str, str, str]] = []

    async def check(self, person_id: str, category: str, provider: str) -> bool:
        self.calls.append((person_id, category, provider))
        return self.allowed and (person_id, category, provider) == (
            "person-a",
            "llm_content",
            "claude",
        )


def source() -> PromptInput:
    return PromptInput.from_payload(
        {
            "step_instruction": "Reescribe solo el párrafo elegido.",
            "task_text": "No enviar.\n\n  Texto 🦜 elegido.\r\n\nTampoco enviar.",
            "memory_preferences": {
                "tone": "professional",
                "language": "es-EC",
                "format": "paragraph",
            },
        }
    )


def selection(text: str = "  Texto 🦜 elegido.\r\n") -> TextSelection:
    start = source().task_text.index(text)
    return TextSelection(start, start + len(text))


def build(**kwargs: object) -> object:
    arguments: dict[str, object] = {
        "person_id": "person-a",
        "provider": "claude",
        "selection": selection(),
    }
    arguments.update(kwargs)
    return asyncio.run(build_prompt(source(), **arguments))  # type: ignore[arg-type]


def test_default_checker_denies_and_no_prompt_is_returned() -> None:
    with pytest.raises(ConsentError, match="^consent.denied$"):
        build()
    assert asyncio.run(DenyConsentChecker().check("person-a", "llm_content", "claude")) is False


def test_selected_text_and_requested_preferences_only_are_in_the_payload() -> None:
    checker = ConsentFake()
    prompt = asyncio.run(
        build_prompt(
            source(),
            person_id="person-a",
            provider="claude",
            selection=selection(),
            preference_names=("tone",),
            checker=checker,
        )
    )
    assert checker.calls == [("person-a", "llm_content", "claude")]
    assert prompt.to_payload() == {
        "step_instruction": "Reescribe solo el párrafo elegido.",
        "task_text": "  Texto 🦜 elegido.\r\n",
        "memory_preferences": {"tone": "professional"},
    }
    assert prompt.person_id == "person-a" and prompt.provider == "claude"
    assert "elegido" not in repr(prompt) + repr(source())
    with pytest.raises(FrozenInstanceError):
        prompt.task_text = "Cambio"  # type: ignore[misc]
    exported = prompt.to_payload()
    exported["task_text"] = "Cambio"
    assert prompt.to_payload()["task_text"] == "  Texto 🦜 elegido.\r\n"


def test_memory_is_not_sent_unless_explicitly_selected() -> None:
    prompt = asyncio.run(
        build_prompt(
            source(),
            person_id="person-a",
            provider="claude",
            selection=selection(),
            checker=ConsentFake(),
        )
    )
    assert "memory_preferences" not in prompt.to_payload()


@pytest.mark.parametrize(
    "field",
    [
        "capability_profile",
        "declared_condition",
        "crisis_events",
        "person_id",
        "provider",
        "access_token",
        "api_key",
        "history",
        "messages",
        "tools",
        "system",
        "consent",
    ],
)
def test_forbidden_or_undeclared_fields_are_rejected_not_silently_removed(field: str) -> None:
    payload = {"step_instruction": "Un paso", "task_text": "Una nota", field: "Contenido privado"}
    with pytest.raises(PromptError, match="^prompt.input.invalid$") as caught:
        PromptInput.from_payload(payload)
    assert "privado" not in str(caught.value)
    assert caught.value.__context__ is None


@given(
    st.text(min_size=1).filter(
        lambda key: key not in {"step_instruction", "task_text", "memory_preferences"}
    )
)
def test_every_unknown_top_level_field_is_rejected(field: str) -> None:
    with pytest.raises(PromptError):
        PromptInput.from_payload({"step_instruction": "Un paso", "task_text": "Nota", field: True})


@pytest.mark.parametrize(
    "bad",
    [
        {"capability_profile": "Datos"},
        {"condition": "Datos"},
        {"tone": {"private": "Datos"}},
        {"language": "Datos privados"},
        {"tone": "Datos privados"},
        {"format": "Datos privados"},
        ["Datos privados"],
        None,
    ],
)
def test_memory_preferences_are_a_closed_vocabulary_not_an_arbitrary_context(bad: object) -> None:
    with pytest.raises(PromptError):
        PromptInput.from_payload(
            {
                "step_instruction": "Un paso",
                "task_text": "Nota",
                "memory_preferences": bad,
            }
        )


@pytest.mark.parametrize("field", ["step_instruction", "task_text"])
@pytest.mark.parametrize("bad", [None, 1, True, {}, [], "", " \r\n"])
def test_required_text_is_strict_and_nonempty(field: str, bad: object) -> None:
    payload: dict[str, object] = {"step_instruction": "Un paso", "task_text": "Nota"}
    payload[field] = bad
    with pytest.raises(PromptError):
        PromptInput.from_payload(payload)


def test_source_is_immutable_and_copied_from_the_callers_objects() -> None:
    memory = {"tone": "professional"}
    data = {"step_instruction": "Un paso", "task_text": "Nota", "memory_preferences": memory}
    parsed = PromptInput.from_payload(data)
    memory["tone"] = "warm"
    assert parsed.memory_preferences == MemoryPreferences(tone="professional")


@pytest.mark.parametrize(("start", "end"), [(True, 2), (-1, 2), (1, 1), (2, 1), (0, 10000)])
def test_invalid_or_out_of_range_selection_is_denied_before_consent(start: int, end: int) -> None:
    checker = ConsentFake()
    with pytest.raises(PromptError, match="^prompt.selection.invalid$"):
        build(selection=TextSelection(start, end), checker=checker)
    assert not checker.calls


def test_whitespace_only_selection_is_not_a_model_request() -> None:
    text = source().task_text
    start = text.index("\n\n")
    checker = ConsentFake()
    with pytest.raises(PromptError):
        build(selection=TextSelection(start, start + 2), checker=checker)
    assert not checker.calls


def test_unknown_or_duplicate_preference_requests_are_denied_before_consent() -> None:
    for names in [("capability_profile",), ("tone", "tone")]:
        checker = ConsentFake()
        with pytest.raises(PromptError):
            build(preference_names=names, checker=checker)
        assert not checker.calls


def test_check_is_bound_to_the_person_and_provider_not_a_boolean_from_payload() -> None:
    for person, provider in [("person-b", "claude"), ("person-a", "openrouter")]:
        checker = ConsentFake()
        with pytest.raises(ConsentError, match="^consent.denied$"):
            build(person_id=person, provider=provider, checker=checker)
        assert checker.calls == [(person, "llm_content", provider)]


def test_revocation_is_seen_on_every_build_without_a_cached_permission() -> None:
    checker = ConsentFake()
    assert build(checker=checker) is not None
    checker.allowed = False
    with pytest.raises(ConsentError, match="^consent.denied$"):
        build(checker=checker)
    assert len(checker.calls) == 2


@pytest.mark.parametrize("decision", [None, 1, "true", {"allowed": True}])
def test_truthy_non_boolean_consent_is_not_accepted(decision: object) -> None:
    class MalformedChecker:
        async def check(self, person_id: str, category: str, provider: str) -> bool:
            return decision  # type: ignore[return-value]

    with pytest.raises(ConsentError, match="^consent.unavailable$"):
        build(checker=MalformedChecker())


def test_checker_exception_does_not_leak_content_or_exception_context() -> None:
    class BrokenChecker:
        async def check(self, person_id: str, category: str, provider: str) -> bool:
            raise RuntimeError("Contenido privado")

    with pytest.raises(ConsentError, match="^consent.unavailable$") as caught:
        build(checker=BrokenChecker())
    assert caught.value.__context__ is None


def test_cancellation_is_not_converted_into_permission_or_an_automatic_retry() -> None:
    class CancelledChecker:
        async def check(self, person_id: str, category: str, provider: str) -> bool:
            raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        build(checker=CancelledChecker())


def test_gateway_must_check_again_after_preparation() -> None:
    checker = ConsentFake()
    assert build(checker=checker) is not None
    checker.allowed = False
    with pytest.raises(ConsentError):
        asyncio.run(require_consent(checker, "person-a", "llm_content", "claude"))
