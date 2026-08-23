"""The wire shape of the departure route: ADR-0086's screen, and Now's update.

**It reuses Now's objects rather than declaring its own.** The place, the money,
the seat counting and the whole situation half are the *same* models
``GET /api/v1/now`` sends, so a client narrows one union and draws one card body
on two screens. ADR-0074's argument against repeating a fact in two answers
applies to shapes too: two definitions of *where and when* is how two answers
come to disagree.

**It is not a card.** No fit badge, no emphasis flag, no card stamp — all three
are judgements the composition made about a card's *place on Now*, and none of
them means anything on a screen with one thing on it. What the screen keeps is
the spine's four facts and the situation half.

**No ``phase`` field**, deliberately and per ADR-0086: the four standings already
say which phase she is in, and a phase name would be a second vocabulary
answering a question already answered.

**Nothing here mentions transferring a seat.** It is the leaver's best outcome
and it belongs to the invite flow, which is out of scope — *"advertising a door
that is not there is worse than the gap."*
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.kernel import Outcome

from app.modules.now.application.departure import DepartureAnswer
from app.modules.now.domain.departure import DepartureScreen, OutcomeRow
from app.modules.now.domain.screen import NowUpdate
from app.modules.now.domain.vocabulary import OutcomeStanding
from app.modules.now.presentation.schemas import (
    MatchCardResponse,
    MoneyResponse,
    PlaceResponse,
    SeatCountsResponse,
    SituationHalfResponse,
)


class OutcomeRowResponse(BaseModel):
    """One of the four outcomes, and where it stands right now.

    ``opens_at`` is present **exactly** on ``opens`` and on no other standing.
    The phone subtracts it and derives nothing else (ADR-0053); a moment beside
    *spent* would be a moment nothing counts to, and a row that is *still
    possible* has none to give, which is precisely what distinguishes it.
    """

    outcome: Outcome
    standing: OutcomeStanding
    opens_at: datetime | None = None

    @classmethod
    def from_domain(cls, row: OutcomeRow) -> "OutcomeRowResponse":
        return cls(outcome=row.outcome, standing=row.standing, opens_at=row.opens_at)


class DepartureScreenResponse(BaseModel):
    """What leaving is worth right now, and what it could still become."""

    match_id: UUID
    # The one clock slot, carried because the spine carries one and a screen
    # about a deadline should not be the place it goes missing. Empty on a card
    # that is over or cancelled — those count to nothing rather than to zero.
    clock: datetime | None = None
    where: PlaceResponse
    # The seat's amount: her own share inside this match, which is the figure the
    # outcomes are percentages of. One number and never a second copy of it under
    # another name — the court's total is beside it in the situation half, where
    # it has no audience at all.
    price: MoneyResponse
    situation: SituationHalfResponse

    # **A server boolean, and the phone derives none of it** (ADR-0086). False
    # after the match starts, under ADR-0046's private-court lock, for a leaver
    # who has already left, for a viewer holding a live seat claim, and for a
    # match that has been cancelled.
    may_depart: bool
    # The **one live outcome** and never the set: the ordering is defined over
    # single labels, so quoting the table would make the refuse-if-worse rule
    # compare sets.
    quote: Outcome
    # All four, always — two on a private court, where only those two are
    # reachable. A table that quietly drops *forfeited* once it is unreachable
    # is also a table that never showed it while it was.
    outcomes: list[OutcomeRowResponse]
    # The quote's reasons, drawn beside it. They ride here rather than only
    # inside the situation half because that half is the one a phone reads only
    # when it knows the name, and a fact the screen always draws cannot live
    # only in the half that may be skipped.
    counts: SeatCountsResponse
    # `None` on a private court, and that is the fact rather than a gap: the
    # court was bought at booking, so there is no commitment for a deadline to
    # be about.
    commitment_deadline: datetime | None = None

    @classmethod
    def from_domain(cls, screen: DepartureScreen) -> "DepartureScreenResponse":
        return cls(
            match_id=screen.match_id,
            clock=screen.clock,
            where=PlaceResponse.from_domain(screen.where),
            price=MoneyResponse.from_domain(screen.price),
            situation=SituationHalfResponse.from_domain(screen.situation),
            may_depart=screen.may_depart,
            quote=screen.quote,
            outcomes=[OutcomeRowResponse.from_domain(row) for row in screen.outcomes],
            counts=SeatCountsResponse.from_domain(screen.counts),
            commitment_deadline=screen.commitment_deadline,
        )


class NowUpdateResponse(BaseModel):
    """What Now needs to correct itself off the player's own tap (ADR-0070).

    **One card and nothing else, today.** A departure returns the card *changed,
    in place* — same match, same region, new rendering — so neither viewer-owned
    region's contents or order moves and there is nothing for a region slot to
    hold. The first action that moves one is taking a seat, and shipping the
    slots ahead of it would be the *"two fields with no reader"* ADR-0071
    refuses. The shelves are never in an update at all.
    """

    card: MatchCardResponse

    @classmethod
    def from_domain(cls, update: NowUpdate) -> "NowUpdateResponse":
        return cls(card=MatchCardResponse.from_domain(update.card))


class DepartureWriteResponse(BaseModel):
    """A write's answer: its own screen, and Now's update, in one response.

    ADR-0074's rule, and this is the second act to take it up. Recomposing on
    the pop was refused there — every ask pays the full funnel, and paying it on
    a return from a screen the server has just finished computing is a cost
    bought for tidiness.

    **The refusal path returns this too.** A quote that has fallen, a match that
    has started, a second tap by somebody who has already left: all of them come
    back as what a success returns, which is what is true now.
    """

    screen: DepartureScreenResponse
    update: NowUpdateResponse
    # What this tap **did**: the outcome the departure was made at, and `null`
    # exactly when nothing was applied. It is the one field here that is a fact
    # about the command rather than about the match, and it exists so that *was
    # I refused* is not a rule on the phone — deriving it from `may_depart`
    # still being true would be one, and ADR-0053 leaves the phone none.
    #
    # On a **replay** it is the outcome she got the first time, off ADR-0030's
    # command log rather than off the aggregate: what happened, not what leaving
    # would be worth now.
    applied: Outcome | None = None

    @classmethod
    def from_domain(cls, answer: DepartureAnswer) -> "DepartureWriteResponse":
        return cls(
            screen=DepartureScreenResponse.from_domain(answer.screen),
            update=NowUpdateResponse.from_domain(answer.update),
            applied=answer.applied,
        )


class DepartRequest(BaseModel):
    """*Leave*, at the outcome she was looking at, under her own request key.

    ``quote`` is a **label and never an amount** (ADR-0033). An amount moves for
    reasons that have nothing to do with leaving — a discount landing, a club
    price change — and refusing on those is noise; the label is what she was
    shown as the basis for deciding.

    ``idempotency_key`` is generated by the client and is **not** the version
    ADR-0074 refused. A version would make the phone hold a rule about its own
    staleness; a key encodes no rule and states no belief about freshness, and
    it answers the one case a version could not — a phone that loses the answer
    to a departure it already made.
    """

    quote: Outcome
    idempotency_key: str = Field(min_length=1, max_length=128)
