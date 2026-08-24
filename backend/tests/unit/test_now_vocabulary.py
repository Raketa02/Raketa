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

from app.kernel import CAUSE_COUNT, COVER_COUNT, Cause, Cover, HoldReason
from app.modules.now.domain import vocabulary
from app.modules.now.domain.vocabulary import (
    ACT_COUNT,
    CARD_HOLD_REASON_OF,
    DOOR_CODE_COUNT,
    ActCode,
    BlockType,
    CaptionCode,
    CardHoldReason,
    CardType,
    Currency,
    DoorCode,
    ShelfCode,
)

ROOT = Path(__file__).resolve().parents[2]
NOW = ROOT / "app" / "modules" / "now"

#: The one function in this package that may write a sentence, and the whole of
#: the exception. ADR-0075 states it **by class** — *copy the server composes is
#: copy the player reads outside the app* — and this is the class's only member:
#: the OS draws a push line on a locked phone, where no client of ours is
#: running to hold a copy table. ADR-0062 fixes the sentence itself.
#:
#: Keyed on the **function** and not on the module, exactly as the `logger`
#: exemption is keyed on the call: a sentence anywhere else in `push.py` — a
#: constant, a title, a second composer — is still a failure, and the control
#: below drives that both ways.
SERVER_COPY: tuple[Path, str] = (Path("domain") / "push.py", "push_body")


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
    assert {c.value for c in Currency} == {"PLN"}
    assert {c.value for c in CaptionCode} == {"undeclaredPreferences"}


def test_cover_is_the_kernel_s_and_this_module_does_not_redeclare_it() -> None:
    """ADR-0090 moved it: a club authors a roof and Now renders one.

    Asserted from here rather than only from the kernel's own suite, because the
    failure this guards is a *second* declaration — somebody adding two values
    back to this module so Now stops importing them. That reads as tidy and is
    the mapper-between-two-spellings the innermost ring exists to refuse, and no
    test in `tests/unit/test_kernel_*` can see it.
    """

    assert not hasattr(vocabulary, "Cover")
    assert {c.value for c in Cover} == {"indoor", "outdoor"}
    assert len(Cover) == COVER_COUNT


def _is_a_log_line(node: ast.Call) -> bool:
    """Whether this call is ``logger.<level>(...)`` and therefore an operator's.

    Keyed on the receiver being named ``logger`` rather than on the method name,
    because the level is what varies and the receiver is what makes it a log at
    all. A function called ``logger`` would satisfy it too and there is none;
    what this must not match is a *field* called ``note`` or ``line``, which is
    the shape the rule exists for.
    """

    return (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "logger"
    )


def _server_copy(tree: ast.AST, path: Path | None) -> set[int]:
    """The one function allowed to compose a sentence, by node identity.

    Empty for every file but the one `SERVER_COPY` names, and empty for that
    file's other functions. A push body is the only string in this package a
    player ever reads, and it is composed here because the operating system
    draws it where no client of ours is running (ADR-0075, ADR-0062).
    """

    if path is None or not str(path).endswith(str(SERVER_COPY[0])):
        return set()
    exempt: set[int] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == SERVER_COPY[1]
        ):
            for inner in ast.walk(node):
                if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                    exempt.add(id(inner))
    return exempt


def _exempt_strings(tree: ast.AST, path: Path | None = None) -> set[int]:
    """String constants that are not player copy, by node identity.

    Six kinds, and each is exempt for a stated reason rather than because it
    was in the way. A docstring is the module explaining itself. An
    ``invariant()`` message is addressed to whoever broke a precondition, and it
    lands in a stack trace and never in a payload. A ``summary=`` or
    ``description=`` keyword is API documentation for a client developer, which
    reaches the OpenAPI document and never a screen. And a ``logger`` call's
    argument is addressed to an **operator**: it goes to a log and cannot reach
    a response, which is the identical argument the ``invariant`` exemption
    makes — the invitation cascade is the first thing in this package with a
    degradation worth reporting (a club it cannot see, a rating stream that will
    not replay), and the alternative was writing those sentences in three words
    so a walk about player copy would let them through.

    The fifth is a `sa.text()` fragment — an index predicate is addressed to a
    **database**, reaches no response, and is the one place in this package
    where four English words are a `WHERE` clause. It is keyed on the call, so a
    sentence assigned beside one still fails.

    The sixth is the push body, which is the one sentence in this package a
    player genuinely reads — see `SERVER_COPY`, and note that it is keyed on the
    function for the same reason the others are keyed on the call.

    The exemption is on the **call**, not on the module: a sentence assigned to
    a constant in a file that also logs is still a failure, which the negative
    control below drives both ways.
    """

    exempt: set[int] = _server_copy(tree, path)
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
            if named in {"invariant", "text"} or _is_a_log_line(node):
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
        exempt = _exempt_strings(tree, path)
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
        'logger.warning("no court is held for this match yet")\n'
    )
    # The exemption is on the *call* and not on the file: a module that logs
    # does not thereby get to carry copy, which is the half a per-module
    # exemption would have lost.
    beside_a_log = ast.parse(
        'logger.warning("could not read a band")\n'
        'REASON = "no court is held for this match yet"\n'
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

    beside_a_predicate = ast.parse(
        'sa.text("dispatched_at IS NOT NULL")\n'
        'REASON = "no court is held for this match yet"\n'
    )

    assert offending(caught) == ["no court is held for this match yet"]
    assert offending(missed) == []
    assert offending(beside_a_log) == ["no court is held for this match yet"]
    assert offending(beside_a_predicate) == ["no court is held for this match yet"]


def test_the_server_copy_exemption_is_one_function_in_one_file() -> None:
    """The second negative control, driven both ways and on the real file.

    The exemption is worth exactly what proves it is narrow: a sentence outside
    `push_body` in the very module that composes one must still fail, or *this
    file writes copy* has quietly become the rule instead of *this function
    does*. The positive half asserts the function is really there — an exemption
    naming a function nobody wrote is decoration that would let the next
    sentence through in whatever file inherited the name.
    """

    path = NOW / SERVER_COPY[0]
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assert any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == SERVER_COPY[1]
        for node in ast.walk(tree)
    )
    assert _server_copy(tree, path), "the composer's own sentence is not exempt"

    beside_it = ast.parse(
        f"def {SERVER_COPY[1]}(): return 'a padel seat just opened'\n"
        "TITLE = 'a padel seat just opened'\n"
    )
    exempt = _exempt_strings(beside_it, path)
    assert [
        node.value
        for node in ast.walk(beside_it)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in exempt
    ] == ["a padel seat just opened"]

    # And the same function in any other file is not exempt at all.
    assert not _server_copy(beside_it, NOW / "domain" / "screen.py")


def test_the_walk_reaches_the_tree_it_is_claiming_about() -> None:
    # A glob matching nothing passes silently; the count is asserted rather than
    # trusted.
    assert len(list(NOW.rglob("*.py"))) >= 12
