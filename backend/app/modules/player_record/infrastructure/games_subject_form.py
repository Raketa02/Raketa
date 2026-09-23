"""``SubjectForm`` over ``games``' published history. **The run of five, per sport.**

Two words change at this seam and nothing else does. ``games`` answers with
``CountedResult`` — a game id, a sport, an outcome and when it was played — and a
record draws none of those but one: the run is **outcomes in order and no dates**,
which is a run of form rather than a statement about when anybody was last here.
Activity recency is a standing refusal on this platform, at every granularity, and
the safest place to honour it is a type that cannot carry a moment.

``Outcome`` is ``games``' word and ``GameOutcome`` is this context's; they carry
the same two strings deliberately, and the agreement is asserted rather than
assumed (``docs/adr/0159``) — the way ``OnCourtVerdict`` is against
``PhotoReviewDecision`` one file over. The translation is a **table and not a
cast**, so a third ending added over there is a ``KeyError`` at this seam rather
than a string that means nothing on a sheet.

**Two numbers meet here too**, and the module refuses to import if they ever part
company: how long a run is is spelled once in this context's domain and once in
``games``, because neither may import the other's.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from typing import Mapping

from app.kernel import Instant, Sport
from app.modules.games.domain.ports import RECENT_RESULTS, GameHistoryQuery
from app.modules.games.domain.results import Outcome
from app.modules.player_record.domain.record import LAST_FIVE, GameOutcome

#: Which agreed outcome becomes which drawn one, and **nothing else does**. A
#: table rather than a cast, so a value arriving from the writer with no reader
#: here is a ``KeyError`` at the seam instead of a string that means nothing on a
#: sheet — the shape ``games_card_records`` takes for the same two words.
_RESULTS: Mapping[Outcome, GameOutcome] = {
    Outcome.WIN: GameOutcome.WIN,
    Outcome.LOSS: GameOutcome.LOSS,
}

# **The length of the run, checked at import against its second spelling.**
# ``player_record`` may not import a provider's constant into its domain any more
# than it may import its types, so *how many* is written down once per context —
# and what is avoidable about that is it being silent. A sheet that asked for
# five and was handed six would draw a run longer than the one it says it draws,
# and nothing would fail. This is the seam where the two meet, so a disagreement
# stops the process from starting; it is the guard ``games_card_records`` already
# puts the same pair of numbers through.
if LAST_FIVE != RECENT_RESULTS:
    raise RuntimeError(
        "the run of form is spelled twice and the two spellings disagree: "
        f"the record draws {LAST_FIVE} and games publishes {RECENT_RESULTS}"
    )


@final
class GamesSubjectForm:
    """How their last few counted games in one sport went."""

    def __init__(self, games: GameHistoryQuery) -> None:
        self._games = games

    async def last_results_in(
        self, player_id: UUID, *, sport: Sport, now: Instant
    ) -> tuple[GameOutcome, ...]:
        """The outcomes, oldest to newest, and **never how many there should be.**

        The trim and the sport filter are the provider's, in that order, because
        a run cut to five across every sport and then narrowed would show three
        results to somebody who has played thirty in this one.
        """

        return tuple(
            _RESULTS[result.outcome]
            for result in await self._games.recent_results_in(
                player_id, sport=sport, now=now
            )
        )


__all__ = ["GamesSubjectForm"]
