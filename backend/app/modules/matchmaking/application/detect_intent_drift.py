"""The drift loop. **It notices, and then it declines to act.**

*"Your last five padel searches were competitive. Update your profile?"* — with
*Update it* and *Just for this search*. That is the whole of what happens when
behaviour and a declaration disagree (``matchmaking-engine.md`` §6.3): the
platform watches, notices, raises a prompt, and accepts whatever answer comes
back.

**The matcher never reads the disagreement and never writes the value.** This is
the one place the product deliberately looks away from data it holds, and the
reason is that a declaration is a *preference*: it has no true answer to check it
against, so a silent correction would be the platform overruling somebody about
what they want. The temptation to "correct" a stale declaration gets stronger the
moment there is data, which is why the refusal is decided now rather than by
drift later.

**A loop rather than a read on the search path.** Five searches back is an
unbounded scan in front of a player waiting for a shortlist. So it runs daily,
leaves a prompt in the ledger, and the next search picks it up in one lookup.

**Idempotent and safe beside itself** (``docs/adr/0092``): it reads searches and
declarations, writes nothing but a prompt, and raising the same prompt in four
processes leaves exactly what one raise leaves. Two runs over an unchanged window
raise the identical set.

**A player who has declined this question is still raised at here**, and that is
deliberate: the suppression is read **downstream**, by the one filter in
``run_shortlist_search._raised`` where every prompt converges (``declines.py``).
Checking it here would put the same rule in two places and would make this loop
something other than what the paragraphs above say it is — it notices, it leaves
a prompt, and it acts on nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Mapping
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Clock, Sport
from app.modules.matchmaking.domain.prompts import (
    INTENT_DRIFT_SEARCHES,
    Prompt,
    PromptLedger,
)
from app.modules.matchmaking.domain.search_store import SearchModeReading, SearchStore
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.ports import PlayIntentDeclarationRepository

#: How far back one tick looks. Wider than the daily cadence on purpose — a tick
#: that missed, or a process that was down over a deploy, must not create a day
#: nobody's drift was ever noticed in.
DRIFT_WINDOW = timedelta(days=7)

#: The most searches one tick will read. A bound on the work rather than a page:
#: a loop that could read an unbounded day is a loop that falls over on the first
#: busy one, and a prompt missed today is raised again tomorrow.
DRIFT_SCAN_LIMIT = 5_000

#: Which declaration each search mode agrees with. ``NO_PREFERENCE`` agrees with
#: **both**, and that is the whole reason this is a mapping rather than an
#: equality: a player who declared no preference has said nothing a search can
#: contradict, so no run of searches ever drifts from it.
_AGREES_WITH: Mapping[SearchMode, frozenset[PlayIntent]] = {
    SearchMode.COMPETITIVE: frozenset(
        {PlayIntent.COMPETITIVE, PlayIntent.NO_PREFERENCE}
    ),
    SearchMode.FOR_FUN: frozenset({PlayIntent.FOR_FUN, PlayIntent.NO_PREFERENCE}),
}


@dataclass(frozen=True)
class IntentDriftReport:
    """What one tick saw and asked. **The job's only output.**

    ``searches_read`` separates *the loop ran and the city was quiet* from *the
    loop ran against a store that answered nothing*, which are the two states a
    log line with only a count of prompts cannot tell apart.
    """

    searches_read: int
    pairs_examined: int
    prompts_raised: int


class DetectIntentDrift:
    """Raise a prompt where behaviour and a declaration keep disagreeing."""

    def __init__(
        self,
        *,
        searches: SearchStore,
        declarations: PlayIntentDeclarationRepository,
        prompts: PromptLedger,
        clock: Clock,
    ) -> None:
        self._searches = searches
        self._declarations = declarations
        self._prompts = prompts
        self._clock = clock

    async def execute(self) -> IntentDriftReport:
        readings = await self._searches.modes_since(
            since=self._clock.now() - DRIFT_WINDOW, limit=DRIFT_SCAN_LIMIT
        )
        runs = _most_recent_runs(readings)
        raised = 0
        for (player_id, sport), modes in runs.items():
            drifting = _drifting_mode(modes)
            if drifting is None:
                continue
            declaration = await self._declarations.load(
                player_id=player_id, sport=sport
            )
            if declaration is None:
                # Nothing to drift **from**. A player with no declaration cannot
                # search at all — the route refuses with `play_intent_not_declared`
                # — so this is a declaration retracted since, and asking somebody
                # to update a value they do not have would be asking the wrong
                # question.
                continue
            if declaration.intent in _AGREES_WITH[drifting]:
                continue
            await self._prompts.raise_prompt(
                player_id=player_id,
                prompt=Prompt.UPDATE_PLAY_INTENT,
                sport=sport,
                detail=drifting.value,
            )
            raised += 1
        return IntentDriftReport(
            searches_read=len(readings),
            pairs_examined=len(runs),
            prompts_raised=raised,
        )


def _most_recent_runs(
    readings: tuple[SearchModeReading, ...],
) -> Mapping[tuple[UUID, Sport], tuple[SearchMode | None, ...]]:
    """The last few searches per ``(player, sport)``, newest first.

    The readings arrive newest first, so the first ``INTENT_DRIFT_SEARCHES`` of
    each pair are its most recent — which is the run §6.3 means by *your last
    five*, and not *five of your searches somewhere in the week*.
    """

    runs: dict[tuple[UUID, Sport], list[SearchMode | None]] = {}
    for reading in readings:
        run = runs.setdefault((reading.searcher_id, reading.sport), [])
        if len(run) < INTENT_DRIFT_SEARCHES:
            run.append(reading.mode)
    return {pair: tuple(modes) for pair, modes in runs.items()}


def _drifting_mode(modes: tuple[SearchMode | None, ...]) -> SearchMode | None:
    """The one mode a full run of searches all chose, or nothing.

    Three ways this answers *no drift*, and each is a different sentence worth
    keeping apart from *they disagree with their profile*: the run is too short
    to be a pattern, it mixes modes so there is nothing to update **to**, or it
    holds a search with no mode at all — the deck, which scores against the
    declaration itself and so cannot be evidence against it.
    """

    if len(modes) < INTENT_DRIFT_SEARCHES:
        return None
    if any(mode is None for mode in modes):
        return None
    chosen = set(modes)
    if len(chosen) != 1:
        return None
    return chosen.pop()
