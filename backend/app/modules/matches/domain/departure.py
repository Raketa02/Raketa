"""What one player's leaving was worth, on an axis of its own.

**A departure and the vacancy it leaves are two facts** (ADR-0033). The hole is
``vacancy.py`` — which seat, when it opened, whether it has closed — and the
ladder reads it to answer *is this match short a player*. This record answers
the other question, *is her money decided*, and the two do not imply each other:
a filler closes the **oldest open vacancy** and settles the **oldest unsettled
departure**, and those are not always the same departure. That is the whole
reason the two live in separate files with no field in common but the seat.

**Settlement is monotonic upward and this type has no way down.** ADR-0030 fixes
that a club-side failure may improve a settled 50 % to a full refund and that
*"nothing may reduce a settled outcome"*. Rather than guard a setter, the only
mutator here is ``raise_to``, which cannot lower one — the guarantee is
structural, so a caller cannot get it wrong and a future caller cannot be added
that does.

**Two forms of money, never one with an optional amount** (ADR-0072).
``NothingTaken`` is a leave that took nothing — before the match committed, or by
somebody who held a seat and never paid for it — and it is **born settled**,
because there is no money whose fate could still change. ``Recoverable`` names
what she paid; the outcome says what became of it. The two are kept in step with
the outcome by an invariant rather than by convention: *nothing taken* is
``REVERSED`` and ``REVERSED`` is *nothing taken*, in both directions and for
life.

*Its ``is_settled`` is the glossary's **Settlement** — one player's money — and
is not ``Match.is_settled``, which asks whether anything further can happen to
the match at all. ``CONTEXT.md`` warns about exactly this pair; the two words
are one apart and the objects are not.*
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import (
    Instant,
    LeaverMoney,
    NothingTaken,
    Outcome,
    outcome_rank,
)


@final
@dataclass
class Departure:
    """One leaving: whose seat, when, what she was promised, and what she got."""

    id: UUID
    seat_index: int
    player_id: UUID
    departed_at: Instant

    #: The outcome label she was shown and acted on (ADR-0033's **Quote**).
    #: Stored rather than re-derived: every deadline hangs off ``start``, and a
    #: consented shift moves all five, so *what was she promised* stops being
    #: answerable from the record the moment the match moves.
    quoted: Outcome

    #: Her money, in one of the two forms and never an optional amount.
    money: LeaverMoney

    #: ``None`` until no further seat event can change it. Never lowered.
    outcome: Outcome | None = None
    settled_at: Instant | None = None

    def __post_init__(self) -> None:
        nothing_taken = isinstance(self.money, NothingTaken)
        if nothing_taken and self.outcome is not Outcome.REVERSED:
            raise ValueError(
                "a departure that took nothing is born settled as reversed, "
                f"not {self.outcome}"
            )
        if not nothing_taken and self.outcome is Outcome.REVERSED:
            raise ValueError(
                "a reversal took nothing, so it cannot name an amount"
            )
        if (self.outcome is None) != (self.settled_at is None):
            raise ValueError(
                "a settlement is an outcome and the moment it landed, or neither"
            )

    @property
    def is_settled(self) -> bool:
        """Whether no further seat event can change **this player's** money."""

        return self.outcome is not None

    @property
    def took_nothing(self) -> bool:
        """Whether her card names no amount at all."""

        return isinstance(self.money, NothingTaken)

    def raise_to(self, outcome: Outcome, *, at: Instant) -> bool:
        """Settle at this outcome, or improve to it. Never lower one.

        Answers whether anything moved, so a caller announces exactly the
        changes there were. Three ways to move nothing, and each is a decision:

        - **Nothing was taken.** There is no money to return, so an improvement
          would be an announcement about a refund that cannot happen. A
          reversal is final in the only sense that matters to the player.
        - **Already at least this good.** A fan-out over every departure on a
          club cancellation reaches settled and unsettled ones alike, and the
          settled ones that are already better must be left exactly as they are
          — silently, because *"you are still refunded in full"* is not a change
          anybody needs explained.
        - **Strictly worse than where it stands.** Refused by having no way to
          express it rather than by raising, which is what makes *"monotonic
          upward"* a property of the type and not of its callers.
        """

        if self.took_nothing:
            return False
        if self.outcome is not None and outcome_rank(outcome) <= outcome_rank(
            self.outcome
        ):
            return False
        self.outcome = outcome
        self.settled_at = at
        return True


def born_settled(money: LeaverMoney) -> bool:
    """Whether this departure has nothing left to decide the moment it is made.

    ADR-0033: *"a pre-commitment leave is a full reversal — the seat is cleared
    and unpaid, nothing is owed, so the departure is born settled."* The test is
    the money and not the clock, which is what makes it hold for the other
    born-settled case too — a player who held a seat and never paid for it, at
    any distance from the match.
    """

    return isinstance(money, NothingTaken)


def oldest_unsettled(departures: list[Departure]) -> Departure | None:
    """The departure a filler settles: oldest first, **settlement** not vacancy.

    ADR-0033 calls two FIFO queues over one list *"a real implementation
    hazard"* — they are ordered by the same instant and differ only in their
    filter, so a single sorted traversal that stops at the first match silently
    does the wrong thing, and the symptom is *one player was never refunded*,
    months later, and never an error. This is one of the two, written out; the
    other is ``Match.open_vacancies``.

    A leave that took nothing is born settled, so it is skipped here — which is
    exactly the case the ADR's worked example turns on.
    """

    open_ones = [one for one in departures if not one.is_settled]
    if not open_ones:
        return None
    return min(open_ones, key=lambda one: (one.departed_at, one.seat_index))
