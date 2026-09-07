"""*Not today* — the quietest control on the platform, in three steps.

1. It resolves the **origin key** off the cited search's own record
   (``origins.py``, shared with the yes). A pass whose origin cannot be proved is
   refused before anything else happens, because ``PASS_SUPPRESS``'s only
   falsifier is *pass rate on **re-shown** profiles* and a pass that came from
   nowhere is counted against nothing.
2. It writes the **durable row and commits**. That row is the evidence, and it
   does not expire.
3. It writes the **suppression**, after the commit, into a cache that fails soft.
   That key is the gate, and it lapses in thirty days.

**The gate is the cache; the evidence is the row** (``the-engine.md`` §12), and
the order above is what that sentence costs. A suppression written before the
record could outlive a transaction that rolled back — a card silently gone from a
deck with nothing anywhere saying why. A suppression that could not be written at
all is a repeated card, which is the cheaper failure by a wide margin: applying
*a gate that cannot be evaluated excludes* to a courtesy would empty the deck
rather than protect anybody.

**Nothing is returned.** Not to the passer, not as a count, not as *"you have
passed on twelve people"* — §21's refusal, and the route answers ``204`` because
there is no shape a pass may cross the wire in.

**Nothing is notified**, and nothing escalates. A second pass on the same person
buys the same thirty days and no more; it is only reachable after the first has
lapsed anyway, because a live suppression keeps the card out of the deck. Where
repetition leads is a **Block**, which exists, is reversible, and requires
somebody to mean it (``docs/adr/0128``).
"""

from __future__ import annotations

from typing import final

from app.application.ports import UnitOfWork
from app.engines.matchfit.ruleset import Ruleset
from app.kernel import Clock
from app.modules.matchmaking.application.commands import RecordPassCommand
from app.modules.matchmaking.application.origins import resolve_origin
from app.modules.matchmaking.domain.ledgers import SuppressionLedger
from app.modules.matchmaking.domain.passes import Pass, PassLedger
from app.modules.matchmaking.domain.search_store import SearchStore


@final
class RecordPass:
    """One pass: a row that is kept, and a key that lapses."""

    def __init__(
        self,
        *,
        clock: Clock,
        ruleset: Ruleset,
        passes: PassLedger,
        suppression: SuppressionLedger,
        searches: SearchStore,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._clock = clock
        self._ruleset = ruleset
        self._passes = passes
        self._suppression = suppression
        self._searches = searches
        self._uow = unit_of_work

    async def execute(self, command: RecordPassCommand) -> None:
        """Record it, commit it, then suppress it. **Answers nothing.**

        The return type is the contract as much as the route's ``204`` is: a use
        case that answered something would be a shape a route could be tempted to
        render, and *no route ever returns a pass* would then be a matter of
        route discipline rather than of what exists.
        """

        now = self._clock.now()
        origin = await resolve_origin(
            self._searches,
            actor_id=command.passer_id,
            subject_id=command.passed_id,
            sport=command.sport,
            search_id=command.search_id,
        )
        await self._passes.record(
            Pass(
                passer_id=command.passer_id,
                passed_id=command.passed_id,
                sport=command.sport,
                at=now,
                origin=origin,
            )
        )
        await self._uow.commit()
        # After the commit, deliberately, and outside any refusal: the row is the
        # fact and this is the courtesy derived from it. The window is passed in
        # from the released ruleset because a mechanism holding its own copy of a
        # product number would be a second place for it to be true.
        await self._suppression.suppress(
            passer_id=command.passer_id,
            passed_id=command.passed_id,
            for_days=self._ruleset.interest.pass_suppress_days,
        )
