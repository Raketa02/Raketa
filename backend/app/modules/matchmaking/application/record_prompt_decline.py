"""*Not now* — the answer that writes no value, in two steps.

1. It refuses a decline of the one prompt that buys no silence, before anything
   is written.
2. It writes the **durable row and commits**. That row is the evidence, and it
   does not expire.

**There is no third step, and its absence is the design.** A pass writes a
suppression into a cache after its commit; this one does not, because the row
*is* the gate — the filter reads this table directly and the window is a cut-off
on the moment, so there is no second store for the two halves to disagree about.
That discharges one of ADR-0094's own stated costs: *"two things now have to
agree about the same suppression window, and a change to one that forgets the
other produces either nagging or silence."*

**It retires nothing.** The standing prompt in the ephemeral ledger is left
exactly where it is, to expire on ``PROMPT_TTL`` like any other, because
``PromptLedger`` is *two methods and no delete* — a method to clear one would be
a method something reaches for on the request path, which is how a question
nobody answered quietly stops being asked. Suppressing stops the next **raise**
and clears nothing.

**Nothing is returned**, and nothing is notified. A second decline of the same
question is a second row with its own moment; nothing counts them, and what it
buys is exactly the same month the first did.
"""

from __future__ import annotations

from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.matchmaking.application.commands import RecordPromptDeclineCommand
from app.modules.matchmaking.domain.declines import (
    PromptDecline,
    PromptDeclineLedger,
    keyed_sport,
    suppresses,
)
from app.modules.matchmaking.domain.errors import PromptDoesNotSuppress


@final
class RecordPromptDecline:
    """One *not now*: a row that is kept, and a question that is not re-asked."""

    def __init__(
        self,
        *,
        clock: Clock,
        declines: PromptDeclineLedger,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._clock = clock
        self._declines = declines
        self._uow = unit_of_work

    async def execute(self, command: RecordPromptDeclineCommand) -> None:
        """Record it and commit it. **Answers nothing.**

        The return type is the contract as much as the route's ``204`` is: a use
        case that answered something would be a shape a route could be tempted to
        render, and *no route ever returns a decline* would then be a matter of
        route discipline rather than of what exists.
        """

        if not suppresses(command.prompt):
            raise PromptDoesNotSuppress(
                f"{command.prompt.value} is asked again on the next search "
                "and a decline of it buys no silence"
            )
        await self._declines.record(
            PromptDecline(
                player_id=command.player_id,
                prompt=command.prompt,
                # The sport the client sent is *which screen asked*; what the
                # silence is keyed on is decided here, from the prompt alone.
                sport=keyed_sport(command.prompt, command.sport),
                at=self._clock.now(),
            )
        )
        await self._uow.commit()
