"""**On request: the club confirms** (#543; the mechanics §16.3, §16.8, §16.16;
the screens B2, B4; ``docs/adr/0189`` §3).

At an On request club a full game waits for the club's answer, and nobody pays
until it accepts. This is the club's side of that wait, and the clock's:

- **what waits** — every game at the club still waiting for its answer, the one
  due first, first, with the players' Names and the countdown: the Overview's
  *waiting for your answer* and the Bookings page's *Waiting for you*. A
  request whose deadline has passed is not on it: it can no longer be
  answered, whether or not the timeout has recorded it yet;
- **Accept** — everybody is charged now, all together or not at all, on the
  court held for the answer; the game is booked and its Game and chat open. A
  share that cannot be held **waits for its player** (#626; Q109, Q112): the
  club's yes and the court are kept for their time to pay, and the payment in
  time books it without asking the club again — or, the game's book-by having
  come, there is no time left and it is called off at once. A pair In that
  stopped fitting while it waited opens a seat instead: nobody pays, the
  request is off, and the game is filling again — the club is asked again once
  it is full;
- **Refuse**, with the club's own note, and **no answer** by the deadline —
  the timeout job's: *Called off · refused* or *· no answer*, nobody paid, the
  court the club's again, and **the same players dealt a new card first** — by
  the proposer, which the game's turning down makes due (``propose_games.py``).

**Every act locks the game first**, as a yes does, so a club's answer, a
player's leaving and the timeout arriving together are one after another; and
each is one transaction.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant, invariant
from app.modules.proposals.application.fill import Fill
from app.modules.proposals.domain.errors import (
    BookingNotFound,
    RequestNotWaiting,
    RequestTimedOut,
)
from app.modules.proposals.domain.ports import (
    ClubRequest,
    ClubRequests,
    PlayerNames,
    ProposalRepository,
    UndecidedCharges,
)
from app.modules.proposals.domain.proposal import ClubAnswer, Proposal

#: The longest note a club may keep with a refusal — a line, not a letter.
REFUSAL_REASON_MAX = 200


@final
@dataclass(frozen=True, slots=True)
class WaitingRequests:
    #: The instant the list was read at — what each countdown runs from.
    read_at: Instant
    #: The one due first, first.
    requests: tuple[ClubRequest, ...]
    #: Each player's Name; an account that can no longer be named is absent.
    names: Mapping[UUID, str]


@final
class ReadWaitingRequests:
    def __init__(
        self, *, requests: ClubRequests, names: PlayerNames, clock: Clock
    ) -> None:
        self._requests = requests
        self._names = names
        self._clock = clock

    async def execute(self, club_id: UUID) -> WaitingRequests:
        now = instant(self._clock.now())
        waiting = tuple(
            request
            for request in await self._requests.waiting_at(club_id)
            if now < request.answer_by
        )
        names = await self._names.names_of(
            {player for request in waiting for player in request.players}
        )
        return WaitingRequests(read_at=now, requests=waiting, names=names)


class AcceptOutcome(StrEnum):
    """What the club's yes came to."""

    #: Everybody paid and the game is booked.
    BOOKED = "BOOKED"
    #: A share could not be held: the yes and the court are kept while its
    #: player has time to pay (#626).
    WAITING_FOR_A_PAYMENT = "WAITING_FOR_A_PAYMENT"
    #: A share could not be held and no time was left to pay — the game's
    #: book-by had come: called off, nobody paid (#626).
    CALLED_OFF = "CALLED_OFF"
    #: A pair In stopped fitting: nobody paid, a seat is open and the game is
    #: filling again.
    SEAT_OPENED = "SEAT_OPENED"


@final
@dataclass(frozen=True, slots=True)
class Acceptance:
    outcome: AcceptOutcome
    #: The court the players were given — on a booked game only.
    court_name: str | None
    #: When the payment the yes waits on is due — waiting for one only.
    pay_by: Instant | None = None


@final
class AcceptTheRequest:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        requests: ClubRequests,
        fill: Fill,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._requests = requests
        self._fill = fill
        self._uow = uow
        self._clock = clock

    async def execute(self, *, club_id: UUID, booking_id: UUID) -> Acceptance:
        now = instant(self._clock.now())
        proposal, request = await _a_waiting_request(
            self._proposals, self._requests, club_id, booking_id, now=now
        )
        outcome = await self._fill.accept(proposal, request, now=now)
        await self._proposals.save(proposal)
        await self._uow.commit()
        if outcome.booked is not None:
            return Acceptance(
                outcome=AcceptOutcome.BOOKED, court_name=request.court_name
            )
        if outcome.paying_until is not None:
            return Acceptance(
                outcome=AcceptOutcome.WAITING_FOR_A_PAYMENT,
                court_name=None,
                pay_by=outcome.paying_until,
            )
        if outcome.called_off:
            return Acceptance(outcome=AcceptOutcome.CALLED_OFF, court_name=None)
        return Acceptance(outcome=AcceptOutcome.SEAT_OPENED, court_name=None)


