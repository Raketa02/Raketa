# ADR-0056 — A movement has two parties, and custody follows what was sold

- **Status:** Accepted
- **Date:** 2026-08-21
- **Corrects:** [ADR-0042](0042-a-share-returns-to-the-seats-last-funder.md)'s *"the club was paid at booking and keeps its money"*
- **Narrows:** [ADR-0047](0047-we-hold-no-money-and-a-failed-collection-is-a-debt.md) — *"we hold no money"* is about the owner's liability, not about seat payments
- **Retires:** `now-section-domain-spec.md` §H.5's `held: true` ledger field

## Context

Three accepted records disagree about who is holding a player's money, and the disagreement was
invisible because each was written from inside one path.

`now-section-domain-spec.md` §H.5 says a seat payment is **captured and held by the platform** —
*"`held: true` on the ledger line"* — until `settledNow(m)`, and only then settled to the club.
[ADR-0045](0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md) says an arriving
share *"is paid straight through to the club exactly as before"*, and bounds Raketa's float to
the **refunds we advance**. [ADR-0047](0047-we-hold-no-money-and-a-failed-collection-is-a-debt.md)
is titled *"We hold no money"*. Read flatly, the second and third delete the first, and with it
the entire refundability of an open match.

**They are not in conflict; they are describing two different products, and nobody said so.**

| | What exists when the money arrives | So the money is | And it comes back when |
| --- | --- | --- | --- |
| **Open match** | nothing — no court is booked | **held by Raketa** until the match commits | the match never commits (`cancelledIncomplete`), whole |
| **Private split court** | the court, already bought | **paid through to the club** as it arrives | a marketplace joiner withdraws, or the format goes unmet — out of Raketa's own money |

A second, quieter contradiction sits underneath.
[ADR-0042](0042-a-share-returns-to-the-seats-last-funder.md) argues from *"the club was paid at
booking and keeps its money"*; ADR-0045 says shares reach the club **as they arrive**. The gap
is not a wording quibble. If a club is paid the whole court at booking, Raketa fronts every
unpaid share from booking until reconciliation — under ADR-0047's two-week booking horizon, a
fortnight of working capital on every split court, which is precisely the position ADR-0045
says we do not carry.

And `held` itself is the wrong shape. A movement is an **event**: it happened at an instant and
nothing later changes what happened. *"Is Raketa still holding this"* is a fact about money
**over time** that changes with no new fact about the original event — so as a stored flag it is
a mutable field on an immutable record, the dual write
[ADR-0017](0017-rating-context-event-sourced.md) refused.

## Decision

**We will record every money event as a movement with two parties and a direction, and let
custody follow what was sold.**

- **A movement is `payer → payee`, an amount in gross grosze
  ([ADR-0023](0023-money-integer-grosze-gross-whole-zloty.md)), a seat, a reservation, a
  reference and a cause ([ADR-0057](0057-every-movement-names-the-rule-that-caused-it.md)).**
  The parties are drawn from a closed set — **player · club · Raketa** — and every movement in
  scope has exactly one player party. This is *not* a general double-entry system with a chart
  of accounts; it is a two-sided record over three named parties.
- **Raketa's float is derived, never stored.** It is `Σ in − Σ out` for the Raketa party, per
  seat or in total. So is `held`: for a seat,
  `Σ(player→Raketa) − Σ(Raketa→club) − Σ(Raketa→player)`. **§H.5's `held: true` field is
  retired**; the player-facing sentence it backed — *"Nothing has reached the club yet"* — is
  unaffected and now reads a computed number.
- **Two custody regimes, named.** On an **open match** seat money is genuinely held by Raketa
  until the match commits and the court is booked — that is the money `cancelledIncomplete`
  returns whole, and without it the open path has no refund to give. On a **private split
  court** the court is already bought and every share is paid through on arrival; Raketa holds
  nothing and its float is only the refunds it advances.
  **ADR-0047's *"we hold no money"* is hereby read as *"no instrument stands behind an owner's
  liability"*** — it abolished the pre-authorisation, not the open path's custody.
- **The club is paid the owner's share at booking, each further share as it arrives, and the
  remainder at reconciliation.** ADR-0042's clause is corrected, not reversed: its *argument*
  survives whole under this reading — a leaver's refund still leaves Raketa's account and is
  still replenished by the stranger's payment — because the club was never holding the leaver's
  money to be clawed back from.
- **An online share is two movements, not one:** `player → Raketa`, then `Raketa → club`. It has
  to be, or `held` and the float are not derivable and a refund has no movement to compensate.
  The single-movement `player → club` form exists for exactly one case: cash across a club
  counter, where Raketa genuinely never touched the money
  ([ADR-0059](0059-the-clubs-cash-is-on-the-ledger-and-a-late-mark-is-refused.md)).
- **The club-side movement on the open path is per court, not per seat.** The club sold a court.
  This is where [ADR-0023](0023-money-integer-grosze-gross-whole-zloty.md)'s exactness property
  — `share × players == price` — stops being a comment and becomes the nightly invariant that
  catches a broken split.
- **Which door a payer came through stays on the match record, not on the ledger.**
  [ADR-0044](0044-a-marketplace-seat-is-a-promise-of-a-game.md) requires the seat to remember it,
  because it decides who is refunded when the sold format goes unmet — and that is an input to a
  **rule** the derivation kernel evaluates from the record and the clock alone
  ([ADR-0055](0055-the-ledger-is-event-sourced-one-stream-per-player.md): Matches never reads
  Money). The ledger **references** a seat; it does not define one.

## Considered options

- **One custody regime for both paths.** Whichever one is chosen, the other path breaks: holding
  private shares makes us the party clawing money back from a club we promised never to debit;
  passing open-match shares straight through sells a refundable seat with the money already gone.
- **Full double-entry with accounts.** The correct end state if Raketa ever becomes a finance
  system. Rejected as premature: it is a chart of accounts and a posting engine bought before the
  payment provider that would feed it, and the three named parties give the same checkable
  invariants for none of the ceremony.
- **Keep `held` as a stored flag and maintain it.** Cheapest to read and it is what §H.5 wrote.
  Rejected on ADR-0017's rule — the day the flag and the movements disagree there is nothing to
  say which one lied.
- **Amend ADR-0042 in place.** Refused on the repo's own rule: accepted ADRs are immutable, and
  the reason a past decision looked right is itself information. It carries a scope note pointing
  here instead.

## Consequences

**Easier**

- **One sentence answers *who has my money right now*, per path**, and it is the same sentence a
  support agent and a player can both hold.
- **The float and `held` cannot drift**, because there is nothing to drift from — both are folds
  over the same movements.
- **"The club is only ever paid, never debited" becomes checkable**: no movement may name a club
  as payer, and a nightly query says so.

**Harder**

- **Two regimes is two things to learn**, and the difference is invisible on the screen — the
  same 30 zł buys a held seat on one path and a passed-through share on the other. The
  distinction is real, and it will have to be explained to whoever writes the refund copy.
- **Every online payment writes two movements**, doubling the volume for the one benefit of a
  derivable float. Accepted, because the alternative is a stored number that can be wrong.
- **Raketa carries a working-capital position on the private path that only reconciliation
  clears** — every refund advanced out of our own money, recovered from the owner hours after
  the slot ends. ADR-0045 named this; this record makes it a number that can be read off the
  ledger rather than an acknowledged risk.
