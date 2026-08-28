"""Where *the ledgers fail soft* stops being prose and starts being enforced.

**A gate that cannot be evaluated excludes; a term that cannot be evaluated
stands down** (``docs/adr/0095``). The three ledgers here are on the second side, and
it is worth saying out loud because the rule reads like it should not reach
them: applying *exclude what you could not check* to a suppression would
**empty the deck rather than protect anybody**, and applying it to exposure
would withhold a shortlist because a cache was restarting. A suppression is a
courtesy — *do not show me that person again just yet* — and a block is a safety
control; only one of them may take a surface down with it.

**One wrapper for both, at one seam.** The alternative arrangements were both
worse. A ``try`` inside each adapter method makes *the store answered nothing*
and *the store could not be reached* indistinguishable from outside, so the
posture becomes untestable at the exact moment it matters. A ``try`` at each
call site makes it a discipline, and a discipline is what
``matchmaking/application/outward_reads.py`` already refuses for the outward
demands, for the same reason: *a caller cannot quietly soften a gate by handing
it a default, and cannot forget to soften a term.* Those ports get that from a
table; these get it from a type, because there is no call site to route through
— the ledgers are written and read from several places, and one of them is a
background job with no request to refuse.

**One helper, carried on a shared base rather than passed at every call.** Each
wrapper knows which ledger it is once, in its class, instead of restating the
name in every method body beside the operation's — two strings travelling
together at eleven call sites is a fact about the object, not about the call.

**It catches broadly, deliberately.** A store that raises and a store that
answers something malformed are the same event to a courtesy — it could not be
consulted — and the degraded answer is right for both. What keeps that from
being silent is the log line each one writes: a degraded search must not look
identical to a duller one.

**Every degraded answer is the empty one, and empty means the same thing the
ledger's own emptiness means.** Nobody is suppressed, nobody has been shown,
no threshold has been published. That collapse — *we could not tell* reading as
*there is nothing to tell* — is a deliberate loss of information and it is only
safe because neither ledger is evidence for anything. It would be indefensible
for a block.
"""

from __future__ import annotations

import logging
from typing import Awaitable, Callable, Collection, Mapping, TypeVar
from uuid import UUID

from app.kernel import Sport
from app.modules.matchmaking.domain.ledgers import (
    ExposureLedger,
    ExposureWeek,
    SuppressionLedger,
)
from app.modules.matchmaking.domain.prompts import Prompt, PromptLedger

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


class _FailSoft:
    """Runs one ledger operation, or degrades to an answer that excludes nobody.

    A base for the two wrappers rather than a free function, so that *which
    ledger this is* is stored once instead of handed in at every call.
    """

    #: What the log line calls this ledger. Set by each subclass.
    _ledger: str

    async def _softly(
        self, operation: str, read: Callable[[], Awaitable[_T]], degraded: _T
    ) -> _T:
        try:
            return await read()
        except Exception:
            # Warning rather than error: nothing is broken for the player, and a
            # degraded ledger during a Redis restart is an expected state. It is
            # not info either — a search whose spread quietly stopped working is
            # exactly the failure that hides in an info stream.
            logger.warning(
                "ephemeral ledger unavailable, degrading",
                extra={"ledger": self._ledger, "operation": operation},
                exc_info=True,
            )
            return degraded


