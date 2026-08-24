"""`kernel.seat_price`: what a filler pays, and why it is `refill_outcome`'s mirror.

ADR-0061 prices the open call *"full from the vacancy, 50 % from the rescue
deadline"*; ADR-0033 says the leaver *"recovers what the filler paid: full price
from the vacancy, half from the rescue deadline."* Those are **one boundary read
by two parties**, so the load-bearing claim in this file is not either function
on its own — it is that they agree, at every instant, on every record shape.

That is asserted as a property rather than as a pair of examples, because the
failure it guards against is a boundary moved in one of them: a discount that
starts an hour before the refund it is supposed to fund is money the platform
invents, and no single-instant case would see it.
"""

from __future__ import annotations

import pytest

from app.kernel import (
    RESCUE_FRACTION,
    Grosze,
    MatchKind,
    Outcome,
    PayModel,
    SeatShare,
    apply_fraction,
    deadlines,
    grosze,
    minutes,
    percent,
    refill_outcome,
    seat_price,
    shifted,
)

from tests.unit.match_records import a_match

SHARE: SeatShare = SeatShare(grosze(3800))
#: An odd number of grosze, so *half* is not an integer and the rounding rule is
#: exercised rather than stepped over.
ODD: SeatShare = SeatShare(grosze(3801))


def test_the_discount_is_half() -> None:
    """The one case comparing the constant against its literal."""

    assert RESCUE_FRACTION == percent(50)


def test_a_seat_is_full_price_before_the_rescue_deadline() -> None:
    record = a_match(paid=1, committed_at=a_match().created)
    rescue = deadlines(record).rescue

    assert seat_price(record, SHARE, shifted(rescue, minutes(-1))) == SHARE


def test_a_seat_is_half_price_from_the_rescue_deadline() -> None:
    """Asserted a minute either side, because a region is not a boundary."""

    record = a_match(paid=1, committed_at=a_match().created)
    rescue = deadlines(record).rescue
    half = SeatShare(apply_fraction(Grosze(SHARE), RESCUE_FRACTION))

    assert seat_price(record, SHARE, shifted(rescue, minutes(-1))) == SHARE
    assert seat_price(record, SHARE, rescue) == half
    assert seat_price(record, SHARE, shifted(rescue, minutes(1))) == half


def test_a_private_court_has_no_discount_tier_at_any_distance() -> None:
    """The sentence `refill_outcome` already carries, from the other side.

    That path bought the court at booking, so there is no court to save and
    nothing the discount would be for.
    """

    record = a_match(paid=1, kind=MatchKind.PRIVATE, pay_model=PayModel.SPLIT)
    when = deadlines(record)

    for moment in (
        shifted(when.rescue, minutes(-60)),
        when.rescue,
        shifted(when.check, minutes(60)),
    ):
        assert seat_price(record, SHARE, moment) == SHARE


def test_there_is_no_checkpoint_tier() -> None:
    """Past the checkpoint a seat is still sold at the rescue price.

    ADR-0033 is explicit that a filler who *nonetheless arrives* pays it, and a
    third step here would make the money that arrives differ from the money that
    goes back.
    """

    record = a_match(paid=1, committed_at=a_match().created)
    when = deadlines(record)
    half = SeatShare(apply_fraction(Grosze(SHARE), RESCUE_FRACTION))

    assert seat_price(record, SHARE, shifted(when.check, minutes(1))) == half
    assert seat_price(record, SHARE, shifted(when.check, minutes(60))) == half


@pytest.mark.parametrize("share", [SHARE, ODD])
def test_the_price_and_the_refund_turn_at_the_same_instant(share) -> None:
    """**The property this whole module exists for**, over a moving clock.

    `seat_price` is the full share exactly when `refill_outcome` answers
    `REFUNDED_IN_FULL`. Walked minute by minute across the rescue deadline on
    two record shapes, so a boundary moved in either function disagrees with the
    other rather than passing quietly.
    """

    record = a_match(paid=1, committed_at=a_match().created)
    rescue = deadlines(record).rescue

    for offset in range(-120, 121, 7):
        now = shifted(rescue, minutes(offset))
        paid_in_full = seat_price(record, share, now) == share
        refunded_in_full = refill_outcome(record, now) is Outcome.REFUNDED_IN_FULL
        assert paid_in_full == refunded_in_full, (offset, now)


def test_a_private_courts_price_and_refund_also_agree_at_every_distance() -> None:
    """The same property on the path that has no tier at all.

    Both sides answer *full*, always — and asserting it here is what stops one
    of the two growing a private-court branch the other does not have.
    """

    record = a_match(paid=1, kind=MatchKind.PRIVATE, pay_model=PayModel.SPLIT)
    rescue = deadlines(record).rescue

    for offset in range(-120, 121, 7):
        now = shifted(rescue, minutes(offset))
        assert seat_price(record, SHARE, now) == SHARE
        assert refill_outcome(record, now) is Outcome.REFUNDED_IN_FULL


def test_half_of_an_odd_share_rounds_away_from_zero_like_every_other_refund() -> None:
    """The money kernel's rule, and not a second rounding decision here.

    3801 grosze halves to 1900,5 — and the player receives at most one grosz
    *more* than the exact half, which is the direction `round_half_away_from_zero`
    exists to fix.
    """

    record = a_match(paid=1, committed_at=a_match().created)
    at_rescue = deadlines(record).rescue

    assert int(seat_price(record, ODD, at_rescue)) == 1901
