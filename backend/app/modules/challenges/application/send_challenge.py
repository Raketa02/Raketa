"""Send a challenge: one act, one transaction, everybody asked at once.

**Five facts are re-verified here, in the send's own transaction.** Four are the
fail-closed gates ``read_back_search`` already re-evaluates on a stored search —
a block either way, a hold, an account ``users`` may not show, and the mutual
gender preference — and they live in ``court_safety.py``. The fifth is
``OPEN_CHALLENGE``, the one gate deliberately left soft and out of the read-back
with **the send named as its backstop**, and it is checked here because it is a
statement about every *other* challenge: an aggregate that could see them would
not be an aggregate.

**Nothing in Play background-refetches, so the client cannot have noticed.** The
searcher may have built this line-up an hour ago; the court is re-verified
against live state rather than against the answer that produced it.

**Whole-send, never per-seat.** A partial send that silently dropped one invitee
would hand the organiser an arrangement they did not choose — the exact harm
recording the arrangement exists to prevent, arriving through the safety check
instead of through the proposal. A refused send writes nothing, so there is no
half-sent challenge to reconcile, and **the absence is the only way the rule is
provable**.

**Three refusals, in one order.**

1. *Nobody to invite*, and who else is on the court. The aggregate's own rule,
   run here first because it needs **no reads** and is true regardless of
   anybody else's state — telling an organiser their line-up went stale when
   they invited nobody sends them refreshing a screen that was never wrong. The
   one refusal in that family that cannot come first is the court's *shape*: it
   is the sport's, and the sport is the search's to say.
2. **The organiser's own hold**, with the same ``account_held`` the search
   returns. ADR-0130's consequences settled the shape once: a hold that stops you
   searching but lets you send invitations is that hole with the blast radius
   pointed at other people.
3. The two about **everybody else**, and both are read for one press, because
   fixing one and being refused for the other is the same interruption twice.

**Neither of those last two names anybody, and neither carries a payload.**
``AppError.details`` is ``Dict[str, Any]``, invisible to the central response
fence and ungeneratable against ``docs/adr/0006``, so a refusal states the class
of problem and the client re-reads the two sources it already owns:
``line_up_no_longer_sendable`` sends it back to the **origin search**, whose
read-back re-evaluates the same four gates and marks the rows it withholds, and
the open-challenge refusal sends it to **its own challenges**, which were always
theirs to read. Identical outcome, zero new disclosure.

**The remedy reads the origin back; it does not re-run the search.** A line-up is
bound to one ``search_id`` and a forecast refuses anybody who did not appear in
it, so re-running the pool mints a new id the whole line-up must adopt — and its
other seats are only *probably* in the new answer.

**The pair rule is asked across the whole court and across every sport.** Sharing
a line-up makes a pair: every occupied seat but your own is somebody you have an
open game with, co-invitees and organiser alike, so the check is one bulk read
over all six pairs of a four rather than three reads from the organiser outwards.
And two people are either arranging a game or they are not — asking for padel
while your tennis challenge sits unanswered is pestering with a sport chip on it.

**No row is written for a refused send.** The test is whether the outcome is
recoverable from anything else, and here it partly is: the search record holds
the line-up and this context holds the sends. More to the point, this is a race
between two clocks, and counting races is instrumentation.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.challenges.application.commands import SendChallengeCommand
from app.modules.challenges.application.court_safety import CourtSafety
from app.modules.challenges.application.court_verification import (
    CourtVerification,
    everybody_on,
    newly_asked,
    seats_of,
)
from app.modules.challenges.domain.challenge import Challenge, refuse_a_bad_court
from app.modules.challenges.domain.errors import TheCourtDidNotComeFromThatSearch
from app.modules.challenges.domain.ports import (
    ChallengeRepository,
    CourtOrigin,
    OpenChallengeQuery,
    OriginSearchQuery,
)
from app.modules.challenges.domain.seats import SeatPlan
from app.shared.ids import new_uuid


@final
class SendChallenge:
    """One press: a court, re-verified, minted whole or not at all."""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        open_challenges: OpenChallengeQuery,
        origins: OriginSearchQuery,
        safety: CourtSafety,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._challenges = challenges
        self._origins = origins
        self._court = CourtVerification(
            safety=safety, open_challenges=open_challenges
        )
        self._uow = uow
        self._clock = clock

    async def execute(self, command: SendChallengeCommand) -> UUID:
        """Mint the challenge, or refuse the whole send. Returns its id.

        **The order of what follows is the design**, and every step is placed
        against how much it has to read.
        """

        at = instant(self._clock.now())

        # 1. The shape of the court, before anything is read at all. The
        #    aggregate owns the rule and runs it again below; what is here is the
        #    **order** — a send with nobody to ask is refused without an
        #    organiser ever being told their line-up went stale.
        refuse_a_bad_court(
            [choice.player_id for choice in command.court],
            organiser_id=command.organiser_id,
        )

        # 2. Their own hold, at the entry point, with the same code the search
        #    returns. It is about the caller and nobody else, so it is asked
        #    before a single fact about another person — or about a search that
        #    may not be theirs — is read.
        await self._court.refuse_a_held_caller(command.organiser_id)

        # 3. The search the court was built on, which is where the sport, the
        #    kind of evening, the window and every seat's position come from.
        origin = await self._origin_of(command)
        challenge = Challenge.sent(
            challenge_id=new_uuid(),
            sport=origin.sport,
            mode=origin.mode,
            window=origin.window,
            organiser_id=command.organiser_id,
            arrangement=self._arrangement(command, origin),
            occurred_at=at,
        )

        # 4. The two about everybody else, in the order and with the refusal
        #    ``court_verification.py`` holds for both presses. **This send
        #    excepts no challenge**: every open pair on this court refuses it,
        #    which is the whole of the rule and the thing a fill narrows by
        #    exactly one id.
        await self._court.refuse_a_court_that_moved(
            everybody_on(command.court), at=at
        )

        await self._challenges.save(challenge)
        await self._uow.commit()
        return challenge.id

    async def _origin_of(self, command: SendChallengeCommand) -> CourtOrigin:
        """What the cited search says about this court, or a refusal.

        The organiser is left out of the question: a search never returns its own
        searcher, so asking where *they* sat would refuse every send ever made.
        """

        origin = await self._origins.court_origin(
            search_id=command.search_id,
            organiser_id=command.organiser_id,
            invitee_ids=newly_asked(
                command.court, frozenset({command.organiser_id})
            ),
        )
        if origin is None:
            raise TheCourtDidNotComeFromThatSearch()
        return origin

    @staticmethod
    def _arrangement(
        command: SendChallengeCommand, origin: CourtOrigin
    ) -> tuple[SeatPlan, ...]:
        """The court as the aggregate takes it, each invitation citing its seat.

        **The organiser is the whole of who is *already in* on a send**, and
        naming them as a set rather than as a comparison is what lets a fill —
        where *already in* is every live member — build its arrangement through
        the same function (``court_verification.seats_of``).
        """

        return seats_of(
            command.court,
            search_id=command.search_id,
            origin=origin,
            already_in=frozenset({command.organiser_id}),
        )
