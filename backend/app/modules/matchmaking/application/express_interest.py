"""*Let's play* — one tap, costing nothing, that actually does something.

**The order of the five things this use case does is load-bearing**, the same way
the search's is.

1. It resolves the **origin key** off the cited search's own record
   (``origins.py``, shared with the pass). That read is the authorization check,
   the sport check and the position lookup at once, and it happens **first**: an
   interest whose origin cannot be proved is refused before anything else is
   considered, because a link that cannot be made true is not a link to drop
   quietly.
2. It looks for an **existing live yes**, and keeps it unchanged if there is one.
   A second tap creates nothing, spends no cap slot and — the part that matters —
   does **not** re-date the expiry, because a button that says it costs nothing
   must not be a way to keep a yes alive for ever.
3. It checks the **cap**, and refuses at it. Nothing of the player's is quietly
   shortened to make room (``docs/adr/0127`` §3).
4. It writes the row, and then reads whether the yes is **mutual**.
5. When it is, it **opens the challenge inline** and commits the two together.

**The mutual read moved before the commit, and the reason is a promise.** E7 says
*that player has left the deck for good, because you now have an open game
together* — and with the outbox in the middle that sentence is false for however
long the worker takes. So the challenge is minted in this transaction, through a
port the other context signs (``domain/mutual_challenge.py``), and the yes and the
game commit together or neither does.

**Nobody is notified.** A one-sided yes is silent: it becomes visible only when
the other person goes looking for a game, and then only as a lift with its reason
printed. The one thing this answer tells the sender about the recipient is whether
the yes was **mutual** — and that is only knowable because they had already said
yes themselves.

**No event and no outbox for the yes itself.** Interest is durable without being
an aggregate with a life story, and nothing subscribes to one being written: the
lift is a read on the next search, and a mutual is what two rows facing each other
already say. What is *not* true any more is that nothing downstream happens — the
mint above is a second write in the same transaction, and it is a call rather than
a subscription precisely so that it cannot be late.

**A mint that is refused is not a failure of this use case.** The other context
re-verifies the same gates a send does, because a *Let's play* may cite a search
from a month ago and a search record never expires; when it refuses, it mints
nothing and says so by answering nothing. The yes stands, ``mutual`` is still
``True``, and the two of them have a mutual with no game opened — which is the
honest state and is exactly what a block taken between two stale yeses should
produce.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.engines.matchfit.ruleset import Ruleset
from app.kernel import Clock, Sport
from app.modules.matchmaking.application.commands import ExpressInterestCommand
from app.modules.matchmaking.application.origins import resolve_origin
from app.modules.matchmaking.domain.errors import OutstandingInterestCapReached
from app.modules.matchmaking.domain.mutual_challenge import (
    MutualChallengeMinting,
)
from app.modules.matchmaking.domain.interest import (
    Interest,
    InterestLedger,
    OutstandingCount,
    expires_at,
)
from app.modules.matchmaking.domain.search_store import SearchStore


@final
@dataclass(frozen=True, slots=True)
class ExpressedInterest:
    """What the sender is told back, and it is deliberately little.

    The yes itself — so the client can render *until when* off a moment the
    backend computed rather than one a phone derived — plus the pair a cap the
    player cannot see would otherwise hide, plus the one fact about the other
    person they have earned by having been said yes to first.

    ``created`` is ``False`` on a repeat tap. It says *nothing changed* rather
    than *nothing happened*: the yes stands, with the expiry it was born with.
    """

    interest: Interest
    #: Where this sport now stands against its cap — **the same type the screen
    #: renders**, so the number after a tap and the number on the list cannot be
    #: two different readings of one rule.
    outstanding: OutstandingCount
    mutual: bool
    created: bool


@final
class ExpressInterest:
    """One yes, written once, cited to the search that surfaced the person."""

    def __init__(
        self,
        *,
        clock: Clock,
        ruleset: Ruleset,
        interest: InterestLedger,
        searches: SearchStore,
        challenges: MutualChallengeMinting,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._clock = clock
        self._ruleset = ruleset
        self._interest = interest
        self._searches = searches
        self._challenges = challenges
        self._uow = unit_of_work

    async def execute(self, command: ExpressInterestCommand) -> ExpressedInterest:
        now = self._clock.now()
        rules = self._ruleset.interest
        origin = await resolve_origin(
            self._searches,
            actor_id=command.from_player_id,
            subject_id=command.to_player_id,
            sport=command.sport,
            search_id=command.search_id,
        )

        standing = await self._interest.find(
            from_player_id=command.from_player_id,
            to_player_id=command.to_player_id,
            sport=command.sport,
            now=now,
        )
        if standing is not None:
            yes, created = standing, False
        else:
            standing_count = await self._counted(
                command.from_player_id, command.sport, now
            )
            if standing_count.reached:
                raise OutstandingInterestCapReached(
                    f"you already have {standing_count.outstanding} outstanding "
                    f"*Let's play* yeses for {command.sport.value}"
                )
            yes = Interest(
                from_player_id=command.from_player_id,
                to_player_id=command.to_player_id,
                sport=command.sport,
                at=now,
                expires_at=expires_at(now, rules.ttl_days),
                origin=origin,
            )
            await self._interest.record(yes)
            created = True

        answer = await self._answer(yes, now=now, created=created)
        # **One commit, whichever branch ran.** A repeat tap writes no interest
        # row and may still have opened a game: the pair could have been refused
        # a mint when the first yes landed — a gate that was closed then and is
        # open now — and there is nothing else that would ever come back for it.
        await self._uow.commit()
        return answer

    async def _answer(
        self, yes: Interest, *, now: datetime, created: bool
    ) -> ExpressedInterest:
        """The yes, the pair the cap is shown through, and whether it came back.

        The outstanding count is re-read **after** the write rather than adjusted
        from the number the cap was checked against: the two are the same query,
        and a caller adding one to the other would be a second definition of
        *outstanding* — the one thing ``docs/adr/0127`` §4 says the player must be
        able to predict a refusal from.

        The mutual read is a :meth:`find` in the **other** direction, which is
        the only shape in which somebody else's yes may be looked at: it answers
        about one named pair, on a request the recipient of that yes made
        themselves, and it can say nothing about anybody who has not been said
        yes to.

        **The mint hangs off that read and never off ``created``.** It is the
        second yes that makes a game, and whether *this* tap wrote a row is a
        different question — a repeat tap on a pair whose mint was refused is the
        only occasion the platform ever gets to try again.

        ``mutual`` is what the two rows say and is **not** narrowed to *a game
        was opened*: the mutual is true either way, and reporting it as false
        because a gate refused would tell the sender something about the other
        person that no refusal here is allowed to say.
        """

        theirs = await self._interest.find(
            from_player_id=yes.to_player_id,
            to_player_id=yes.from_player_id,
            sport=yes.sport,
            now=now,
        )
        if theirs is not None:
            await self._challenges.open_from_mutual_interest(
                sport=yes.sport,
                player_id=yes.from_player_id,
                other_player_id=yes.to_player_id,
            )
        return ExpressedInterest(
            interest=yes,
            outstanding=await self._counted(yes.from_player_id, yes.sport, now),
            mutual=theirs is not None,
            created=created,
        )

    async def _counted(
        self, player_id: UUID, sport: Sport, now: datetime
    ) -> OutstandingCount:
        """This sport's live count beside the cap in force.

        One helper, so the number the cap is checked against and the number the
        answer carries are the same read of the same rule. A sport absent from
        the ledger's answer has nothing in flight, which is the zero it is.
        """

        counts = await self._interest.outstanding(player_id=player_id, now=now)
        return OutstandingCount(
            sport=sport,
            outstanding=counts.get(sport, 0),
            cap=self._ruleset.interest.outstanding_cap_per_sport,
        )
