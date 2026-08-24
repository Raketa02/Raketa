"""The departure screen: four outcomes, their standings, and one live quote.

ADR-0086's route in values. It is **not a card** — no fit badge, no emphasis
flag, no card stamp, because all three are judgements the *composition* made
about a card's place on Now and none of them means anything on a screen with one
thing on it. What it does carry is the same spine and the same situation half a
card carries, off the same ladder, so entry from Now and this screen never
disagree about what the match is doing.

**All four outcomes, always, each with a server-composed standing.** Not only
the reachable ones: *"a table that quietly drops forfeited once it is
unreachable is also a table that never showed it while it was"*, and the whole
reason this act got a route rather than a card was room. On a private court the
table is **two rows**, because ``CONTEXT.md`` already fixes that only *refunded
in full* and *forfeited* are reachable there — the glossary being read, not a
second rule.

**The quote is the one live outcome and never the set.** ``CONTEXT.md`` orders
the four over single labels, so quoting the table would make the refuse-if-worse
rule compare sets. The other rows are shown as possibilities and are not quoted.

**No ``phase`` field.** The prototype names four — *free cancellation ·
full-price search · 50/50 Rescue · past the checkpoint* — and the standings
already say which one she is in. A phase name is a second vocabulary answering a
question already answered, which is the shape ADR-0040 refuses.

**Nothing here mentions transferring a seat.** It is the leaver's *best* outcome
and it is the invite flow, which this map rules out; ADR-0086: *"advertising a
door that is not there is worse than the gap."*
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import (
    Instant,
    MatchKind,
    MatchRecord,
    Outcome,
    deadlines,
    invariant,
    live_outcome,
)

from app.modules.now.domain.screen import (
    Money,
    Place,
    SeatCounts,
    SituationHalf,
)
from app.modules.now.domain.vocabulary import OutcomeStanding


@final
@dataclass(frozen=True)
class OutcomeRow:
    """One of the four outcomes, and where it stands for this viewer now.

    ``opens_at`` is present **exactly** on ``OPENS`` and nowhere else, which is
    the same rule every fact on a card follows: a moment beside *spent* would be
    a moment nothing counts to, and a row that is *still possible* has no moment
    to give — that is precisely what distinguishes it.
    """

    outcome: Outcome
    standing: OutcomeStanding
    opens_at: Instant | None = None

    def __post_init__(self) -> None:
        invariant(
            (self.standing is OutcomeStanding.OPENS)
            == (self.opens_at is not None),
            f"a standing that names a moment: {self.standing} "
            f"with {self.opens_at!r}",
        )


@final
@dataclass(frozen=True)
class DepartureScreen:
    """What leaving is worth right now, and what it could still become.

    The first four fields are the card's spine, composed by the **same** function
    that composes the strip's card, so the screen she arrives on cannot describe
    the match differently from the card she tapped. ``may_depart`` is likewise
    the card's own boolean rather than a second reading of the same rules.

    ``counts`` and ``commitment_deadline`` ride here rather than only inside the
    situation half, and that is a deliberate duplication of the first: the
    situation half is the half a phone reads **only when it knows the name**, and
    these two are the reasons printed beside the quote on every rendering. A fact
    the screen must always draw cannot live only in the half that may be skipped.
    """

    match_id: UUID
    where: Place
    price: Money
    situation: SituationHalf

    may_depart: bool
    quote: Outcome
    outcomes: tuple[OutcomeRow, ...]
    counts: SeatCounts

    clock: Instant | None = None
    commitment_deadline: Instant | None = None


def commitment_deadline(record: MatchRecord) -> Instant | None:
    """When this match's seats stop being freely refundable, as a moment.

    ``None`` on a private court, and that is the fact rather than a gap: the
    court was bought at booking, so there is no commitment for a deadline to be
    about (ADR-0030). An absent moment is *there is no such deadline*, which is
    the only thing its absence could mean here.
    """

    if record.kind is MatchKind.PRIVATE:
        return None
    return deadlines(record).commit


def outcome_table(record: MatchRecord, now: Instant) -> tuple[OutcomeRow, ...]:
    """Every outcome this match can put a leaver on, in the order they arrive.

    Ordered by the **quote's own timeline** and not by how good they are, so the
    table reads as *what she has passed and what is ahead*: a row above the
    searching one is spent, a row below it is coming.
    """

    if record.kind is MatchKind.PRIVATE:
        return _private(record, now)
    return _open(record, now)


def _private(record: MatchRecord, now: Instant) -> tuple[OutcomeRow, ...]:
    """Two rows, and the moment that separates them is the start.

    ADR-0046: *"no pre-match cutoff kills a converted match — the seat keeps
    selling until match time"*, so a share is refunded whenever somebody takes
    the seat and the promise turns at ``start`` rather than at the join cutoff.
    There is no rescue tier at all, because the discount exists to save a court
    that would otherwise be lost and this court is already bought.
    """

    started = now >= record.start
    return (
        OutcomeRow(
            outcome=Outcome.REFUNDED_IN_FULL,
            standing=(OutcomeStanding.SPENT if started else OutcomeStanding.SEARCHING),
        ),
        OutcomeRow(
            outcome=Outcome.FORFEITED,
            standing=(OutcomeStanding.SEARCHING if started else OutcomeStanding.OPENS),
            opens_at=None if started else record.start,
        ),
    )


def _open(record: MatchRecord, now: Instant) -> tuple[OutcomeRow, ...]:
    """Four rows, three deadlines, and one thing that is not a deadline at all.

    **Commitment is an event and never a clock**, which is where
    ``STILL_POSSIBLE`` comes from and why it is not the same word as ``OPENS``.
    ``live_outcome`` reads ``committed_at`` rather than the commitment deadline
    — *"a match past its own deadline and still short has bought nothing"* — so
    on a match that has not filled, the three money outcomes are not a moment
    away, they are a **fill** away, and nothing can say when that will be.
    Naming a moment there would be the screen promising a turn that may never
    come.
    """

    when = deadlines(record)
    committed = record.committed_at is not None
    quote = live_outcome(record, now)

    def row(outcome: Outcome, *, spent: bool, opens_at: Instant | None) -> OutcomeRow:
        if outcome is quote:
            return OutcomeRow(outcome=outcome, standing=OutcomeStanding.SEARCHING)
        if spent:
            return OutcomeRow(outcome=outcome, standing=OutcomeStanding.SPENT)
        if opens_at is None:
            return OutcomeRow(outcome=outcome, standing=OutcomeStanding.STILL_POSSIBLE)
        return OutcomeRow(
            outcome=outcome, standing=OutcomeStanding.OPENS, opens_at=opens_at
        )

    return (
        # Commitment is one-way, so the free reversal is behind her the moment
        # the match fills and can never come back.
        row(Outcome.REVERSED, spent=committed, opens_at=None),
        # The full-price search ends at the rescue deadline whatever the match
        # does, which is why this row is spent on the clock alone.
        row(Outcome.REFUNDED_IN_FULL, spent=now >= when.rescue, opens_at=None),
        row(
            Outcome.REFUNDED_HALF,
            spent=now >= when.check,
            opens_at=when.rescue if committed and now < when.rescue else None,
        ),
        # Never spent: there is nothing past it, and a match with nobody to take
        # the seat lands here at any distance.
        row(
            Outcome.FORFEITED,
            spent=False,
            opens_at=when.check if committed and now < when.check else None,
        ),
    )


@final
@dataclass(frozen=True)
class AppliedDeparture:
    """What a departure actually did: her outcome, and the hole it left.

    **Two facts and not one**, which is ADR-0033 arriving in a return type: the
    outcome is what her money settled at and the hole is what the match is now
    short. The command log remembers the first; the invitation cascade is opened
    on the second.

    ``vacancy`` is ``None`` when the hole was closed before this value was built
    — nobody can do that inside one transaction today, so it is the honest
    answer to a question that is not asked rather than a case with a meaning.
    A cascade is simply not opened for a hole that is not there.
    """

    outcome: Outcome
    vacancy: UUID | None
