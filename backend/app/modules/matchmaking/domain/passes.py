"""*Not today* — the quietest control on the platform, and the durable row under it.

A pass is one tap on a deck card. It keeps somebody out of **my** deck for
``PASS_SUPPRESS`` days and reaches nothing else, and it is invisible to
everybody, the passer included: **no route ever returns one**, not as a card, not
as a count, not as *"you have passed on twelve people"*.

**The gate is the cache; the evidence is the row** (``the-engine.md`` §12). The
live suppression is the Redis TTL on ``ledgers.SuppressionLedger`` and it fails
soft; what is here is the record it is derived from, and the two are different
stores for one reason. ``PASS_SUPPRESS``'s only falsifier is *pass rate
on **re-shown** profiles*, and a suppression that has lapsed leaves no trace the
pair was ever passed — so at the exact moment a re-show happens, the fact that
makes it a re-show has expired. The Origin key was bought for that falsifier and
pays only half of it: it records where a pass came from, never that a later card
is the same person coming back.

**A pass record does not expire.** An interest lapses and its row is deleted;
this one is kept, and joins ``docs/adr/0104``'s rule that erasure is the only
thing that ever removes a row.

**Three boundaries, all of them the opposite of a Block's**
(``docs/adr/0128``), because *a pass is a statement about my deck and a block is
a statement about a person*: deck only, one-directional, and never escalating. Two
of the three are structural in the ledger port beside this one; the first is the
deck's own to honour, and the named cost is *pass on somebody tonight, find them
third in your shortlist tomorrow.*
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Sport, invariant
from app.modules.matchmaking.domain.interest import OriginKey


@final
@dataclass(frozen=True, slots=True)
class Pass:
    """One *not today*, and where the card that prompted it came from.

    ``(passer, passed, sport, at, search_id, position)`` — the shape
    ``search-telemetry.md`` §6 names, with the last two carried as the Origin key
    the interest row beside it already carries.

    There is no ``expires_at`` and no state. The 30-day window belongs to the
    suppression cache; this row is what happened, and what happened does not
    lapse.
    """

    passer_id: UUID
    passed_id: UUID
    sport: Sport
    at: datetime
    origin: OriginKey

    def __post_init__(self) -> None:
        invariant(
            self.passer_id != self.passed_id,
            "a pass on yourself",
        )


def suppression_lapsed_at(
    passed_at: datetime, now: datetime, suppress_days: int
) -> bool:
    """Whether the window a pass bought has run out. **A date, never a flag.**

    The same rule the newcomer window and the interest expiry are written under,
    for the same reason: a stored *is it still suppressed* goes stale hourly and
    a date does not. Here it also keeps the answer **independent of the cache**,
    which is what the re-show flag needs — the row says when, the ruleset says
    how long, and neither of them is a key that may have been evicted.

    ``suppress_days`` is passed in and never known here: it is the released
    ruleset's ``interest.pass_suppress_days``, and a mechanism holding its own
    copy of a product number would be a second place for it to be true.
    """

    invariant(suppress_days >= 1, f"a suppression of {suppress_days} days")
    return now - passed_at >= timedelta(days=suppress_days)


@runtime_checkable
class PassLedger(Protocol):
    """Every pass ever made, and the only two shapes it answers in.

    **Write-only from the outside.** There is no method here that lists a
    player's passes, counts them, or answers *who has passed on me* — the second
    for the reason :class:`~app.modules.matchmaking.domain.ledgers.SuppressionLedger`
    has no such shape, and the first two because ``the-play-screens.md`` §7
    refuses the passer their own list as firmly as it refuses the passed theirs.
    What the ledger answers is one question the deck asks about the deal it is
    dealing, and one that a background reader will ask about the corpus.
    """

    async def record(self, passed_on: Pass) -> None:
        """Write one pass. **In the caller's own transaction, never committed here.**

        Append-only. A second pass on the same person is a second row with its
        own moment and its own origin — nothing counts them and nothing may, so
        the rows are the evidence rather than a tally somebody could grow a
        penalty out of (``docs/adr/0128`` §3). It is only reachable thirty days
        after the first anyway, because a live suppression keeps the card out of
        the deck.
        """
        ...

    async def last_passed_at(
        self, *, passer_id: UUID, sport: Sport, candidate_ids: Collection[UUID]
    ) -> Mapping[UUID, datetime]:
        """When the passer last passed on each of these, in this sport.

        One keyed read over the deal, never a query per card, and it answers only
        about ids it was asked about — the shape every set-membership read in
        this module has. Somebody never passed on is **absent**, which is not a
        date and is not a zero.

        **It answers a moment rather than a boolean, and that is the whole of
        what makes the re-show flag trustworthy.** ``suppression_lapsed`` is
        *whether this pairing had a pass whose window has since lapsed*, and both
        halves of that are computable from here: the pass, and its age against
        the released ``PASS_SUPPRESS``. Read as a boolean instead, the second
        half would have to come from the suppression **cache** — which fails
        soft, so during an outage a live-suppressed player is dealt and would be
        stamped a re-show they are not, corrupting *pass rate on re-shown
        profiles* at exactly the moment extra re-shows are happening. The record
        does not fail soft, and this is why it is read.
        """
        ...
