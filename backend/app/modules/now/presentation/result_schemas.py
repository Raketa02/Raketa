"""The wire shape of the result route: ADR-0074's screen, and Now's update.

**It reuses Now's objects rather than declaring its own.** The place, the money,
the seat counting, the scoreline and the whole situation half are the *same*
models ``GET /api/v1/now`` sends, so a client narrows one union and draws one
card body on two screens. Two definitions of *where and when* is how two answers
come to disagree.

**It is not a card.** No fit badge, no emphasis flag, no card stamp — all three
are judgements the composition made about a card's *place on Now*, and none of
them means anything on a screen with one thing on it.

**No ``phase`` and no version.** The situation says which of ADR-0060's five
renderings this is; a version would make the phone hold a rule about its own
staleness and buy a distinction the player cannot act on differently.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.now.application.result import ResultAnswer
from app.modules.now.domain.result import ResultBlock, ResultScreen
from app.modules.now.presentation.schemas import (
    MoneyResponse,
    NowUpdateResponse,
    PlaceResponse,
    ScoreLineResponse,
    SeatCountsResponse,
    SituationHalfResponse,
)


#: One side's count in one set or game. Non-negative because a negative one is
#: not a number a pad can produce, and three digits because the pads top out at
#: 21 — this is the door, not the rule. The rule is the server's permissive
#: validator, which knows the sport.
Games = Annotated[int, Field(ge=0, le=999)]


class ResultBlockResponse(BaseModel):
    """What is on the table, and who has spoken. Four facts and no history.

    **Always present and empty when nothing is on the table** — an empty score
    and a zero count on `needsResult`, never an absent object. It makes no
    claim, so it follows a region's rule rather than a shelf's, and *not there*
    and *there and empty* cannot then be handled in one place and not the other.

    **No history.** A counter *replaces* what was on the table; printing the
    score it beat invites arguing with a number that is no longer live, and none
    of the five renderings draws a timeline.
    """

    # Whether this score has settled — by an opponent's tap or by the silence
    # that confirms it. ADR-0048 makes those one outcome, so there is one field.
    agreed: bool
    # How many **sides** have spoken, capped at two. Never how many taps there
    # were: replacing your own side's live score is a correction, and ADR-0048
    # says in as many words that it is not one of the attempts.
    proposals: int
    # `null` when nothing is on the table, which is the only thing its absence
    # can mean. The viewer's side is `sides[0]` and `first` in every set, the
    # same flip the card's scoreline makes.
    score: ScoreLineResponse | None = None
    # Which side put it there, as an index into `score.sides` — so `0` is always
    # *your side* and the phone derives nothing to know whose score it is
    # reading. A side and never a player: proposals are capped per side, and
    # naming the teammate who typed it would put a person into an argument the
    # model holds between two halves of a net.
    proposed_by: int | None = None

    @classmethod
    def from_domain(cls, block: ResultBlock) -> "ResultBlockResponse":
        return cls(
            agreed=block.agreed,
            proposals=block.proposals,
            score=(
                None
                if block.score is None
                else ScoreLineResponse.from_domain(block.score)
            ),
            proposed_by=block.proposed_by,
        )


class ResultScreenResponse(BaseModel):
    """The result conversation, for one viewer, at one instant."""

    match_id: UUID
    where: PlaceResponse
    # The seat's amount: her own share inside this match. The court's total is
    # beside it in the situation half, where it has no audience at all.
    price: MoneyResponse
    situation: SituationHalfResponse

    result: ResultBlockResponse
    # The reasons printed beside the conversation. They ride here rather than
    # only inside the situation half because that half is the one a phone reads
    # only when it knows the name, and a fact the screen always draws cannot
    # live only in the half that may be skipped.
    counts: SeatCountsResponse

    # **Three server booleans, and the phone derives none of them** (ADR-0074).
    # Not a generic list of act codes: that invents a vocabulary to describe
    # three things nothing else in the product reads. ADR-0048's cap — a side
    # proposes once — and its exclusions — never a leaver, never a standby
    # player — are enforced in one place rather than mirrored onto two clients
    # that will drift.
    #
    # *May put my side's score up*: the first entry and a correction of my own
    # side's live one are one act at two moments, and which of the two this
    # would be is the rule the phone does not hold.
    may_enter: bool
    # *May agree with what is on the table.* Opposing side only, and one
    # opponent suffices: a teammate agreeing with a teammate proves nothing.
    may_accept: bool
    # *May put a different score up against it.* False once my side has spoken,
    # because from two proposals only an explicit acceptance settles it.
    may_counter: bool

    # **The hero clock** (ADR-0060): when this conversation ends by itself — the
    # live proposal's own deadline once there is one, and the entry deadline
    # before that. `null` once the answer is in: a settled result and an
    # unscored evening count to nothing rather than to zero.
    settlement_deadline: datetime | None = None
    # **The second, quieter line, present only while it runs.** Inside it a
    # counter beats a pending acceptance, so a screen that hid it would say
    # *settled* half an hour early — which is the outcome ADR-0048 built the
    # grace to prevent, inverted.
    acceptance_grace: datetime | None = None

    @classmethod
    def from_domain(cls, screen: ResultScreen) -> "ResultScreenResponse":
        return cls(
            match_id=screen.match_id,
            where=PlaceResponse.from_domain(screen.where),
            price=MoneyResponse.from_domain(screen.price),
            situation=SituationHalfResponse.from_domain(screen.situation),
            result=ResultBlockResponse.from_domain(screen.result),
            counts=SeatCountsResponse.from_domain(screen.counts),
            may_enter=screen.may_enter,
            may_accept=screen.may_accept,
            may_counter=screen.may_counter,
            settlement_deadline=screen.settlement_deadline,
            acceptance_grace=screen.acceptance_grace,
        )


class ResultWriteResponse(BaseModel):
    """A write's answer: its own screen, and Now's update, in one response.

    ADR-0074's rule, and this is the route it was written for. **The refusal
    path returns this too**: a stale accept comes back as the counter's
    situation with `may_accept` false, and the player *sees* the correction
    rather than being told it.
    """

    screen: ResultScreenResponse
    update: NowUpdateResponse

    @classmethod
    def from_domain(cls, answer: ResultAnswer) -> "ResultWriteResponse":
        return cls(
            screen=ResultScreenResponse.from_domain(answer.screen),
            update=NowUpdateResponse.from_domain(answer.update),
        )


class ProposeScoreRequest(BaseModel):
    """*This is what we played*, as sets of two integers and never a string.

    **The viewer's side first**, which is the order the screen showed her: the
    server puts her side first on the way out, so the same order coming back is
    the one thing that cannot be misread. Which player each integer belongs to
    is the seats' business and hers is not on the wire at all.

    One body for entering, correcting and countering: they are one act at three
    moments and the server is what tells them apart. A field naming which the
    client thought this was would be the phone holding ADR-0048's cap.
    """

    # Bounded here as a **shape** and never as a rulebook. A pair of
    # non-negative integers is what a set is; whether 7-6 is a real padel set is
    # the server's permissive validator, which declines the obviously impossible
    # and nothing else. The bounds below only stop a body that could not be
    # drawn on any pad from reaching a domain type that raises rather than
    # refuses.
    sets: list[tuple[Games, Games]] = Field(min_length=1, max_length=16)

    def pairs(self) -> tuple[tuple[int, int], ...]:
        return tuple((one[0], one[1]) for one in self.sets)
