"""The availability-staleness backstop. **A question, never a dock.**

§9.3.5 priced a stale grid by multiplying the availability term by a staleness
curve. [ADR-0120] struck the curve — it read *account age*, not the pair, and the
clamp bound at day 156 so the published constant was never reached — and the
observation that produced it survives: **a grid three months old quietly ruins
every match it touches**, and now also mislabels the window of every challenge
sent from one (``docs/adr/0100``).

The mechanism that replaces it is the one the product already has. *Keep these
times?* appears at the moment the player has done the work; this loop is its
**backstop**, for the player who never edits their week on a search screen and so
is never asked. It reads the profile's own grid — through the index, which is
where the platform keeps its picture of who ticked what and when — and leaves a
prompt.

**What it may not do is dock anybody**, and the difference is the whole point:
the searcher's grid is their own ask, so it is the one thing relaxation may
touch, and it is touched by asking them. A background job that quietly weakened a
term would be scoring a person on how recently they opened an app.

**Idempotent and safe beside itself** (``docs/adr/0092``). It writes nothing but
prompts, over the same rows, from a snapshot every process holds its own copy of;
four processes raising the same prompt four times a day leave exactly what one
raise leaves.

**A player who has declined this question is still raised at here**, and the
suppression is read **downstream** instead, by the one filter in
``run_shortlist_search._raised`` (``declines.py``). This is the rudest of the
four prompts if nothing filters it — the condition holds until the player edits
their week, the loop is daily and ``PROMPT_TTL`` is three days — which is the
argument for the filter, not an argument for putting it here: a copy of the rule
in every raiser is four chances for one of them to answer differently.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.kernel import Clock, Sport, instant
from app.modules.matchmaking.domain.candidate_index import Partition
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSource
from app.modules.matchmaking.domain.prompts import (
    GRID_STALE_AFTER,
    Prompt,
    PromptLedger,
)


@dataclass(frozen=True)
class StaleGridReport:
    """What one tick saw and asked. **The job's only output.**

    ``grids_examined`` is what separates *the loop ran and every week is fresh*
    from *the loop ran against an index holding nobody*, which a count of prompts
    alone cannot tell apart.
    """

    grids_examined: int
    prompts_raised: int


class OfferToRefreshStaleGrids:
    """Ask the players whose described week has stopped describing a week."""

    def __init__(
        self,
        *,
        candidates: CandidateSource,
        prompts: PromptLedger,
        clock: Clock,
    ) -> None:
        self._candidates = candidates
        self._prompts = prompts
        self._clock = clock

    async def execute(self) -> StaleGridReport:
        now = self._clock.now()
        # **Once per player, not once per row.** The index is keyed
        # ``(player, sport)`` and the availability grid is neither — it is one
        # week, and a player rated in three sports would otherwise be asked the
        # same question three times.
        stale: set[UUID] = set()
        examined: set[UUID] = set()
        for sport in Sport:
            snapshot = self._candidates.snapshot(Partition.for_sport(sport))
            for row in snapshot.rows:
                player_id = UUID(row.player_id)
                examined.add(player_id)
                if now - instant(row.grid_updated_at) >= GRID_STALE_AFTER:
                    stale.add(player_id)
        for player_id in sorted(stale):
            # No sport on the prompt: the week is one week. A sport-shaped
            # prompt here would be a question about a fact that has no sport.
            await self._prompts.raise_prompt(
                player_id=player_id, prompt=Prompt.REFRESH_YOUR_TIMES
            )
        return StaleGridReport(
            grids_examined=len(examined), prompts_raised=len(stale)
        )
