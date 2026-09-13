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

**And the cited search has to be for this challenge's sport.** A send's sport is
the origin's, so it has nothing to check; here the sport is the *challenge's*, and
padel and badminton both seat four — without the check a filler could seat people
off a search this court's own gates never judged.

**Any live member may press it; ending a court is a different act with a
different permission** — removing a court that was never a game is the
organiser's while nobody has joined and nobody's once somebody has, and calling
off the game a court became is any player's on it (``docs/adr/0165`` §4–§5).
Growing a court and ending one get different permissions. The case
that decides it is the mutual-born doubles challenge: ``LINE_UP_INCOMPLETE`` from
birth, both players on side A, and an "organiser" who is only whoever's yes
arrived second — making that arbitrary tiebreak the only person who can finish
the four would leave the other looking at a court they could neither complete
nor leave. **They can leave now** (``docs/adr/0162``), and the same fill is how a
court somebody left is completed: the organiser's seat is required on the posted
court only while the organiser is still on it.

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
from app.kernel import Clock, Instant, Sport, instant
from app.modules.challenges.application.challenge_of_yours import AChallengeOfYours
from app.modules.challenges.application.commands import FillSeatsCommand
from app.modules.challenges.application.court_safety import CourtSafety
from app.modules.challenges.application.court_verification import (
    CourtVerification,
    everybody_on,
    newly_asked,
    seats_of,
)
from app.modules.challenges.application.seat_change import (
    refuse_a_court_closed_to_seating,
)
from app.modules.challenges.application.read_challenges import StandingChallenge
from app.modules.challenges.domain.challenge import Challenge, refuse_a_bad_court
from app.modules.challenges.domain.errors import (
    TheCourtDidNotComeFromThatSearch,
    TheFillIsTheLiveMembers,
)
from app.modules.challenges.domain.ports import (
    ChallengeRepository,
    CourtOrigin,
    OpenChallengeQuery,
    OriginSearchQuery,
    PlayerHandles,
)
from app.modules.challenges.domain.seatable_game import SeatableGameQuery


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
        games: SeatableGameQuery,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        super().__init__(
            challenges=challenges, handles=handles, uow=uow, clock=clock
        )
        self._origins = origins
        self._games = games
        self._court = CourtVerification(
            safety=safety, open_challenges=open_challenges
        )

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
            organiser_id=challenge.organiser_seat_required(at),
        )

        # 3. Their own hold, with the same code a search returns. About the
        #    caller and nobody else, so it is asked before a single fact about
        #    another person is read.
        await self._court.refuse_a_held_caller(command.player_id)

        # 3b. On a court that has been a game, and only there: whether its seats
        #     may still change (``docs/adr/0162`` §4). A game that has happened
        #     or never will, and one whose agreed moment has passed, both
        #     refuse — a newcomer seated into *Sunday* on Monday would be seated
        #     into a game whose moment is gone.
        await refuse_a_court_closed_to_seating(
            challenge, at=at, games=self._games
        )

        # 4. The search this fill was built on, for the **newly seated only**.
        #    Everybody already in came from somewhere else, and a plan carrying
        #    an origin for one of them is refused by the aggregate.
        origin = await self._origin_of(
            command,
            newly_asked(command.court, still_in),
            sport=challenge.sport,
        )

        # 5. The two about everybody else, in the order and with the refusal the
        #    send shares. **This court's own challenge is excepted**, and it is
        #    the only one: an open challenge between two of these people that is
        #    not this one still refuses.
        await self._court.refuse_a_court_that_moved(
            everybody_on(command.court), at=at, except_challenge_id=challenge.id
        )

        challenge.invite(
            seats_of(
                command.court,
                search_id=command.search_id,
                origin=origin,
                already_in=still_in,
            ),
            by=command.player_id,
            occurred_at=at,
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

    async def _origin_of(
        self,
        command: FillSeatsCommand,
        newly_seated: frozenset[UUID],
        *,
        sport: Sport,
    ) -> CourtOrigin:
        """What the cited search says about the people being newly asked.

        The mode and the window on the answer are **read and discarded**: this
        challenge already holds both, and a fill that adopted the search's would
        be re-stamping facts other people have already answered against. What is
        used is ``positions``, which is the other half of every new seat's origin
        key.

        **The sport is read and *checked*, and that is the one place this differs
        from a send.** A send's sport *is* the origin's — it is where the court's
        shape comes from — so there is nothing there to disagree with. Here the
        sport is the challenge's, and nothing else would stop a filler citing a
        search they ran for another sport that seats the same number: padel and
        badminton both seat four. Those are people this padel court's own gates
        never judged, and every seat's origin would join to a search about a
        different game.

        **It is the same refusal and not a new code.** ``court_origin_not_found``
        already stands for four causes on the rule that telling them apart would
        answer questions about a stranger's search one probe at a time, and a
        fifth changes nothing about that argument.

        The caller is left out of the question for the reason a send leaves the
        organiser out: a search never returns its own searcher.
        """

        origin = await self._origins.court_origin(
            search_id=command.search_id,
            organiser_id=command.player_id,
            invitee_ids=newly_seated,
        )
        if origin is None or origin.sport is not sport:
            raise TheCourtDidNotComeFromThatSearch()
        return origin


__all__ = ["FillSeats"]
