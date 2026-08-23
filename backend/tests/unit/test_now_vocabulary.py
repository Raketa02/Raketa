"""The closed enumerations Now composes, and the one projection it makes.

Each of these is a set somebody decided, and the test for a decided set is that
it is *pinned* rather than counted: growing one has to be a diff on this file as
well as on the module, so a member arriving is something a reviewer sees.

The projection is the load-bearing one. ADR-0040's rule is that a consumer
needing a coarser vocabulary writes a **total table** off the kernel's, asserted
exhaustive at module load — never a second ladder. ``CARD_HOLD_REASON_OF`` is the
second such table in the tree after ``MATCH_PHASE_OF``, and the failure it exists
to prevent is a thirteenth kernel reason being silently absorbed into *no reason
at all*, which reads on a card as a court that is not held.
"""

import ast
from pathlib import Path

import pytest

from app.kernel import CAUSE_COUNT, Cause, HoldReason
from app.modules.now.domain.vocabulary import (
    ACT_COUNT,
    CARD_HOLD_REASON_OF,
    DOOR_CODE_COUNT,
    ActCode,
    BlockType,
    CaptionCode,
    CardHoldReason,
    CardType,
    Cover,
    Currency,
    DoorCode,
    ShelfCode,
)

ROOT = Path(__file__).resolve().parents[2]
NOW = ROOT / "app" / "modules" / "now"


def test_the_seven_acts_are_exactly_the_seven() -> None:
    # ADR-0083 opened the set at six; ADR-0087 added the seventh *with* the write
    # that receives it, which is the only way an eighth arrives.
    assert [act.value for act in ActCode] == [
        "takeSeat",
        "finishPaying",
        "enterResult",
        "answerResult",
        "seeAlternatives",
        "gettingIn",
        "leaveStandby",
    ]
    assert len(ActCode) == ACT_COUNT == 7


def test_the_shelf_codes_carry_both_titles_of_shelf_one_and_the_dark_shelf() -> None:
    codes = {code.value for code in ShelfCode}
    # Two codes for one shelf: nothing over the floor retitles it and drops the
    # floor, which is how shelf 1 never goes silent.
    assert {"bestFit", "sameLevel"} <= codes
    # Kept in the enum and never composed, so the shelf's return is a server
    # change rather than a client release (ADR-0085).
    assert "recentlyViewed" in codes
    assert codes == {
        "bestFit",
        "sameLevel",
        "fullWorthWaiting",
        "recentlyViewed",
        "newPlayers",
        "newClubs",
    }


def test_the_shelves_list_holds_two_kinds_of_block() -> None:
    # ADR-0084 puts the door *in* the list, so the list stops being homogeneous
    # and one field tells the two apart — on the same rule `card_type` follows.
    assert {block.value for block in BlockType} == {"shelf", "door"}


def test_the_door_shows_one_of_two_sentences() -> None:
    # Named for the fact rather than for the words: the copy is the client's and
    # changes without a backend release, where *has she started* is what the
    # server knows. A third is a copy decision somebody makes in a diff.
    assert [code.value for code in DoorCode] == ["noRunYet", "runParked"]
    assert len(DoorCode) == DOOR_CODE_COUNT == 2


def test_the_door_code_count_is_a_literal_and_not_its_own_length() -> None:
    """`DOOR_CODE_COUNT = len(DoorCode)` satisfies its own invariant for ever.

    The defect `OUTCOME_COUNT` and `MOVEMENT_CAUSE_COUNT` each shipped with, read
    the same way both times: from the source, because a pin that computes itself
    is green on the day somebody adds a member and green afterwards.
    """

    source = (NOW / "domain" / "vocabulary.py").read_text(encoding="utf-8")
    assert "DOOR_CODE_COUNT = 2" in source
    assert "DOOR_CODE_COUNT = len(" not in source


def test_the_five_causes_include_the_one_that_never_reaches_a_card() -> None:
    assert [cause.value for cause in Cause] == [
        "inventoryLost",
        "clubCancelled",
        "formCancelled",
        "checkpointCancelled",
        "settlementReopened",
    ]
    assert len(Cause) == CAUSE_COUNT == 5
    # In the enumeration rather than beside it: a cause the ledger may write and
    # the enumeration may not name is the same defect in the other direction.
    assert Cause.SETTLEMENT_REOPENED in set(Cause)


def test_a_card_names_five_hold_reasons_and_the_kernel_knows_thirteen() -> None:
    assert {reason.value for reason in CardHoldReason} == {
        "committed",
        "far",
        "near",
        "stale",
        "extended",
    }
    assert len(HoldReason) == 13


