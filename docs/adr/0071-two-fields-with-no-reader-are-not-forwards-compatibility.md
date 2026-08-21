# ADR-0071 — Two fields with no reader are not forwards compatibility

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

[ADR-0038](0038-now-is-polled-the-push-is-specified-and-deferred.md) decided that `GET /now`
carries **`listVersion`, `cardVersion`, `serverTime` and `nextTransition` from day one, though
nothing reads them yet**, on one argument: *"adding them later is a breaking change against
phones that cannot be forced to update, which is the entire reason they ship now."*

That argument has since been undermined from two directions, and neither was noticed because
nothing had to draw the envelope until now.

**Two of the four were declared dead.**
[ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md) settled that the phone holds no
rules and that its countdown runs on the device's own clock, uncorrected — and recorded the
consequence in ADR-0038's own header as a scope note: `nextTransition` and `serverTime` have
**"no reader and no prospect of one."** *No prospect* is the load-bearing half. Forwards
compatibility buys the ability to give a field a reader later; a field that will never have one
is an option on nothing.

**The premise is also false as a matter of fact.** Both clients generate their wire types with
`openapi-typescript` (`make gen-api`, [ADR-0006](0006-backend-owns-api-contract.md)) — types
only, erased at build, with no runtime validation anywhere in either client. A field arriving
that an installed phone does not know about is silently ignored; there is no parser to reject it.
So **adding** a field later strands nobody. What strands an old phone is a field it depends on
being **removed**, and nothing depends on these two.

ADR-0038 is not wrong about the danger — it is pointed the wrong way round. The asymmetry is
real; it just does not apply to fields nothing reads.

This decision is recorded separately from
[ADR-0070](0070-now-is-three-regions-and-a-card-has-two-halves.md), which draws the envelope,
because its job is to be **findable by somebody reading ADR-0038's four-field clause and
wondering what became of half of it.** A section inside a long envelope ADR is not.

## Decision

**We will drop `serverTime` and `nextTransition` from the `GET /now` contract, and keep the two
version stamps as monotonically increasing integers.**

- **`serverTime` is dropped.** ADR-0053 refused server-side time correction as an edge case a
  network-synced phone does not produce, and the countdown runs on the device's clock. There is
  no reader and no design in which one appears.
- **`nextTransition` is dropped.** ADR-0053 refused the transition list, refused predictive
  rendering, and fixed that a card names **the one moment it is about** — which ADR-0070 makes a
  structural clock slot on every card's spine. The moment a card is *about* and the moment it
  next *changes* are routinely different, and the field that survives is the first.
- **`listVersion` and `cardVersion` stay**, as increasing integers, in the homes ADR-0070 gives
  them: one stamp per region, one per card. Their reader is named and specified — the deferred
  frame protocol in [`deltas/live-delivery.md`](../specs/now/deltas/live-delivery.md), whose
  monotonic acceptance asks *is this newer than what I hold*. They also do real work today, in
  the race ADR-0070 records between a pull and a tap.
- **ADR-0038's forwards-compatibility rule is narrowed, not withdrawn.** Its shape stands: ship a
  field early when a reader is coming and the phones cannot be updated to receive it later. What
  is corrected is the reason underneath — the trigger is a **named future reader**, never *it
  might be expensive to add later*, because adding is free.

**This is a reversal and is recorded as one.** Two fields that a standing ADR requires are being
removed from a contract before it is written. Left unrecorded, the next session reads ADR-0038,
finds the rule, and re-adds them.

## Consequences

**Easier**

- The envelope contains nothing a build agent has to implement without being able to say what it
  is for. Every field in ADR-0070 has either a reader today or a named, specified reader.
- Nobody finds a `serverTime` in the contract in three years, assumes it is authoritative, and
  builds against a value we never took seriously.
- The rule that survives is stated in terms of a **reader** rather than a cost, which is the form
  that can actually be checked when the next candidate field appears.

**Harder**

- **If the live channel is ever built and wants a server clock for drift, it has to add the
  field.** That is now known to be cheap, and this ADR is the record that it is — but it is a
  step somebody will have to take, and they will find this document rather than a field.
- **Two ADRs now govern ADR-0038's clauses** — [ADR-0054](0054-now-refreshes-when-asked-never-on-a-timer.md)
  took the cadence, this one takes half the fields. ADR-0038 is increasingly a document read for
  its deferral of the push channel and little else, and its header has to carry both pointers.

**Neutral**

- The bytes saved are negligible and were never the argument. The argument is that a declared
  field nothing populates correctly is a trap, and a contract that promises less is easier to
  keep.
