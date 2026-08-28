"""*Let's play* — the first durable ledger in the module, and its origin key.

One tap, costing nothing, that actually does something: the sender rises in the
recipient's next search by a flat ``+14``, **printed**, so the lift is never
mistaken for a match. This is what turns the engine from a ranking into a product
loop, and everything about the shape here is chosen against two refusals.

**A one-sided yes is never revealed to its recipient as an inbox**
(``docs/adr/0109``). That is what keeps saying yes low-stakes, and it is
structural rather than a filter somebody remembers: :class:`InterestLedger` has
no method that answers *who has said yes to me*. What it can answer is *which of
these specific people said yes to me* — asked over a candidate set the searcher
was going to be shown anyway — and *which of my own yeses came back*. An inbox is
not a query this port can express.

**Nothing quietly decays** (``docs/adr/0127``). A yes lasts ``ttl_days`` and then
**lapses**; the lift is flat for the whole of that life and then absent, with no
final-week taper, because the age of the yes already crosses as evidence and a
taper would charge one fact twice — once visibly and once not. At the cap the
platform **refuses** rather than silently shortening a yes the player already
sent: a soft cap reaches *backwards*, under a rule nobody was told, because a
twenty-first arrived.

**The origin key is two columns on the interest row, never a third table**
(``search-telemetry.md`` §4). The link is 1:1 with the interest, a separate table
buys a join for nothing, and when ``matches`` lands the chain is
``match ← interest ← search`` — still foreign keys, still no third table. An
interest citing a search that is unknown, that belongs to somebody else, or that
never showed that person **is refused and never linked as null**: a silently
dropped link is a denominator that lies.

**Durable, in the module, and no suppression cache stands in for it**
(``the-engine.md`` §12). It is the one thing in this context a human would miss —
a person reached out to another person — so unlike exposure and suppression it is
a row rather than a key with a TTL. It is durable **without being an aggregate
with a life story**: a small fact with an expiry date, no event stream, no
outbox.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Sport, invariant


@final
@dataclass(frozen=True, slots=True)
class OriginKey:
    """Where a yes came from: **the search, and the position in it.**

    ``position`` always resolves against ``band = RETURNED``, because no route
    ever returns a near-miss row for a player to act on — so a position here that
    could not be found in the returned band is not a position at all, and the
    write is refused rather than recorded with a null.
    """

    search_id: UUID
    position: int

    def __post_init__(self) -> None:
        invariant(
            self.position >= 1,
            f"an origin position below one: {self.position}",
        )


@final
@dataclass(frozen=True, slots=True)
class Interest:
    """One *Let's play* yes: silent, one-directional, sport-scoped, expiring.

    **The expiry is dated at birth and never announced at death**
    (``docs/adr/0127`` §5). ``expires_at`` is on the row from the moment it is
    created, so the player can see what is still live; on expiry the row is
    simply gone, and there is no ``expired`` state and no archive — a list of
    yeses that were not returned is the inverted shape of what ``docs/adr/0109``
    refused.

    It carries no *state*. Whether it is live, whether it is outstanding and
    whether it is mutual are all read off dates and the other person's own row —
    the same rule the newcomer window is written under, for the same reason: a
    stored flag goes stale hourly and a date does not.
    """

    from_player_id: UUID
    to_player_id: UUID
    sport: Sport
    at: datetime
    expires_at: datetime
    origin: OriginKey

    def __post_init__(self) -> None:
        invariant(
            self.from_player_id != self.to_player_id,
            "a *Let's play* sent to yourself",
        )
        invariant(
            self.expires_at > self.at,
            f"a yes that expired before it was sent: {self.expires_at} <= {self.at}",
        )

    def is_live_at(self, now: datetime) -> bool:
        """Whether the yes still stands. **A date, never a flag.**"""

        return now < self.expires_at

    def days_ago_at(self, now: datetime) -> int:
        """How old the yes is, in whole days — **the lift's recorded input.**

        Never a boolean, and that is ``search-telemetry.md`` §3's rule about this
        exact column: ``docs/adr/0127`` makes the ``+14`` flat, so a boolean would
        be the *sufficient* input and the age would be lost within the month. It
        is the entire x-axis of *acceptance by age of yes*.
        """

        return max(0, (now - self.at).days)


def expires_at(at: datetime, ttl_days: int) -> datetime:
    """When a yes sent now will lapse. **Flat, and then absent.**

    ``ttl_days`` is passed in and never known here: it is the released ruleset's
    ``interest.ttl_days``, and a mechanism holding its own copy of a released
    number would be a second place for it to be true. The ledger is the store;
    the number is the product decision.
    """

    invariant(ttl_days >= 1, f"an interest TTL of {ttl_days} days")
    return at + timedelta(days=ttl_days)


@final
@dataclass(frozen=True, slots=True)
class Lapsed:
    """What one run of the expiry loop removed, and what it cost nobody.

    ``never_lifted`` is the day-one falsifier for ``INTEREST_TTL``
    (``the-five-numbers.md`` §8): *yeses that expired having never lifted
    anybody* — the other person never ran a search while the yes stood. If most
    yeses expire unfired, 21 days is answering the wrong question and the pool is
    too quiet.

    It is counted **as the rows are removed**, because that is the last moment
    they exist. A lapsed row leaves no trace by design, so a figure computed a day
    later would have nothing to count — which is the same argument that made the
    pass record durable one ledger over, arriving at the opposite answer because
    an interest is a statement about *now* and a pass is a statement about a pair.
    """

    removed: int
    never_lifted: int

    def __post_init__(self) -> None:
        invariant(
            0 <= self.never_lifted <= self.removed,
            f"{self.never_lifted} of {self.removed} yeses lifted nobody",
        )


@runtime_checkable
class InterestLedger(Protocol):
    """The durable record of every *Let's play*, and the only shapes it answers in.

    **There is no method here that lists who has said yes to me**, and that
    absence is the contract rather than an omission. ``docs/adr/0109`` banks a
    one-sided yes under a promise of silence, and a port that could enumerate an
    inbox is a port a screen eventually reads.

    Every read is keyed the way the search path reads: **one keyed read over a
    population**, never a query per row. That is the shape every set-membership
    read in this module has, and it is here for the same reason — the population
    is decided by the bounding box, once, before anything is scored.
    """

    async def find(
        self,
        *,
        from_player_id: UUID,
        to_player_id: UUID,
        sport: Sport,
        now: datetime,
    ) -> Interest | None:
        """This person's own live yes to that person, in that sport, if any.

        **Idempotency is a read and then a decision, not a database trick.** A
        second yes returns the first unchanged — it does not re-date the expiry,
        does not spend a cap slot and does not move the origin key, because all
        three would let a client extend a yes indefinitely by tapping a button
        that says it costs nothing.

        A lapsed row is not returned: it is gone, and *lapsed* and *never sent*
        are deliberately the same answer here.
        """
        ...

    async def record(self, interest: Interest) -> None:
        """Write one yes. **In the caller's own transaction, never committed here.**

        The transaction boundary is the command's decision, exactly as it is for
        the search record beside it.
        """
        ...

    async def outstanding(
        self, *, player_id: UUID, sport: Sport, now: datetime
    ) -> int:
        """How many of this player's yeses are still in flight, in this sport.

        **Outstanding means sent, unexpired and not yet mutual** — a mutual has
        been answered and is no longer in flight (``docs/adr/0127`` §3). That
        definition is the port's and not a caller's: a cap counted one way at the
        write and another on the screen that shows it is a refusal the player
        cannot predict, which is the exact failure §4 of that record exists to
        prevent.
        """
        ...

    async def outgoing(
        self, *, player_id: UUID, now: datetime
    ) -> tuple[Interest, ...]:
        """Every live yes this player has **sent**, newest first.

        Their own rows, in every sport. The mutuals are in here too — a mutual is
        still a yes this player sent — and which of them came back is
        :meth:`mutual`'s answer, over the same rows.
        """
        ...

    async def mutual(
        self, *, player_id: UUID, now: datetime
    ) -> tuple[Interest, ...]:
        """This player's own live yeses that **came back**.

        The one shape in which somebody else's yes reaches its recipient, and it
        reaches them only because they said yes first: **a mutual is told to both
        sides**, and a one-sided yes is told to nobody.

        It answers in *this player's own rows* rather than in the other person's,
        which is what keeps the inbox unrepresentable: every row here is one this
        player wrote, and the other person's row is read only to decide whether
        this one is returned at all. A subset of :meth:`outgoing`, by
        construction — so a caller can split one list rather than merge two.
        """
        ...

    async def days_ago_towards(
        self,
        *,
        player_id: UUID,
        sport: Sport,
        senders: Collection[UUID],
        now: datetime,
    ) -> Mapping[UUID, int]:
        """Which of **these** people said *Let's play* to this player, and how long ago.

        The lift's read, and the only read that answers about incoming yeses at
        all. It is bounded by ``senders`` — the candidates the bounding box
        already admitted — so it cannot become an inbox: asking it about the whole
        city would mean already having a list of the whole city.

        Answers only about ids it was asked about, and names **only** the ones who
        said yes; an id absent from the answer said nothing, which is the same
        collapse every set read in this module makes.
        """
        ...

    async def lapse(self, *, now: datetime) -> Lapsed:
        """Remove every yes whose ``expires_at`` has passed. **The whole of expiry.**

        Safe beside itself with no lock (``docs/adr/0092``): removing a row twice
        removes it once, and two processes racing over the same batch leave what
        one leaves. It counts what it removed on the way out, because
        :class:`Lapsed`'s docstring says why that is the last moment to.
        """
        ...