def test_the_hold_projection_is_total_over_the_kernel() -> None:
    # The assertion the module makes at import, restated where a reader looks for
    # it: every kernel reason has an answer, even if the answer is *no reason*.
    assert set(CARD_HOLD_REASON_OF) == set(HoldReason)


@pytest.mark.parametrize("reason", list(HoldReason))
def test_every_kernel_reason_has_an_answer(reason: HoldReason) -> None:
    assert reason in CARD_HOLD_REASON_OF


def test_no_card_hold_reason_is_unreachable() -> None:
    # A name nothing produces is a name somebody eventually builds against, and
    # no test can fail — the argument ADR-0072 used to refuse leaving
    # `privateFull` unreachable.
    assert {r for r in CARD_HOLD_REASON_OF.values() if r is not None} == set(
        CardHoldReason
    )


def test_the_diagnostic_reasons_reach_no_card() -> None:
    for reason in (
        HoldReason.PRIVATE,
        HoldReason.CLUB,
        HoldReason.FULL,
        HoldReason.NEAR_LAPSED,
        HoldReason.FAR_LAPSED,
        HoldReason.THIN,
        HoldReason.NO_SPECULATIVE_HOLD,
    ):
        assert CARD_HOLD_REASON_OF[reason] is None


def test_the_three_card_types_and_the_two_small_closed_sets() -> None:
    assert {t.value for t in CardType} == {"match", "person", "club"}
    assert {c.value for c in Cover} == {"indoor", "outdoor"}
    assert {c.value for c in Currency} == {"PLN"}
    assert {c.value for c in CaptionCode} == {"undeclaredPreferences"}


def _exempt_strings(tree: ast.AST) -> set[int]:
    """String constants that are not player copy, by node identity.

    Three kinds, and each is exempt for a stated reason rather than because it
    was in the way. A docstring is the module explaining itself. An
    ``invariant()`` message is addressed to whoever broke a precondition, and it
    lands in a stack trace and never in a payload. A ``summary=`` or
    ``description=`` keyword is API documentation for a client developer, which
    reaches the OpenAPI document and never a screen.
    """

    exempt: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            body = getattr(node, "body", [])
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                exempt.add(id(body[0].value))
        if isinstance(node, ast.Call):
            named = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if named == "invariant":
                for argument in ast.walk(node):
                    if isinstance(argument, ast.Constant):
                        exempt.add(id(argument))
            for keyword in node.keywords:
                if keyword.arg in {"summary", "description", "title"}:
                    for argument in ast.walk(keyword.value):
                        if isinstance(argument, ast.Constant):
                            exempt.add(id(argument))
    return exempt


def test_the_module_tree_holds_no_sentence() -> None:
    """No player-facing copy anywhere under `app/modules/now/`.

    ADR-0041 puts every sentence in the client's own table, and ``hold.note`` —
    a sentence the server wrote — was the one place in the whole specification set
    that broke the rule. This walk is what keeps it broken-and-fixed rather than
    fixed-until-somebody-adds-one: a string literal that could be a phrase a
    player reads is a failure, and the three kinds that provably cannot be are
    exempted by name above rather than by being short enough to slip through.
    """

    offenders: list[str] = []
    for path in sorted(NOW.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        exempt = _exempt_strings(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if id(node) in exempt:
                continue
            if len(node.value.split()) > 3:
                offenders.append(f"{path.relative_to(ROOT)}: {node.value[:70]!r}")

    assert offenders == [], offenders


def test_the_sentence_walk_can_tell_a_sentence_from_a_code() -> None:
    """The negative control: the walk's own detector, driven both ways.

    A guard that has never been seen to fire is one nobody should watch, and this
    one is cheap to drive: a module with a sentence in a place that is not
    exempt fails, and the same sentence inside an `invariant` does not.
    """

    caught = ast.parse(
        'REASON = "no court is held for this match yet"\n'
    )
    missed = ast.parse(
        'invariant(False, "no court is held for this match yet")\n'
    )

    def offending(tree: ast.AST) -> list[str]:
        exempt = _exempt_strings(tree)
        return [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in exempt
            and len(node.value.split()) > 3
        ]

    assert offending(caught) == ["no court is held for this match yet"]
    assert offending(missed) == []


def test_the_walk_reaches_the_tree_it_is_claiming_about() -> None:
    # A glob matching nothing passes silently; the count is asserted rather than
    # trusted.
    assert len(list(NOW.rglob("*.py"))) >= 12
