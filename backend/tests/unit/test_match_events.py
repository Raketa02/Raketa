"""Every change announces itself, specifically — and nothing here is a comment.

ADR-0034 buys the support timeline by paying for event types now, and it is
blunt about what nobody checks: *"nothing mechanical catches an event that is
published too coarsely."* This file is what mechanism there can be.

1. **A mutating method that announces nothing fails the build.** An AST walk
   over the aggregate, with the read-only members written out — so a write added
   tomorrow without a name is red on the day it is written, not on the day a
   support agent cannot explain it.
2. **No name is a generic verb.** *matchUpdated* is the one event ADR-0034
   forbids by name, and it has many spellings.
3. **The catalog and the module agree in both directions.** An event nothing
   registers is history filed under nothing; a registration for an event that no
   longer exists is a name that decodes into nothing.
4. **Every announcement survives the codec**, because the outbox is where they
   are read from and a durable contract that only encodes is not one.
"""

from __future__ import annotations

import ast
import inspect
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from app.application.events.catalog import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.kernel import (
    HoldPolicy,
    MatchKind,
    Outcome,
    SeatShare,
    Sport,
    grosze,
    hours,
    instant,
    minutes,
)
from app.modules.matches.application.event_subscriptions import (
    MATCH_EVENTS,
    register_match_events,
)
from app.modules.matches.domain import events as event_module
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.score import Score, SetScore

ROOT = Path(__file__).resolve().parents[2]
AGGREGATE = ROOT / "app" / "modules" / "matches" / "domain" / "match.py"

#: The public members of `Match` that read and never write. Written out rather
#: than detected, because *"this one does not need an event"* is exactly the
#: judgement this walk exists to stop somebody making silently.
READ_ONLY = frozenset(
    {"as_record", "open_vacancies", "is_settled", "seat_of", "seat_at",
     "departure_of", "pull_events", "unended_claims", "live_claim_of",
     "seats_under_claim", "side_of", "vacancy_left_by"}
)

#: Twenty-seven changes and twenty-seven names. Pinned, so that deleting an event
#: is as loud as adding an unnamed write — a count that only ever goes up
#: catches half of the rule.
EXPECTED_EVENTS = 27

#: The many spellings of the one event ADR-0034 forbids.
GENERIC = ("updated", "changed", "modified", "touched", "amended", "mutated")


