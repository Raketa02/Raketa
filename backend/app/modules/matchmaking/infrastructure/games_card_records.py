"""The card's record block, over ``games``' own published reads.

**The card's second author, and its second provider.** ``PlayerCardSource``
answers who somebody is — a nickname, a photograph, a verdict on it — and this
answers what the platform has watched them do: how many counted games they have
played, and how the last five of those went. Two ports rather than five fields on
one, because ``docs/adr/0098`` splits by *who supplies the fact* and these are
``games``' facts (``docs/adr/0137``).

**It reads the provider's own port and never its streams**, exactly as
``games_match_history`` beside it does. A fold over somebody else's log written
here would make the matcher a second author of what *counted* and *confirmed*
mean, and the two would part company on the first ruleset that moved a window.

**And it inverts one rule on the way through, deliberately.**
``counted_games_for`` answers a **measured zero** for everybody it is asked about
— the games were counted and none of them was theirs — which is the right answer
to the question ``games`` was asked. It is the wrong thing to print: on a card,
*0 games* and *no record* are one absence in two spellings, and the whole
discipline of that surface is that absence has one. So a player with nothing is
dropped here rather than carried through as a nought, and the inversion is
written down where it happens.
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.kernel import Clock, instant
from app.modules.games.domain.ports import RECENT_RESULTS, GameHistoryQuery
from app.modules.games.domain.results import Outcome
from app.modules.matchmaking.domain.cards import CardRecord
from app.modules.matchmaking.domain.searches import LAST_FIVE, GameResult

#: Which agreed outcome becomes which recorded one, and **nothing else does**. A
#: table rather than a cast, so a value arriving from the writer with no reader
#: here is a ``KeyError`` at the seam instead of a string that means nothing on a
#: card — the shape ``games_match_history``'s outcome map has, one fact over.
_RESULTS: Mapping[Outcome, GameResult] = {
    Outcome.WIN: GameResult.WIN,
    Outcome.LOSS: GameResult.LOSS,
}


def _refuse_two_runs(card: int, games: int) -> None:
    """The length of the run, checked at import against the second spelling of it.

    ``games`` may not import ``matchmaking``, so *how many* is written down once
    per context — and what is avoidable about that is it being **silent**. A card
    that asked for five and was handed six would draw a run longer than the one
    it says it draws, and nothing would fail. This is the seam where the two
    spellings meet, so a disagreement stops the process from starting.
    """

    if card != games:
        raise RuntimeError(
            "the run of form is spelled twice and the two spellings disagree: "
            f"the card draws {card} results, games answers {games}"
        )


# The call **is** the check: there is no value here anybody needs, only a reason
# for this module to refuse to import if the two spellings ever part company.
_refuse_two_runs(LAST_FIVE, RECENT_RESULTS)


@final
class GamesPlayedAndAgreed:
    """``PlayerRecordSource`` over ``games``' published history."""

    def __init__(self, *, games: GameHistoryQuery, clock: Clock) -> None:
        self._games = games
        self._clock = clock

    async def records_for(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, CardRecord]:
        """Each of these players' counted-game count and run of form.

        **Two reads for the whole shortlist, never one per row.** They are two
        because they are two facts with two absence rules and ``games`` publishes
        them apart; what matters to the caller is that neither is per-row, which
        is what makes the price bounded by the twenty rows that survived the
        floor rather than by the pool.

        **A player with no counted game is absent from the answer.** So is one
        whose only games were friendlies: a friendly was never evidence about
        anybody, by the choice of the people who arranged it, so there is nothing
        for a record block to say about it.

        The clock is read here rather than taken, because *was this played* and
        *has this result become final* are both folds against the instant the
        read happens — and a caller holding one could hold a stale one.
        """

        wanted = set(player_ids)
        if not wanted:
            return {}

        now = instant(self._clock.now())
        counts = await self._games.counted_games_for(wanted, now=now)
        results = await self._games.recent_results_for(wanted, now=now)

        return {
            player_id: CardRecord(
                counted_games=count,
                # Already oldest to newest and already trimmed by the provider —
                # reversing or re-slicing here would be a second answer to
                # *which five*, written where nobody would look for it.
                last_five=tuple(
                    _RESULTS[one.outcome] for one in results.get(player_id, ())
                ),
            )
            for player_id, count in counts.items()
            # **The inversion, in one line.** A measured nought is the honest
            # answer to what ``games`` was asked and the wrong thing to print, so
            # it becomes the absence the card already spells one way.
            if count >= 1
        }
