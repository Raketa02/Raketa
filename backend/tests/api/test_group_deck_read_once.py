"""A deck read loads each event stream once, and answers exactly as it did when
it loaded them again and again (#704, ADR-0197 §2c).

``GET /pools/{id}/deck``'s adapters each replayed what they needed on their
own: a person's rating stream for the pair rule, again for the forecasts and
again for the card's people; their profile twice; a rescue's candidates again.
They now share one ``ReadOnceEventStore`` for the life of the request. The
claims here:

- within one read, **no stream is loaded twice**, counted at the store;
- **the same response with and without the reuse**, across a deck with cards,
  a rescue offered, an empty segment and a segment the reader's intent hides;
- **a write beside the read still sees its own events** — the reuse is the deck
  read's and reaches no use case that writes.

The clock stands on **Monday 5 October 2026, 08:00 in Kraków**.
"""

from __future__ import annotations

import re
from collections import Counter
from uuid import UUID

import pytest

from app.api.dependencies import get_clock
from app.bootstrap import composition
from app.bootstrap.composition import (
    build_decks,
    build_read_group_deck,
    build_read_group_deck_once,
    build_say_yes,
)
from app.core.config import get_settings
from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.infrastructure.events.read_once_event_store import ReadOnceEventStore
from app.infrastructure.events.sqlalchemy_domain_event_store import SqlAlchemyEventStore
from app.modules.proposals.application.commands import (
    AnswerProposalCommand,
    ReadGroupDeckCommand,
)
from tests.api import players_world as players
from tests.api.proposals_world import (
    MONDAY_MORNING,
    a_club_and_its_desk,
    a_group,
    a_member,
    live_ids,
    makes,
    says_yes,
    warsaw,
)
from tests.unit.fake_clock import MovableClock


@pytest.fixture
def clock(app):
    """Monday 5 October 2026, 08:00 in Kraków."""

    fixed = MovableClock(MONDAY_MORNING)
    app.dependency_overrides[get_clock] = lambda: fixed
    return fixed


@pytest.fixture
async def club(client) -> str:
    """Bonarka Arena, Instant: one padel court, a 24-hour cut-off."""

    club_id, _desk = await a_club_and_its_desk(client, way="INSTANT")
    return club_id


@pytest.fixture
async def crowd(client, session_factory, payments) -> list[dict]:
    """Ola — the reader — and seven others, all at padel 2,5, free every hour,
    competitive, each with a card that pays."""

    return [
        await a_member(client, session_factory, payments, name)
        for name in ("ola", "kuba", "ewa", "tomek", "ania", "marek", "zofia", "piotr")
    ]


@pytest.fixture
async def group(client, club, crowd) -> UUID:
    return await a_group(client, crowd[0], club, *crowd[1:])


@pytest.fixture
def without_the_reuse(monkeypatch: pytest.MonkeyPatch):
    """The deck read as it was before #704: every adapter over the store
    itself. A fixture a test asks for *after* reading with the reuse."""

    def off() -> None:
        monkeypatch.setattr(composition, "ReadOnceEventStore", lambda inner: inner)

    return off


@pytest.fixture
def stream_loads(monkeypatch: pytest.MonkeyPatch) -> Counter:
    """Every ``load_stream`` the store answers, by stream."""

    loads: Counter = Counter()
    original = SqlAlchemyEventStore.load_stream

    async def counting(self, *, aggregate_type: str, aggregate_id: UUID):
        loads[(aggregate_type, aggregate_id)] += 1
        return await original(
            self, aggregate_type=aggregate_type, aggregate_id=aggregate_id
        )

    monkeypatch.setattr(SqlAlchemyEventStore, "load_stream", counting)
    return loads


async def deck_of(
    client, player: dict, group: UUID, *, kind: str = "COMPETITIVE"
) -> dict:
    read = await client.get(
        f"/api/v1/pools/{group}/deck",
        params={"sport": "PADEL", "kind": kind},
        headers=player["headers"],
    )
    assert read.status_code == 200, read.text
    return read.json()


def unsigned(deck: dict) -> str:
    """The response with each photo URL's signature and its date taken off:
    those change with the wall clock on every signing, and nothing else in a
    deck does."""

    return re.sub(r"\?X-Amz-[^\"]*", "", str(deck))