def _aggregate_tree() -> ast.ClassDef:
    tree = ast.parse(AGGREGATE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Match":
            return node
    raise AssertionError("app/modules/matches/domain/match.py has no `Match`")


def _announces(node: ast.FunctionDef) -> bool:
    """Whether this method calls ``_record`` anywhere inside it.

    An attribute call rather than ``self._record`` specifically, because
    ``post`` is a classmethod and announces through the instance it built.

    ``commit_if_due``, ``resolve_departures_to`` and ``agree_result`` are the
    three public methods that announce **on behalf of a caller**: a payment that
    fills a match past its deadline commits it, a cancellation reopens every
    settlement it improves, and the timekeeper's silence settles a result the
    same way an opponent's tap does. Naming them here rather than inlining their
    ``_record`` calls is what keeps one change one announcement — and it is what
    makes *settled by silence* and *settled by agreement* one event with a flag
    on it, which is ADR-0048's own reading of them.
    """

    return any(
        isinstance(inner, ast.Call)
        and isinstance(inner.func, ast.Attribute)
        and inner.func.attr
        in {"_record", "commit_if_due", "resolve_departures_to", "agree_result"}
        for inner in ast.walk(node)
    )


def _public_methods() -> list[ast.FunctionDef]:
    return [
        node
        for node in _aggregate_tree().body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    ]


# --- 1 · a write with no name --------------------------------------------


def test_the_aggregate_has_public_methods_to_walk():
    """A walk over nothing passes silently and reads as a rule that held.

    The lesson `Raketa02/Raketa#93` paid for, applied to a class body rather
    than to a glob.
    """

    assert len(_public_methods()) >= 20


@pytest.mark.parametrize(
    "method", sorted(node.name for node in _public_methods())
)
def test_every_public_write_announces_itself(method):
    node = next(one for one in _public_methods() if one.name == method)
    if method in READ_ONLY:
        assert not _announces(node), f"{method} is listed read-only and writes"
        return
    assert _announces(node), (
        f"`Match.{method}` changes the record and announces nothing. "
        "ADR-0034: every change a support agent would need to explain is its "
        "own named event."
    )


def test_the_read_only_list_names_only_members_that_exist():
    """An allowlist that has drifted is an allowlist that exempts nothing."""

    public = {node.name for node in _public_methods()}
    public |= {
        node.target.id
        for node in _aggregate_tree().body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    public |= {"open_vacancies", "is_settled"}

    assert READ_ONLY <= public


# --- 2 · no generic name --------------------------------------------------


@pytest.mark.parametrize("event_cls, name", MATCH_EVENTS)
def test_no_event_is_a_generic_verb(event_cls, name):
    lowered = f"{event_cls.__name__} {name}".lower()
    for word in GENERIC:
        assert word not in lowered, (
            f"`{name}` reads as a generic change. ADR-0034 forbids "
            '"match updated" and every synonym of it.'
        )


def test_no_event_name_is_bare_match():
    names = {name for _, name in MATCH_EVENTS}

    assert "matches.match" not in names
    assert all(name.startswith("matches.") for name in names)


# --- 3 · the catalog and the module agree ---------------------------------


def _declared_events() -> set[type]:
    return {
        value
        for value in vars(event_module).values()
        if isinstance(value, type)
        and is_dataclass(value)
        and value.__module__ == event_module.__name__
    }


def test_every_declared_event_is_registered_and_nothing_else_is():
    """Equality, both directions. A subset either way is a silent hole."""

    assert {event_cls for event_cls, _ in MATCH_EVENTS} == _declared_events()


def test_the_event_count_is_pinned():
    assert len(MATCH_EVENTS) == EXPECTED_EVENTS
    assert len({name for _, name in MATCH_EVENTS}) == EXPECTED_EVENTS


def test_the_real_catalog_accepts_every_one_at_version_one():
    catalog = EventCatalog()
    register_match_events(catalog)

    for event_cls, name in MATCH_EVENTS:
        contract = catalog.contract_for(event_cls)
        assert (contract.name, contract.version) == (name, 1)


@pytest.mark.parametrize("event_cls, name", MATCH_EVENTS)
def test_every_event_names_its_match_and_when_it_happened(event_cls, name):
    carried = {field.name for field in fields(event_cls)}

    assert "match_id" in carried
    assert "occurred_at" in carried


def test_no_event_carries_the_whole_record():
    """An event holding a snapshot is a second copy of the row, ageing at once."""

    for event_cls, _ in MATCH_EVENTS:
        annotations = {
            field.name: str(field.type) for field in fields(event_cls)
        }
        assert not any(
            "Match" in hint and "match_id" != name
            for name, hint in annotations.items()
        )


# --- 4 · the announcements survive the outbox -----------------------------


def _codec() -> JsonEventCodec:
    catalog = EventCatalog()
    register_match_events(catalog)
    return JsonEventCodec(catalog)


def _drive_every_write() -> list:
    """One match through every announcement this context can make.

    A table of calls rather than one call per test, because what is asserted is
    that the *set* of names a full life produces is the set that is registered.
    """

    def at(day, hour=12, minute=0):
        return instant(datetime(2026, 9, day, hour, minute, tzinfo=timezone.utc))

    announced = []
    match = Match.post(
        match_id=uuid4(),
        club_id=uuid4(),
        category_id=uuid4(),
        sport=Sport.PADEL,
        start=at(8, 18),
        duration=hours(1),
        share=SeatShare(grosze(3800)),
        policy=HoldPolicy(window=hours(24), join_cut=minutes(30)),
        at=at(1),
    )
    players = [uuid4() for _ in range(4)]
    match.hold_court(at=at(1))
    match.release_court(at=at(1))
    match.hold_court(at=at(1))
    match.lock_court(at=at(1))
    match.extend_hold(at=at(1))
    match.move_start(at(8, 19), at=at(1))
    # Past `commit` (start - 24h = the 7th at 19:00), so the fourth payment
    # commits the match on the spot and `MatchCommitted` is produced.
    for player in players:
        match.take_seat(player, at=at(7, 20))
        match.pay_seat(player, at=at(7, 20))
    # Committed, so this leaver is owed something and her departure is born
    # **unsettled** — which is what makes the filler below produce
    # `DepartureSettled` rather than the departure itself.
    match.depart(players[0], quote=Outcome.REFUNDED_IN_FULL, at=at(7, 21))
    match.begin_transfer(1, at=at(7, 21))
    match.end_transfer(1, at=at(7, 21))
    match.take_seat(uuid4(), at=at(7, 22))
    match.record_no_show(at=at(8, 21))
    match.propose_score(
        Score((SetScore(6, 4),)), by=players[1], at=at(8, 21)
    )
    match.agree_result(at=at(8, 22))
    announced.extend(match.pull_events())

    private = Match.post(
        match_id=uuid4(),
        club_id=uuid4(),
        category_id=uuid4(),
        sport=Sport.PADEL,
        start=at(8, 18),
        duration=hours(1),
        share=SeatShare(grosze(3800)),
        policy=HoldPolicy(window=hours(24), join_cut=minutes(30)),
        at=at(1),
        kind=MatchKind.PRIVATE,
    )
    private.open_seats_to_the_marketplace(2, at=at(1))
    private.lose_inventory(at=at(2))
    announced.extend(private.pull_events())

    # The three claim announcements, and each arrives a different way: one is
    # redeemed inside its five minutes, one runs out and is reaped, and one is
    # ended by the match dying underneath it. The third produces the same name
    # as the second, which is ADR-0081's *"one rule ends a claim, whatever ended
    # it"* — so the set below is three names from four writes.
    claimed = Match.post(
        match_id=uuid4(),
        club_id=uuid4(),
        category_id=uuid4(),
        sport=Sport.PADEL,
        start=at(8, 18),
        duration=hours(1),
        share=SeatShare(grosze(3800)),
        policy=HoldPolicy(window=hours(24), join_cut=minutes(30)),
        at=at(1),
    )
    buyer, dawdler, latecomer = uuid4(), uuid4(), uuid4()
    claimed.open_claim(buyer, at=at(7, 20))
    claimed.redeem_claim(buyer, at=at(7, 20))
    claimed.open_claim(dawdler, at=at(7, 20))
    claimed.reap_lapsed_claims(at=at(7, 21))
    claimed.open_claim(latecomer, at=at(7, 21))
    claimed.cancel_for_weather(at=at(7, 21))
    announced.extend(claimed.pull_events())

    # A settled departure improving, which is the only way an outcome ever
    # moves once it has landed: she recovered half, and then the club lost the
    # court from under everybody.
    improved = Match.post(
        match_id=uuid4(),
        club_id=uuid4(),
        category_id=uuid4(),
        sport=Sport.PADEL,
        start=at(8, 18),
        duration=hours(1),
        share=SeatShare(grosze(3800)),
        policy=HoldPolicy(window=hours(24), join_cut=minutes(30)),
        at=at(1),
    )
    for player in (players := [uuid4() for _ in range(4)]):
        improved.take_seat(player, at=at(7, 20))
        improved.pay_seat(player, at=at(7, 20))
    improved.depart(players[0], quote=Outcome.REFUNDED_HALF, at=at(8, 15))
    improved.take_seat(uuid4(), at=at(8, 15))
    improved.cancel_by_club(at=at(8, 16))
    announced.extend(improved.pull_events())

    for cancel in (
        "cancel_by_club",
        "cancel_for_weather",
        "settle_incomplete_cancellation",
        "settle_checkpoint_cancellation",
    ):
        one = Match.post(
            match_id=uuid4(),
            club_id=uuid4(),
            category_id=uuid4(),
            sport=Sport.SQUASH,
            start=at(8, 18),
            duration=hours(1),
            share=SeatShare(grosze(3800)),
            policy=HoldPolicy(window=hours(24), join_cut=minutes(30)),
            at=at(1),
        )
        one.pull_events()
        getattr(one, cancel)(at=at(2))
        announced.extend(one.pull_events())

    return announced


def test_a_full_life_produces_every_registered_name():
    """The behavioural half of the walk above.

    The AST walk proves each write announces *something*; this proves the set of
    somethings is the set that is registered, so an event class that exists and
    is never produced is caught too.
    """

    produced = {type(event) for event in _drive_every_write()}

    assert produced == {event_cls for event_cls, _ in MATCH_EVENTS}


def test_every_announcement_round_trips_through_the_codec():
    """The outbox writes what `encode` gives and the worker reads `decode`.

    A score therefore rides as lists of integers rather than tuples: JSON has no
    tuple, and an event that does not decode into itself is a durable contract
    in one direction.
    """

    codec = _codec()
    for event in _drive_every_write():
        encoded = codec.encode(event)
        decoded = codec.decode(
            SerializedEventEnvelope(
                id=uuid4(),
                event_type=encoded.event_type,
                schema_version=encoded.schema_version,
                payload=encoded.payload,
                occurred_at=event.occurred_at,
            )
        )
        assert decoded == event, f"{type(event).__name__} does not survive the outbox"


def test_the_aggregate_drains_what_it_announced():
    """`pull_events` empties, so a second save cannot publish the same change."""

    events = _drive_every_write()
    assert events
    match = Match.post(
        match_id=uuid4(),
        club_id=uuid4(),
        category_id=uuid4(),
        sport=Sport.PADEL,
        start=instant(datetime(2026, 9, 8, 18, tzinfo=timezone.utc)),
        duration=hours(1),
        share=SeatShare(grosze(3800)),
        policy=HoldPolicy(),
        at=instant(datetime(2026, 9, 1, tzinfo=timezone.utc)),
    )

    assert len(match.pull_events()) == 1
    assert match.pull_events() == []


def test_the_walk_reads_the_file_the_aggregate_lives_in():
    """Guards the guard: a moved module must not turn this suite into a no-op."""

    assert AGGREGATE.exists()
    assert inspect.getsourcefile(Match) == str(AGGREGATE)