@final
class RefuseTheRequest:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        requests: ClubRequests,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._requests = requests
        self._undecided = undecided
        self._uow = uow
        self._clock = clock

    async def execute(
        self, *, club_id: UUID, booking_id: UUID, reason: str | None
    ) -> None:
        now = instant(self._clock.now())
        proposal, _ = await _a_waiting_request(
            self._proposals, self._requests, club_id, booking_id, now=now
        )
        await _turn_down(
            proposal,
            ClubAnswer.REFUSED,
            reason=_a_note(reason),
            proposals=self._proposals,
            requests=self._requests,
            undecided=self._undecided,
            at=now,
        )
        await self._uow.commit()


@final
@dataclass(frozen=True, slots=True)
class Unanswered:
    """What one timeout run recorded, and how many another process reached
    first."""

    requests: int
    conflicts: int


@final
class ExpireUnansweredRequests:
    """**No answer by the deadline** (the mechanics §16.16: *the club forgets to
    answer a request — it expires*). The job's.

    **Correctness depends on it**, unlike the book-by sweep's: until it runs, an
    unanswered game holds its court and owes its players nothing — every read
    already refuses an answer past the deadline, but only this calls the game
    off, frees the court and makes the players due a new card. **One
    transaction per request**, over a clock-derived list in one order on every
    process, so a version conflict is counted and stepped over."""

    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        requests: ClubRequests,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._requests = requests
        self._undecided = undecided
        self._uow = uow
        self._clock = clock

    async def execute(self) -> Unanswered:
        now = instant(self._clock.now())
        recorded = conflicts = 0
        for booking_id in await self._requests.unanswered(now=now):
            try:
                if await self._time_out(booking_id, now=now):
                    await self._uow.commit()
                    recorded += 1
                else:
                    await self._uow.rollback()
            except EventStreamVersionConflict:
                await self._uow.rollback()
                conflicts += 1
        return Unanswered(requests=recorded, conflicts=conflicts)

    async def _time_out(self, booking_id: UUID, *, now: Instant) -> bool:
        proposal = await self._proposals.load_for_update(booking_id)
        request = await self._requests.find(booking_id)
        if (
            proposal is None
            or request is None
            or not request.waiting
            or now < request.answer_by
            or not proposal.waiting_for_the_club
        ):
            return False
        await _turn_down(
            proposal,
            ClubAnswer.NO_ANSWER,
            reason=None,
            proposals=self._proposals,
            requests=self._requests,
            undecided=self._undecided,
            at=now,
        )
        return True


async def _a_waiting_request(
    proposals: ProposalRepository,
    requests: ClubRequests,
    club_id: UUID,
    booking_id: UUID,
    *,
    now: Instant,
) -> tuple[Proposal, ClubRequest]:
    """The game, locked, and its request — refused unless it is this club's
    and still waiting for its answer."""

    proposal = await proposals.load_for_update(booking_id)
    request = await requests.find(booking_id)
    if proposal is None or request is None or request.club_id != club_id:
        raise BookingNotFound()
    if not request.waiting:
        raise RequestNotWaiting()
    if now >= request.answer_by:
        raise RequestTimedOut()
    invariant(
        proposal.waiting_for_the_club,
        f"{booking_id} waits for its club with a seat open",
    )
    return proposal, request


async def _turn_down(
    proposal: Proposal,
    answer: ClubAnswer,
    *,
    reason: str | None,
    proposals: ProposalRepository,
    requests: ClubRequests,
    undecided: UndecidedCharges,
    at: Instant,
) -> None:
    """Called off, nobody paid: the game is over and its people owed a new
    card first, the court is the club's again, and a payment a player had
    confirmed for it is let go."""

    proposal.turn_down(answer, at=at)
    await proposals.save(proposal)
    await requests.turn_down(proposal.proposal_id, answer=answer, reason=reason, at=at)
    await undecided.release(proposal.proposal_id, keeping=(), at=at)


def _a_note(reason: str | None) -> str | None:
    """The club's note as it is kept: trimmed, and nothing for a blank one."""

    if reason is None:
        return None
    trimmed = reason.strip()
    return trimmed[:REFUSAL_REASON_MAX] or None
