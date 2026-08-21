# ADR-0055 — The Money context is event-sourced, with one stream per player

- **Status:** Accepted
- **Date:** 2026-08-21
- **Discharges:** the promise [ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md) borrowed — *"the money ledger — event-sourced, every movement referenced"* — which was named as an existing answer while nothing of it existed

## Context

[ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md) argued that the Matches context
needs no history because everything genuinely disputable is answered somewhere else, and its
table put the biggest row — *"what was I charged, what came back"* — on **the ledger**. That
argument is only as good as the ledger, and the ledger did not exist: no module, no aggregate,
no decision. `now-section-domain-spec.md` §H.6 asserts in one line that it is event-sourced
*"even though the match is a record with an outbox"*, and stops there.

[ADR-0002](0002-event-sourced-user-aggregate.md) makes event sourcing a **per-context choice
that must be argued**, and [ADR-0018](0018-aggregate-repositories-over-the-event-store.md)
refused a generic `EventSourcedRepository[A]` precisely so that the question could not be
answered by inheritance. ADR-0034 answered it *against* event sourcing for Matches, on the
grounds that almost nothing about a match is stored and the record is the explanation. **The
ledger is the mirror image.** Nothing about a movement is derived; every movement is a fact
that happened at an instant and can never stop having happened. There is no "current state of
the money" that is not a fold over those facts.

**The question an aggregate's stream key has to answer is: what invariant does this aggregate
protect?** The ledger has exactly one — a **balance** — and a balance is per player. The other
natural read axis is per **reservation**: *why was one payer refunded and another not, on the
same court* is the hardest question a support agent is asked, and it spans four people. Only
one of the two can be the stream.

## Decision

**We will model money as its own bounded context — `Money` — event-sourced, with one stream
per player, and we will never delete a movement.**

- **One stream per player**, id derived rather than minted:
  `ledger_stream_id(player_id) = uuid5(namespace, player)`, matching `skill_rating_id`'s rule
  under [ADR-0019](0019-deterministic-assessment-stream-ids.md). Every movement in scope has
  **exactly one player party** — a share paid online, a share marked at a counter, an owner
  reimbursed, a joiner withdrawing, a reconciliation charge, a leaver's settlement, a failed
  collection, a debt cleared — so no movement is homeless and none is written to two streams.
  The one party-less-of-a-player movement, the Raketa→club payout run, is out of this context's
  scope (below).
- **The court view is a query, not a stream.** *"Everything that happened on this reservation"*
  reads across the streams of the people involved, on the reservation reference every movement
  carries. It is a scan; [ADR-0018](0018-aggregate-repositories-over-the-event-store.md)'s
  projection escape hatch applies if and when it stops being tens of rows.
- **The dependency is one-way: Money reads Matches; Matches never reads Money.** This is what
  keeps the derivation kernel a pure function of the record and the clock
  ([ADR-0021](0021-kernel-in-backend-clients-derive-by-comparison.md),
  [ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md)). A ledger read inside state
  derivation would make the ladder depend on a second aggregate's fold, and every state on the
  screen would inherit the ledger's consistency lag.
- **A movement is born in one place, fed by two mouths.** Match-caused movements arrive over the
  **outbox** ([ADR-0003](0003-transactional-outbox-for-event-delivery.md)) — which is what
  ADR-0034 left Matches *"a record with an outbox"* for; externally-caused ones (a payment
  provider reporting a landing, a club marking a counter share) arrive inbound. Both pass
  through one application entry point. **No movement is ever written inside a match
  transaction:** a card charge can fail after the match record is already correct, and pretending
  those are one consistency domain is how a match ends up rolled back because a bank was slow.
- **The reconciliation asserts and pages; it never repairs.** Three standing invariants: **no
  movement has a club as payer** ([ADR-0045](0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md)'s
  promise, enforced rather than trusted); **no player balance is above zero**
  ([ADR-0058](0058-one-balance-and-it-never-goes-above-zero.md)); **every seat's funding chain
  closes** to zero or to its share. The **projection** may be rebuilt at will — §H.6 already
  calls that the disaster-recovery story — but the movements are never touched. A ledger that
  repairs itself has destroyed the evidence of the bug that made the repair necessary, and this
  is the one place in Raketa where the record *is* the answer to a dispute.
- **A movement is never deleted, and account deletion pseudonymises the player party.**
  Accounting records carry a legal-obligation basis that survives an erasure request. Stating
  it here is what makes ADR-0034's *"the answer already lives on the ledger"* unconditional
  rather than true-until-somebody-closes-their-account.

**What this context does not own.** The payment provider and its event mapping, VAT
decomposition and invoice numbering, the club payout run, the Money screen, and debt
write-off or escalation ([ADR-0047](0047-we-hold-no-money-and-a-failed-collection-is-a-debt.md)
stops deliberately short of the last). Those are plumbing and product around a settled
boundary; what is settled here is what a movement **means**.

## Considered options

- **One stream per reservation.** It puts the hardest support question inside one aggregate and
  needs no cross-stream query. Rejected because it protects nothing: a reservation has no
  invariant, and the balance — the one thing that must never be wrong — would then be a fold
  across every reservation a player ever touched, recomputed on every read and enforceable by
  nothing.
- **One global append-only log.** Trivially correct and totally ordered. Rejected on the same
  grounds plus contention: one stream means one version, and every payment in Raketa serialises
  behind every other.
- **A row per movement, no event sourcing.** Consistent with ADR-0034's own choice for Matches.
  Rejected because ADR-0034's reasoning does not transfer — it turned on there being little
  state to have a history *of*, and here the history is the entire content. A row with an
  `amount` that can be updated is exactly the dual write
  [ADR-0017](0017-rating-context-event-sourced.md) refused.

## Consequences

**Easier**

- **ADR-0034 stops being a promissory note.** *"Take it up with the ledger"* now names a thing
  with a stream, an invariant and a retention rule.
- **A player's whole money history is one stream**, so *"what was I charged"* is a fold and not
  a join.
- **The reconciliation invariants are queries.** *"The club is only ever paid, never debited"*
  either passes or fails nightly, instead of being a sentence in an ADR everyone believes.

**Harder**

- **The court view is a cross-stream scan**, and it is the query support actually runs. It is
  cheap now and it is the first thing that will need a projection.
- **The ledger is eventually consistent with the match record.** A movement the outbox lost
  shows up as a seat whose funding chain does not close, hours later, in a nightly job — not at
  the moment it is lost. That lag is the price of not writing money inside a match transaction,
  and the assertion is what makes it survivable rather than silent.
- **Account deletion is now constrained by a context that does not own it.** Money is the second
  thing this effort has bounded without building; the erasure flow has to be designed knowing
  the ledger will refuse to forget.
