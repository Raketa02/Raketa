# ADR-0047 — We hold no money, and a failed collection becomes a debt

- **Status:** Accepted
- **Date:** 2026-08-20
- **Answers:** the hold-lifecycle question left open by [ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) — by removing the hold

## Context

[ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) said the owner's guarantee is *"held
against their account rather than paid to the club"*, and [#17](https://github.com/Raketa02/Raketa/issues/17)
called it **uncaptured**. Neither said what the hold physically is, and the two readings diverge
completely: a **card pre-authorisation** is real money fenced — collectable, and therefore
lapsable — while a **ledger obligation** is a debt with nothing behind it.

We started from the authorisation, because the owner's liability does two jobs nothing else does:
it is the sole protection for a stranger who paid, and the sole deterrent against booking a
private court as a free speculative open match
([ADR-0043](0043-opening-a-court-is-the-private-paths-commitment.md)). An obligation we cannot
collect converts both into nothing, silently.

The authorisation then failed on its own terms. **A card guarantee survives about a week; a court
may be booked far further out.** So a fence placed at booking evaporates weeks before anyone
plays, and nothing announces it. Renewing it automatically every few days for the life of the
booking is a month of unattended machinery whose failure mode is a quiet decline on a Tuesday —
discovered at the same late moment we would have discovered it with no fence at all, having built
the machinery to get there.

And [ADR-0046](0046-one-reconciliation-two-hours-after-the-reservation-ends.md) removed the last
argument for holding money early. Once collection happens *after* the event, there is no earlier
moment a fence is protecting.

The remaining exposure is therefore real and cannot be engineered away: between booking and
reconciliation we carry the owner's word. The only question is what happens when the word does
not convert into money. An earlier proposal — refuse split payment at clubs offering no free
cancellation — was a special case built on an escape hatch that ADR-0046 has already removed for
every club, so it protected nothing that the general answer does not.

## Decision

**We will hold no money before reconciliation, and we will treat a failed collection as a debt to
Raketa.**

- **No pre-authorisation anywhere in the model.** At booking we take the owner's own share, save
  their card, and obtain **explicit consent to charge unpaid shares later**. The liability is
  stated at the moment they choose split payment, not discovered afterwards.
- **A failed collection becomes a player debt.** The club has been paid throughout
  ([ADR-0045](0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md)), so the club is
  never at risk. Raketa carries the receivable and the owner owes Raketa.
- **A debt blocks only what creates new liability.** The player cannot book a court or start a
  split reservation while they owe for one. They **may** still pay for a seat in someone else's
  match, because that is their money up front and carries no risk to us. Freezing a player out of
  the paid seats stops them spending money they are willing to spend, makes the debt harder to
  clear, and turns a collectable receivable into a deleted app.
- **A private booking may be made at most two weeks ahead**, and the horizon is **uniform** — it
  applies to solo bookings and open-match creation as well, not only to the split path that
  motivates it. The money argument justifies only the narrow version; a booking horizon a player
  must learn twice is one they meet as a surprise at the worst possible moment.
- **The owner is told four times**, and two of those messages exist to change outcomes rather
  than to inform:
  1. **At booking** — split payment means she is the booking owner and is liable for unpaid
     shares, with consent to charge taken there.
  2. **Throughout** — a standing Paid/Pending view inside the reservation, so exposure is watched
     rather than discovered.
  3. **At the club's cancellation deadline** — the only moment she can still act for free: cancel
     at no cost, chase an invited player, or open the seat to the marketplace.
  4. **Before we charge her** — which is what makes the amount something she was expecting.

  A player reminder also goes to everyone who still owes, one hour before the match starts.

## Considered options

- **Pre-authorise and renew.** Real money guarded for the whole booking, at the price of
  long-running unattended machinery with a silent failure mode and the same eventual outcome.
- **Charge the owner the outstanding amount up front and refund as shares arrive.** No credit
  risk at all — and it is solo booking wearing a hat, destroying the reason the split path exists.
- **Refuse bookings beyond the authorisation horizon.** Amputates the far-ahead booking, which is
  most of the reason to book a private court.
- **Refuse split payment at clubs with no free cancellation.** A special case whose premise
  ADR-0046 removed.

## Consequences

**Easier**

- **Nothing to lapse, renew, capture or release.** The hold's entire lifecycle — the question
  this decision was opened to answer — stops existing.
- **One credit rule for every club**, rather than a policy that changes with a club's
  cancellation terms.
- **A failed card is not a crisis.** The club is whole, the match already happened, and what
  remains is an ordinary receivable against an identified player who wants to keep using Raketa.

**Harder**

- **We are unsecured for the whole life of a booking.** Up to two weeks of carrying a promise,
  bounded by the horizon and by nothing else. This is the honest cost of the model and it is not
  disguised.
- **A debt-and-block mechanism has to exist** — balance, blocking rule, clearing path, and the
  copy for all three. It is new machinery on a surface that had none.
- **Write-off and escalation are undecided.** How long a debt sits, whether it is ever pursued
  beyond blocking, and who decides — a collections question, out of this map's scope, and it must
  not be answered by whoever builds the block.
- **A uniform two-week horizon constrains paths that carry no credit risk**, solo bookings
  included. Accepted for legibility, not for safety.
