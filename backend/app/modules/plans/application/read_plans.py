"""Reading a player's plans back. **The clock is read once, and it does not
travel.**

One row for every court this reader may plan, written or not, joined by
challenge id — the only plan read there is (``docs/adr/0148`` §7 as amended by
``docs/adr/0164``). Now issues two reads and joins them by the game's
``challenge_id``; the conversation draws the same cached list by its own.

**There is no ``read_at`` on the answer, and that is a decision rather than an
omission** (``docs/adr/0148`` §10). ADR-0143 §7 put an instant at the envelope so
a client's countdowns and the standings beside them could not come from two
readings of the clock — and a *second* envelope carrying a second instant is
exactly what that rule exists to prevent. **A plan folds nothing against the
clock**: the conversion consults no *now*, and a plan's day and hour are
wall-clock facts drawn literally and never counted down. There is no instant for
it to have been folded against, so the card is folded against ``games``'
``read_at`` and **Now has one clock by construction** rather than by convention.

The clock is still read *here*, once, and it is spent entirely on the port: which
courts are still open to planning is a standing, and a standing is folded against
an instant. It buys the order and it never reaches the answer.

**Ordered like its owner** — newest arrangement first, on each court's anchor —
so the two lists Now joins arrive in the same order and a client that renders
them side by side does not have to sort one of them itself.
"""

from __future__ import annotations

from typing import final

from app.kernel import Clock, instant
from app.modules.plans.application.commands import ReadPlansCommand
from app.modules.plans.application.plan_row import PlanRow
from app.modules.plans.domain.plan import Plan
from app.modules.plans.domain.ports import PlanDirectory, PlannableCourts


@final
class ReadPlans:
    """Every plan for the courts this player holds an accepted seat on."""

    def __init__(
        self, *, plans: PlanDirectory, courts: PlannableCourts, clock: Clock
    ) -> None:
        self._plans = plans
        self._courts = courts
        self._clock = clock

    async def execute(self, command: ReadPlansCommand) -> tuple[PlanRow, ...]:
        """The rows, newest arrangement first.

        **The courts are asked first and the plans are asked about their
        answer**, which is what makes this read gated without a gate: a court
        the reader holds no accepted seat on never becomes an id this asks
        about, so there is no id to refuse and no ``plan_not_found`` on a read
        path.

        **A court with nothing agreed is a row with three empty slots**
        (``docs/adr/0164`` §4). The store spells that by having no stream, and
        this spells it as an unwritten plan — the same value the write path
        starts from — because the client needed the row for two things, the
        anchor and the fact that there is a plan to draw, and a missing row
        would say neither.
        """

        courts = await self._courts.plannable_for(
            command.reader_id, now=instant(self._clock.now())
        )
        written = {
            plan.challenge_id: plan
            for plan in await self._plans.for_challenges(tuple(courts))
        }
        return tuple(
            sorted(
                (
                    PlanRow(
                        plan=written.get(challenge_id, Plan.unwritten(challenge_id)),
                        anchor=court.anchor,
                    )
                    for challenge_id, court in courts.items()
                ),
                key=lambda row: (row.anchor, row.plan.challenge_id),
                reverse=True,
            )
        )
