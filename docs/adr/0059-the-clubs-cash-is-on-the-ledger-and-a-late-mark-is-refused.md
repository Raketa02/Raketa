# ADR-0059 — The club's cash is on the ledger, and a mark that arrives too late is refused

- **Status:** Accepted
- **Date:** 2026-08-21
- **Closes:** the hole in [ADR-0046](0046-one-reconciliation-two-hours-after-the-reservation-ends.md)'s *"a share reported after reconciliation reimburses the owner — no new machinery"*

## Context

[ADR-0046](0046-one-reconciliation-two-hours-after-the-reservation-ends.md) legitimised a
payment channel the model had not accounted for: **an invited player can pay their share at the
club counter**, and the club marks it paid. It scoped the channel tightly — marketplace seats
are always bought from Raketa online, because *"a refundable seat's money must sit somewhere we
control"* — and it gave the club until `reservationEnd + 2 h` to report.

Then it disposed of the late case in one line: *"A share reported after reconciliation reimburses
the owner. No new machinery: the seat's last funder was the owner, and a paid share returns to
the seat's last funder
([ADR-0042](0042-a-share-returns-to-the-seats-last-funder.md))."*

**That line does not close.** Trace the money. Ania books a 120 zł padel court split four ways
and pays her 30. Bartek pays his 30 in cash at the counter on Saturday. The club does not mark it
before 17:30, so reconciliation charges Ania the 30 that reads as outstanding. On Monday the club
marks Bartek's share paid.

Under ADR-0046 we now reimburse Ania 30 zł. **The club is holding that 30 zł** — Bartek handed it
across the counter — and
[ADR-0045](0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md) says *"the club is
only ever paid, and never debited."* So the reimbursement leaves Raketa's account with no path
back. That is not float; it is an unbounded loss, priced by how slow a club's admin is, and it
is available to any club that discovers it.

There is a prior question underneath. A counter-paid share is money that **never touched
Raketa** — is it on the ledger at all?

## Decision

**A counter-paid share is recorded on the ledger, and a mark arriving after reconciliation is
refused.**

- **A counter-paid share is a `player → club` movement with Raketa as neither party**, cause
  `shareAtCounter`, recorded on the club's word. It is the one movement that is not
  `player → Raketa → club`
  ([ADR-0056](0056-a-movement-has-two-parties-and-custody-follows-what-was-sold.md)), and it has
  to exist: without it the seat reads unpaid forever and the nightly assertion that a seat's
  funding chain closes to its share never passes on any court with a cash payer.
  **The club's mark is authoritative** — ADR-0046 already fixed that reconciliation waits for it.
- **After reconciliation closes, the mark is refused.** The window is the whole match plus two
  hours. A mark arriving after it is rejected with a stated reason: the share was settled by the
  owner, and **the club returns the cash to the player at the counter**. Nothing moves on
  Raketa's side, no reimbursement is owed, and ADR-0045 is untouched. The party holding the money
  is the party who puts it right.
- **The mitigation is entirely in the club console**, and it is a condition of the channel rather
  than a nice-to-have: outstanding shares and the closing window must be visible to the club
  throughout, and a share still unmarked as the window nears its close is chased. A club that
  cannot see the deadline will miss it, and the player pays for that in an argument at a counter.
  **The console surface itself is out of this map's scope** — what is fixed here is what it must
  make visible.

## Considered options

- **Reimburse the owner and net it off the club's next payout.** The honest answer, and what a
  mature system does. It also has a better argument than it first appears: ADR-0045's actual
  sentence is *"a **player's change of mind** can never reach into a club's account"*, and a
  club's own late reporting is not a player's change of mind — so this violates the ADR's letter
  while respecting its reason. Rejected for v1 because it needs a club-side receivable, a
  netting rule and a payout that can go negative — a second money path built for a case that is
  a club's administrative failure, and one that quietly makes *"never debited"* false in a way no
  club has agreed to.
- **Reimburse the owner and absorb it.** No new machinery, genuinely. Rejected: it is unbounded,
  it is cheapest for the club that is worst at reporting, and nothing in it improves over time.
- **Keep the counter-paid share off the ledger.** Defensible — we never touched the money.
  Rejected because the ledger then cannot answer *"was this seat paid"*, which is the question
  reconciliation is built on, and the nightly invariant would have to carve out an exception for
  every cash court.
- **Extend the window when a club is late.** Moves the problem and removes the only moment the
  model has ([ADR-0046](0046-one-reconciliation-two-hours-after-the-reservation-ends.md)'s whole
  point is that there is exactly one).

## Consequences

**Easier**

- **One reconciliation still means one reconciliation.** No movement exists after it, so the
  *"the owner's card is touched once"* promise survives the cash channel.
- **The nightly seat-chain invariant passes on cash courts**, because the cash is on the ledger.
- **ADR-0045 stays absolute.** *"The club is only ever paid, never debited"* needs no exception
  clause, which keeps it a query rather than a query-with-a-carve-out.

**Harder**

- **The player is the one standing at the counter.** Bartek paid in good faith and has to ask for
  his cash back from a club that has already had it for two days, while Ania was charged for a
  share he thought he had paid. Raketa's position is correct and the experience is somebody
  else's problem — which is exactly the shape that erodes trust in a platform whose stated
  constraint is *if the rules are not clear enough, players leave*.
- **A club channel now has a hard deadline with a real consequence**, and this record creates an
  obligation on a console that does not exist yet. Shipping the cash channel before that surface
  ships would be shipping the failure mode without the mitigation.
- **The better long-term answer is the one refused here.** If cash volume grows, netting against
  the club payout is where this goes, and it will arrive as a decision to make *"never debited"*
  conditional — which should be reopened deliberately, on evidence, and not by whoever first
  meets an angry club.