async def a_seat_left(client, session_factory, clock, club, group, crowd) -> str:
    """The four's game on Saturday at 17:00, booked by Tomek's yes, and Kuba
    leaving it — a seat on the board for whoever fits and is free."""

    four = crowd[:4]
    proposal = await makes(
        session_factory, clock, pool_id=group, club_id=club, versions=(tuple(four),)
    )
    for player in four[:3]:
        assert (await says_yes(client, player, proposal)).status_code == 200
    last = await says_yes(client, four[3], proposal)
    assert last.status_code == 200, last.text
    booking = last.json()["booked"]["booking_id"]
    left = await client.post(
        f"/api/v1/bookings/{booking}/departure", headers=four[1]["headers"]
    )
    assert left.status_code == 200, left.text
    return booking


# --------------------------------------------------------------------------- #
# Each stream once
# --------------------------------------------------------------------------- #


@pytest.fixture
async def two_cards(client, session_factory, clock, club, crowd, group) -> list:
    """Ola's two cards: a pick with Ewa In, and Piotr's post in two versions
    with Ania and Marek In on the other one."""

    ola, kuba, ewa, tomek, ania, marek, zofia, piotr = crowd
    first = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((ola, kuba, ewa, tomek),),
    )
    second = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(11, 18),
        poster=piotr,
        versions=((ola, ewa, tomek), (ania, marek, zofia)),
    )
    await says_yes(client, ewa, first)
    await says_yes(client, ania, second)
    await says_yes(client, marek, second)
    return [first, second]


async def test_one_read_loads_no_stream_twice(
    client, crowd, group, two_cards, stream_loads
):
    ola = crowd[0]
    stream_loads.clear()

    deck = await deck_of(client, ola, group)

    assert len(deck["cards"]) == 2
    loaded_twice = {stream: n for stream, n in stream_loads.items() if n > 1}
    assert loaded_twice == {}
    # The streams the read's adapters share were each loaded, once.
    kinds = {aggregate_type for aggregate_type, _ in stream_loads}
    assert {"player_profile", "skill_rating", "proposal"} <= kinds, kinds
    assert stream_loads[("player_profile", ola["id"])] == 1


async def test_a_read_with_a_rescue_offered_loads_no_stream_twice(
    client, session_factory, clock, club, crowd, group, stream_loads
):
    await a_seat_left(client, session_factory, clock, club, group, crowd)
    zofia = crowd[6]
    stream_loads.clear()

    deck = await deck_of(client, zofia, group)

    assert [card["type"] for card in deck["cards"]] == ["SEAT_OPEN"]
    assert {stream: n for stream, n in stream_loads.items() if n > 1} == {}
    assert "booking" in {aggregate_type for aggregate_type, _ in stream_loads}


# --------------------------------------------------------------------------- #
# The same responses
# --------------------------------------------------------------------------- #


async def test_a_deck_with_cards_reads_the_same_with_and_without_the_reuse(
    client, crowd, group, two_cards, without_the_reuse
):
    ola = crowd[0]

    with_reuse = await deck_of(client, ola, group)
    without_the_reuse()
    without_reuse = await deck_of(client, ola, group)

    assert len(with_reuse["cards"]) == 2
    assert unsigned(with_reuse) == unsigned(without_reuse)


async def test_a_rescue_offered_reads_the_same_with_and_without_the_reuse(
    client, session_factory, clock, club, crowd, group, without_the_reuse
):
    await a_seat_left(client, session_factory, clock, club, group, crowd)
    zofia = crowd[6]

    with_reuse = await deck_of(client, zofia, group)
    without_the_reuse()
    without_reuse = await deck_of(client, zofia, group)

    assert [card["type"] for card in with_reuse["cards"]] == ["SEAT_OPEN"]
    assert unsigned(with_reuse) == unsigned(without_reuse)


async def test_an_empty_segment_reads_the_same_with_and_without_the_reuse(
    client, clock, crowd, group, without_the_reuse
):
    ola = crowd[0]

    with_reuse = await deck_of(client, ola, group)
    without_the_reuse()
    without_reuse = await deck_of(client, ola, group)

    assert with_reuse["cards"] == []
    assert with_reuse["segments"] == [{"kind": "COMPETITIVE", "count": 0}]
    assert unsigned(with_reuse) == unsigned(without_reuse)


