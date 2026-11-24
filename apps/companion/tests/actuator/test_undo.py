import threading

import pytest
from coalsense_companion.actuator.action_classes import ACTION_POLICIES, ActionKind, Reversibility
from coalsense_companion.actuator.undo_stack import UndoBusy, UndoEntry, UndoNotApplied, UndoStack


def test_every_local_action_has_an_explicit_reversibility_policy() -> None:
    assert set(ACTION_POLICIES) == set(ActionKind)
    assert ACTION_POLICIES[ActionKind.KEY_PRESS] == Reversibility.NEVER
    assert ACTION_POLICIES[ActionKind.POINTER_CLICK] == Reversibility.NEVER
    assert ACTION_POLICIES[ActionKind.TEXT_DICTATION] == Reversibility.VERIFIED


def test_empty_and_irreversible_top_never_revert_an_older_action() -> None:
    stack = UndoStack()
    assert stack.undo().code == "input.undo.empty"
    changes: list[str] = []
    stack.push(UndoEntry(ActionKind.MODE_SET, revert=lambda: changes.append("mode")))
    stack.push(UndoEntry(ActionKind.KEY_PRESS))
    assert stack.undo().code == "input.undo.irreversible"
    assert stack.undo().code == "input.undo.irreversible"
    assert changes == []


def test_text_requires_verified_context_and_an_unsafe_target_blocks_reversal() -> None:
    with pytest.raises(ValueError):
        UndoEntry(ActionKind.TEXT_DICTATION, revert=lambda: None)
    changes: list[str] = []
    safe = False
    stack = UndoStack()
    stack.push(
        UndoEntry(
            ActionKind.TEXT_DICTATION,
            revert=lambda: changes.append("removed"),
            can_revert=lambda: safe,
        )
    )
    assert stack.undo().code == "input.undo.unverified" and changes == []
    safe = True
    result = stack.undo()
    assert result.changed and result.kind == ActionKind.TEXT_DICTATION
    assert changes == ["removed"] and stack.undo().code == "input.undo.empty"
    assert "dictado" in result.message_es


def test_unknown_partial_failure_is_a_barrier_and_cannot_be_retried_blindly() -> None:
    attempts: list[int] = []

    def failed() -> None:
        attempts.append(1)
        raise OSError("contenido privado")

    stack = UndoStack()
    stack.push(UndoEntry(ActionKind.MODE_SET, revert=failed))
    first = stack.undo()
    assert first.code == "input.undo.uncertain" and not first.changed
    assert stack.undo().code == "input.undo.uncertain" and attempts == [1]
    assert "contenido privado" not in repr(first)


def test_pre_effect_cancellation_and_bounded_history_keep_correct_order() -> None:
    changes: list[str] = []
    stack = UndoStack(capacity=2)
    for value in ["first", "second", "third"]:
        stack.push(UndoEntry(ActionKind.MODE_SET, revert=lambda value=value: changes.append(value)))
    assert stack.evictions == 1
    assert stack.undo().changed and stack.undo().changed
    assert changes == ["third", "second"]

    def not_applied() -> None:
        raise UndoNotApplied()

    stack.push(UndoEntry(ActionKind.PROFILE_SWITCH, revert=not_applied))
    assert stack.undo().code == "input.undo.blocked"
    assert stack.undo().code == "input.undo.blocked"


def test_concurrent_undo_and_history_changes_cannot_duplicate_a_reversal() -> None:
    stack = UndoStack()
    entered, release = threading.Event(), threading.Event()
    results = []

    def reverse() -> None:
        entered.set()
        assert release.wait(3)

    stack.push(UndoEntry(ActionKind.MODE_SET, revert=reverse))
    worker = threading.Thread(target=lambda: results.append(stack.undo()))
    worker.start()
    try:
        assert entered.wait(3)
        assert stack.undo().code == "input.undo.busy"
        with pytest.raises(UndoBusy):
            stack.push(UndoEntry(ActionKind.KEY_PRESS))
        with pytest.raises(UndoBusy):
            stack.clear()
    finally:
        release.set()
        worker.join(3)
    assert len(results) == 1 and results[0].changed
    assert stack.undo().code == "input.undo.empty"


@pytest.mark.parametrize(
    "kind", [kind for kind, policy in ACTION_POLICIES.items() if policy != Reversibility.NEVER]
)
def test_every_reversible_class_reports_what_was_undone(kind: ActionKind) -> None:
    changes = []
    stack = UndoStack()
    stack.push(UndoEntry(kind, revert=lambda: changes.append(1), can_revert=lambda: True))
    result = stack.undo()
    assert result.changed and result.kind == kind and result.message_es
    assert changes == [1]


def test_reversible_class_can_record_an_irreversible_occurrence() -> None:
    stack = UndoStack()
    stack.push(UndoEntry(ActionKind.POINTER_DRAG_TOGGLE, reversible=False))
    assert stack.undo().code == "input.undo.irreversible"
    with pytest.raises(ValueError):
        UndoEntry(ActionKind.KEY_PRESS, reversible=True, revert=lambda: None)
