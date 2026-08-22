"""The four Money use cases, over the real repository and a faked event store.

The store is faked, not the repository — so the stream id, the version
bookkeeping and the round trip through the real codec are all exercised. A
repository fake would leave every one of them tested by nothing.

**The share cases are the ones to read.** ADR-0056's two custody regimes produce
two different *chains*, and the difference is invisible on a screen: the same
30 zł is held on one path and gone on the other. Each is asserted as the
movements it writes and as the number ``held_for`` folds out of them.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest

from app.application.events.store import EventStreamVersionConflict
from app.bootstrap.composition import build_ledger_repository
from app.kernel import grosze
from app.modules.money.application.commands import (
    Compensation,
    HeldByRaketa,
    NewMovement,
    PaidAtTheCounter,
    PassedToTheClub,
    PseudonymisePlayerCommand,
    RecordMovementsCommand,
    RecordShareCommand,
)
from app.modules.money.application.pseudonymise_player import PseudonymisePlayer
from app.modules.money.application.record_movements import RecordMovements
from app.modules.money.application.record_share import RecordShare
from app.modules.money.domain.causes import MovementCause
from app.modules.money.domain.movement import SeatRef
from app.modules.money.domain.parties import ClubParty, PlayerParty, RaketaParty
from app.modules.money.domain.reference import Reference, ReferenceKind
from tests.unit.fake_event_store import (
    CountingUnitOfWork,
    FrozenClock,
    InMemoryEventStore,
    RecordingPublisher,
    money_event_codec,
    utc,
)

SHARE = grosze(3800)


def pay(token: str) -> Reference:
    return Reference(ReferenceKind.PAYMENT, token)


class _World:
    """One session's worth of Money wiring, built from the composition root."""

    def __init__(self) -> None:
        self.store = InMemoryEventStore(codec=money_event_codec())
        self.events = RecordingPublisher()
        self.uow = CountingUnitOfWork()
        self.clock = FrozenClock(at=utc(2026, 8, 24))
        self.ledgers = build_ledger_repository(
            event_store=self.store, events=self.events
        )
        self.movements = RecordMovements(self.ledgers, self.uow, self.clock)
        self.shares = RecordShare(self.movements)
        self.erase = PseudonymisePlayer(self.ledgers, self.uow, self.clock)


@pytest.fixture
def world() -> _World:
    return _World()


@pytest.fixture
def player():
    return uuid4()


@pytest.fixture
def seat() -> SeatRef:
    return SeatRef(match_id=uuid4(), index=1)


# ---------------------------------------------------------------------------
# The two custody regimes, and the counter
# ---------------------------------------------------------------------------


async def test_an_open_matchs_share_writes_one_movement_and_is_held(
    world, player, seat
):
    ledger = await world.shares.execute(
        RecordShareCommand(
            player_id=player,
            seat=seat,
            amount=SHARE,
            reference=pay("a1"),
            arrival=HeldByRaketa(),
        )
    )

    assert [movement.cause for movement in ledger.movements] == [
        MovementCause.SHARE_ONLINE
    ]
    assert ledger.movements[0].payer == PlayerParty(player)
    assert ledger.movements[0].payee == RaketaParty()
    assert ledger.held_for(seat) == SHARE
    assert world.uow.commits == 1


async def test_a_private_courts_share_writes_two_movements_that_land_together(
    world, player, seat
):
    club = uuid4()
    ledger = await world.shares.execute(
        RecordShareCommand(
            player_id=player,
            seat=seat,
            amount=SHARE,
            reference=pay("a1"),
            arrival=PassedToTheClub(club_id=club, settlement=pay("a2")),
        )
    )

    assert len(ledger.movements) == 2
    assert ledger.movements[0].payee == RaketaParty()
    assert ledger.movements[1].payer == RaketaParty()
    assert ledger.movements[1].payee == ClubParty(club)
    assert ledger.held_for(seat) == 0
    # One append, so a failure cannot leave the first half on its own.
    assert world.store.appends == 1
    assert world.uow.commits == 1


