# ADR-0033 — A departure's settlement and its vacancy are independent

- **Status:** Accepted
- **Date:** 2026-08-19
- **Amends:** [ADR-0030](0030-a-departure-is-an-audience-not-a-state.md)

## Context

[ADR-0030](0030-a-departure-is-an-audience-not-a-state.md) replaced the `vacated` scalar with
`vacancies[]` and gave the filler rule as: *"When a filler arrives, **FIFO by `vacatedAt`**
decides whose departure it settles."* The same ADR establishes two other facts that, taken with
it, do not compose:

- a pre-commitment leave is a **full reversal** — the seat is cleared *and* unpaid, nothing is
  owed, so the departure is **born settled**;
- **transfers and gifts are departures born settled** too.

Resolving [the ladder's structural defects](https://github.com/Raketa02/Raketa/issues/8) forced
the collision into the open. That ticket kept rungs producing `formingBack` / `protectedBack` as
a **time-boxed annotation** — a departure marks the match for twenty-four hours, guarded on
`now − vacatedAt < 24 h` **and the emptied seat still being empty**. The ladder therefore needs
to read *is there still a hole in this match*, while the leaver's card reads *is this person's
money decided*. Those are different questions, and the model has one word for both.

Here is the case that breaks the published rule. A four-seat match is full and committed. Kuba
transfers his seat to a named friend who has not paid yet — departure D1, **born settled**,
vacancy open. Ola then leaves — departure D2, **unsettled**, vacancy open. A marketplace filler
arrives. FIFO by `vacatedAt` hands the filler to D1, which has nothing to settle, and **Ola stays
owed while a seat gets filled.** The money goes nowhere and the only person waiting on it is
skipped.

The root `CONTEXT.md` glossary is already most of the way to the fix without saying so. It
defines a **Vacancy** as existing *"only while the seat is unfilled — so a gifted seat creates a
departure and no vacancy at all"*, and defines **Settlement** on the **Departure**. Two nouns,
two lifecycles. ADR-0030's filler rule collapsed them by keying both off one timestamp.

A second question arrives from the same ticket. `5-now_screen_architecture_review.md` §B8 calls
two simultaneous leaves *"not rare enough to leave unhandled"*, and `3.1` §9.3 concedes *"a
second `vacated` overwrites the first."* ADR-0030 made two departures **expressible**; it did not
say what happens when the second one lands on a match the first has already changed. Under
single-writer optimistic concurrency the second leave retries against a match whose seat count
and hold have both moved — and the outcome the player was shown before they tapped may no longer
be the outcome they would get. The sharp case: the first leave drops the match below the
checkpoint threshold, and the second player's free reversal becomes a forfeit between the tap
and the apply.

The alternatives considered for that second question:

**Outcome is a function of state at apply time.** Recompute, apply, tell them afterwards. Correct
for a machine and indefensible at the till: `3.1` shows the player all four outcomes *as the
basis for the decision*, and silently landing a worse one is the same class of defect as the
leaver's card vanishing — which is what ADR-0030 exists to fix.

**First-writer-wins on the whole window.** The second leave is rejected until the first settles.
Safe, and it blocks a normal Saturday: with four seats, a four-hour rescue window and a group who
know each other, two departures are ordinary.

## Decision

**We will treat a departure's settlement and its vacancy as independent facts.** A departure is
**settled** when no further seat event can change its outcome. A **vacancy** exists while the
seat it emptied is unfilled. Neither implies the other: a pre-commitment reversal and a transfer
are settled departures that still leave a hole, and a departure awaiting a rescue is an
unsettled departure whose vacancy may be closed by the very filler that settles a different one.

**We will state which fact each reader uses.** The resolution ladder reads **vacancy existence**
— rung 9's twenty-four-hour annotation is about a hole in the match. The leaver's card reads
**settlement** — it is about their money. No reader may substitute one for the other.

**We will amend ADR-0030's filler rule to run over two sets.** A filler **closes the oldest open
vacancy** and **settles the oldest unsettled departure**, and those are not always the same
departure. FIFO orders each set by `vacatedAt` independently. A filler arriving when every
departure is already settled closes a vacancy and settles nothing, which is correct.

**We will resolve concurrent leaves by quote-and-confirm.** The leave command carries the
**outcome label** the player was shown. On apply the outcome is recomputed against current state;
if the recomputed outcome is **strictly worse** than the quoted one, the command is refused and
the player is re-presented with the new position. Equal or better applies.

- The quoted subject is the **label**, not the amount. An amount can move for reasons unrelated
  to the leave — a discount landing, a club price change — and refusing on those is noise. The
  label is what the player was actually shown as the basis for deciding.
- The ordering is `refunded in full > refunded half > forfeited = reversed-with-nothing-returned`.
  **Forfeit ranks equal to a zero refund, not below it.** The quote protects money, and the money
  is identical; a confirmation dialog that says *"still zero"* is friction bought for no
  protection. That the match is now cancelling around them is a **notification** at the moment
  the checkpoint fires, not a refusal at the moment they leave.
- The quote carries no expiry of its own. It is meaningful only within the request, and
  ADR-0030's command log already covers replay.

**Two refusals are absolute and are not quote-driven**: a player who no longer holds a seat, and
the owner of a private court (ADR-0030's one refused departure). Everything else re-evaluates.

## Consequences

**ADR-0030's filler rule as published is wrong and this ADR is the correction.** ADRs are
immutable here, so 0030 keeps its text and gains an index annotation. Anyone implementing the
cascade from 0030 alone will write the collapsed rule; the amendment has to be found, which is
the cost of the immutability convention and the reason the annotation matters more than usual.

**Two FIFO queues over one list is a real implementation hazard.** They are ordered by the same
timestamp and differ only in their filter, so a single sorted traversal that stops at the first
match will silently do the wrong thing. This is the kind of defect that shows up as *one player
was never refunded*, months later, and never as an error.

**Quote-and-confirm makes leaving a two-phase act in the worst case.** A player who taps leave
during a concurrent departure gets a dialog instead of a completed action. That is the intended
cost, and it lands precisely on the case where the stakes changed — but it also means the leave
flow needs a re-present state that did not previously exist, on a screen where the player is
already unhappy.

**The client must not compute the quote.** It carries the label the server sent it. A client that
derives the outcome locally and quotes its own derivation will disagree with the server about
what "worse" means, and the refusal will fire on the wrong cases — or fail to fire.

**Ranking forfeit equal to zero means one real degradation passes silently.** A player quoted 0 %
whose match is cancelling at the checkpoint leaves without a second confirmation and learns from
a notification. This is a deliberate acceptance, and the notification is now load-bearing rather
than courteous.

**Settlement is monotonic upward (ADR-0030) and vacancy existence is not.** A vacancy opens and
closes and can open again if the filler themselves leaves. Anything that assumes both axes move
in one direction — a projection, a conformance suite, a cached card — is wrong about the second.
