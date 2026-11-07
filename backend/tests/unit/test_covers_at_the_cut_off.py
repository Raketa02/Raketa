"""**A cover is taken or let go at the cut-off, and only there** (#751;
``docs/adr/0202`` §6, call 7; the friends mechanics §8.3, §10.3).

Tomek sent Saturday 10:00 at 25 zł a share, with the cut-off Friday 10:00. His
card holds his own share and a cover for each of the other three seats. At the
cut-off one cover is **let go for each seat whose own player paid**, and every
other stays held for the take that follows: with *Split the cost*, Ewa's and
Magda's covers go and Ania's empty seat's is taken; with *Whole court*, nobody
else pays, and all four of his holds stay.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.kernel import Sport, instant
from app.modules.payments.application.covers import SettleTheCovers
from app.modules.payments.application.seat_charges import TakeTheHeldShares
from app.modules.payments.domain.provider import Payment, PaymentStatus
from app.modules.payments.domain.seat_charge import (
    RefundReason,
    SeatCharge,
    SeatChargeStatus,
)
from app.shared.domain import DomainEvent
from app.shared.ids import new_uuid

TOMEK, EWA, MAGDA = new_uuid(), new_uuid(), new_uuid()
GAME, CLUB = new_uuid(), new_uuid()
MONDAY = instant(datetime(2026, 11, 9, 18, tzinfo=timezone.utc))
SATURDAY = MONDAY + timedelta(days=4, hours=15)
CUT_OFF = SATURDAY - timedelta(hours=24)


class InMemoryCharges:
    """``SeatChargeRepository``, as far as the cut-off reads it."""

    def __init__(self) -> None:
        self._streams: dict[UUID, list[DomainEvent]] = {}

    async def load(self, charge_id: UUID) -> SeatCharge | None:
        stream = self._streams.get(charge_id)
        return None if stream is None else SeatCharge.from_history(stream)

    async def save(self, charge: SeatCharge) -> None:
        self._streams.setdefault(charge.charge_id, []).extend(charge.pull_events())

    async def of_game(self, game_id: UUID) -> Sequence[SeatCharge]:
        found = [SeatCharge.from_history(stream) for stream in self._streams.values()]
        return [charge for charge in found if charge.game_id == game_id]


async def _held(charges: InMemoryCharges, player: UUID, *, cover: bool) -> UUID:
    charge = SeatCharge.held(
        charge_id=new_uuid(),
        player_id=player,
        game_id=GAME,
        club_id=CLUB,
        account_id="acct_club",
        payment=Payment(
            payment_id=f"pi_{new_uuid().hex}",
            status=PaymentStatus.AUTHORISED,
            amount_grosze=25_00,
        ),
        sport=Sport.PADEL,
        starts_at=SATURDAY,
        at=MONDAY,
        cover=cover,
    )
    charge.keep(booking_id=GAME, until=CUT_OFF, at=MONDAY)
    await charges.save(charge)
    return charge.charge_id


async def _the_senders_court(charges: InMemoryCharges) -> list[UUID]:
    """Tomek's share, then a cover for each of the other three seats."""

    return [
        await _held(charges, TOMEK, cover=False),
        *[await _held(charges, TOMEK, cover=True) for _ in range(3)],
    ]


async def _statuses(charges: InMemoryCharges, ids: Sequence[UUID]) -> list[str]:
    found = []
    for charge_id in ids:
        charge = await charges.load(charge_id)
        assert charge is not None
        found.append(charge.status.value)
    return found


async def test_split_lets_go_a_cover_for_each_seat_its_own_player_paid():
    charges = InMemoryCharges()
    tomek = await _the_senders_court(charges)
    ewa = await _held(charges, EWA, cover=False)
    magda = await _held(charges, MAGDA, cover=False)

    let_go = await SettleTheCovers(charges=charges).execute(GAME, at=CUT_OFF)
    taken = await TakeTheHeldShares(charges=charges).execute(GAME, at=CUT_OFF)

    assert let_go == 2
    # His share, the empty seat's cover, Ewa's and Magda's shares.
    assert taken == 4
    statuses = await _statuses(charges, [*tomek, ewa, magda])
    assert statuses.count("RELEASING") == 2
    assert statuses.count("TAKING") == 4
    assert await _statuses(charges, [tomek[0], ewa, magda]) == ["TAKING"] * 3


async def test_a_cover_let_go_says_its_seat_was_paid_and_was_held_till_then():
    charges = InMemoryCharges()
    tomek = await _the_senders_court(charges)
    await _held(charges, EWA, cover=False)

    await SettleTheCovers(charges=charges).execute(GAME, at=CUT_OFF)

    released = [
        charge
        for charge_id in tomek
        if (charge := await charges.load(charge_id)) is not None
        and charge.status is SeatChargeStatus.RELEASING
    ]
    assert len(released) == 1
    assert released[0].cover
    # Held until the cut-off, never let go before: its receipt says so.
    assert released[0].released_at == CUT_OFF


async def test_whole_court_takes_every_one_of_the_senders_holds():
    charges = InMemoryCharges()
    tomek = await _the_senders_court(charges)

    let_go = await SettleTheCovers(charges=charges).execute(GAME, at=CUT_OFF)
    taken = await TakeTheHeldShares(charges=charges).execute(GAME, at=CUT_OFF)

    assert (let_go, taken) == (0, 4)
    assert await _statuses(charges, tomek) == ["TAKING"] * 4


async def test_every_seat_paid_by_its_own_player_lets_every_cover_go():
    charges = InMemoryCharges()
    tomek = await _the_senders_court(charges)
    for _ in range(3):
        await _held(charges, new_uuid(), cover=False)

    assert await SettleTheCovers(charges=charges).execute(GAME, at=CUT_OFF) == 3
    assert await _statuses(charges, tomek) == ["HELD", *["RELEASING"] * 3]


async def test_a_share_let_go_before_the_cut_off_pays_for_no_seat():
    """A friend whose own share was let go — they left (#752) — has not paid:
    their seat's cover is taken."""

    charges = InMemoryCharges()
    await _the_senders_court(charges)
    ewa = await charges.load(await _held(charges, EWA, cover=False))
    assert ewa is not None
    ewa.let_go(at=MONDAY + timedelta(days=1), reason=RefundReason.LEFT)
    await charges.save(ewa)

    assert await SettleTheCovers(charges=charges).execute(GAME, at=CUT_OFF) == 0


async def test_settling_twice_lets_nothing_more_go():
    charges = InMemoryCharges()
    await _the_senders_court(charges)
    await _held(charges, EWA, cover=False)
    settle = SettleTheCovers(charges=charges)

    assert await settle.execute(GAME, at=CUT_OFF) == 1
    assert await settle.execute(GAME, at=CUT_OFF) == 0


async def test_a_game_with_no_cover_has_nothing_to_settle():
    charges = InMemoryCharges()
    for player in (TOMEK, EWA, MAGDA):
        await _held(charges, player, cover=False)

    assert await SettleTheCovers(charges=charges).execute(GAME, at=CUT_OFF) == 0
