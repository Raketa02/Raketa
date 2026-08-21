# ADR-0057 — Every movement names the rule that caused it, and a mistake is compensated

- **Status:** Accepted
- **Date:** 2026-08-21
- **Extends:** [ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md)'s four-cancellation-flags argument to money

## Context

The hardest thing a support agent will be asked is not *what moved* but *why this and not that*.
[ADR-0044](0044-a-marketplace-seat-is-a-promise-of-a-game.md) creates the case deliberately:
on one court, a marketplace payer is refunded when the sold format goes unmet and a pre-opening
payer is not — *"two payers on one court with different deals, because they came through
different doors and were told different things."* Its own Consequences flag the cost:
*"a support agent has to be able to explain why one refund happened and the other did not."*

Parties, amount and seat do not explain it. From those alone an agent has to re-derive
ADR-0044's rule in their head, against a court they are seeing for the first time, while
somebody is on the phone. That is not an audit trail; it is a bank statement.

[ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md) already made this exact argument
one context over, about cancellation: the model *"does not carry one cancelled flag — it carries
four, because they are four different stories and the player deserves to know which one
happened."* The same claim is true of money and nobody had made it.

**Event-sourced also means nothing is ever edited**, and money gets recorded wrongly in ways that
have nothing to do with bugs: a club marks the wrong seat, a duplicate webhook lands, a
chargeback posts weeks after the game. The ledger needs a correction shape before it needs any
of them.

`now-section-domain-spec.md` §H.6 records the trap waiting for whatever shape is chosen: on
`inventoryLost` and `cancelledClub`, *"everybody is refunded in full, including anybody who had
already left"* — so a player who left at T−20h and took a 50 % outcome gets the other 50 % back,
and *"a reconciliation that assumes refunds are monotone will flag these as duplicates."*

## Decision

**Every movement carries a `cause` from a closed enumeration, and a wrong movement is corrected
by a compensating movement, never by an amendment.**

- **The cause is a closed enum, not free text.** A cause nobody enumerated is a rule nobody
  decided. It names the rule that fired — `shareOnline`, `shareAtCounter`, `ownerReimbursed`,
  `withdrawnBeforeLock`, `formatUnmetRefund`, `reconciliationOwnerCharge`, `leaverReversed`,
  `leaverFull`, `leaverRescue`, `leaverForfeit`, `collectionFailed`, `debtCleared`, and one per
  terminal cancellation.
- **The enum is derived from the situation model and owned with it.** The rule: **every terminal
  situation that moves money contributes exactly one cause.** So the 33 situations generate the
  list, and adding a 34th forces *"what does this do to money"* at the moment the situation is
  added rather than at the moment somebody is charged wrongly. This is why the enum is short by
  four today — the four terminal cancellation flags (`inventoryLost`, `clubCancelled`,
  `formCancelled`, `checkpointCancelled`) are four different stories about money as well as
  about the match. **Enumerating the full list is not this record's work**; it is a mechanical
  walk of the 33 that belongs with the `GET /now` wire contract, where they are enumerated once
  already.
- **`settlementReopened` is its own cause.** The §H.6 asymmetry is not another refund of the same
  kind — it is a compensating movement against a departure that was already *settled*, and it is
  the one movement not explained by the situation the player is currently in. Given its own name,
  the monotone-refund assumption fails loudly at the enum instead of quietly at the totals.
- **Corrections are compensating movements.** `REV-…` is already reserved in the reference
  vocabulary for exactly this, and a compensation carries its own cause. Nothing is amended and
  nothing is deleted
  ([ADR-0055](0055-the-ledger-is-event-sourced-one-stream-per-player.md)).
- **A chargeback is a movement, not an erasure**, and it becomes a debt by the same path as a
  failed collection ([ADR-0047](0047-we-hold-no-money-and-a-failed-collection-is-a-debt.md)) —
  the outcome is identical: we paid out and did not collect.

**What this buys, stated concretely.** On an unfilled private court, `formatUnmetRefund` appears
against the marketplace payer and simply **does not exist** for the pre-opening payer on the
same court. The difference is a thing an agent can read aloud, rather than a rule they have to
reconstruct. And *"read a debt back to the seat that caused it"* is a query over causes —
`collectionFailed` names its reservation — not a schema of line items
([ADR-0058](0058-one-balance-and-it-never-goes-above-zero.md)).

## Considered options

- **Free-text reason.** Costs nothing and stays accurate forever, because it can say anything.
  Rejected: it makes the ledger unqueryable, and it lets a rule ship without anyone noticing a
  decision was needed.
- **No cause; derive it from the situation at the time.** Appealing, since the situation model is
  a pure function of the record. Rejected because it is a function of the record **and the
  clock** — the situation that caused a movement is not the situation the match is in now, and
  reconstructing "what would this have said in April" is precisely the history ADR-0034 chose not
  to keep.
- **Amend a wrong movement.** Simplest possible support workflow and it loses the one thing the
  ledger exists to hold.

## Consequences

**Easier**

- **A support conversation is reading, not deriving.** The ledger says which rule fired, on which
  seat, in which reservation.
- **Adding a situation forces the money question**, so the enum cannot silently fall behind the
  ladder.
- **The monotone-refund trap has a name**, and the nightly reconciliation can exclude
  `settlementReopened` explicitly rather than special-casing two cancellation flags.

**Harder**

- **A closed enum is a migration every time the model grows a terminal situation** — which is the
  point, and it is a cost paid by whoever adds the situation rather than by whoever debugs the
  charge.
- **The enum is knowingly incomplete as this record is accepted.** Four causes are missing and
  named as missing; a reader who takes the list as exhaustive will be wrong. The completing walk
  is owed by the wire-contract work.
- **Compensations double the row count on every correction**, and a naive *"what did this player
  pay"* sum that ignores causes will be wrong in both directions.
