"""What a leaver recovers: four names, one ranking, and the two money forms.

A **departure** is a player vacating a seat they hold, and its **outcome** is
what that was worth. Four names and no more —
``docs/adr/0030-a-departure-is-an-audience-not-a-state.md`` fixed the set and
``CONTEXT.md`` writes it out: *reversed*, *refunded in full*, *refunded half*,
*forfeited*. The record itself belongs to Matches; what is here is the
vocabulary three contexts read verbatim.

**It lives in the kernel because a second implementation of it would be a
defect** — ADR-0022's own test, and the same answer ``causes.py`` got. Matches
produces the outcome and refuses a command whose quote it has fallen below,
Money turns it into a movement, and Now renders it beside the situation. Three
readers of one ordering is what the innermost ring is for; two spellings of
*is this worse* is a refusal that fires on the wrong cases, which
``docs/adr/0033-settlement-and-occupancy-are-independent.md`` names as the
client-side version of the same bug.

**Forfeit ranks equal to a zero refund, not below it.** ADR-0033 is explicit and
it is the one line of this module somebody will otherwise "fix": the quote
protects *money*, the money in both cases is nothing, and a confirmation dialog
that says *still zero* is friction bought for no protection. The consequence is
stated there and is deliberate — a player quoted 0 % whose match is cancelling
at the checkpoint leaves without a second confirmation and learns from a
notification.

**Two questions one word apart, and they are not the same function.**
``live_outcome`` is *what do I get if I leave now* — the quote's subject.
``refill_outcome`` is *what does somebody who has already left recover when a
filler pays now*. They differ past the checkpoint: leaving then is quoted
``FORFEITED``, because two hours out is the last moment anything about the
roster can change and the honest promise is nothing; a filler who nonetheless
arrives pays the rescue price and the leaver's outcome **improves** to
``REFUNDED_HALF``. Monotonic upward is what makes that asymmetry safe — a quote
may under-promise for ever and may never over-promise once.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias, final

from app.kernel.invariants import invariant
from app.kernel.matches import MatchKind, MatchRecord, deadlines
from app.kernel.money import Grosze
from app.kernel.time import Instant


class Outcome(str, Enum):
    """A departure's result: what the leaver got back, or will.

    Ordered here by how good they are for the player, which is **not** the
    ranking below — two of them tie, and an enumeration cannot express a tie.
    """

    #: Nothing was ever taken. A leave before the match committed: the seat is
    #: cleared *and* unpaid, so there is nothing left to derive from and the
    #: card can name no amount at all (ADR-0030).
    REVERSED = "reversed"
    #: Her whole share came back — a full-price replacement paid, or the club
    #: failed and everybody was refunded.
    REFUNDED_IN_FULL = "refundedInFull"
    #: Half came back: a rescue player took the seat at the discount that exists
    #: to save a court that would otherwise be lost.
    REFUNDED_HALF = "refundedHalf"
    #: She paid and nothing came back. The match played short, or it cancelled
    #: at its checkpoint.
    FORFEITED = "forfeited"


#: Pinned rather than counted, so a member arriving or leaving is a decision
#: somebody made in a diff — the rule ``CAUSE_COUNT`` and ``SITUATION_COUNT``
#: already hold.
OUTCOME_COUNT = 4

invariant(
    len(Outcome) == OUTCOME_COUNT,
    f"the enumeration names {len(Outcome)} outcomes, not {OUTCOME_COUNT}",
)

#: *refunded in full > refunded half > forfeited = reversed* (ADR-0033).
#:
#: Written out row by row rather than derived from the declaration order,
#: because the whole content of the decision is the **tie** at the bottom and a
#: derivation cannot express one. A table also makes a fifth outcome a build
#: error here rather than a silent rank of zero.
_RANK: dict[Outcome, int] = {
    Outcome.REFUNDED_IN_FULL: 2,
    Outcome.REFUNDED_HALF: 1,
    Outcome.FORFEITED: 0,
    Outcome.REVERSED: 0,
}

invariant(
    set(_RANK) == set(Outcome),
    f"the ranking covers {len(_RANK)} of {len(Outcome)} outcomes",
)


def outcome_rank(outcome: Outcome) -> int:
    """How good this outcome is for the player, with the two zeroes tied."""

    return _RANK[outcome]


def outcome_worse_than(candidate: Outcome, quote: Outcome) -> bool:
    """Whether ``candidate`` is **strictly** worse than what she was shown.

    Strictly, so *equal or better applies* (ADR-0033) and a forfeit quoted
    against a reversal — identical money — is not a refusal.
    """

    return outcome_rank(candidate) < outcome_rank(quote)


def live_outcome(record: MatchRecord, now: Instant) -> Outcome:
    """What a player who leaves **now** is being promised. The quote's subject.

    One outcome and never the set: the ordering above is defined over single
    labels, so quoting the whole table would make the refuse-if-worse rule
    compare sets (ADR-0086). The other three are shown beside it as
    possibilities and are not quoted.

    **A private court has two outcomes, not four** (ADR-0030): no commitment
    deadline, because the court was bought at booking, and no rescue tier,
    because the discount exists to save a court that would otherwise be lost and
    nothing here is at risk. A share is refunded exactly when somebody takes the
    seat, and *"no pre-match cutoff kills a converted match — the seat keeps
    selling until match time"* (ADR-0046), so the moment the promise turns is
    the start and not the join cutoff.

    **On an open match the subject is commitment, not the deadline.** A match
    past its own deadline and still short has bought nothing — it will cancel
    incomplete — so leaving it is still a reversal. A match that filled *after*
    the deadline committed on the spot, and leaving that one is not.
    """

    if record.kind is MatchKind.PRIVATE:
        if now < record.start:
            return Outcome.REFUNDED_IN_FULL
        return Outcome.FORFEITED

    if record.committed_at is None:
        return Outcome.REVERSED

    when = deadlines(record)
    if now < when.rescue:
        return Outcome.REFUNDED_IN_FULL
    if now < when.check:
        return Outcome.REFUNDED_HALF
    return Outcome.FORFEITED


def refill_outcome(record: MatchRecord, now: Instant) -> Outcome:
    """What an unsettled departure settles at when a filler pays **now**.

    The leaver recovers what the filler paid: full price from the vacancy, half
    from the rescue deadline. There is no checkpoint tier — a seat sold past the
    checkpoint is still sold at the rescue price, and the money that arrives is
    the money that goes back.

    A private court's share is refunded in full whenever somebody takes the
    seat, at any distance, because that path has no discount tier at all.
    """

    if record.kind is MatchKind.PRIVATE:
        return Outcome.REFUNDED_IN_FULL
    if now < deadlines(record).rescue:
        return Outcome.REFUNDED_IN_FULL
    return Outcome.REFUNDED_HALF


@final
@dataclass(frozen=True)
class NothingTaken:
    """Her money never left, so there is no amount and no field to hold one.

    ADR-0030: before commitment the seat is cleared *and* unpaid, *"so there is
    nothing left to derive from and the card can name no amount at all."*
    """


@final
@dataclass(frozen=True)
class Recoverable:
    """What she paid in, which is the number her card names.

    Whether any of it comes back is the **outcome's** answer and never this
    payload's — a settled ``FORFEITED`` departure still carries the amount,
    because *you paid 38,00 zł and got none of it back* is the sentence, and a
    payload that dropped the figure would leave the card unable to say it.
    """

    amount: Grosze


#: The leaver's money, in **two forms** rather than one with an optional amount
#: (ADR-0072). An optional field is one whose absence the phone has to
#: interpret, and the phone interprets nothing (ADR-0053): *nothing was taken*
#: and *nothing has come back yet* are opposite sentences and a blank cannot
#: tell them apart.
LeaverMoney: TypeAlias = NothingTaken | Recoverable
