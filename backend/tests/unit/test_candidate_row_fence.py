"""The three claims an index row makes, walked rather than reviewed.

``the-candidate-index.md`` §3 makes three assertions about a ``CandidateRow`` and
calls all three build-failing. They guard rules nobody will notice breaking, so
each is driven against a deliberately broken source as well as against the real
one — a gate that has never been observed to fail is indistinguishable from one
that does not work.

1. **No shard-key field** (``docs/adr/0101``). The partition is derived, so there
   is no field for a future matching conjunct to attach to.
2. **No name, photo, email, date of birth, nationality or precise location.**
   Gender is present and fenced one layer out (``docs/adr/0096``); the coarse
   area is present because it is the only spatial truth the index has, and it is
   coarse **by construction** rather than by a word nobody may spell.
3. **No reference cycles**, which is what makes ``gc.freeze()`` safe
   (``docs/adr/0112``). One automatic gen-2 collection over a live index cost
   57.9 ms stop-the-world; freezing is only safe if the frozen objects cannot
   become unreachable garbage, and refcounting frees an outgoing row the moment
   the last container drops it — precisely because there is no cycle holding it.

The walk is shared with ``tests/unit/test_scorable_candidate_fence.py`` rather
than copied. The two fences guard different lists over different types, and one
walk with two word lists is what keeps them from drifting into two walks that
disagree about what *transitive* means.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.kernel import InvariantViolated
from app.modules.matchmaking.domain import candidate_index
from app.modules.matchmaking.domain.candidate_index import (
    CandidateRow,
    IndexedArea,
    Partition,
    partition_of,
)
from tests.unit.test_scorable_candidate_fence import reachable_fields, _words

#: Located through the module rather than by this file's own depth. A path
#: counted in ``..``s goes silently wrong the day the tests move, and a walk
#: pointed at nothing reports no breach on any tree at all.
FENCED = Path(candidate_index.__file__)

FENCED_TYPES = ("CandidateRow",)

#: What may never be reachable from an index row, as whole words.
#:
#: **``gender`` is deliberately not here**, and that absence is the difference
#: between this fence and the scorer's. Gender reaches candidate generation and
#: the mutual gate and stops at the engine's package boundary
#: (``docs/adr/0096``), so a list that forbade it here would forbid the gate its
#: own input.
#:
#: **``latitude`` and ``longitude`` are not here either**, for a reason with an
#: assertion behind it rather than a preference: the row's only spatial fact *is*
#: a pair of degrees, and what makes it safe is that ``IndexedArea`` refuses one
#: finer than the platform keeps. A word list cannot tell a coarse degree from a
#: precise one; a constructor can, and does — see the test below.
FORBIDDEN_WORDS = frozenset(
    {
        "name",
        "nickname",
        "photo",
        "photos",
        "avatar",
        "image",
        "email",
        "phone",
        "birthdate",
        "birthday",
        "birth",
        "dob",
        "nationality",
        "shard",
        # The live-truth facts `docs/adr/0111` forbids the index outright. A
        # column for one of these is the change that would make staleness cost
        # safety, and it is the change somebody will one day have a good
        # performance reason for.
        "block",
        "blocked",
        "held",
        "hold",
        "disabled",
        "suspended",
    }
)


def _breaches(source: str) -> list[str]:
    return [
        f"{owner}.{field}: {annotation} — names {sorted(offending)}"
        for owner, field, annotation in reachable_fields(source, FENCED_TYPES)
        if (offending := (_words(field) | _words(annotation)) & FORBIDDEN_WORDS)
    ]


# ---------------------------------------------------------------------------
# 2 — the forbidden facts
# ---------------------------------------------------------------------------


def test_an_index_row_carries_no_forbidden_fact() -> None:
    assert _breaches(FENCED.read_text(encoding="utf-8")) == []


def test_the_walk_reaches_the_fields_it_claims_to_guard() -> None:
    """The check that stops the one above passing for the wrong reason."""

    reached = {
        f"{owner}.{field}"
        for owner, field, _ in reachable_fields(
            FENCED.read_text(encoding="utf-8"), FENCED_TYPES
        )
    }
    assert {
        "CandidateRow.player_id",
        "CandidateRow.gender",
        "CandidateRow.areas",
        "CandidateRow.applied_through_sequence_no",
        # One hop in, through the area set.
        "IndexedArea.latitude",
    } <= reached


def test_the_walk_refuses_a_forbidden_fact_declared_directly() -> None:
    broken = """
from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateRow:
    player_id: str
    nickname: str
"""
    assert _breaches(broken) == ["CandidateRow.nickname: str — names ['nickname']"]


def test_the_walk_refuses_a_forbidden_fact_reached_through_another_type() -> None:
    """The break a review misses, and the reason the walk is transitive.

    A row holding a whole player profile behind one innocent field name satisfies
    every eyeball and none of the rule.
    """

    broken = """
from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    photo_id: str


@dataclass(frozen=True)
class CandidateRow:
    player_id: str
    card: Card
"""
    assert _breaches(broken) == ["Card.photo_id: str — names ['photo']"]


def test_the_walk_refuses_a_live_truth_fact_the_index_may_never_hold() -> None:
    """The change somebody will one day have a good performance reason for.

    An ``is_blocked`` column would make staleness cost **safety**, which is the
    one thing ``docs/adr/0111``'s invariant exists to prevent — and it is the
    change that makes §18's refusal a safety stop again after this build spent
    an ADR arguing it is not.
    """

    broken = """
from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateRow:
    player_id: str
    blocked_by: tuple[str, ...]
