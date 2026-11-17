"""**A payment to confirm is new in Needs your answer once** — over HTTP, with
the fake provider (#815; ``docs/adr/0205`` §3).

Time to pay's own world (``test_time_to_pay.py``): Saturday's padel at Bonarka
Arena fills on Monday morning with Ivan's yes, and **Paula's** bank wants her
to confirm every payment, so her share is refused at the fill — a *To confirm*
row, *Fix your card by 08:30*. It arrived then, at its refusal, and **a change
of state never moves that**: once her time runs out the row stays, now
*Confirm* with no time, and it is not new again.
"""

from __future__ import annotations

from datetime import timedelta

from tests.api.proposals_world import runs_out
from tests.api.test_needs_your_answer import closes_the_sheet, home_of, new_for
from tests.api.test_time_to_pay import (
    a_game,
    bonarka,
    clock,
    confirms,
    four,
    to_confirm,
)

__all__ = ["bonarka", "clock", "four"]


async def test_a_refused_share_is_one_new_item_for_its_payer_alone(
    client, session_factory, clock, payments, bonarka, four
):
    club, _ = bonarka
    paula, marta, *_ = four
    assert await new_for(client, paula) == 0

    await a_game(client, session_factory, clock, club, four)

    [owed] = await to_confirm(client, paula)
    assert owed["time_to"] == "FIX_THE_CARD"
    home = await home_of(client, paula)
    assert home["needs_your_answer"]["new_count"] == 1
    assert home["needs_your_answer"]["watermark"] is not None
    # Home's tab badge counts it as it always did.
    assert home["needing_you"] == 1
    assert await new_for(client, marta) == 0


async def test_home_serves_the_to_confirm_rows_its_watermark_covers(
    client, session_factory, clock, payments, bonarka, four
):
    """The sheet draws all four sections off one read, so the payment its
    watermark covers is one it showed — the same row its own read gives."""

    club, _ = bonarka
    paula, marta, *_ = four
    await a_game(client, session_factory, clock, club, four)

    home = await home_of(client, paula)

    assert home["payments_to_confirm"] == await to_confirm(client, paula)
    assert len(home["payments_to_confirm"]) == home["needing_you"] == 1
    assert (await home_of(client, marta))["payments_to_confirm"] == []


async def test_fix_your_card_turning_into_confirm_is_not_new(
    client, session_factory, clock, payments, bonarka, four
):
    club, _ = bonarka
    paula = four[0]
    await a_game(client, session_factory, clock, club, four)
    seen = (await home_of(client, paula))["needs_your_answer"]["watermark"]
    await closes_the_sheet(client, paula, seen)
    clock.move(timedelta(minutes=30))

    assert (await runs_out(session_factory, clock)).games == 1

    [owed] = await to_confirm(client, paula)
    assert (owed["confirm_by"], owed["time_to"]) == (None, None)
    home = await home_of(client, paula)
    assert home["needs_your_answer"] == {"new_count": 0, "watermark": seen}
    assert home["needing_you"] == 1


async def test_confirming_the_payment_drops_it_from_the_count(
    client, session_factory, clock, payments, bonarka, four
):
    club, _ = bonarka
    paula = four[0]
    await a_game(client, session_factory, clock, club, four)
    [owed] = await to_confirm(client, paula)

    confirmed = await confirms(client, payments, paula, owed["seat_charge_id"])

    assert confirmed.status_code == 200, confirmed.text
    assert await to_confirm(client, paula) == []
    assert (await home_of(client, paula))["needs_your_answer"] == {
        "new_count": 0,
        "watermark": None,
    }