class FailSoftExposureLedger(_FailSoft):
    """An ``ExposureLedger`` whose outage costs a spread and nothing else."""

    _ledger = "exposure"

    def __init__(self, inner: ExposureLedger) -> None:
        self._inner = inner

    async def record_shown(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> None:
        await self._softly(
            "record_shown",
            lambda: self._inner.record_shown(
                sport=sport, week=week, player_ids=player_ids
            ),
            None,
        )

    async def times_shown(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> Mapping[UUID, int]:
        # Every id answered, as the port promises, so a caller that iterates the
        # candidate set finds every one of them present and unremarkable rather
        # than missing. A degraded read must not be able to look like a gate.
        return await self._softly(
            "times_shown",
            lambda: self._inner.times_shown(
                sport=sport, week=week, player_ids=player_ids
            ),
            {player_id: 0 for player_id in player_ids},
        )

    async def record_shown_to_a_newcomer(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> None:
        await self._softly(
            "record_shown_to_a_newcomer",
            lambda: self._inner.record_shown_to_a_newcomer(
                sport=sport, week=week, player_ids=player_ids
            ),
            None,
        )

    async def times_shown_to_a_newcomer(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> Mapping[UUID, int]:
        # Zero for everybody, which is the answer that binds nothing: a cap that
        # bound because a cache was restarting would drop a lift on a suspicion
        # of a suspicion.
        return await self._softly(
            "times_shown_to_a_newcomer",
            lambda: self._inner.times_shown_to_a_newcomer(
                sport=sport, week=week, player_ids=player_ids
            ),
            {player_id: 0 for player_id in player_ids},
        )

    async def all_times_shown(
        self, *, sport: Sport, week: ExposureWeek
    ) -> Mapping[UUID, int]:
        return await self._softly(
            "all_times_shown",
            lambda: self._inner.all_times_shown(sport=sport, week=week),
            {},
        )

    async def publish_busy_threshold(
        self, *, sport: Sport, week: ExposureWeek, threshold: int
    ) -> None:
        await self._softly(
            "publish_busy_threshold",
            lambda: self._inner.publish_busy_threshold(
                sport=sport, week=week, threshold=threshold
            ),
            None,
        )

    async def busy_threshold(self, *, sport: Sport, week: ExposureWeek) -> int | None:
        # `None` is already the port's *no roll has published one yet*, and the
        # rung that reads it does not fire either way. There is nothing to
        # invent here, and inventing a threshold would dock somebody.
        return await self._softly(
            "busy_threshold",
            lambda: self._inner.busy_threshold(sport=sport, week=week),
            None,
        )


class FailSoftSuppressionLedger(_FailSoft):
    """A ``SuppressionLedger`` whose outage costs repetition and nothing else.

    A deck dealt during an outage may show a card the player passed on last
    week. That is the price, it is named here rather than discovered, and it is
    strictly the better half of the trade: the alternative is a player opening
    an empty deck in a city that has people in it.
    """

    _ledger = "suppression"

    def __init__(self, inner: SuppressionLedger) -> None:
        self._inner = inner

    async def suppress(
        self, *, passer_id: UUID, passed_id: UUID, for_days: int
    ) -> None:
        # A pass whose suppression could not be written is still a pass: the
        # durable record is written by the use case that owns it, and this is
        # only the live half. Failing the request would refuse the player's own
        # action over a cache.
        await self._softly(
            "suppress",
            lambda: self._inner.suppress(
                passer_id=passer_id, passed_id=passed_id, for_days=for_days
            ),
            None,
        )

    async def suppressed_for(
        self, *, passer_id: UUID, candidate_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        return await self._softly(
            "suppressed_for",
            lambda: self._inner.suppressed_for(
                passer_id=passer_id, candidate_ids=candidate_ids
            ),
            frozenset(),
        )


class FailSoftPromptLedger(_FailSoft):
    """A ``PromptLedger`` whose outage costs a question and nothing else.

    The degraded read is *no prompt standing*, which is the same thing the
    ledger's own emptiness means and is the safe direction in both halves: a
    question that was not asked this week is asked next week, where a question
    asked about a value that has since changed is the platform being wrong out
    loud. The degraded write is the same trade seen from the loop's end — the
    next tick raises it again.
    """

    _ledger = "prompt"

    def __init__(self, inner: PromptLedger) -> None:
        self._inner = inner

    async def raise_prompt(
        self,
        *,
        player_id: UUID,
        prompt: Prompt,
        sport: Sport | None = None,
        detail: str | None = None,
    ) -> None:
        await self._softly(
            "raise_prompt",
            lambda: self._inner.raise_prompt(
                player_id=player_id, prompt=prompt, sport=sport, detail=detail
            ),
            None,
        )

    async def raised_for(
        self, *, player_id: UUID, sport: Sport
    ) -> Mapping[Prompt, str | None]:
        return await self._softly(
            "raised_for",
            lambda: self._inner.raised_for(player_id=player_id, sport=sport),
            {},
        )
