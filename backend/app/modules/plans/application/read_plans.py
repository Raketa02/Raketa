"""Reading a player's plans back. **The clock is read once, and it does not
travel.**

Every plan for the games this reader is on the court of, joined by game id — the
only plan read there is (``docs/adr/0148`` §7). Now issues two reads and joins
them; the conversation draws the same cached list.

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
games are still open to planning is a standing, and a standing is folded against
an instant. It buys the order and it never reaches the answer.

**Ordered like its owner** — newest arrangement first, on ``games``' own
``planned_at`` — so the two lists Now joins arrive in the same order and a client
that renders them side by side does not have to sort one of them itself.
"""

from __future__ import annotations

from typing import final

from app.kernel import Clock, instant
from app.modules.games.domain.ports import PlanningCourt
from app.modules.plans.application.commands import ReadPlansCommand
from app.modules.plans.domain.plan import Plan
from app.modules.plans.domain.ports import PlanDirectory


@final
class ReadPlans:
    """Every plan for the games this player is on the court of."""

    def __init__(
        self, *, plans: PlanDirectory, court: PlanningCourt, clock: Clock
    ) -> None:
        self._plans = plans
        self._court = court
        self._clock = clock

    async def execute(self, command: ReadPlansCommand) -> tuple[Plan, ...]:
        """The plans, newest arrangement first.

        **The court is asked first and the plans are asked about its answer**,
        which is what makes this read gated without a gate: a game the reader was
        not on the court of never becomes a game id this asks about, so there is
        no id to refuse and no ``plan_not_found`` on a read path.

        **A game with nothing agreed is simply absent.** *No plan* is the state
        such a game draws, and the directory spells it by having no stream to
        return — never by a row of three nulls, which a client could not tell
        from a plan somebody emptied and nothing here can produce.
        """

        games = await self._court.plannable_for(
            command.reader_id, now=instant(self._clock.now())
        )
        found = await self._plans.for_games(tuple(games))
        return tuple(
            sorted(
                found,
                key=lambda plan: (games[plan.game_id].planned_at, plan.game_id),
                reverse=True,
            )
        )