"""
    assert _breaches(broken) == [
        "CandidateRow.blocked_by: tuple[str, ...] — names ['blocked']"
    ]


def test_the_walk_does_not_refuse_the_gender_the_mutual_gate_reads() -> None:
    """A guard that refused it would be a guard somebody deletes.

    ``docs/adr/0096`` puts gender in the index and out of the engine, and naming
    that here is what stops this list being read as *the scorer's list, again*.
    """

    broken = """
from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateRow:
    gender: str | None
    gender_preference: str
"""
    assert _breaches(broken) == []


# ---------------------------------------------------------------------------
# 1 — no shard key
# ---------------------------------------------------------------------------


def test_no_field_on_an_index_row_is_a_shard_key() -> None:
    """``docs/adr/0101``: the partition is derived, and has nothing to attach to."""

    assert not [
        f"{owner}.{field}"
        for owner, field, annotation in reachable_fields(
            FENCED.read_text(encoding="utf-8"), FENCED_TYPES
        )
        if "shard" in _words(field) or "partition" in _words(field)
    ]


def test_the_partition_is_computed_from_the_row_rather_than_read_off_it() -> None:
    assert partition_of(_row()) == Partition(sport="PADEL")


# ---------------------------------------------------------------------------
# 2b — the area is coarse by construction, not by a forbidden word
# ---------------------------------------------------------------------------


def test_an_area_refuses_a_fix_finer_than_the_platform_keeps() -> None:
    """A caller holding a device fix cannot put it here, whatever they call it.

    This is what a word list cannot do, and it is why ``latitude`` is absent from
    the forbidden list above rather than present with an exception beside it.
    """

    with pytest.raises(InvariantViolated):
        IndexedArea(latitude=52.229676, longitude=21.012229)


def test_an_area_accepts_the_coarse_pair_the_stream_actually_carries() -> None:
    assert IndexedArea(latitude=52.23, longitude=21.01).latitude == 52.23


# ---------------------------------------------------------------------------
# 3 — no reference cycles, which is what makes gc.freeze() safe
# ---------------------------------------------------------------------------


def test_an_index_row_is_frozen_and_slotted() -> None:
    """Both halves of the memory claim, and of the immutability one.

    ``__slots__`` is the 782-bytes-a-row figure; frozen is what lets a delta
    refresh share a row between two containers without either being able to
    change it under the other.
    """

    row = _row()
    assert is_dataclass(row) and hasattr(CandidateRow, "__slots__")
    assert "__dict__" not in dir(row)
    with pytest.raises(FrozenInstanceError):
        row.mu = 3.0  # type: ignore[misc]


def test_an_index_row_holds_no_reference_cycle() -> None:
    """Walked over a real row, following every field and every element.

    A cycle anywhere reachable from a row would mean refcounting could not free
    an outgoing row on its own — and a frozen generation that accumulates
    unreachable garbage is the failure ``gc.freeze()`` trades a 57.9 ms pause
    for.
    """

    assert _cycles_from(_row()) == []


def test_the_cycle_walk_finds_a_back_pointer_to_a_container() -> None:
    """The break this guards: a row that knows which snapshot holds it.

    It is the natural thing to reach for the first time a row needs to answer a
    question about its neighbours, and it is exactly the shape that makes the
    frozen generation grow.
    """

    class _Container:
        def __init__(self) -> None:
            self.rows: list[object] = []

    class _RowWithBackPointer:
        __slots__ = ("container",)

        def __init__(self, container: _Container) -> None:
            self.container = container

    container = _Container()
    row = _RowWithBackPointer(container)
    container.rows.append(row)

    assert _cycles_from(row) != []


def _cycles_from(root: object) -> list[str]:
    """Every path from ``root`` back to something already on it."""

    found: list[str] = []

    def walk(node: object, path: tuple[int, ...], names: tuple[str, ...]) -> None:
        if id(node) in path:
            found.append(" → ".join(names))
            return
        if isinstance(node, (str, bytes, int, float, bool, type(None), datetime)):
            return
        path = path + (id(node),)
        if isinstance(node, (tuple, list, set, frozenset)):
            for index, element in enumerate(node):
                walk(element, path, names + (f"[{index}]",))
            return
        if is_dataclass(node):
            for field in fields(node):
                walk(getattr(node, field.name), path, names + (field.name,))
            return
        for slot in getattr(type(node), "__slots__", ()):
            walk(getattr(node, slot), path, names + (slot,))
        for attribute, value in getattr(node, "__dict__", {}).items():
            walk(value, path, names + (attribute,))

    walk(root, (), ("<row>",))
    return found


def _row() -> CandidateRow:
    when = datetime(2026, 8, 27, 9, 0, tzinfo=timezone.utc)
    return CandidateRow(
        player_id="11111111-1111-1111-1111-111111111111",
        sport="PADEL",
        mu=2.71,
        sigma=0.34,
        confidence=62,
        band="Improver",
        band_lower=2.5,
        band_upper=3.0,
        rating_status="INITIAL_ESTIMATE",
        calibration_priority="STANDARD",
        declared_intent="COMPETITIVE",
        social_tags=("competitive_edge",),
        tags_updated_at=when,
        availability=("1:MORNING",),
        grid_updated_at=when,
        areas=(IndexedArea(latitude=52.23, longitude=21.01),),
        search_radius_km=12,
        proposals_opt_in=True,
        gender="FEMALE",
        gender_preference="ANY",
        profile_created_at=when,
        last_active_at=when,
        applied_through_sequence_no=41,
    )