async def test_a_counter_paid_share_writes_the_single_player_to_club_form(
    world, player, seat
):
    club = uuid4()
    ledger = await world.shares.execute(
        RecordShareCommand(
            player_id=player,
            seat=seat,
            amount=SHARE,
            reference=pay("a1"),
            arrival=PaidAtTheCounter(club_id=club),
        )
    )

    assert len(ledger.movements) == 1
    assert ledger.movements[0].payer == PlayerParty(player)
    assert ledger.movements[0].payee == ClubParty(club)
    assert ledger.movements[0].cause is MovementCause.SHARE_AT_COUNTER
    assert ledger.raketa_float == 0
    assert ledger.funded_by_the_player_for(seat) == SHARE


async def test_the_two_regimes_are_two_different_chains(world, player):
    """The same amount, the same cause, and a different answer to *who has it*."""

    open_seat = SeatRef(match_id=uuid4(), index=0)
    private_seat = SeatRef(match_id=uuid4(), index=0)

    await world.shares.execute(
        RecordShareCommand(
            player_id=player,
            seat=open_seat,
            amount=SHARE,
            reference=pay("a1"),
            arrival=HeldByRaketa(),
        )
    )
    ledger = await world.shares.execute(
        RecordShareCommand(
            player_id=player,
            seat=private_seat,
            amount=SHARE,
            reference=pay("b1"),
            arrival=PassedToTheClub(club_id=uuid4(), settlement=pay("b2")),
        )
    )

    assert ledger.held_for(open_seat) == SHARE
    assert ledger.held_for(private_seat) == 0
    assert ledger.raketa_float == SHARE


# ---------------------------------------------------------------------------
# The entry point
# ---------------------------------------------------------------------------


async def test_a_share_and_its_reversal_can_be_one_write(world, player, seat):
    """#70's shape: money arrived for a seat that had already gone.

    There is no instant at which the stored ledger says Raketa kept 30 zł,
    because both movements are in one append.
    """

    ledger = await world.movements.execute(
        RecordMovementsCommand(
            player_id=player,
            drafts=(
                NewMovement(
                    payer=PlayerParty(player),
                    payee=RaketaParty(),
                    amount=SHARE,
                    cause=MovementCause.SHARE_ONLINE,
                    reference=pay("a1"),
                    seat=seat,
                ),
                Compensation(
                    original=pay("a1"),
                    reference=Reference(ReferenceKind.REVERSAL, "a1"),
                    cause=MovementCause.CLAIM_LAPSED,
                ),
            ),
        )
    )

    assert len(ledger.movements) == 2
    assert ledger.held_for(seat) == 0
    assert world.store.appends == 1
    assert world.uow.commits == 1


class _TickingClock:
    """A clock that moves a second every time it is read.

    A frozen one cannot see this rule at all: *one read per command* and *a read
    per draft* return the same instant, so the test would pass either way.
    """

    def __init__(self) -> None:
        self._reads = 0

    def now(self):
        self._reads += 1
        return utc(2026, 8, 24) + timedelta(seconds=self._reads)


async def test_both_halves_of_one_command_share_one_instant(world, player, seat):
    """A pass-through share is one event, not two a second apart."""

    world.movements._clock = _TickingClock()  # noqa: SLF001 — the point of the test

    ledger = await world.shares.execute(
        RecordShareCommand(
            player_id=player,
            seat=seat,
            amount=SHARE,
            reference=pay("a1"),
            arrival=PassedToTheClub(club_id=uuid4(), settlement=pay("a2")),
        )
    )
    first, second = ledger.movements
    assert first.occurred_at == second.occurred_at


async def test_a_movement_is_published_as_well_as_stored(world, player, seat):
    await world.shares.execute(
        RecordShareCommand(
            player_id=player,
            seat=seat,
            amount=SHARE,
            reference=pay("a1"),
            arrival=HeldByRaketa(),
        )
    )
    assert len(world.events.published) == 1


