"""The two ledgers that are allowed to be lossy.

**The gate is the cache; the evidence is the row** (``the-engine.md`` §12,
``docs/adr/0093``). Everything the matcher must be able to say a year from now —
a search it ran, an interest somebody sent, a pass somebody made — is a durable
row somewhere else. What lives here is the *live* half of two of those facts:
how often a player has been shown this week, and whom this player has recently
passed on. Both are recomputable-in-effect, cheap to lose, and each carries a
TTL that destroys it on purpose.

**Both fail soft, and that is a promise about the ports rather than a hope about
their callers.** ``docs/adr/0095``'s rule — *a gate that cannot be evaluated
excludes* — reads like it should reach these, and it must not: applying it to a
courtesy would **empty the deck rather than protect anybody**. A suppression is
*do not show me that person again just yet*; a block is a safety control. So an
unreachable store degrades **ordering and repetition** and nothing else, and
that is enforced one layer out, at
``matchmaking/infrastructure/fail_soft_ledgers.py``, so that no caller can get
it wrong and no caller has to remember to.

**Neither ledger is the evidence for anything.** Nothing here may be read to
answer a question about the past:

- *Was this player shown to anybody in week 34?* is answered by the search
  record's returned rows, which are durable and unexpiring
  (``docs/adr/0104``) — the exposure Gini is computed from those, never from
  this (``the-replay-harness.md`` §8).
- *Did these two ever get passed on?* is answered by the **durable pass
  record** (``docs/adr/0128``), because ``PASS_SUPPRESS``'s only falsifier is
  *pass rate on re-shown profiles*, and a lapsed suppression leaves no trace
  the pair was ever passed. That is the exact fact a TTL destroys, and it is
  why the record and the suppression are two different stores rather than one.

A read that came back empty and a fact that never happened are **the same answer
here**, and a caller that needs to tell them apart is holding the wrong store.
``tests/unit/test_ledgers.py`` asserts that neither port offers a shape that
could distinguish the two.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport, invariant
from app.modules.matchmaking.domain.ports import FailPosture
# The third ephemeral ledger, declared with its own vocabulary in ``prompts.py``
# because a standing question is not an exposure count — but registered here,
# where *how a ledger fails* is stated once for all of them.
from app.modules.matchmaking.domain.prompts import PromptLedger

#: How many weeks of exposure the ledger keeps before the store drops it.
#:
#: **Domain, not configuration**, on the rule the photo sweep's retention window
#: already established: how *long* a fact survives decides what can be asked of
#: it, and an environment that could shorten it would be an environment that
#: selects behaviour. What is configuration is the roll's cadence.
#:
#: Three, from ``matchmaking-engine.md`` §14.1, and it is deliberately more than
#: the one week anything reads: a roll running at a week boundary, and a search
#: served moments after one, must both still find the week they were asked
#: about. One week of retention would make the boundary a data loss rather than
#: a rollover.
EXPOSURE_RETENTION_WEEKS = 3


@final
@dataclass(frozen=True, order=True)
class ExposureWeek:
    """One ISO week in UTC — the bucket exposure is counted in.

    **Derived from an instant, never stored as a flag.** It is the same argument
    that struck the newcomer-window loop: a stored *which week is it* goes stale
    hourly and a date does not. The roll does not open or close a bucket; the
    bucket is a function of ``now``, and the previous one expires on its own.

    UTC and ISO, both deliberately. A local week would make *shown this week*
    mean different things for two players in one city at the wrong hour, and the
    ISO calendar is the one week numbering that is total — every day belongs to
    exactly one week, including the ones either side of New Year.
    """

    iso_year: int
    iso_week: int

    def __post_init__(self) -> None:
        invariant(
            1 <= self.iso_week <= 53,
            f"an ISO week outside 1..53: {self.iso_week}",
        )
        invariant(
            self.iso_year >= 1,
            f"an ISO year below one: {self.iso_year}",
        )

    @property
    def label(self) -> str:
        """``2026-W35`` — how the week is spelled wherever it is named.

        Zero-padded so that the spelling sorts the way the week does, which is
        what makes a key scan over a store's own key space readable by a human
        looking for last week's bucket.
        """

        return f"{self.iso_year:04d}-W{self.iso_week:02d}"


def week_of(at: Instant) -> ExposureWeek:
    """Which exposure week an instant falls in."""

    calendar = at.isocalendar()
    return ExposureWeek(iso_year=calendar.year, iso_week=calendar.week)


@runtime_checkable
class ExposureLedger(Protocol):
    """How often each player has been **shown**, this week, in this sport.

    Read to **reorder** and never to admit: the exposure adjustment is
    ``−6 … +6`` and silent, and *exposure fairness is not a reason to show
    somebody a bad evening* (``docs/adr/0099``, amended by #175). So a ledger
    that answers nothing costs a search its spread and costs nobody their place
    in it.

    Written once per search, for every player the answer contained — the
    **returned** rows, not the generated ones, because the ledger's whole
    subject is *who was seen*.

    **Two counts per player, in one bucket.** The second is
    ``NEWCOMER_ABSORPTION_CAP``'s tally — appearances in a **newcomer's**
    shortlist, *same shape, same cadence, no second ledger*
    (``the-newcomer-path.md`` §5) — written as a second field family inside the
    same ``(sport, week)`` bucket rather than a key of its own, so that one
    expiry covers both and neither can be read half-present.

    **It is wired and it never binds**, because the constant *keeps its rule and
    refuses its integer* (``the-engine.md`` §6): with
    ``newcomer_absorption_cap = None`` the tally is counted, carried and read,
    and no comparison against it can be true. Counting it now is what makes the
    integer arguable later — the cap's own falsifier is a regression of answer
    rate on absorption, and a number chosen against a week of tallies is a
    number somebody can defend.
    """

    async def record_shown(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> None:
        """Add one appearance each to the week's bucket.

        **Additive and unordered**: two searches finishing at once each add
        their own, and there is no read-modify-write for either to lose. That is
        what lets this be written from a request path with no lock and no
        transaction.

        A player named twice is counted twice — a collection rather than a set,
        because one player can legitimately appear in two answers in one write.

        An empty collection is a legal no-op: a search that returned nobody
        still finished, and making the caller branch on it would put the
        ledger's emptiness rule in every caller.
        """
        ...

    async def times_shown(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> Mapping[UUID, int]:
        """How often each of these players was shown, this week, this sport.

        One keyed read for the whole candidate set, never a query per row —
        the shape every set-membership read in this module has, and for the
        same reason.

        Answers about **every id it was asked about**, zeroes included, so that
        a caller cannot accidentally read *absent from the answer* as *the store
        had nothing to say*. Those zeroes are measured, not invented: a player
        the bucket does not name was shown to nobody. What is deliberately not
        representable is *the store did not answer* — that degrades to all
        zeroes, and the module docstring says why that collapse is safe here and
        would be indefensible for a gate.
        """
        ...

    async def record_shown_to_a_newcomer(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> None:
        """Add one **newcomer** appearance each to the week's bucket.

        Written only by a search a newcomer ran, and over the same rows
        :meth:`record_shown` was given — being volunteered into a newcomer's
        list is being shown, plus one further fact about who was looking. So the
        caller makes the two writes together, and this one never names somebody
        the other was not given.

        **They are two writes and not one, so they can be lost apart.** Both
        fail soft, so an outage can drop either and leave the other, and neither
        count is evidence for anything — the durable answer to *who was shown*
        is the search record. A tally slightly under its appearances is a cap
        that binds slightly late, which is the right way round for a bound whose
        whole posture is *never withhold*.

        Additive, unordered and empty-tolerant, for the reasons
        :meth:`record_shown` is.
        """
        ...

    async def times_shown_to_a_newcomer(
        self,
        *,
        sport: Sport,
        week: ExposureWeek,
        player_ids: Collection[UUID],
    ) -> Mapping[UUID, int]:
        """How often each of these was volunteered into a newcomer's list.

        Read on a newcomer's search and on no other, because that is the only
        search the cap can bind in: the bound is on *the ask*, and dropping a
        player's lift in a search that is not adding to their absorption would
        take something from them for a load incurred somewhere else.

        Answers about every id it was asked about, zeroes included, on
        :meth:`times_shown`'s rule and for its reason.
        """
        ...

    async def all_times_shown(
        self, *, sport: Sport, week: ExposureWeek
    ) -> Mapping[UUID, int]:
        """The whole week's bucket for one sport — **the roll's input only.**

        The one unbounded read on either port, and it is bounded in practice by
        what it counts: a row per player shown at least once in that sport this
        week, which is at most the eligible pool.

        It is here rather than on a second port because the roll is a reader of
        this ledger like any other, and a second port over one bucket would be a
        second opinion about what the bucket holds.
        """
        ...

    async def publish_busy_threshold(
        self, *, sport: Sport, week: ExposureWeek, threshold: int
    ) -> None:
        """Record what *shown more often than most* means this week.

        Written by the exposure roll and by nothing else. It is a **cached
        scalar** in the store rather than a computed one on the search path
        (``matchmaking-engine.md`` §14.2): recomputing a percentile over the
        whole bucket per search would put an unbounded read on the request path
        to answer a question whose answer barely moves within an hour.
        """
        ...

    async def busy_threshold(self, *, sport: Sport, week: ExposureWeek) -> int | None:
        """What the last roll published, or ``None``.

        ``None`` means *no roll has published one for this week yet* — the
        ordinary state for the first hour of every week, and also what an
        unreachable store degrades to. Both mean the same thing to the one
        signal that reads it: the *shown more than most* rung does not fire, and
        the two rungs that lift are unaffected.
        """
        ...


@runtime_checkable
class SuppressionLedger(Protocol):
    """Whom this player has recently passed on — **their deck, and nowhere else.**

    ``PASS_SUPPRESS`` is 30 days, deck-only, one-directional and never
    escalating (``docs/adr/0128``). Two of those four are structural here rather
    than left to a caller:

    - **One-directional.** Every method takes a ``passer_id`` and asks only
      about that person's own deck. There is no shape here that could answer
      *has anybody passed on me*, and there never will be: my pass costs the
      other person nothing, and a port that could answer the reverse is a port
      somebody eventually asks.
    - **Never escalating.** A second pass on the same person is the same call
      with the same duration. Nothing counts passes, so nothing can grow a
      penalty out of them — where repetition leads is a Block, which is
      symmetric, reversible, and requires somebody to mean it.

    **Deck-only** is the caller's to honour: nothing prevents the shortlist from
    consulting this, except that it must not. *A search is a question about the
    city and a swipe may not edit the answer* — you can pass on somebody tonight
    and find them third in your shortlist tomorrow, and that cost is named in
    ``the-five-numbers.md`` §9 rather than designed away.
    """

    async def suppress(
        self, *, passer_id: UUID, passed_id: UUID, for_days: int
    ) -> None:
        """Keep this person out of the passer's deck for this long.

        ``for_days`` is **passed in, never known here**: it is the ruleset's
        ``interest.pass_suppress_days``, and a mechanism that held its own copy
        of a released ruleset's number would be a second place for it to be
        true. The ledger is the store; the number is the product decision.

        Re-passing after a lapse restarts the window from the new pass, which is
        the only way the second call is reachable at all — a live suppression
        keeps the card out of the deck, so there is nothing to pass on twice
        inside one window.
        """
        ...

    async def suppressed_for(
        self, *, passer_id: UUID, candidate_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        """Which of these the passer has a **live** suppression against.

        One keyed read for the whole deal, and it answers only about ids it was
        asked about. A lapsed suppression is simply absent — this port cannot
        tell *lapsed* from *never passed*, and the surface that needs to
        (``search_candidate.suppression_lapsed``, which is what makes *pass rate
        on re-shown profiles* computable) reads the durable pass record instead.

        An empty answer means *nothing is suppressed*, and is also what an
        unreachable store degrades to. That collapse is the whole reason this
        fails soft: the alternative reading — *exclude what we could not check*
        — excludes everybody.
        """
        ...


#: How each ledger fails. **All soft, and stated where the ports live.**
#:
#: Not a row in ``ports.py``'s ``FAIL_POSTURE`` — see the note beside that table.
#: These two are the matchmaking module's **own** ports, not demands it makes of
#: a context it does not write, and #203 settled that a port's posture belongs
#: where the port is declared rather than restated per consumer.
#:
#: Declared as data rather than left in prose so that *a ledger that never said
#: how it fails* is a question something can ask — the suite asserts this table
#: is exhaustive over ``EPHEMERAL_LEDGERS``, which is the only thing that makes
#: a third ledger arriving without a posture go red.
#:
#: **It is a claim, not the mechanism.** Nothing reads it at runtime: the
#: posture is enforced structurally by the wrapper in
#: ``infrastructure/fail_soft_ledgers.py``, and that separation is deliberate.
#: The five outward ports take theirs from a table because their callers are
#: request paths that can be routed through one function; these have no such
#: call site — one of their callers is a background job with no request to
#: refuse — so the type carries what the table would otherwise have to be
#: trusted for.
LEDGER_FAIL_POSTURE: Mapping[type, FailPosture] = {
    ExposureLedger: FailPosture.SOFT,
    SuppressionLedger: FailPosture.SOFT,
    PromptLedger: FailPosture.SOFT,
}

#: The module's ephemeral store, as the suite in ``tests/unit/test_ledgers.py``
#: walks it. Two lists that check each other, in the idiom ``MATCHER_DEMANDS``
#: established beside ``FAIL_POSTURE``.
EPHEMERAL_LEDGERS: tuple[type, ...] = (
    ExposureLedger,
    SuppressionLedger,
    PromptLedger,
)
