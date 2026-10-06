"""``MatchHistoryQuery`` over ``games`` — what was played, and nothing arranged.

**One contract, and since #578 one provider.** ``PLAYED`` and
``PLANNED_NEVER_PLAYED`` are ``games``' facts. The challenge half — ``ACCEPTED``
and ``DECLINED``, the open-challenge set and the load count — went with the
challenges context, and what is left of it here is a **measured absence**: no
challenge is open and nobody's inbox holds one, because nothing sends one. The
port goes with the searches and the deck that read it (#579).

**It reads the provider's own port and never its streams.** The fold over the
log belongs to the context that owns it; a ``select`` written here would make
the matcher a second reader of somebody else's log, and a second author of what
*played* means.
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.kernel import Clock, Minutes, instant
from app.modules.games.domain.ports import (
    PLAYED_COUNTERPART_BOUND,
    GameCounterpart,
    GameHistoryQuery,
    PlayedOutcome,
)
from app.modules.matchmaking.domain.ports import (
    PAIRWISE_COUNTERPART_BOUND,
    OpenChallenge,
    OutcomeTally,
    PairwiseCounterpart,
    PairwiseOutcome,
)

#: Which played outcome becomes which pairwise one, and **nothing else does**.
#: A table rather than a cast, so a value arriving from the writer with no reader
#: is a ``KeyError`` at the seam instead of a string that means nothing
#: downstream.
_OUTCOMES: Mapping[PlayedOutcome, PairwiseOutcome] = {
    PlayedOutcome.PLAYED: PairwiseOutcome.PLAYED,
    PlayedOutcome.PLANNED_NEVER_PLAYED: PairwiseOutcome.PLANNED_NEVER_PLAYED,
}


def _refuse_two_bounds(reader: int, writer: int) -> None:
    """The bound, checked at import against the second spelling of it.

    ``games`` may not import ``matchmaking``, so the 500 is written down once
    per context. What is avoidable about that is it
    being *silent*: a bound raised on one side alone would leave the matcher
    promising a page it no longer gets. This is the seam where the spellings
    meet, so a disagreement stops the process from starting.
    """

    if reader != writer:
        raise RuntimeError(
            "the pairwise counterpart bound is spelled twice and the two "
            f"spellings disagree: the matcher demands {reader}, games answers "
            f"{writer}"
        )


# The call **is** the check: there is no value here anybody needs, only a reason
# for this module to refuse to import if the two spellings ever part company.
_refuse_two_bounds(PAIRWISE_COUNTERPART_BOUND, PLAYED_COUNTERPART_BOUND)


@final
class GamesPlayed:
    """The matcher's history: what was played, and no challenge open."""

    def __init__(self, *, games: GameHistoryQuery, clock: Clock) -> None:
        self._games = games
        self._clock = clock

    async def pairwise_counterparts(
        self, searcher_id: UUID
    ) -> tuple[PairwiseCounterpart, ...]:
        """Everything that was played between this searcher and anybody —
        **newest first, then the bound**, which ``games`` already applies."""

        now = instant(self._clock.now())
        rows = [
            PairwiseCounterpart(
                player_id=counterpart.player_id, outcomes=_tallies(counterpart)
            )
            for counterpart in await self._games.played_counterparts(
                searcher_id, now=now
            )
        ]
        rows.sort(key=lambda one: (one.last_at, one.player_id), reverse=True)
        return tuple(rows[:PAIRWISE_COUNTERPART_BOUND])

    async def open_challenges(self, searcher_id: UUID) -> tuple[OpenChallenge, ...]:
        """None, because nothing sends a challenge any more (#578)."""

        return ()

    async def late_change_threshold(self) -> Minutes | None:
        """``games``' answer, and it is still ``None``: *late* is a fact about a
        game, and the context that owns games says there is no number for it."""

        return await self._games.late_change_threshold()

    async def open_challenge_counts(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, int]:
        """A **measured zero** for everybody asked: nobody holds a seat
        awaiting their answer, because nothing invites anybody to one (#578)."""

        return {player_id: 0 for player_id in player_ids}


def _tallies(
    counterpart: GameCounterpart,
) -> Mapping[PairwiseOutcome, OutcomeTally]:
    """One person's games, in the reader's vocabulary."""

    return {
        _OUTCOMES[outcome]: OutcomeTally(count=tally.count, last_at=tally.last_at)
        for outcome, tally in counterpart.outcomes.items()
    }