# ---------------------------------------------------------------------------
# The repository
# ---------------------------------------------------------------------------


async def test_a_ledger_survives_a_round_trip_through_the_store(world, player, seat):
    await world.shares.execute(
        RecordShareCommand(
            player_id=player,
            seat=seat,
            amount=SHARE,
            reference=pay("a1"),
            arrival=PassedToTheClub(club_id=uuid4(), settlement=pay("a2")),
        )
    )

    reloaded = await build_ledger_repository(
        event_store=world.store, events=world.events
    ).load(player)

    assert len(reloaded.movements) == 2
    assert reloaded.held_for(seat) == 0
    assert reloaded.player_id == player


async def test_a_second_write_appends_at_the_version_the_first_left(
    world, player, seat
):
    for token in ("a1", "a2"):
        await world.shares.execute(
            RecordShareCommand(
                player_id=player,
                seat=seat,
                amount=SHARE,
                reference=pay(token),
                arrival=HeldByRaketa(),
            )
        )
    reloaded = await world.ledgers.load(player)
    assert reloaded.version == 2


async def test_a_stale_writer_loses_rather_than_interleaving(world, player, seat):
    """Two ledgers read at the same version, and the second append is refused."""

    other = build_ledger_repository(event_store=world.store, events=world.events)
    mine = await world.ledgers.load(player)
    theirs = await other.load(player)

    from app.modules.money.domain.movement import Movement
    from app.kernel import instant

    for ledger, token in ((mine, "a1"), (theirs, "a2")):
        ledger.record(
            Movement(
                id=uuid4(),
                payer=PlayerParty(player),
                payee=RaketaParty(),
                amount=SHARE,
                seat=seat,
                reservation=None,
                reference=pay(token),
                cause=MovementCause.SHARE_ONLINE,
                occurred_at=instant(world.clock.now()),
            )
        )

    await world.ledgers.save(mine)
    with pytest.raises(EventStreamVersionConflict):
        await other.save(theirs)


async def test_every_ledger_is_found_by_the_scan(world, seat):
    players = [uuid4(), uuid4(), uuid4()]
    for index, player in enumerate(players):
        await world.shares.execute(
            RecordShareCommand(
                player_id=player,
                seat=seat,
                amount=SHARE,
                reference=pay(f"a{index}"),
                arrival=HeldByRaketa(),
            )
        )

    found = await world.ledgers.all_ledgers()
    assert {ledger.player_id for ledger in found} == set(players)


async def test_a_player_with_no_stream_loads_as_an_empty_ledger(world, player):
    ledger = await world.ledgers.load(player)
    assert ledger.movements == ()
    assert ledger.balance == 0


async def test_saving_nothing_never_asks_the_store(world, player):
    ledger = await world.ledgers.load(player)
    await world.ledgers.save(ledger)
    assert world.store.appends == 0


# ---------------------------------------------------------------------------
# Erasure
# ---------------------------------------------------------------------------


async def test_erasure_leaves_the_movements_standing(world, player, seat):
    await world.shares.execute(
        RecordShareCommand(
            player_id=player,
            seat=seat,
            amount=SHARE,
            reference=pay("a1"),
            arrival=HeldByRaketa(),
        )
    )

    erased = await world.erase.execute(PseudonymisePlayerCommand(player_id=player))
    reloaded = await world.ledgers.load(player)

    assert erased.is_pseudonymised
    assert len(reloaded.movements) == 1
    assert reloaded.movements[0].amount == SHARE
    assert reloaded.subject_id == erased.subject_id
    assert reloaded.movements[0].payer == PlayerParty(erased.subject_id)


async def test_the_pseudonym_is_not_derivable_from_the_player(world, player, seat):
    """Minted, so nobody holding the player id can recompute it."""

    from app.modules.money.domain.ids import ledger_stream_id

    erased = await world.erase.execute(PseudonymisePlayerCommand(player_id=player))
    assert erased.subject_id != player
    assert erased.subject_id != ledger_stream_id(player)
