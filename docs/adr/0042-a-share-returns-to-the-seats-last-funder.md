# ADR-0042 — A paid share returns to the seat's last funder

- **Status:** Accepted
- **Date:** 2026-08-20

## Context

`3.1-enrolled_match_states_and_transitions.md` ADJACENT governs the money on a private court in
one sentence: *"Every public share that is paid reduces the owner's guarantee, złoty for
złoty."* [The leaver](https://github.com/Raketa02/Raketa/issues/7) then settled that a **solo**
booking is paid in full at booking — the split-vs-solo fork is made at booking, and adding
friends afterwards is a roster act with no money attached.

Those two decisions collide. A solo owner who opens a seat to the marketplace has no guarantee
left to reduce, because a solo booking holds nothing back. A stranger pays, and the sentence has
nothing to act on.

**The collision is not about solo courts.** It is that one sentence was written for one of three
cases and applied to all of them. A seat standing empty got there in exactly one of three ways,
and each has a different party owed:

| The empty seat | Who funded it | What an arriving share does |
| --- | --- | --- |
| Nobody ever took it | **Nobody** — the owner's uncaptured hold covers it | Releases that much of the hold |
| Someone paid and left | **The departed player** | Settles their departure at 100 % |
| The owner bought the court outright | **The owner, in cash, at booking** | *undefined* |

The spec wrote down the first. [The leaver](https://github.com/Raketa02/Raketa/issues/7) wrote
down the second — *"100 % if anyone takes the seat, 0 % if nobody does."* Only the third was
homeless.

**The reconciliation shape the third case was charged for is already on the bill.** The ticket
framed refunding the owner as *"the platform pays out on a booking it already settled with the
club, which is a reconciliation shape nobody has designed."* But the second case is that shape
exactly: the club was paid at booking and keeps its money, so the leaver's refund leaves the
platform's account and is replenished by the stranger's payment. Paying an owner back is the
same motion aimed at a different person. Nothing new is bought.

## Decision

**A paid share returns to whoever last funded that seat.** One rule, three funders, differing
only in where that funder's money currently sits — an uncaptured hold is released, a departed
player is refunded, an owner who paid cash is reimbursed. `guarantee` stops being the money
model and becomes a *derived view* of the first case.

Three consequences fixed with it:

- **The price of a marketplace seat is always the court price divided by the sport's sold
  format**, and never a figure the owner names. `divide_among_players` is the one constructor;
  an owner-named price would make Raketa a resale market with surge pricing on club courts, and
  would end the property that two seats on the Now screen are comparable.
- **The owner is reimbursed immediately**, not held to match end. In the hold case this is a
  non-event — nothing was ever captured. In the cash case it is a real payment out, and the gap
  it opens (a club cancelling after we have paid the owner) is a debt owed to us by a business we
  hold a contract with, not a reason to make the owner wait.
- **The owner's seat is not sellable.** An owner may hand their playing spot to a named person —
  the mechanism every participant already has — but may never put it on the marketplace. This
  restores [ADR-0030](0030-a-departure-is-an-audience-not-a-state.md)'s refusal of an owner
  departure in full, and it is why an injured owner's court still reads 4/4 with no vacancy for
  the marketplace to find.

## Considered options

- **Hold the share and release it when the match plays.** The only thing this protects against
  is an owner collecting and then walking away — which [ADR-0043](0043-opening-a-court-is-the-private-paths-commitment.md)
  solves directly by making them unable to walk away. Withholding money that is already theirs
  is a clumsy instrument for a problem with a precise one.
- **Refuse the sale: a solo-booked court may not open a seat at all.** Cheapest, and consistent
  with the fork being made at booking — but only if the fork is genuinely irreversible, which it
  is (see [ADR-0043](0043-opening-a-court-is-the-private-paths-commitment.md)). It was rejected
  on the product: at booking an owner has four players and no reason to split; the seat comes
  open on Thursday. Refusing it forbids the single case the marketplace exists for — *I have a
  court and I am one player short* — and it removes a bridge `3.1` explicitly calls one.

## Consequences

**Easier**

- One sentence covers every empty seat on both match kinds, so a fourth way for a seat to empty
  arrives with its answer already written.
- `guarantee` shrinks to a derived number with a single job, and the solo path stops needing a
  parallel money model.
- The three cases are distinguishable from the record without a flag: who last funded a seat is
  a fact the seat already carries.

**Harder**

- **A real payment out to a player now exists on a path the club has already been settled on.**
  It existed before this ADR — the leaver's refund — but this makes it ordinary rather than
  exceptional, and it is the shape a ledger will have to account for.
- **We carry the window between reimbursing an owner and a club cancellation.** Small, rare, and
  recoverable from the club, but it is exposure we did not have.
- **The seat price rule forecloses owner-side discounting** — an owner who cannot shift a seat
  has no lever except waiting. If that is ever wanted, it is a feature where the owner chooses to
  drop their own price, never one where the platform discounts on their behalf
  ([ADR-0043](0043-opening-a-court-is-the-private-paths-commitment.md) refuses the latter).