async def test_a_segment_the_intent_hides_reads_the_same_with_and_without_the_reuse(
    client, session_factory, clock, club, crowd, group, without_the_reuse
):
    """Competitive Ola asks for the For fun segment: its card is not dealt and
    the segment is not shown, with the reuse and without."""

    ola, kuba, ewa, tomek, ania, marek, zofia, _ = crowd
    await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((ola, kuba, ewa, tomek),),
    )
    for_fun = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        start=warsaw(11, 18),
        kind=SearchMode.FOR_FUN,
        versions=((ola, ania, marek, zofia),),
    )
    await says_yes(client, ania, for_fun)

    with_reuse = await deck_of(client, ola, group, kind="FOR_FUN")
    without_the_reuse()
    without_reuse = await deck_of(client, ola, group, kind="FOR_FUN")

    assert with_reuse["cards"] == []
    assert with_reuse["segments"] == [{"kind": "COMPETITIVE", "count": 1}]
    assert unsigned(with_reuse) == unsigned(without_reuse)


# --------------------------------------------------------------------------- #
# Scoped to the read
# --------------------------------------------------------------------------- #


@pytest.fixture
def read_once_stores_built(monkeypatch: pytest.MonkeyPatch) -> list:
    """Every ``ReadOnceEventStore`` the composition builds."""

    built: list = []

    def counting(inner):
        store = ReadOnceEventStore(inner)
        built.append(store)
        return store

    monkeypatch.setattr(composition, "ReadOnceEventStore", counting)
    return built


async def test_the_reuse_is_the_requests_alone(
    session_factory, clock, read_once_stores_built
):
    """The route's builder is the one that loads each stream once. The plain
    builder — the notifications handler's, which asks the deck ``shows`` for
    every row of an outbox batch beside handlers that append, and the seed's
    — reads the session's own store, as every other composition does."""

    settings = get_settings()
    async with session_factory() as session:
        build_read_group_deck(session, settings=settings, clock=clock)
        build_decks(session, settings=settings)
        assert read_once_stores_built == []

        build_read_group_deck_once(session, settings=settings, clock=clock)
        assert len(read_once_stores_built) == 1


async def test_a_yes_in_one_session_is_read_by_the_next_deck_read_in_it(
    client, session_factory, clock, club, crowd, group, payments
):
    """A write path beside the deck read, in **one session**: a yes appends to
    the proposal's stream and the deck built after it in the same session —
    the request's and the plain one alike — shows it In."""

    ola, kuba, ewa, tomek = crowd[:4]
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((ola, kuba, ewa, tomek),),
    )
    settings = get_settings()
    command = ReadGroupDeckCommand(
        player_id=ola["id"],
        pool_id=group,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
    )
    async with session_factory() as session:
        [card] = (
            await build_read_group_deck_once(
                session, settings=settings, clock=clock
            ).execute(command)
        ).cards
        assert card.in_ == ()

        await build_say_yes(
            session, clock=clock, provider=payments, settings=settings
        ).execute(AnswerProposalCommand(proposal_id=proposal, player_id=ewa["id"]))

        for build in (build_read_group_deck, build_read_group_deck_once):
            [card] = (
                await build(session, settings=settings, clock=clock).execute(command)
            ).cards
            assert card.in_ == (ewa["id"],), build.__name__


async def test_a_write_beside_the_deck_read_sees_its_own_events(
    client, session_factory, clock, club, crowd, group
):
    """A yes appends to the proposal's stream and reloads it in one session,
    and the next deck read — and the next yes — see what it wrote. The reuse
    is the deck read's and nothing else's, so neither is reading a copy."""

    ola, kuba, ewa, tomek = crowd[:4]
    proposal = await makes(
        session_factory,
        clock,
        pool_id=group,
        club_id=club,
        versions=((ola, kuba, ewa, tomek),),
    )
    [card] = (await deck_of(client, ola, group))["cards"]
    assert card["in_count"] == 0

    assert (await says_yes(client, ewa, proposal)).status_code == 200
    [card] = (await deck_of(client, ola, group))["cards"]
    assert card["in_count"] == 1

    assert (await says_yes(client, ola, proposal)).status_code == 200
    assert (await deck_of(client, ola, group))["cards"] == []
    assert await live_ids(client, ola) == [str(proposal)]

    # The last two yeses book the court, off the stream the first two wrote.
    for player in (kuba, tomek):
        answered = await says_yes(client, player, proposal)
        assert answered.status_code == 200, answered.text
    assert answered.json()["booked"] is not None

    # And an intent declared after a read is what the next read deals from.
    await players.declare_intent(client, ola["token"], intent="FOR_FUN")
    assert (await deck_of(client, ola, group, kind="FOR_FUN"))["segments"] == [
        {"kind": "FOR_FUN", "count": 0}
    ]
