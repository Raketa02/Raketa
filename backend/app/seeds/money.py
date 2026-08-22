"""Which ledgers exist, and what state each one is in.

Same rule as the four catalogs beside it: **a ledger is named for the state it
represents**, and the name is a checked claim rather than a comment. Five players
who each paid for a seat would be one scenario — *a share arrived* — five times;
what breaks a screen, and what ADR-0056 was written for, is that the same 30 zł
means two different things depending on what was sold. So this is a list of
those edges.

**A paid seat does not yet write a movement, and none is authored here.** The
seeded matches have fourteen paid seats between them and the ledgers below name
five movements' worth of state. That gap is a ticket, not an oversight:
``Raketa02/Raketa#70`` is the transaction that writes the seat, the reservation
and both movements together, and seeding the join here would be writing down the
answer to the question that ticket exists to compute — the rule the court hold
and the leaver's outcome are already seeded under.

**The claims are the folds, because the folds are the whole context.**
``balance``, ``held`` and the movement count are computed from the movements and
stored nowhere (ADR-0056 retires ``held: true`` by name), so checking them
against the *stored* ledger on every run is checking the arithmetic a screen and
a support conversation both read. Retune what a cause does to a balance and the
seed stops and says whose money just changed.

**And the whole set is asserted sound**, through the same three invariants the
nightly reconciliation calls. A seeded database that breaks a ledger invariant is
one every future Money test would be developed against.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.kernel import Grosze, grosze

from app.seeds.matches import SHARE

#: What a failed collection left behind. Deliberately **not** ``SHARE``: a debt
#: and a share are two different numbers that happen to be equal on one court,
#: and a seed whose two claims are the same literal cannot tell them apart.
DEBT = grosze(3000)


class Arrival(str, Enum):
    """How the money in one scenario got where it is.

    A closed set rather than raw movement drafts, because the catalog's job is to
    name a **state** and the drafts are how the runner reaches it. A sixth shape
    is a decision somebody made in a diff.
    """

    #: An open match: nothing is booked, so Raketa holds the share.
    HELD = "held"
    #: A private court, already bought: the share passes through on arrival.
    PASSED_THROUGH = "passedThrough"
    #: Cash across a counter. Raketa is neither party.
    AT_COUNTER = "atCounter"
    #: A share that arrived for a seat that had gone, and its ``REV-`` reversal.
    CORRECTED = "corrected"
    #: We paid out and did not collect.
    COLLECTION_FAILED = "collectionFailed"


@dataclass(frozen=True)
class LedgerClaim:
    """What a seeded ledger promises, checked against the stored one.

    ``held`` is about the scenario's **named seat** and ``balance`` is about the
    whole player, which is why no two scenarios on one account may both move a
    balance — the catalog refuses that below rather than leaving the second claim
    quietly wrong.
    """

    promise: str
    #: How many movements this scenario writes.
    movements: int
    #: Raketa's position on the named seat once it has.
    held: Grosze
    #: The player's balance once it has. Zero unless the scenario is a debt.
    balance: Grosze


@dataclass(frozen=True)
class SeedLedger:
    """One deterministic ledger state: whose, about which seat, and how it arrived.

    ``account_slug`` and ``match_slug`` name the two catalogs' own entries, so a
    ledger cannot point at a player or a match that does not exist without the
    run stopping.

    ``token`` is what the references are built from — ``PAY-<token>``,
    ``PAY-<token>s`` for a pass-through's settlement half, ``REV-<token>`` for a
    correction. Fixed rather than generated, because the reference is also the
    idempotency probe: a second run finds the movement it already wrote instead
    of writing a second one beside it.
    """

    slug: str
    description: str
    claim: LedgerClaim
    account_slug: str
    match_slug: str
    seat_index: int
    arrival: Arrival
    token: str
    amount: Grosze = SHARE

    def __post_init__(self) -> None:
        if not self.token.isalnum():
            raise ValueError(
                f"'{self.slug}' has a reference token that is not letters and "
                f"digits: {self.token!r}"
            )
        moves_a_balance = self.arrival is Arrival.COLLECTION_FAILED
        if moves_a_balance != bool(self.claim.balance):
            raise ValueError(
                f"'{self.slug}' says its balance is {self.claim.balance} and its "
                f"arrival is '{self.arrival.value}'. Exactly one arrival moves a "
                f"balance, and a claim that disagrees with it is a claim about a "
                f"number nothing computes that way."
            )


HOLDING_A_SHARE = SeedLedger(
    slug="ledger-holding-a-share",
    description=(
        "She paid for a seat on an **open** match, so nothing is booked yet and "
        "the money is Raketa's to hold until the match commits. This is the "
        "money `cancelledIncomplete` gives back whole, and without it the open "
        "path has no refund to give (ADR-0056). One movement, and `held` reads "
        "the share."
    ),
    claim=LedgerClaim(
        promise="a share Raketa is holding against a match that has not committed",
        movements=1,
        held=SHARE,
        balance=grosze(0),
    ),
    account_slug="assessment-abandoned",
    match_slug="match-holding-a-court-softly",
    seat_index=2,
    arrival=Arrival.HELD,
    token="hs1",
)

PASSED_THROUGH = SeedLedger(
    slug="ledger-with-a-share-passed-through",
    description=(
        "The owner's own share of her own **private** court. The court is "
        "already bought, so the share is paid through to the club on arrival "
        "and Raketa holds nothing. **Two** movements, because ADR-0056 requires "
        "the pair — with only the second, `held` and the float are not derivable "
        "and a refund has no movement to compensate. Same 30 zł as the scenario "
        "above, and a different answer to *who has it*."
    ),
    claim=LedgerClaim(
        promise="a share that reached the club the moment it arrived",
        movements=2,
        held=grosze(0),
        balance=grosze(0),
    ),
    account_slug="brand-new-player",
    match_slug="match-private-with-seats-opened",
    seat_index=0,
    arrival=Arrival.PASSED_THROUGH,
    token="pt1",
)

AT_THE_COUNTER = SeedLedger(
    slug="ledger-with-a-counter-paid-share",
    description=(
        "An invited player handed cash across the club's counter and the club "
        "marked it paid. The **one** movement that is `player → club` with "
        "Raketa as neither party (ADR-0059). It is on the ledger even though we "
        "never touched the money — without it the seat reads unpaid for ever, "
        "and the nightly assertion that a seat's chain closes never passes on "
        "any court with a cash payer."
    ),
    claim=LedgerClaim(
        promise="cash the club took, recorded on a ledger Raketa was never party to",
        movements=1,
        held=grosze(0),
        balance=grosze(0),
    ),
    account_slug="assessment-in-progress",
    match_slug="match-private-with-seats-opened",
    seat_index=1,
    arrival=Arrival.AT_COUNTER,
    token="ct1",
)

CORRECTED = SeedLedger(
    slug="ledger-with-a-corrected-movement",
    description=(
        "Her seat claim ran out while the money was still in flight. The share "
        "is recorded as `shareOnline` and then **compensated** by a `REV-` "
        "movement with cause `claimLapsed` (ADR-0081) — nothing is edited and "
        "nothing is deleted, so both stand and `held` folds to zero. The seat "
        "is empty on the match, which is the point: a slow bank does not get to "
        "silently keep 38 zł for a seat nobody got."
    ),
    claim=LedgerClaim(
        promise="a movement corrected by its reversal, with both still standing",
        movements=2,
        held=grosze(0),
        balance=grosze(0),
    ),
    account_slug="assessment-completed",
    match_slug="match-forming",
    seat_index=0,
    arrival=Arrival.CORRECTED,
    token="cl1",
)

IN_DEBT = SeedLedger(
    slug="ledger-in-debt",
    description=(
        "We paid out and did not collect, so she owes 30 zł (ADR-0047). **A "
        "debt is the balance and not a record of its own** (ADR-0058): one "
        "number, one sign, and its provenance read from the cause behind it "
        "rather than from line items. It blocks booking a court and creating a "
        "match, and never paying for a seat in somebody else's — which is the "
        "one line Now puts on the screen (`Raketa02/Raketa#92`)."
    ),
    claim=LedgerClaim(
        promise="a player who owes Raketa money and can still pay for a seat",
        movements=1,
        held=grosze(-DEBT),
        balance=grosze(-DEBT),
    ),
    account_slug="rating-barely-established",
    match_slug="match-private-with-seats-opened",
    seat_index=2,
    arrival=Arrival.COLLECTION_FAILED,
    token="cf1",
    amount=DEBT,
)

LEDGERS: tuple[SeedLedger, ...] = (
    HOLDING_A_SHARE,
    PASSED_THROUGH,
    AT_THE_COUNTER,
    CORRECTED,
    IN_DEBT,
)
