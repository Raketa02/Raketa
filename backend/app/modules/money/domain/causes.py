"""The rule that fired, in eighteen closed names, and what each one decides.

ADR-0057: *every movement names the rule that caused it*, from a **closed
enumeration**, because *"a cause nobody enumerated is a rule nobody decided"*.
It listed twelve and left the four terminal cancellations to be walked out of
the situation model — which ADR-0073 did, into ``kernel.Cause``.

**Why this is a wider enum and not ``kernel.Cause`` grown to eighteen.** The
kernel's five are the causes a *card* may carry: four match endings a player is
told about, plus ``settlementReopened``, which reaches no card and is in the
enumeration so that the ledger cannot write a name the enumeration does not
hold. They cross the wire — ``GET /api/v1/now`` emits ``Cause`` as an OpenAPI
enum and both clients generate an exhaustive table over it. Growing that
enumeration by thirteen ledger-only names would oblige every client to hold
thirteen sentences no card can ever print, which is ADR-0071's *a field with no
reader* wearing an enum's clothes, in the direction that costs another app work.

So this is the **wider** vocabulary and the kernel's is embedded in it, by
**value** rather than by restatement: each shared member is spelled
``Cause.X.value``, so the durable string exists once, and ``invariant`` below
asserts the inclusion in both directions of the set relation at module load. A
sixth kernel cause that nobody gave a ledger meaning fails the build here. It is
the same shape Now's five-name ``CardHoldReason`` has against the kernel's
twelve ``HoldReason`` — a consumer whose vocabulary is a different width writes
its own and pins the relation (ADR-0040) — pointed the other way.

**One table, two questions, asked once per cause.** ``CAUSE_RULES`` is total
over the enumeration and asserted exhaustive at module load, so a nineteenth
cause cannot be added without answering both:

* *does it move the player's balance?* — ADR-0058's whole model. Two causes do:
  a collection that failed creates a debt, and clearing one discharges it.
  Everything else is money changing hands in settlement of something that
  happened at the same moment, and leaves what she **owes** untouched. Without
  this, *"a balance is never above zero"* is either false the moment anybody
  pays for a seat, or a rule written down in prose beside a fold that does not
  implement it.
* *does it name a seat?* — every cause but one does. A movement that forgot its
  seat is refused at the door rather than found months later by a reconciliation
  that cannot attribute it. ``debtCleared`` is the exception, and deliberately:
  ADR-0058 refuses line items and ageing, so a payment against a debt is *one
  movement and the number moves* — attaching it to a seat would be the first
  brick of the allocation machinery that record rules out by name.

**A reservation is not in the table**, because it is a fact about the world and
not about the rule: a ``shareOnline`` paid into a match that has not earned a
court yet has no reservation to name, and the same cause on a committed match
has one.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping, final

from app.kernel import Cause, Outcome, invariant


class MovementCause(str, Enum):
    """Why this money moved. Closed, durable, and never free text.

    The five that are also ``kernel.Cause`` take their **value** from it, so the
    string a movement carries for ever is written in exactly one place.
    """

    # --- a share arriving -------------------------------------------------
    #: A share bought from Raketa, online. Never a single movement: it is
    #: `player → Raketa`, and then `Raketa → club` — on arrival for a private
    #: court, at commit for an open match (ADR-0056).
    SHARE_ONLINE = "shareOnline"
    #: Cash across a club counter, marked paid by the club. The **one** movement
    #: that is `player → club` with Raketa as neither party (ADR-0059).
    SHARE_AT_COUNTER = "shareAtCounter"

    # --- money going back -------------------------------------------------
    #: A seat claim ran out with the money already in flight. The share is
    #: recorded and then compensated, so a slow bank does not silently keep
    #: 30 zł (ADR-0081).
    CLAIM_LAPSED = "claimLapsed"
    #: A joiner withdrew before the roster locked.
    WITHDRAWN_BEFORE_LOCK = "withdrawnBeforeLock"
    #: The court was sold as a format it never reached. Owed to a marketplace
    #: payer and **not** to a pre-opening one, on the same court — which is the
    #: case ADR-0057 exists for (ADR-0044).
    FORMAT_UNMET_REFUND = "formatUnmetRefund"
    #: A private court's owner got a share back, because somebody else paid it.
    OWNER_REIMBURSED = "ownerReimbursed"

    # --- a leaver's settlement, one per outcome ---------------------------
    #: She left before the match committed; nothing was ever taken.
    LEAVER_REVERSED = "leaverReversed"
    #: A full-price replacement paid, so her whole share came back.
    LEAVER_FULL = "leaverFull"
    #: A rescue player took the seat at the discount, so half came back.
    LEAVER_RESCUE = "leaverRescue"
    #: Nobody replaced her. Her share settles to the club.
    LEAVER_FORFEIT = "leaverForfeit"

    # --- reconciliation, and what it can leave behind ---------------------
    #: The one charge a split reservation's owner is put through, two hours
    #: after the slot ends (ADR-0046).
    RECONCILIATION_OWNER_CHARGE = "reconciliationOwnerCharge"
    #: We paid out and did not collect. A chargeback arrives by this same door,
    #: because the outcome is identical (ADR-0047, ADR-0057).
    COLLECTION_FAILED = "collectionFailed"
    #: A debt paid off. One movement, and the number moves (ADR-0058).
    DEBT_CLEARED = "debtCleared"

    # --- the five the kernel owns -----------------------------------------
    #: The club sold the court out from under a forming match.
    INVENTORY_LOST = Cause.INVENTORY_LOST.value
    #: The club cancelled the match itself.
    CLUB_CANCELLED = Cause.CLUB_CANCELLED.value
    #: The match never reached the format it was sold as.
    FORM_CANCELLED = Cause.FORM_CANCELLED.value
    #: Still short at its checkpoint. Club credit, not a refund.
    CHECKPOINT_CANCELLED = Cause.CHECKPOINT_CANCELLED.value
    #: A settled departure reopened. The one movement not explained by the
    #: situation the player is in, and named so the monotone-refund assumption
    #: fails at the enum rather than quietly at the totals (ADR-0057).
    SETTLEMENT_REOPENED = Cause.SETTLEMENT_REOPENED.value


#: Pinned rather than counted, on the rule ``CAUSE_COUNT``, ``OUTCOME_COUNT`` and
#: ``SITUATION_COUNT`` already hold: a member arriving or leaving is a decision
#: somebody made in a diff, not a number that follows along.
MOVEMENT_CAUSE_COUNT = 18

invariant(
    len(MovementCause) == MOVEMENT_CAUSE_COUNT,
    f"the ledger names {len(MovementCause)} causes, not {MOVEMENT_CAUSE_COUNT}",
)

invariant(
    {cause.value for cause in Cause} <= {cause.value for cause in MovementCause},
    "a kernel cause the ledger cannot record: "
    f"{sorted({c.value for c in Cause} - {c.value for c in MovementCause})}",
)


def cause_of(cause: Cause) -> MovementCause:
    """The ledger's name for a cause the kernel produced.

    A lookup by value rather than a table, because the inclusion above is what
    makes it total — a table here would be a second statement of the same
    relation, and two of them can disagree.
    """

    return MovementCause(cause.value)


#: Which cause a leaver's settlement is written under, one per ``Outcome``.
#:
#: A table rather than a name derived from the outcome's own value, because it
#: is a **decision** per row — *what does this outcome do to money* — and a
#: fifth outcome must fail the build here rather than fall through to a name
#: that looks plausible. ``forfeited`` is the row worth reading: the leaver gets
#: nothing, and the movement it names is her share settling **to the club**.
CAUSE_OF_OUTCOME: Mapping[Outcome, MovementCause] = MappingProxyType(
    {
        Outcome.REVERSED: MovementCause.LEAVER_REVERSED,
        Outcome.REFUNDED_IN_FULL: MovementCause.LEAVER_FULL,
        Outcome.REFUNDED_HALF: MovementCause.LEAVER_RESCUE,
        Outcome.FORFEITED: MovementCause.LEAVER_FORFEIT,
    }
)

invariant(
    set(CAUSE_OF_OUTCOME) == set(Outcome),
    "an outcome with no money cause: "
    f"{sorted(outcome.value for outcome in set(Outcome) - set(CAUSE_OF_OUTCOME))}",
)


@final
@dataclass(frozen=True)
class CauseRule:
    """What a cause decides about the movement carrying it."""

    #: Whether the amount moves the player's balance — ADR-0058's one number.
    bears_on_balance: bool
    #: Whether the movement must name the seat it is about.
    names_a_seat: bool


#: Total over ``MovementCause``, asserted exhaustive at module load.
CAUSE_RULES: Mapping[MovementCause, CauseRule] = MappingProxyType(
    {
        MovementCause.SHARE_ONLINE: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        MovementCause.SHARE_AT_COUNTER: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        MovementCause.CLAIM_LAPSED: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        MovementCause.WITHDRAWN_BEFORE_LOCK: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        MovementCause.FORMAT_UNMET_REFUND: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        MovementCause.OWNER_REIMBURSED: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        MovementCause.LEAVER_REVERSED: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        MovementCause.LEAVER_FULL: CauseRule(bears_on_balance=False, names_a_seat=True),
        MovementCause.LEAVER_RESCUE: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        MovementCause.LEAVER_FORFEIT: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        MovementCause.RECONCILIATION_OWNER_CHARGE: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        # The two that move what she owes. A failed collection is money Raketa
        # paid out and did not get back; clearing a debt is her paying it.
        MovementCause.COLLECTION_FAILED: CauseRule(
            bears_on_balance=True, names_a_seat=True
        ),
        # The only cause with no seat: ADR-0058 refuses line items, so a debt
        # payment is against the number and not against an obligation.
        MovementCause.DEBT_CLEARED: CauseRule(
            bears_on_balance=True, names_a_seat=False
        ),
        MovementCause.INVENTORY_LOST: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        MovementCause.CLUB_CANCELLED: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        MovementCause.FORM_CANCELLED: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        MovementCause.CHECKPOINT_CANCELLED: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
        MovementCause.SETTLEMENT_REOPENED: CauseRule(
            bears_on_balance=False, names_a_seat=True
        ),
    }
)

invariant(
    set(CAUSE_RULES) == set(MovementCause),
    "a cause with no rule: "
    f"{sorted(cause.value for cause in set(MovementCause) - set(CAUSE_RULES))}",
)


def rule_for(cause: MovementCause) -> CauseRule:
    """What this cause decides. Total, so there is no fallback to reason about."""

    return CAUSE_RULES[cause]
