"""There is no list of boundaries in the timekeeper, and no way to add one.

ADR-0076's second decision, and the one with nothing behind it but a walk:

> *"The timekeeper's input is the derivation kernel's `nextWakeAt(record, now)` —
> the same function that decides what the card says. A boundary therefore cannot
> exist in one and be missing from the other, which is the defect that produced
> the five omissions. […] Any future document that lists thresholds for the
> timekeeper is a second ladder and should be deleted rather than reconciled."*

**The failure this guards against has already happened once, at full size.** The
ticket that specified the timekeeper introduced its own boundary table as *"fully
enumerated — four tickets built it and nothing here needs discovering"*, and it
was short by five, including the two that **release a club's court**. Nobody was
careless: the candidate set is a *function of the record*, so a hand-maintained
table cannot track it. It is short again the moment a rung moves.

**And it is exactly the kind of edit that looks like an improvement.** *The wake
handler needs to know it is the twelve-hour one* is a plausible sentence, and the
code that follows it reads as clarification. The suite would stay green: the
duplicated threshold would agree with the kernel on the day it was written.

So this walks the timekeeper's own modules for the three shapes a second ladder
arrives in — a duration written down, arithmetic on an instant, and a reach for
one of the kernel functions that *produce* boundaries rather than the one that
chooses between them. Each has a negative control, because a guard nobody has
seen fire is one nobody should watch.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

#: Everything that reads or stores the schedule. Written out rather than globbed:
#: a glob that stops matching is reported green, and this is the file where that
#: would matter most.
TIMEKEEPER = (
    ROOT / "app/modules/matches/application/take_match_wake.py",
    ROOT / "app/modules/matches/infrastructure/sqlalchemy_match_schedule.py",
    ROOT / "app/modules/matches/domain/wake.py",
)

#: The kernel functions that **produce** a boundary. The timekeeper may call
#: `next_wake`, which chooses between them, and none of these — a call to one is
#: the timekeeper deciding a threshold for itself.
BOUNDARY_SOURCES = frozenset(
    {
        "deadlines",
        "door_code_at",
        "court_named_at",
        "match_end",
        "result_window",
        "vacancy_expires_at",
        "hold_boundaries",
        "shifted",
    }
)

#: Numbers that are not durations. `0` and `1` are counting; the batch size is a
#: ceiling on work per tick and names no moment. Anything else in these files is
#: a threshold until somebody argues otherwise here.
NOT_A_DURATION = frozenset({0, 1, 100})


def _sources() -> list[tuple[Path, ast.AST]]:
    return [(path, ast.parse(path.read_text())) for path in TIMEKEEPER]


def _durations(tree: ast.AST) -> list[int]:
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
        and node.value not in NOT_A_DURATION
    ]


def _boundary_calls(tree: ast.AST) -> list[str]:
    return [
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in BOUNDARY_SOURCES
    ]


def _imported(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names |= {alias.asname or alias.name for alias in node.names}
        elif isinstance(node, ast.Import):
            names |= {alias.asname or alias.name for alias in node.names}
    return names


@pytest.mark.parametrize("path", TIMEKEEPER, ids=lambda p: p.name)
def test_the_timekeeper_writes_down_no_duration(path: Path) -> None:
    """Twelve hours, four hours, twenty-four hours, thirty minutes, fifteen
    minutes — every one of them belongs to a rung and to nothing here."""

    found = _durations(ast.parse(path.read_text()))

    assert not found, f"{path.name} writes down a duration: {found}"


@pytest.mark.parametrize("path", TIMEKEEPER, ids=lambda p: p.name)
def test_the_timekeeper_does_no_arithmetic_on_an_instant(path: Path) -> None:
    """`shifted` is how a boundary is built. A timekeeper that builds one has
    stopped asking and started deciding."""

    found = _boundary_calls(ast.parse(path.read_text()))

    assert not found, f"{path.name} builds a boundary itself: {found}"


@pytest.mark.parametrize("path", TIMEKEEPER, ids=lambda p: p.name)
def test_the_timekeeper_imports_no_boundary_source(path: Path) -> None:
    """The import is caught as well as the call, because a name imported and not
    yet used is the first half of the edit and the cheapest place to stop it."""

    reached = _imported(ast.parse(path.read_text())) & BOUNDARY_SOURCES

    assert not reached, f"{path.name} reaches for a boundary source: {reached}"


def test_the_input_is_the_kernel_and_it_is_actually_called() -> None:
    """The positive half. Every assertion above is an absence, and absences are
    all satisfied by a timekeeper that computes nothing at all — including one
    that has stopped arming the schedule."""

    look = ROOT / "app/modules/matches/application/take_match_wake.py"
    tree = ast.parse(look.read_text())

    assert "next_wake" in _imported(tree)
    assert [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "next_wake"
    ]


def test_the_walks_can_tell_the_difference() -> None:
    """The negative control, one probe per walk."""

    a_second_ladder = ast.parse(
        "from app.kernel import shifted, deadlines, hours\n"
        "\n"
        "def re_arm(record, now):\n"
        "    if record.policy.window > 12:\n"
        "        return shifted(record.start, hours(-12))\n"
        "    return deadlines(record).commit\n"
    )

    assert _durations(a_second_ladder) == [12, 12]
    assert sorted(set(_boundary_calls(a_second_ladder))) == ["deadlines", "shifted"]
    assert _imported(a_second_ladder) & BOUNDARY_SOURCES == {"shifted", "deadlines"}
