"""The offers region: seats put in front of her, soonest-to-expire first.

The region above everything (ADR-0052, kept by ADR-0061). *The thing with a clock
is first*, and this is the only region on Now whose cards are about a seat the
viewer neither holds nor has been suggested — she has been **told**, and the card
exists so she can race for it.

**No floor, no cap, no caption and no tail card**, which is a fact about the
*type* rather than a rule applied here: ``OffersRegion`` has nowhere to put any
of the four. That is ADR-0052's own reason for refusing to make this a sixth
shelf — as a shelf it would inherit all four, and become something the server
could order *below* a suggestion.

**Soonest-to-expire and never soonest-to-play.** Sorting by the hour of the game
sorts a player's offers by when the evening is rather than by when the chance
dies, and hiding an offer somebody waited weeks for because another is sooner
costs her a game to save a scroll. The moment is ``cascade.seat_expires_at`` —
the join cutoff, which is the one instant ``Match.open_claim`` enforces.

**The refusal path is the point, and it is one expression.** An offer is a fact
about the past; whether the seat is still there is a question about the match,
asked here at the composing instant through ``cascade.seat_exclusions``. A seat
that has gone therefore falls out of the region **and** loses the offer half of
its own card in the same breath: ``_viewer`` hands the ladder an offer exactly
when there is still a seat to take, so a card recomposed after somebody else took
it resolves to the match's own situation and *says the seat is gone* rather than
going on claiming one. That is what lets a refusal be what a success returns
(ADR-0070) — one card composer, two callers, and no second reading of the record.

**A card here names one act and offers no exit.** ADR-0083's rule is *a card
names an act when the viewer can take it now **and** a v1 surface can receive it*,
and this ticket builds the surface: ``POST /api/v1/matches/{matchId}/seat``. She
holds no seat and no claim, so ``may_depart`` is false by the kernel's own answer
rather than by a literal here.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import (
    Instant,
    SeatShare,
    Situation,
    Sport,
    Viewer,
    card_clock,
    court_named_at,
    grosze,
    may_depart,
    seat_price,
    situation,
)

from app.modules.now.domain.cards import counts_of, hold_note
from app.modules.now.domain.cascade import seat_exclusions, seat_expires_at
from app.modules.now.domain.offers import OfferedSeat
from app.modules.now.domain.ports import OfferedSeats
from app.modules.now.domain.screen import (
    MatchCard,
    Money,
    OffersRegion,
    SituationFacts,
    SituationHalf,
    Stamp,
)
from app.modules.now.domain.vocabulary import ACT_OF, ActCode


class ComposeOffers:
    """The offers region, composed for one viewer at one instant."""

    def __init__(self, *, offered: OfferedSeats) -> None:
        self._offered = offered

    async def compose(
        self,
        *,
        viewer: UUID,
        sport: Sport | None,
        now: Instant,
        stamp: Stamp,
    ) -> OffersRegion:
        """Her live offers, soonest-to-expire, under the chip she has chosen.

        ``sport`` is the **named chip** and never the resolved set, exactly as the
        strip takes it: ``all`` hides nothing. Here the two readings of ``all``
        coincide rather than merely agreeing today — the cascade's pool excludes
        anybody holding no rating at the match's sport, so no offer can exist for
        a sport outside *the sports she holds a rating at*.
        """

        rows = await self._offered.for_player(player_id=viewer, now=now)
        live = [
            row
            for row in rows
            if sport is None or row.record.sport is sport
            if is_still_there(row, now=now)
        ]
        return OffersRegion(
            stamp=stamp,
            cards=tuple(
                offer_card_of(row, now=now, stamp=stamp)
                for row in sorted(live, key=lambda row: _order(row))
            ),
        )


def is_still_there(row: OfferedSeat, *, now: Instant) -> bool:
    """Whether this seat is one she could take right now.

    The cascade's own four seat rules, asked a second time and by the same
    function. A region that decided *the match is full* by its own arithmetic
    would eventually disagree with the pool that wrote the offer, and the visible
    symptom is a card offering a seat the aggregate refuses.
    """

    return not seat_exclusions(
        row.record, already_mine=row.already_mine, now=now
    )


def _order(row: OfferedSeat) -> tuple[Instant, Instant, str]:
    """Soonest-to-expire, then when she was told, then the match.

    The second and third comparators are load-bearing for ``FEED_ORDER``'s own
    reason: without a total final key the order is the query plan, and two
    identical requests reshuffle the region under her thumb. Two seats in one
    club's evening share a cutoff to the second, so the first tie-break is real
    rather than theoretical — and *which she heard about first* is the only
    ordering between two equally-dying seats that means anything to her.
    """

    return (seat_expires_at(row.record), row.offered_at, str(row.match_id))


def offer_card_of(row: OfferedSeat, *, now: Instant, stamp: Stamp) -> MatchCard:
    """One offer as the card a phone draws, and the **only** place one is built.

    A module-level function on ``compose_enrolled.card_of``'s rule: taking a seat
    hands back the card it was about, and a screen a player is corrected onto
    cannot describe the match differently from the card she tapped. A second
    transcription would be two answers to *what is this match doing*.
    """

    record = row.record
    resolved = situation(record, _viewer(row, now=now), now)
    return MatchCard(
        match_id=row.match_id,
        stamp=stamp,
        where=row.where,
        # **The price at this instant and not the one on the offer row.** They
        # differ exactly when the rescue deadline passed between the telling and
        # the tap, and ADR-0061 makes that a real change she is entitled to see:
        # a card quoting the older, dearer number would take her money at a price
        # the platform has since stopped charging.
        price=Money(
            amount=grosze(int(seat_price(record, SeatShare(row.share.amount), now))),
            currency=row.share.currency,
        ),
        situation=SituationHalf(
            situation=resolved,
            facts=SituationFacts(
                counts=counts_of(record, now=now),
                court_total=row.court_total,
                hold=hold_note(record, now=now),
                court=_court(row, now=now),
                # A cause needs a cancellation she is being told about rather
                # than one she is being offered a seat in; a refund needs money
                # she put in; a score needs a match she played; a departure needs
                # a seat she held. An **owner's exposure** is the one that could
                # be composed and must not be: it is what a private court's buyer
                # has at stake, and she is not the buyer — a card offering her a
                # seat would be printing somebody else's liability.
            ),
        ),
        clock=card_clock(record, now),
        act=_act(resolved),
        # The kernel's own answer rather than a literal ``False``. She holds
        # neither a seat nor a claim, so it is false today for two reasons at
        # once; writing the constant would be the one card in the product whose
        # exit control is decided by a transcription instead of by the function
        # ``Match.depart`` refuses on.
        may_depart=may_depart(record, now, holds_seat=False, holds_claim=False),
    )


def _viewer(row: OfferedSeat, *, now: Instant) -> Viewer:
    """The viewer the ladder is handed — with the offer, exactly while it stands.

    **This is the refusal path.** Rung 6 answers ``seatOffered`` / ``seatOpened``
    for anybody carrying an offer and does not look at whether the match is full,
    deliberately: it is above the queue that produced it because *telling her she
    is still queueing while the seat is hers to take* is the sentence that makes
    standby worthless. So the judgement about whether the seat is still hers to
    take belongs **here**, and it is made once — an offer on a seat somebody else
    took is handed over as no offer at all, and the ladder then answers what the
    match is actually doing.

    ``on_standby`` is deliberately absent. Rung 7 is below rung 6, so a queued
    player carrying a live offer resolves to the offer either way; and with the
    offer withdrawn the honest sentence about a filled match is *it is full*
    rather than *you are still queueing for it*, which is what the region above
    would otherwise be correcting her onto.
    """

    return Viewer(
        holds_seat=False,
        offer=row.kind if is_still_there(row, now=now) else None,
    )


def _act(resolved: Situation) -> ActCode | None:
    """Which act this card names, off the one table (ADR-0083).

    Read out of ``ACT_OF`` rather than written as ``TAKE_SEAT`` here, because the
    card composed for a seat that has **gone** must not name it: that card no
    longer resolves to an offer situation, so the table answers nothing and the
    button disappears without a second rule saying when it should.
    """

    return ACT_OF.get(resolved)


def _court(row: OfferedSeat, *, now: Instant) -> str | None:
    """The specific court, and only once it is hers to know.

    ``kernel.court_named_at`` is fifteen minutes before play. Unlike a shelf card
    — which can never reach that window, because eligibility stops at the join
    cutoff — an offer *can*: a club publishing a short cutoff leaves a seat
    takeable inside the naming window, and a player racing for a seat starting in
    ten minutes is exactly who wants the court number.
    """

    if now < court_named_at(row.record.start):
        return None
    return row.court


def offered_matches(region: OffersRegion) -> frozenset[UUID]:
    """Which matches this region is already speaking for.

    Handed to the enrolled strip so that one match is one card. The overlap is
    real and it is rung 1's own audience: a player on a match's standby queue is
    the **first** person the cascade tells, and she then holds both a queue place
    — the strip's fourth membership — and a live offer. The ladder has already
    decided which sentence wins, by putting the seat above the queue that
    produced it; this is that decision applied to the screen rather than to one
    card, since two regions cannot each apply it to their own.
    """

    return frozenset(card.match_id for card in region.cards)
