"""*Fill the seats.* The send's five facts, on a court that already exists.

**The half of ``Challenge.invite`` that was written and never called**
(``docs/adr/0150``). The aggregate has always known how to grow a court — keep
everybody already in on whichever side the new arrangement gives them, refuse to
remove somebody who accepted, refuse a send with nobody new, date each newly
seated player from the moment of the invite — and until now nothing in ``app/``
reached it.

**It is the send one screen later, and it re-verifies the same five facts.** Four
are the fail-closed gates and they are untouched: somebody blocked, held,
deactivated or newly incompatible since they accepted still falls out, and the
refusal names nobody. The fifth is the open-challenge pair rule, and it is the
one thing that changes — this court's own pairs are excepted by id, because
otherwise every fill would be refused for the arrangement it is made of
(``docs/adr/0150`` §3).

**Origins are resolved for the newly seated only.** The people already in came
from somebody else's search, possibly weeks ago, and ``_still_in`` raises if a
plan carries an origin for one of them — so asking this search where they sat
would be asking about people it never showed.

**Any live member may press it; only the organiser may withdraw.** Growing a
court and ending one are different acts and get different permissions. The case
that decides it is the mutual-born doubles challenge: ``LINE_UP_INCOMPLETE`` from
birth, both players on side A, and an "organiser" who is only whoever's yes
arrived second — making that arbitrary tiebreak the only person who can finish
the four would leave the other looking at a court they can neither complete nor
leave.

**Whole-court, never per-seat, and a refusal writes nothing.** The same rule the
send keeps and for the same reason: a partial fill that silently dropped one
invitee would hand the court an arrangement nobody chose.

**The window is not re-stamped and the deadlines are not inherited.**
``SeatsInvited`` carries no window — re-stamping would move a fact other people
have already answered against — and ``_seat_from`` dates each new seat from this
moment, so a seat filled later starts its own day.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant
from app.modules.challenges.application.challenge_of_yours import AChallengeOfYours
from app.modules.challenges.application.commands import (
    FillSeatsCommand,
    SeatChoice,
)
from app.modules.challenges.application.court_safety import CourtSafety
from app.modules.challenges.application.read_challenges import StandingChallenge
from app.modules.challenges.domain.challenge import Challenge, refuse_a_bad_court
from app.modules.challenges.domain.errors import (
    AnOpenChallengeStandsWithThisPair,
    TheCourtDidNotComeFromThatSearch,
    TheFillIsTheLiveMembers,
    TheLineUpIsNoLongerSendable,
)
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.challenges.domain.ports import (
    ChallengeRepository,
    CourtOrigin,
    OpenChallengeQuery,
    OriginSearchQuery,
    PlayerHandles,
)
from app.modules.challenges.domain.seats import SeatPlan
from app.shared.domain.errors import AccountHeld


@final
class FillSeats(AChallengeOfYours):
    """One press: the open seats filled, or the whole fill refused."""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        handles: PlayerHandles,
        open_challenges: OpenChallengeQuery,
        origins: OriginSearchQuery,
        safety: CourtSafety,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        super().__init__(
            challenges=challenges, handles=handles, uow=uow, clock=clock
        )
        self._open_challenges = open_challenges
        self._origins = origins
        self._safety = safety

    async def execute(self, command: FillSeatsCommand) -> StandingChallenge:
        """Grow the court, or refuse the whole fill. Answers with it as it stands.

        **The order below is the design**, and it is the send's own with the
        challenge read first — which it has to be, because who the organiser is,
        who is already seated and what shape the court must be are all facts on
        the aggregate rather than on the request.
        """

        at = instant(self._clock.now())

        # 1. A challenge of theirs, and then a seat of theirs that is still live.
        #    The two are different questions and the refusals differ: a stranger
        #    is told no challenge of theirs has that id, and somebody who
        #    declined is told the fill belongs to the people still on the court —
        #    they can already see it, so hiding it would be the wrong lie.
        challenge = await self._yours(command.challenge_id, command.player_id)
        still_in = self._live_on(challenge, at)
        if command.player_id not in still_in:
            raise TheFillIsTheLiveMembers()

        # 2. The shape of the court, before anything else is read at all. The
        #    aggregate owns the rule and runs it again; what is here is the
        #    **order**, exactly as it is on the send.
        refuse_a_bad_court(
            [choice.player_id for choice in command.court],
            organiser_id=challenge.organiser_id,
        )

        # 3. Their own hold, with the same code a search returns. About the
        #    caller and nobody else, so it is asked before a single fact about
        #    another person is read.
        if command.player_id in await self._safety.held_among([command.player_id]):
            raise AccountHeld("this account is under a hold")

        # 4. The search this fill was built on, for the **newly seated only**.
        #    Everybody already in came from somewhere else, and a plan carrying
        #    an origin for one of them is refused by the aggregate.
        newly_seated = self._newly_seated(command, still_in)
        origin = await self._origin_of(command, newly_seated)

        # 5. The two about everybody else, both read before either is judged —
        #    a press that fixed one and was refused for the other is the same
        #    interruption twice. **This court's own challenge is excepted**, and
        #    it is the only one: an open challenge between two of these people
        #    that is not this one still refuses.
        on_the_court = frozenset(
            choice.player_id
            for choice in command.court
            if choice.player_id is not None
        )
        admitted = await self._safety.admits(on_the_court)
        pairs = await self._open_challenges.open_pairs_among(
            on_the_court, now=at, except_challenge_id=challenge.id
        )
        if not admitted:
            raise TheLineUpIsNoLongerSendable(
                "Somebody on this court can no longer be invited to it"
                + (", and an open challenge already stands on it." if pairs else ".")
            )
        if pairs:
            raise AnOpenChallengeStandsWithThisPair()

        challenge.invite(
            self._arrangement(command, origin, still_in), occurred_at=at
        )
        return await self._committed(
            challenge, await self._written(challenge, at), at
        )

    @staticmethod
    def _live_on(challenge: Challenge, at: Instant) -> frozenset[UUID]:
        """Everybody still in this game through a seat of their own.

        Read off the seats rather than off the standing, because it is the set
        ``invite`` itself keeps: these are the people who may not be removed, and
        everybody else named on the court is somebody new being asked.
        """

        return frozenset(
            seat.player_id
            for seat in challenge.seats
            if seat.player_id is not None and seat.is_live_at(at)
        )

    @staticmethod
    def _newly_seated(
        command: FillSeatsCommand, still_in: frozenset[UUID]
    ) -> frozenset[UUID]:
        """Who this fill is actually inviting. **The court, minus the court.**"""

        return frozenset(
            choice.player_id
            for choice in command.court
            if choice.player_id is not None and choice.player_id not in still_in
        )

    async def _origin_of(
        self, command: FillSeatsCommand, newly_seated: frozenset[UUID]
    ) -> CourtOrigin:
        """What the cited search says about the people being newly asked.

        The sport, the mode and the window on the answer are **read and
        discarded**: this challenge already holds all three, and a fill that
        adopted the search's would be re-stamping facts other people have already
        answered against. What is used is ``positions``, which is the other half
        of every new seat's origin key.

        The caller is left out of the question for the reason a send leaves the
        organiser out: a search never returns its own searcher.
        """

        origin = await self._origins.court_origin(
            search_id=command.search_id,
            organiser_id=command.player_id,
            invitee_ids=newly_seated,
        )
        if origin is None:
            raise TheCourtDidNotComeFromThatSearch()
        return origin

    @staticmethod
    def _arrangement(
        command: FillSeatsCommand,
        origin: CourtOrigin,
        still_in: frozenset[UUID],
    ) -> tuple[SeatPlan, ...]:
        """The court as the aggregate takes it: an origin on the new seats alone.

        **Per seat, never per challenge**, exactly as a send builds one — three
        invitees drawn from one search at three positions are three origins with
        three positions, and the position is what the telemetry join needs.
        """

        def plan(choice: SeatChoice) -> SeatPlan:
            if choice.player_id is None or choice.player_id in still_in:
                return SeatPlan(side=choice.side, player_id=choice.player_id)
            return SeatPlan(
                side=choice.side,
                player_id=choice.player_id,
                origin=SentFromSearch(
                    search_id=command.search_id,
                    position=origin.positions[choice.player_id],
                ),
            )

        return tuple(plan(choice) for choice in command.court)


__all__ = ["FillSeats"]
