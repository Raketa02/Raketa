"""The five facts, re-read together and judged in one order — for both presses.

**Two acts put people in front of each other and they must not come to two
answers about it.** A send mints a court; a fill grows one somebody is already
sitting on. Both re-verify the same five facts in the same transaction, because
the line-up may be an hour old and nothing in Play background-refetches — and
before this module they did it twice, in two files, with the refusal sentence
written out twice.

That is the same argument ``search_workbench.py`` makes one context over: *two
implementations of this would be two answers about which reads fail closed, and
the one that drifted would be the one that quietly softened a gate.* Here the
gate in question is a **safety** one, so the drift would be the expensive kind.

**Four of the five are ``CourtSafety``'s and the fifth is the pair rule**, which
is a statement about every *other* challenge — an aggregate that could see them
would not be an aggregate. What is here is not a sixth fact: it is the **order**
the two presses share, and it is exactly three rules.

*The caller's own hold is asked first, before a single fact about anybody else.*
It is about them and nobody else, and a hold that stops you searching but lets
you invite people is that hole with the blast radius pointed at other people.

*Both of the reads about everybody else happen before either is judged.* A press
that fixed one and was refused for the other is the same interruption twice, and
the client's remedy re-reads both sources it already owns.

*Only one code can cross an envelope that has one*, so the safety refusal wins
and the message — a diagnostic, never copy — carries the second.

**No refusal here names anybody**, and there is no shape in this module that
could: ``CourtSafety`` answers a boolean by construction, and the pair rule's
answer is counted rather than reported.

**What differs between the two presses is one argument.** A send excepts no
challenge; a fill excepts exactly the one it is completing, by id, because
otherwise a court would be refused for the pairs it is made of
(``docs/adr/0150`` §3). Making it a parameter is what keeps the difference
visible in the caller instead of hidden in a branch here.
"""

from __future__ import annotations

from typing import Collection, Sequence, final
from uuid import UUID

from app.kernel import Instant
from app.modules.challenges.application.commands import SeatChoice
from app.modules.challenges.application.court_safety import CourtSafety
from app.modules.challenges.domain.errors import (
    AnOpenChallengeStandsWithThisPair,
    TheLineUpIsNoLongerSendable,
)
from app.modules.challenges.domain.origins import SentFromSearch
from app.modules.challenges.domain.ports import CourtOrigin, OpenChallengeQuery
from app.modules.challenges.domain.seats import SeatPlan
from app.shared.domain.errors import AccountHeld


@final
class CourtVerification:
    """*May this court be put in front of these people, right now?*

    Two collaborators, and they are the two the fifth fact needs beyond the four:
    the gates, and the read that can see other challenges.
    """

    def __init__(
        self, *, safety: CourtSafety, open_challenges: OpenChallengeQuery
    ) -> None:
        self._safety = safety
        self._open_challenges = open_challenges

    async def refuse_a_held_caller(self, player_id: UUID) -> None:
        """**Their own hold, at the entry point**, with the code a search returns.

        Asked before anything about another person — or about a search that may
        not be theirs — is read, because it is a fact about the caller alone and
        true regardless of anybody else's state.
        """

        if player_id in await self._safety.held_among([player_id]):
            raise AccountHeld("this account is under a hold")

    async def refuse_a_court_that_moved(
        self,
        on_the_court: Collection[UUID],
        *,
        at: Instant,
        except_challenge_id: UUID | None = None,
    ) -> None:
        """The two facts about everybody else. **Both read, then judged.**

        ``except_challenge_id`` steps over exactly one challenge and no other: a
        fill grows the court it is already part of, and asking the pair rule over
        that court would return its own pairs. A send passes nothing and gets the
        rule it always had.
        """

        admitted = await self._safety.admits(on_the_court)
        pairs = await self._open_challenges.open_pairs_among(
            on_the_court, now=at, except_challenge_id=except_challenge_id
        )
        if not admitted:
            raise TheLineUpIsNoLongerSendable(
                "Somebody on this court can no longer be invited to it"
                + (", and an open challenge already stands on it." if pairs else ".")
            )
        if pairs:
            raise AnOpenChallengeStandsWithThisPair()


def everybody_on(court: Sequence[SeatChoice]) -> frozenset[UUID]:
    """Who is occupying a seat. **An empty seat is a seat and holds nobody.**"""

    return frozenset(
        choice.player_id for choice in court if choice.player_id is not None
    )


def newly_asked(
    court: Sequence[SeatChoice], already_in: Collection[UUID]
) -> frozenset[UUID]:
    """Who this press is actually inviting: the court, minus who is already in it.

    ``already_in`` is the organiser alone on a send — their seat is accepted from
    birth and nothing asks whether they want the game they just built — and every
    live member on a fill. The two are the same question with a different answer,
    which is why this takes the set rather than branching on which press it is.
    """

    return frozenset(
        choice.player_id
        for choice in court
        if choice.player_id is not None and choice.player_id not in already_in
    )


def seats_of(
    court: Sequence[SeatChoice],
    *,
    search_id: UUID,
    origin: CourtOrigin,
    already_in: Collection[UUID],
) -> tuple[SeatPlan, ...]:
    """The court as the aggregate takes it, each invitation citing its own seat.

    **Per seat, never per challenge.** A doubles press draws its invitees from one
    search at up to three positions, so a challenge-level origin would keep the
    search and lose every position — and the position is what the telemetry join
    needs (``search-telemetry.md`` §19.2).

    **Nobody already in carries an origin**, and the aggregate raises rather than
    dropping one quietly: a plan addressed to somebody who is already in the game
    is a caller that thinks it is inviting somebody it is not.
    """

    return tuple(
        SeatPlan(side=choice.side, player_id=choice.player_id)
        if choice.player_id is None or choice.player_id in already_in
        else SeatPlan(
            side=choice.side,
            player_id=choice.player_id,
            origin=SentFromSearch(
                search_id=search_id, position=origin.positions[choice.player_id]
            ),
        )
        for choice in court
    )


__all__ = [
    "CourtVerification",
    "everybody_on",
    "newly_asked",
    "seats_of",
]
