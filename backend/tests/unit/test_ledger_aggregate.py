"""The Ledger: what it refuses, what it derives, and what erasure leaves.

The folds are the interesting half. ``balance``, ``held`` and Raketa's float are
computed from the movements and stored nowhere (ADR-0056 retires ``held: true``
by name), so each of them is asserted against a chain built movement by movement
rather than against a number anybody wrote down.

**The two custody regimes are asserted as two different chains**, because they
are the same 30 zł and the difference is invisible on the screen: on an open
match ``held`` is the share until the match commits, on a private court it is
zero from the same instant.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.kernel import InvariantViolated, grosze, instant
from app.modules.money.domain.errors import (
    DuplicateMovementReference,
    LedgerAlreadyPseudonymised,
    MovementBelongsToAnotherPlayer,
    NothingToCompensate,
)
from app.modules.money.domain.causes import MovementCause
from app.modules.money.domain.events import MovementRecorded, PlayerPseudonymised
from app.modules.money.domain.ids import ledger_stream_id
from app.modules.money.domain.ledger import Ledger
from app.modules.money.domain.movement import Movement, SeatRef
from app.modules.money.domain.parties import ClubParty, PlayerParty, RaketaParty
from app.modules.money.domain.reference import Reference, ReferenceKind

AT = instant(datetime(2026, 8, 24, 18, 0, tzinfo=timezone.utc))
LATER = instant(AT + timedelta(minutes=5))
SHARE = grosze(3800)


def pay(token: str) -> Reference:
    return Reference(ReferenceKind.PAYMENT, token)


def rev(token: str) -> Reference:
    return Reference(ReferenceKind.REVERSAL, token)


def movement(
    *,
    payer,
    payee,
    reference,
    cause=MovementCause.SHARE_ONLINE,
    seat=None,
    amount=SHARE,
    at=AT,
    reservation=None,
) -> Movement:
    return Movement(
        id=uuid4(),
        payer=payer,
        payee=payee,
        amount=amount,
        seat=seat,
        reservation=reservation,
        reference=reference,
        cause=cause,
        occurred_at=at,
    )


@pytest.fixture
def player():
    return uuid4()


@pytest.fixture
def seat() -> SeatRef:
    return SeatRef(match_id=uuid4(), index=2)


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


def test_a_players_stream_id_is_derived_and_the_same_every_time(player):
    assert Ledger.for_player(player).id == ledger_stream_id(player)
    assert ledger_stream_id(player) == ledger_stream_id(player)


def test_two_players_never_share_a_stream():
    assert ledger_stream_id(uuid4()) != ledger_stream_id(uuid4())


def test_a_player_who_has_moved_no_money_has_an_empty_ledger(player):
    ledger = Ledger.for_player(player)
    assert ledger.movements == ()
    assert ledger.balance == 0
    assert ledger.version == 0


def test_replaying_an_empty_stream_is_refused():
    """*Nothing yet* is an empty ledger, never a ledger with no identity."""

    with pytest.raises(InvariantViolated):
        Ledger.from_history([])


# ---------------------------------------------------------------------------
# What a ledger refuses
# ---------------------------------------------------------------------------


def test_a_movement_naming_another_player_is_refused(player, seat):
    ledger = Ledger.for_player(player)
    with pytest.raises(MovementBelongsToAnotherPlayer):
        ledger.record(
            movement(
                payer=PlayerParty(uuid4()),
                payee=RaketaParty(),
                reference=pay("a1"),
                seat=seat,
            )
        )


def test_the_same_reference_twice_is_refused(player, seat):
    """A duplicate webhook is the same event arriving twice, and nothing happened
    the second time — so it is refused rather than recorded and compensated."""

    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a1"),
            seat=seat,
        )
    )
    with pytest.raises(DuplicateMovementReference):
        ledger.record(
            movement(
                payer=PlayerParty(player),
                payee=RaketaParty(),
                reference=pay("a1"),
                seat=seat,
            )
        )
    assert len(ledger.movements) == 1


def test_a_ledger_has_no_way_to_remove_or_amend_a_movement(player, seat):
    """Stated as an absence, because a positive test cannot say it.

    ``Ledger`` is a mutable dataclass, so this is about the *surface*: there is
    no public method whose name suggests one, and the only one that changes what
    a movement says is ``compensate``, which adds rather than edits.
    """

    surface = {
        name
        for name in dir(Ledger)
        if not name.startswith("_") and callable(getattr(Ledger, name, None))
    }
    assert surface == {
        "for_player",
        "from_history",
        "pull_events",
        "movements_for",
        "movement_under",
        "held_for",
        "settled_to_a_club_for",
        "funded_by_the_player_for",
        "record",
        "compensate",
        "pseudonymise",
    }


# ---------------------------------------------------------------------------
# The two custody regimes
# ---------------------------------------------------------------------------


def test_an_open_matchs_share_is_held_by_raketa(player, seat):
    """No court is booked, so the money is ours to hold — and to give back whole."""

    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a1"),
            seat=seat,
        )
    )
    assert ledger.held_for(seat) == SHARE
    assert ledger.settled_to_a_club_for(seat) == 0
    assert ledger.raketa_float == SHARE


def test_a_private_courts_share_passes_through_and_is_held_for_nothing(player, seat):
    club = uuid4()
    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a1"),
            seat=seat,
        )
    )
    ledger.record(
        movement(
            payer=RaketaParty(),
            payee=ClubParty(club),
            reference=pay("a2"),
            seat=seat,
        )
    )
    assert ledger.held_for(seat) == 0
    assert ledger.settled_to_a_club_for(seat) == SHARE
    assert ledger.raketa_float == 0


def test_a_counter_paid_share_never_touches_raketa(player, seat):
    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=ClubParty(uuid4()),
            reference=pay("a1"),
            cause=MovementCause.SHARE_AT_COUNTER,
            seat=seat,
        )
    )
    assert ledger.held_for(seat) == 0
    assert ledger.raketa_float == 0
    assert ledger.funded_by_the_player_for(seat) == SHARE
    assert ledger.settled_to_a_club_for(seat) == SHARE


def test_a_refund_raketa_advanced_leaves_the_seat_below_zero(player, seat):
    """The working-capital position ADR-0045 names, read rather than estimated."""

    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a1"),
            seat=seat,
        )
    )
    ledger.record(
        movement(
            payer=RaketaParty(),
            payee=ClubParty(uuid4()),
            reference=pay("a2"),
            seat=seat,
        )
    )
    ledger.record(
        movement(
            payer=RaketaParty(),
            payee=PlayerParty(player),
            reference=Reference(ReferenceKind.REFUND, "a3"),
            cause=MovementCause.WITHDRAWN_BEFORE_LOCK,
            seat=seat,
        )
    )
    assert ledger.held_for(seat) == -SHARE
    assert ledger.raketa_float == -SHARE


# ---------------------------------------------------------------------------
# The balance
# ---------------------------------------------------------------------------


def test_paying_for_a_seat_leaves_the_balance_at_zero(player, seat):
    """The rule the whole model rests on: an ordinary payment is not a debt."""

    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a1"),
            seat=seat,
        )
    )
    assert ledger.balance == 0
    assert not ledger.is_in_debt


def test_a_half_refund_is_not_a_debt(player, seat):
    """A rescue leaver got half back and owes nothing — she just lost half."""

    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a1"),
            seat=seat,
        )
    )
    ledger.record(
        movement(
            payer=RaketaParty(),
            payee=PlayerParty(player),
            reference=Reference(ReferenceKind.REFUND, "a2"),
            cause=MovementCause.LEAVER_RESCUE,
            amount=grosze(1900),
            seat=seat,
        )
    )
    assert ledger.balance == 0


def test_a_failed_collection_takes_the_balance_below_zero(player, seat):
    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=RaketaParty(),
            payee=PlayerParty(player),
            reference=pay("a1"),
            cause=MovementCause.COLLECTION_FAILED,
            amount=grosze(3000),
            seat=seat,
            reservation=uuid4(),
        )
    )
    assert ledger.balance == -3000
    assert ledger.is_in_debt


def test_clearing_a_debt_moves_the_number_back_to_zero(player, seat):
    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=RaketaParty(),
            payee=PlayerParty(player),
            reference=pay("a1"),
            cause=MovementCause.COLLECTION_FAILED,
            amount=grosze(3000),
            seat=seat,
        )
    )
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a2"),
            cause=MovementCause.DEBT_CLEARED,
            amount=grosze(3000),
            seat=None,
        )
    )
    assert ledger.balance == 0
    assert not ledger.is_in_debt


def test_a_debt_reads_back_to_the_reservation_that_caused_it(player, seat):
    """ADR-0058 gives up line items and keeps provenance, through the cause."""

    reservation = uuid4()
    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=RaketaParty(),
            payee=PlayerParty(player),
            reference=pay("a1"),
            cause=MovementCause.COLLECTION_FAILED,
            amount=grosze(3000),
            seat=seat,
            reservation=reservation,
        )
    )
    behind_it = [
        found
        for found in ledger.movements
        if found.cause is MovementCause.COLLECTION_FAILED
    ]
    assert [found.reservation for found in behind_it] == [reservation]


def test_the_balance_is_not_clamped(player, seat):
    """A positive balance is a bug, and the fold has to be able to show one.

    Clamping here would hide it from the one assertion that exists to find it.
    """

    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a1"),
            cause=MovementCause.DEBT_CLEARED,
            amount=grosze(1000),
            seat=None,
        )
    )
    assert ledger.balance == 1000


# ---------------------------------------------------------------------------
# Correction
# ---------------------------------------------------------------------------


def test_a_compensation_reverses_the_original_and_leaves_it_standing(player, seat):
    ledger = Ledger.for_player(player)
    original = ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a1"),
            seat=seat,
        )
    )
    correction = ledger.compensate(
        original=pay("a1"),
        movement_id=uuid4(),
        reference=rev("a1"),
        cause=MovementCause.CLAIM_LAPSED,
        at=LATER,
    )

    assert len(ledger.movements) == 2
    assert ledger.movement_under(pay("a1")) == original
    assert correction.payer == original.payee
    assert correction.payee == original.payer
    assert correction.amount == original.amount
    assert correction.seat == original.seat
    assert correction.cause is MovementCause.CLAIM_LAPSED
    assert correction.is_compensation
    assert ledger.held_for(seat) == 0


def test_a_compensation_must_point_at_something(player):
    ledger = Ledger.for_player(player)
    with pytest.raises(NothingToCompensate):
        ledger.compensate(
            original=pay("nope"),
            movement_id=uuid4(),
            reference=rev("nope"),
            cause=MovementCause.CLAIM_LAPSED,
            at=AT,
        )


def test_a_correction_filed_under_a_payment_reference_is_refused(player, seat):
    """The reconciliation reads compensations by kind; a ``PAY-`` one is a
    payment as far as anything downstream is concerned."""

    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a1"),
            seat=seat,
        )
    )
    with pytest.raises(NothingToCompensate):
        ledger.compensate(
            original=pay("a1"),
            movement_id=uuid4(),
            reference=pay("a2"),
            cause=MovementCause.CLAIM_LAPSED,
            at=LATER,
        )


# ---------------------------------------------------------------------------
# Erasure
# ---------------------------------------------------------------------------


def test_erasure_replaces_the_party_and_keeps_every_movement(player, seat):
    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a1"),
            seat=seat,
        )
    )
    before = ledger.movements
    pseudonym = uuid4()

    ledger.pseudonymise(pseudonym=pseudonym, at=LATER)
    after = ledger.movements

    assert ledger.is_pseudonymised
    assert ledger.subject_id == pseudonym
    assert len(after) == len(before) == 1
    assert after[0].amount == before[0].amount
    assert after[0].cause == before[0].cause
    assert after[0].reference == before[0].reference
    assert after[0].seat == before[0].seat
    assert after[0].payer == PlayerParty(pseudonym)
    assert PlayerParty(player) not in {after[0].payer, after[0].payee}


def test_erasure_changes_no_number(player, seat):
    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=RaketaParty(),
            payee=PlayerParty(player),
            reference=pay("a1"),
            cause=MovementCause.COLLECTION_FAILED,
            amount=grosze(3000),
            seat=seat,
        )
    )
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a2"),
            seat=seat,
        )
    )
    balance_before = ledger.balance
    held_before = ledger.held_for(seat)

    ledger.pseudonymise(pseudonym=uuid4(), at=LATER)

    assert ledger.balance == balance_before
    assert ledger.held_for(seat) == held_before


def test_a_ledger_is_pseudonymised_once(player):
    ledger = Ledger.for_player(player)
    ledger.pseudonymise(pseudonym=uuid4(), at=AT)
    with pytest.raises(LedgerAlreadyPseudonymised):
        ledger.pseudonymise(pseudonym=uuid4(), at=LATER)


def test_a_movement_still_lands_after_erasure(player, seat):
    """A chargeback does not stop arriving because an account closed."""

    ledger = Ledger.for_player(player)
    pseudonym = uuid4()
    ledger.pseudonymise(pseudonym=pseudonym, at=AT)
    ledger.record(
        movement(
            payer=RaketaParty(),
            payee=PlayerParty(pseudonym),
            reference=pay("a1"),
            cause=MovementCause.COLLECTION_FAILED,
            amount=grosze(3000),
            seat=seat,
            at=LATER,
        )
    )
    assert ledger.balance == -3000


def test_a_movement_addressed_to_an_erased_player_lands_under_the_pseudonym(
    player, seat
):
    """Whatever writes it holds the id it has always held.

    Refusing it would make erasure a thing that breaks the ledger; storing the
    id it carried would put the identifier back on a ledger that had just had it
    taken off. So it is accepted and rewritten on the way in.
    """

    ledger = Ledger.for_player(player)
    pseudonym = uuid4()
    ledger.pseudonymise(pseudonym=pseudonym, at=AT)

    ledger.record(
        movement(
            payer=RaketaParty(),
            payee=PlayerParty(player),
            reference=pay("a1"),
            cause=MovementCause.COLLECTION_FAILED,
            amount=grosze(3000),
            seat=seat,
            at=LATER,
        )
    )

    assert ledger.balance == -3000
    assert ledger.movements[0].payee == PlayerParty(pseudonym)

    # **Asserted on the event, not on the read.** ``movements`` masks the player
    # on the way out, so it says the pseudonym either way — a test that only
    # looked there would pass on a ledger storing the real id for ever, which is
    # exactly what erasure is supposed to stop happening.
    announced = [
        event for event in ledger.pull_events() if isinstance(event, MovementRecorded)
    ]
    assert [event.payee_id for event in announced] == [pseudonym]
    assert player not in {event.payee_id for event in announced}


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------


def test_a_ledger_replays_to_exactly_what_it_was(player, seat):
    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a1"),
            seat=seat,
            reservation=uuid4(),
        )
    )
    ledger.compensate(
        original=pay("a1"),
        movement_id=uuid4(),
        reference=rev("a1"),
        cause=MovementCause.CLAIM_LAPSED,
        at=LATER,
    )
    ledger.pseudonymise(pseudonym=uuid4(), at=LATER)

    replayed = Ledger.from_history(ledger.pull_events())

    assert replayed.id == ledger.id
    assert replayed.player_id == ledger.player_id
    assert replayed.subject_id == ledger.subject_id
    assert replayed.movements == ledger.movements
    assert replayed.balance == ledger.balance
    assert replayed.held_for(seat) == ledger.held_for(seat)
    assert replayed.version == ledger.version == 3


def test_every_change_announces_itself(player, seat):
    """Two facts happen to a ledger, and both are named events.

    Asserted as the **set** of event types a full life produces, so an event
    class that exists and is never emitted is caught as well as a change that
    announces nothing.
    """

    ledger = Ledger.for_player(player)
    ledger.record(
        movement(
            payer=PlayerParty(player),
            payee=RaketaParty(),
            reference=pay("a1"),
            seat=seat,
        )
    )
    ledger.compensate(
        original=pay("a1"),
        movement_id=uuid4(),
        reference=rev("a1"),
        cause=MovementCause.CLAIM_LAPSED,
        at=LATER,
    )
    ledger.pseudonymise(pseudonym=uuid4(), at=LATER)

    announced = [type(event) for event in ledger.pull_events()]
    assert announced == [MovementRecorded, MovementRecorded, PlayerPseudonymised]
    assert set(announced) == {MovementRecorded, PlayerPseudonymised}
