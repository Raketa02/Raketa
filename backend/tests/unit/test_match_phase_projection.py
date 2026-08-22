"""`MatchPhase` is a table off `Situation`, and a hole in it fails the import.

``docs/adr/0040-one-ladder-resolves-a-situation.md`` found four state
vocabularies over one match record, two of which already disagreed, and settled
it: one ladder, and **every other vocabulary is a total projection off it, owned
by the consumer that needs it and asserted exhaustive at module load**.

``MatchPhase`` is the first of them. It shipped as *borrowed vocabulary awaiting
an owner*, which is why the claim being tested here is not "the table is right"
— three words cannot be right or wrong about thirty-six — but the two structural
ones: that it is **total**, and that it is a **lookup rather than a second
ladder**. A projection that read the record would be the failure ADR-0040 makes
unreachable, arriving by the back door.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.engines.matchmaking import MATCH_PHASE_OF, MatchPhase, match_phase
from app.kernel import Situation

ROOT = Path(__file__).resolve().parents[2]
MATCHMAKING = ROOT / "app" / "engines" / "matchmaking.py"

#: The prototype's third state vocabulary: fifteen `be` values produced by every
#: context and read by nothing in 7 334 lines
#: (``docs/specs/now/research/state-table.md`` §6.5). ADR-0040 deleted it. It
#: never reached this tree, and these six names are the ones distinctive enough
#: that finding one would mean somebody had brought it back — `FORMING`,
#: `CONFIRMED` and `CANCELLED` are excluded because they are also ordinary words
#: in vocabularies that do ship.
DELETED_BE_VALUES = (
    "COURT_PROTECTED",
    "FULL_UNCOMMITTED",
    "PARTIALLY_PAID",
    "PUBLIC_SEATS_OPEN",
    "REPLACEMENT_PENDING",
    "RESCUE_ACTIVE",
)


@pytest.mark.parametrize("name", list(Situation), ids=lambda member: member.value)
def test_every_situation_has_a_phase(name: Situation) -> None:
    assert isinstance(match_phase(name), MatchPhase)


def test_the_table_is_exactly_the_enumeration() -> None:
    """No spare rows either: a key for a name the ladder cannot produce is a
    row nobody will notice has stopped meaning anything."""

    assert set(MATCH_PHASE_OF) == set(Situation)
    assert len(MATCH_PHASE_OF) == len(Situation)


def _the_shipped_exhaustiveness_condition() -> str:
    """The source text of the condition the module asserts at import.

    Read off the file rather than restated, so that what is exercised below is
    the check that actually runs and not a copy of it that could drift into
    being right about a check that had gone wrong.
    """

    tree = ast.parse(MATCHMAKING.read_text(encoding="utf-8"), filename=str(MATCHMAKING))
    conditions = [
        ast.unparse(node.value.args[0])
        for node in tree.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "invariant"
        and "MATCH_PHASE_OF" in ast.unparse(node.value)
    ]
    assert conditions, "the projection is not asserted exhaustive at module load"
    return conditions[0]


def test_the_exhaustiveness_check_runs_at_module_load() -> None:
    """It is a module-level `invariant`, not a docstring and not a branch.

    At module level it fails the *import* of every consumer, which is the whole
    point: a projection with a hole otherwise arrives as a `KeyError` on
    whichever screen happened to meet the new name first.
    """

    assert _the_shipped_exhaustiveness_condition()


def test_the_shipped_check_is_the_one_that_catches_a_hole() -> None:
    """Evaluate the module's own condition against a table missing a row.

    A length comparison passes for a table that swapped one key for another, and
    a truthiness check passes for anything at all. The condition has to be
    strict set equality, and the way to know is to run it.
    """

    holed = dict(MATCH_PHASE_OF)
    holed.pop(Situation.RESCUE)
    condition = _the_shipped_exhaustiveness_condition()

    assert eval(condition, {"MATCH_PHASE_OF": MATCH_PHASE_OF, "Situation": Situation})
    assert not eval(condition, {"MATCH_PHASE_OF": holed, "Situation": Situation})


def test_the_projection_reads_nothing_but_the_situation() -> None:
    """A lookup, never a second ladder.

    `match_phase` takes one argument and its whole body is a subscript. A
    projection that grew a `record` or a `now` parameter would be a second
    derivation of what a match is doing, which is the thing ADR-0040 exists to
    make unreachable — and it would not fail any other test in this suite.
    """

    tree = ast.parse(MATCHMAKING.read_text(encoding="utf-8"), filename=str(MATCHMAKING))
    (function,) = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "match_phase"
    ]
    arguments = function.args
    assert [argument.arg for argument in arguments.args] == ["of"]
    assert not arguments.kwonlyargs and arguments.vararg is None

    body = [node for node in function.body if not isinstance(node, ast.Expr)]
    (statement,) = body
    assert isinstance(statement, ast.Return)
    assert isinstance(statement.value, ast.Subscript)


def test_the_three_words_are_all_used() -> None:
    """A projection nothing maps onto is a member with no meaning left."""

    assert set(MATCH_PHASE_OF.values()) == set(MatchPhase)


def test_a_cancelled_match_is_cancelled_and_nothing_else_is() -> None:
    cancelled = {
        name for name, phase in MATCH_PHASE_OF.items() if phase is MatchPhase.CANCELLED
    }
    assert cancelled == {
        Situation.INVENTORY_LOST,
        Situation.CANCELLED_CLUB,
        Situation.CANCELLED_INCOMPLETE,
        Situation.CANCELLED_CHECKPOINT,
    }


def test_a_played_match_is_never_forming() -> None:
    """Matchmaking cannot join a match being played or one already played."""

    for name in (
        Situation.PLAYED_NO_SHOW,
        Situation.PLAYED_SHORT,
        Situation.COMPLETED,
        Situation.PLAYED_NO_SCORE,
        Situation.CONFIRM_RESULT,
        Situation.NEEDS_RESULT,
        Situation.READY,
    ):
        assert match_phase(name) is MatchPhase.LOCKED


def test_a_committed_match_still_looking_for_a_player_is_forming() -> None:
    """The row that makes the table a decision rather than a mapping.

    A committed match short a player has a seat genuinely for sale, and it is
    the one the cascade most wants ranked. Past the checkpoint it stops, because
    the checkpoint is the last moment the roster can change at all.
    """

    assert match_phase(Situation.REPLACEMENT) is MatchPhase.FORMING
    assert match_phase(Situation.RESCUE) is MatchPhase.FORMING
    assert match_phase(Situation.RESCUE_LATE) is MatchPhase.LOCKED
    assert match_phase(Situation.REPLACEMENT_TRANSFER) is MatchPhase.LOCKED


def test_the_prototypes_third_vocabulary_never_reached_this_tree() -> None:
    """`be` is deleted, and stays deleted.

    Fifteen values, produced by every context and read by nothing. It was never
    ported, so there was no code to remove — which is exactly the state a later
    session would undo by reintroducing it as *"the backend-facing vocabulary"*.
    A walk is what keeps a deletion deleted.
    """

    offenders = [
        f"{path.relative_to(ROOT)}: {value}"
        for path in sorted((ROOT / "app").rglob("*.py"))
        for value in DELETED_BE_VALUES
        if value in path.read_text(encoding="utf-8")
    ]
    assert not offenders, "the deleted `be` vocabulary is back:\n" + "\n".join(
        offenders
    )
    assert len(list((ROOT / "app").rglob("*.py"))) >= 100
