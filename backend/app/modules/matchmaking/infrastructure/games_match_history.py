"""``MatchHistoryQuery``, whole at last — the challenge half and the game half.

**One contract, two providers, and the seam runs *through* one read**
(``docs/adr/0098`` as amended, ``docs/adr/0137``). ``ACCEPTED`` and ``DECLINED``
are ``challenges``' facts; ``PLAYED`` and ``PLANNED_NEVER_PLAYED`` are ``games``'.
Splitting the port to match would cut ``PAIRWISE_COUNTERPART_BOUND`` in half and
leave a caller merging two bounded reads, which is not a bounded read — so the
port stays whole and ``games`` arrives here as a **composing** adapter rather
than as a second signature.

**It composes ``ChallengesButNobodyHasPlayed`` rather than replacing it.** That
class is still exactly what its name says — the challenge half, and a measured
absence where games would be — and it keeps answering for the two reads that are
wholly challenges': the open-challenge set and the load count. What this class
adds is the half that has just acquired a provider.

**Merging two 500-bounded reads and re-applying the bound loses nobody**, and
that is worth writing down because it looks like it should. A counterpart missing
from the merged answer is one outside *both* providers' newest five hundred; the
five hundred who beat them on challenges each have a merged ``last_at`` at least
as recent as the value that beat them, so five hundred people are strictly ahead
of them in the merge too. The property the bound exists for survives: a
counterpart cut off by it stays indistinguishable from one fully decayed by time.

**It reads both providers' own ports and never their streams.** The fold over
each log belongs to the context that owns it; a ``select`` written here would make
the matcher a second reader of somebody else's log, and a second author of what
*open* and *played* mean.
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
    MatchHistoryQuery,
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
    """The bound, checked at import against the third spelling of it.

    ``games`` may not import ``matchmaking`` any more than ``challenges`` may, so
    the 500 is written down once per context. What is avoidable about that is it
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
class GamesPlayedAndChallengesAnswered:
    """The matcher's history, complete: what was arranged and what was played."""

    def __init__(
        self,
        *,
        challenges: MatchHistoryQuery,
        games: GameHistoryQuery,
        clock: Clock,
    ) -> None:
        self._challenges = challenges
        self._games = games
        self._clock = clock

    async def pairwise_counterparts(
        self, searcher_id: UUID
    ) -> tuple[PairwiseCounterpart, ...]:
        """Everything that ever happened between this searcher and anybody.

        **One row per person, with both contexts' outcomes inside it.** Keeping
        them apart is what lets an accept stay visible under a later decline and
        a real game stay visible under a later ghost — collapsed to a latest
        outcome, familiarity and the previous-decline signal would both be
        reading the same erased history.
        """

        now = instant(self._clock.now())
        answered = await self._challenges.pairwise_counterparts(searcher_id)
        played = await self._games.played_counterparts(searcher_id, now=now)

        merged: dict[UUID, dict[PairwiseOutcome, OutcomeTally]] = {
            one.player_id: dict(one.outcomes) for one in answered
        }
        for counterpart in played:
            merged.setdefault(counterpart.player_id, {}).update(
                _tallies(counterpart)
            )

        rows = [
            PairwiseCounterpart(player_id=player_id, outcomes=outcomes)
            for player_id, outcomes in merged.items()
        ]
        # **Newest first, then the bound** — in that order, and applied to the
        # merged answer rather than to either half, because a person's most
        # recent thing may be a game where their most recent challenge is old.
        rows.sort(key=lambda one: (one.last_at, one.player_id), reverse=True)
        return tuple(rows[:PAIRWISE_COUNTERPART_BOUND])

    async def open_challenges(self, searcher_id: UUID) -> tuple[OpenChallenge, ...]:
        """Wholly ``challenges``', and passed straight through.

        A game is never *open* in this sense: the pair rule releases when the
        two of them stop arranging, and they stop the moment the line-up
        completes into a game. That sentence stood here as settled fact for the
        whole time nothing implemented it — ``challenges`` read *has this ended*
        and a completed line-up has not, so a pair that finished arranging a game
        was held for ever. ``standing.py``'s ``ARRANGING`` is what makes it true
        (``docs/adr/0142`` §1).

        **Whether that game was played is still not asked, and that is now a
        decision rather than a filing** (``docs/adr/0152`` §5). The port that
        would answer it exists — ``challenges`` grew ``SettledGameQuery`` onto
        ``games`` to bound the mutual mint — and the record that built it
        declined to use it on this read. Two people with an unplayed game may
        still deal each other into a deck and send each other a court: a send is
        somebody deliberately choosing one, and holding them here would re-add
        #343's block by a side door. This class, the composing adapter holding
        both providers, is still where it would live if that is ever revisited.
        """

        return await self._challenges.open_challenges(searcher_id)

    async def late_change_threshold(self) -> Minutes | None:
        """``games``' answer now, and it is still ``None``.

        The owner changed and the value did not. *Late* is a fact about a plan,
        and the context that owns plans is the one that says a plan here has no
        time in it to be late for.
        """

        return await self._games.late_change_threshold()

    async def open_challenge_counts(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, int]:
        """Wholly ``challenges``', and passed straight through."""

        return await self._challenges.open_challenge_counts(player_ids)


def _tallies(
    counterpart: GameCounterpart,
) -> Mapping[PairwiseOutcome, OutcomeTally]:
    """One person's games, in the reader's vocabulary."""

    return {
        _OUTCOMES[outcome]: OutcomeTally(count=tally.count, last_at=tally.last_at)
        for outcome, tally in counterpart.outcomes.items()
    }
