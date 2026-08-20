# ADR-0044 — A marketplace seat is a promise of a game, not a share of a court

- **Status:** Accepted
- **Date:** 2026-08-20
- **Bounds:** the glossary's *"a funded seat never becomes unfunded, so a guarantee only ever
  decreases"*

## Context

An opened private court can fail to fill. The court is bought and paid for, so nothing about
that failure resembles an open match's `cancelledIncomplete`, where *"the clock passing on an
incomplete match does not commit the people who paid — their money comes back whole"* precisely
because no court was ever bought.

But somebody has still paid us for something they did not get. The pricing kernel already rules
on the arithmetic — *"A padel match with three players still divides by four, because the court
costs what it costs"* — and says nothing about who absorbs the missing player. Three people on a
padel court is not a short game of padel; padel is 2v2, and the sold formats are two and four
with no third.

**Importing the open match's refund wholesale does not balance.** On a 120 zł padel court where
the owner and one friend have each paid 30, the owner opens two seats, a stranger pays 30, and
the last seat never sells: refunding the stranger leaves the owner owing 90 against the 60 they
would have owed had they never opened the court at all. Opening a seat would cost money, and
nobody would do it twice.

**The fork is not about refunds; it is about what was sold.** Either a seat is a quarter of a
court — in which case the stranger carries the same risk as the owner's friend and nobody is
refunded — or a marketplace seat is a promise of a game, which is a different product bought
through a different door.

## Decision

**A marketplace seat is a promise of a game.** When the sport's sold format cannot be met at the
checkpoint, everyone who bought in from the marketplace is refunded in full and the owner carries
the court.

Three things this fixes that the ticket's original phrasing did not:

- **The trigger is an unmet format, not "incomplete."** Fewer than four for padel, fewer than two
  for tennis and squash. *Incomplete* already means something else on the open path and would
  drag that path's consequences with it.
- **It resolves before the match, at the checkpoint** — not after. Three people do not turn up to
  a padel court and then get refunded; the game does not happen.
- **Players who were in before the court was opened are not refunded.** They bought a court with
  the owner, through the owner. The stranger bought a game, from us. Two payers on one court with
  different deals, because they came through different doors and were told different things.

The arithmetic closes: the owner's worst case is the **whole court price**, which is exactly what
they owed before they ever opened it. Opening a court can never leave an owner worse off than
not opening it — it can only fail to help. That is what makes
[ADR-0043](0043-opening-a-court-is-the-private-paths-commitment.md)'s liability a fair bargain
rather than a penalty.

**This bounds an invariant stated absolutely.** The glossary says *"a funded seat never becomes
unfunded, so a guarantee only ever decreases"* — the rule that stops an owner being re-exposed
when somebody else walks away. A format-unmet refund does unfund a seat and does re-expose the
owner, to the whole court, in one step. The rule keeps its job with its scope named: **a
guarantee only decreases while the match is alive; the checkpoint that finds the court unfillable
settles it in one move to the full court price.** Nobody departed — the match failed — and it
happens once, terminally, never as a fluctuation an owner has to watch.

## Considered options

- **A seat is a quarter of a court; nobody is refunded.** Simpler, and it makes the owner's
  downside smaller. Rejected because we would have sold somebody a padel match through a
  marketplace, taken their money, and handed them nothing — and unlike the owner's friend, they
  had no relationship with anyone on the court and no say in whether it filled.
- **Refund the marketplace joiners after the match.** As originally phrased. Rejected on the
  arithmetic above, and on the observation that there is no match to be "after."

## Consequences

**Easier**

- A player buying a seat from the marketplace has a promise that can be stated in one line: *you
  get the game or you get your money.*
- The owner's exposure is bounded by a number they knew before they booked, which is what makes
  the irreversible commitment in [ADR-0043](0043-opening-a-court-is-the-private-paths-commitment.md)
  something a person can consent to.
- The unmet-format check is a clock event the timekeeper already has to carry a boundary for.

**Harder**

- **Two classes of payer exist on one court, with different rights, and nothing in the record
  distinguishes them except how they arrived.** The seat has to remember whether it was sold
  through the marketplace, and a support agent has to be able to explain why one refund happened
  and the other did not.
- **A stated invariant now carries an exception**, and the exception is the one moment it matters
  most to the person it protects. Recorded here rather than left for the first owner to discover.
- **The owner's true worst case is larger than the number on the screen while seats are selling.**
  Two of four seats sold reads as 60 zł of exposure; if the fourth never sells it is 120 zł. The
  card has to say the whole number, not the current one.
