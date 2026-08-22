# ADR-0089 — `heldSince` outlives the reclaim that ends it

- **Status:** Accepted
- **Date:** 2026-08-22
- **Amends:** [ADR-0031](0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md)

## Context

[ADR-0031](0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md) introduced `heldSince` and
gave its lifecycle in one sentence:

> `heldSince` is a new stored fact: written when a hold is first granted, **cleared when it
> lapses**, and rewritten if a hold is granted again.

Two paragraphs earlier the same ADR fixes what the field is *for*:

> We will measure `maxHoldAge` from `heldSince`, not from match creation. […] the clock starts
> when the hold is first granted.

And two paragraphs later it fixes that staleness is re-evaluated rather than latched:

> **A hold that regains certainty is no longer stale.** Staleness is evaluated on the current
> facts, not latched. A third payment on a stale 2-of-4 match takes it to `n−1`, the guard
> closes, and the hold is live again.

Building the ladder ([`Raketa02/Raketa#71`](https://github.com/Raketa02/Raketa/issues/71))
found that those three cannot all hold. Clearing `heldSince` on a stale reclaim clears the very
clock that fired. On the next look the ladder finds a match on two paid seats, twelve hours or
more from its start, with no hold and nothing to age — so it grants one, writes `heldSince` at
the new instant, and the club's cap expires it again a cap later. **Rule 11 becomes a court
flickering rather than a court going back on sale**, and it does so silently: every individual
step is correct, and nothing about a passing test suite would look different.

The defect was found by a property test over the record grid, not by reasoning — the same
grid walk that found the wake off-by-one in `#63`. It asserted that the record a writer leaves
behind having done what the ladder said is one the ladder then leaves alone, and the reclaimed
match came back saying *grant*.

The kernel already assumed the opposite of ADR-0031's sentence and had done since `#63`.
`_STALE_REWRITES` contains `heldReleased`, so `heldReleased → heldStale` is a live rewrite —
and it can only ever fire on a record whose court has gone back **and** whose hold still has an
age to be stale by. Under *cleared when it lapses* that rewrite is unreachable code.

The alternatives considered:

**Clear it, and refuse to re-grant on some other ground.** There is no other ground on the
record. Whether a court should be kept aside is composed from the seats, the policy and the
clock; none of them changed when the club took the court back. Re-deriving *this match already
had its chance* would need a fact, and the fact is `heldSince`.

**Clear it, and let the ladder re-grant.** Honest about the code and indefensible at the club:
a venue that capped speculative holds at forty-eight hours would find the same court kept aside
again on the same terms, for ever, and the instrument it was given would do nothing.

**Latch staleness with a flag.** Directly contradicts ADR-0031's own decision, and it costs the
answer to *what should a payment landing after the cap do* — it must re-earn the hold, and a
latch is what stops it.

## Decision

**We will keep `heldSince` when a hold is reclaimed, and read *is a court being kept aside* from
`heldSince` and `releasedAt` together.**

- `heldSince` is **when the hold being aged was granted**. It is written at a grant and is never
  cleared by a reclaim.
- `releasedAt` is **that the court has gone back**, and is cleared by the next grant.
- `keepingACourt(record)` is `heldSince is not None and releasedAt is None`. Nothing reads
  either field alone to answer that question.

**Staleness stays unlatched, and certainty rising is what ends it.** A third payment closes the
`filled < n−1` guard, the ladder grants again, and the new grant writes a new `heldSince` —
because it is a new hold at a new level of certainty. That is ADR-0031's *"it re-earns the hold
rather than arriving too late for one"*, unchanged and now reachable.

**A reclaimed hold keeps ageing, and its card keeps telling the truth.** `heldStale` renders
`now − heldSince`, so a hold reclaimed at forty-eight hours and looked at a week later says a
week. ADR-0031 requires the age printed to be the hold's real one; that requirement now extends
past the reclaim, which is the only place the number is ever shown.

## Consequences

**ADR-0031's sentence is wrong as published and this ADR is the correction.** ADRs are immutable
here, so 0031 keeps its text and gains an index annotation. Anyone implementing the ladder from
0031 alone will clear the field and build the flicker; the amendment has to be found, which is
the cost of the immutability convention.

**A second field is now load-bearing for a question that reads like one field.** `heldSince is
not None` looks like *a court is held* and is not, which is exactly the kind of near-miss that
survives review. It is why the reading is a named kernel function rather than an expression
callers write out: there is one place to get it right, and
`tests/typecheck/kernel_misuse.py` pins the confusion between *what the ladder says* and *what
the record says* as a type error.

**A match can carry a `heldSince` far older than any hold it currently has.** A support agent
reading the row sees an instant that is not *when this court was taken* but *when the hold we
last aged began*. The name is honest and the pairing is not obvious, and the risk is a future
reader treating the column as a court's start time.

**The cap's wake stays scheduled on a released record**, because `heldStale` can still arrive
after the court has gone. Conditioning that boundary on the court still being kept drops the
instant the `heldReleased → heldStale` rewrite fires — which the wake property test caught, and
which is the second reason this decision is a kernel one rather than a repository detail.

**Nothing about a club's instrument changes.** A club that caps speculative holds still gets its
court back at the cap, still gets it back for ever rather than for one cycle, and still loses it
again the moment the match earns it with a third payment.
