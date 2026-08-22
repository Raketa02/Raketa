"""Nothing is edited and nothing is deleted — asserted structurally.

ADR-0055 makes append-only the whole reason this context exists: *"a wrong
movement is corrected by a second one"*, and *"this is the one place in Raketa
where the record is the answer to a dispute."* ``Ledger`` is a mutable
dataclass holding a plain ``list``, so the rule is one line away from being
broken by an edit that reads like an optimisation.

**The behavioural tests do not cover this, and that was measured rather than
assumed.** ``test_a_ledger_has_no_way_to_remove_or_amend_a_movement`` pins the
*names* on the public surface, so a new ``forget()`` is caught — but a write
inside a method that already exists is not, and neither is a private helper.
Dropping the oldest movements once a ledger holds more than five

    def _prune(self) -> None:
        while len(self._recorded) > 5:
            del self._recorded[0]

passes the entire unit suite: no seeded ledger and no fixture reaches six
movements, so nothing observes the loss. On a real account it is every fold
silently wrong — the balance, ``held``, the float — with the evidence deleted by
the same edit. That is the shape this walk exists to catch, and it is why the
guarantee needs a structural assertion rather than another example.

**One sanctioned write, named here and nowhere else.** ``_apply`` appends what a
stored event rebuilds into, which is what makes the list a projection of the
stream rather than a second copy of the truth. Every other mutation of
``_recorded`` — anywhere in the class, public or private — fails this file.

Carries its own negative control, on the tree's rule that a guard nobody has
seen fire is one nobody should watch.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
AGGREGATE = ROOT / "app" / "modules" / "money" / "domain" / "ledger.py"

#: The attribute the whole rule is about.
RECORDED = "_recorded"

#: The one method allowed to write to it, and the one call it may make. ``_apply``
#: is reached from replay and from ``_record_that``, which records an event in the
#: same breath — so an appended movement always has a stored event behind it.
SANCTIONED = ("_apply", "append")

#: ``list`` methods that change what the list holds. ``append`` is here too: it is
#: legal only inside ``_apply``, which the walk checks separately.
MUTATORS = frozenset(
    {
        "append",
        "extend",
        "insert",
        "remove",
        "pop",
        "clear",
        "sort",
        "reverse",
        "__setitem__",
        "__delitem__",
    }
)


def _is_recorded(node: ast.expr) -> bool:
    """Whether this expression is ``self._recorded`` or a subscript of it."""

    if isinstance(node, ast.Subscript):
        return _is_recorded(node.value)
    return (
        isinstance(node, ast.Attribute)
        and node.attr == RECORDED
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    )


def writes_to_recorded(source: str) -> set[tuple[str, str]]:
    """``(method, how)`` for every write to ``self._recorded`` in the class.

    Three shapes, because the rule has to hold against all of them and a walk
    that only knew about ``.append`` would wave ``del`` straight through:
    a mutating method call, a rebinding assignment, and a ``del``.
    """

    tree = ast.parse(source)
    ledger = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "Ledger"
    )

    found: set[tuple[str, str]] = set()
    for method in ast.walk(ledger):
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(method):
            # self._recorded.append(...) and friends
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in MUTATORS
                and _is_recorded(node.func.value)
            ):
                found.add((method.name, node.func.attr))
            # self._recorded = ... / self._recorded[0] = ...
            elif isinstance(node, (ast.Assign, ast.AugAssign)):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                for target in targets:
                    if _is_recorded(target):
                        found.add((method.name, "assign"))
            # del self._recorded[0]
            elif isinstance(node, ast.Delete):
                for target in node.targets:
                    if _is_recorded(target):
                        found.add((method.name, "del"))
    return found


def test_the_only_write_to_the_movement_list_is_the_append_that_replays_an_event():
    """The rule, over the real aggregate.

    Equality rather than a subset: a write disappearing matters too. If
    ``_apply`` stops appending, the list is no longer a projection of the stream
    and every fold reads empty on a replayed ledger — which is the same defect
    seen from the other side.
    """

    assert writes_to_recorded(AGGREGATE.read_text(encoding="utf-8")) == {SANCTIONED}


@pytest.mark.parametrize(
    "mutation",
    [
        pytest.param(
            "        while len(self._recorded) > 5:\n"
            "            del self._recorded[0]\n",
            id="prune-by-del",
        ),
        pytest.param("        self._recorded.pop()\n", id="pop"),
        pytest.param("        self._recorded.remove(self._recorded[0])\n", id="remove"),
        pytest.param("        self._recorded.clear()\n", id="clear"),
        pytest.param("        self._recorded = []\n", id="rebind"),
        pytest.param(
            "        self._recorded.sort(key=lambda m: m.amount)\n", id="sort"
        ),
        pytest.param(
            "        self._recorded.append(movement)\n", id="append-elsewhere"
        ),
    ],
)
def test_the_walk_fires_on_a_write_it_does_not_sanction(mutation):
    """The negative control, one per shape the rule has to refuse.

    The mutation goes into ``compensate`` — a method that already exists and is
    already allowed to touch the ledger — because that is where a real one would
    land. ``append-elsewhere`` is the subtle row: the *call* is the sanctioned
    one, and it is still refused outside ``_apply``, because a movement appended
    without an event behind it is a ledger that disagrees with its own stream.
    """

    source = AGGREGATE.read_text(encoding="utf-8")
    marker = "        held = self.movement_under(original)\n"
    assert marker in source, "compensate no longer opens the way this control assumes"

    mutated = source.replace(marker, marker + mutation, 1)

    assert writes_to_recorded(mutated) != {SANCTIONED}


def test_the_walk_has_something_to_walk():
    """A parse that found no class, or a rename, would pass everything silently."""

    tree = ast.parse(AGGREGATE.read_text(encoding="utf-8"))
    classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "Ledger" in classes


def test_a_movement_cannot_be_amended_in_place():
    """The other half of *nothing is edited*, and the reason the walk is enough.

    ``Movement`` is frozen, so an in-place amendment is a runtime error rather
    than something the walk above has to recognise. Asserted here so that
    unfreezing it — which would make the walk's coverage a fiction — is red.
    """

    from dataclasses import FrozenInstanceError
    from datetime import datetime, timezone
    from uuid import uuid4

    from app.kernel import grosze, instant
    from app.modules.money.domain.causes import MovementCause
    from app.modules.money.domain.movement import Movement, SeatRef
    from app.modules.money.domain.parties import PlayerParty, RaketaParty
    from app.modules.money.domain.reference import Reference, ReferenceKind

    movement = Movement(
        id=uuid4(),
        payer=PlayerParty(uuid4()),
        payee=RaketaParty(),
        amount=grosze(3800),
        seat=SeatRef(match_id=uuid4(), index=1),
        reservation=None,
        reference=Reference(ReferenceKind.PAYMENT, "a1"),
        cause=MovementCause.SHARE_ONLINE,
        occurred_at=instant(datetime(2026, 8, 24, 18, 0, tzinfo=timezone.utc)),
    )
    with pytest.raises(FrozenInstanceError):
        movement.amount = 1  # type: ignore[misc]
