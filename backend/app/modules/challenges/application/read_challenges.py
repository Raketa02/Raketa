"""*What have I been asked, and what have I asked for.*

One read, keyed on the reader and on nothing else. There is no argument here that
could name somebody else, which is what stops this becoming a way to ask about a
stranger's evening — the same shape ``InterestLedger`` takes, and for the same
reason.

**The standing is derived here, once, against one instant.** Folding each
challenge against its own read of the clock would let a list disagree with itself
about which of two seats had just lapsed. So the clock is read once and every
standing is computed against it.

**Ended challenges are in the list, and their standing says so.** A challenge that
lapsed this morning still happened to the person it was sent to, and a list that
quietly dropped it would be the same class of lie as a read-back that got shorter.
There is no filter parameter: a client that wants only the live ones has the
standing on every row.

**It is also the remedy for a refused send.** When a send is refused on the pair
rule the client re-reads this, because an open game of the organiser's was always
theirs to read — so naming the pair here costs nothing the refusal was protecting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, instant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.ports import ChallengeDirectory
from app.modules.challenges.domain.standing import Standing


@final
@dataclass(frozen=True, slots=True)
class ReadChallengesCommand:
    """*Show me my challenges.* One person, and it is the person asking."""

    reader_id: UUID


@final
@dataclass(frozen=True, slots=True)
class StandingChallenge:
    """One challenge, and what it is at the instant the list was read.

    The standing travels **beside** the challenge rather than on it, because
    nothing stores one: it is a fold of the seats against a clock, and a field on
    the aggregate would be the status column ``standing.py`` refuses.
    """

    challenge: Challenge
    standing: Standing


@final
class ReadChallenges:
    """Every challenge this player holds a seat in, newest first."""

    def __init__(self, *, directory: ChallengeDirectory, clock: Clock) -> None:
        self._directory = directory
        self._clock = clock

    async def execute(
        self, command: ReadChallengesCommand
    ) -> tuple[StandingChallenge, ...]:
        now = instant(self._clock.now())
        return tuple(
            StandingChallenge(challenge=challenge, standing=challenge.standing_at(now))
            for challenge in await self._directory.seating(command.reader_id)
        )
