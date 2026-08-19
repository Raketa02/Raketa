# ADR-0023 — Money is integer grosze, gross, and a court price is a whole number of złoty

- **Status:** Accepted
- **Date:** 2026-08-16

## Context

Every złoty figure in Raketa passes through one module. The source specification documents
require integer grosze and give a JavaScript-specific reason — IEEE-754 doubles, and
`0.1 + 0.2 !== 0.3`. Python has `Decimal` and arbitrary-precision integers, so the reason
changes while the conclusion does not: integer minor units is the standard for money that has
to add up, and it leaves no rounding mode to argue about at a call site.

The load-bearing part is the **rounding order**, which the documents call the specification
rather than an implementation detail. Multipliers compound, then one rounding to whole złoty
at the court level, then the divide by the sport's sold player count:

```
96 zł × 0.90 = 86.4  →  86 zł court  →  ÷ 4  →  21,50 zł share
```

Dividing first gives 21,60. The order is the difference.

They then prove the split exact: a whole-złoty court price is a multiple of 100 grosze, and
both 100 ÷ 2 and 100 ÷ 4 are integers, so `divide_among_players` never rounds and never loses
a grosz. They conclude that the worry about a split silently gaining or losing money is
*unreachable*.

**The proof holds only while its premise does, and the premise is not a fact about money.** It
is a property of the seeded rate table and of the rounding function. A club pricing a court at
89,50 zł breaks it silently — 8950 ÷ 4 = 2237.5 — and nothing in the documents notices.

The documents also never mention **VAT**, in roughly five thousand lines. Poland charges it on
court hire, and a booking with real money moving produces a real invoice. So there is a
decision hiding inside the type — is a `Grosze` gross or net? — and it interacts directly with
the rounding, because a price that is whole *gross* is not whole *net*, and the proof protects
only whichever one is rounded.

The alternatives considered:

- **`Decimal` throughout.** Exact, and it moves the rounding decision to every call site
  rather than fixing it at one — the opposite of what this module exists for.
- **Float with a two-decimal round at each step.** The prototype idiom, and the documents are
  right that it is correct as a convention and wrong as a foundation, because the next
  operation reintroduces the error.
- **Integer grosze, with the whole-złoty court price treated as an observation.** Keeps the
  exactness proof as a comment that will quietly stop being true.
- **Integer grosze, with the whole-złoty court price made a law and validated where prices are
  configured.**

## Decision

We will represent money as **integer grosze**, and make the property the exactness proof rests
on an enforced invariant rather than an observation.

- `Grosze` and its refinements `CourtPrice`, `SeatShare` and `Payable` are `NewType`s, each
  with exactly one validating factory. `divide_among_players` accepts only a `CourtPrice`, so
  **dividing before rounding does not typecheck** — there is no path from a raw number to a
  `SeatShare`.
- **The rounding order is the specification.** Multipliers compound, one rounding to whole
  złoty at the court level, then the split by the sport's **sold** player count — the format
  the court is sold in, never the current occupancy. A padel match with three players still
  divides by four, because the court costs what it costs.
- **A court price is a whole number of złoty. This is marketplace law**, not an observation.
  It is validated where a club configures a rate: a rate and multiplier pair whose product
  does not round cleanly is **rejected at configuration**, not discovered at a split. That
  converts the premise into an invariant.
- The exactness property is asserted over the whole catalogue: for every court price and
  player count of 2 or 4, `share × players == price`. A failure means the rounding order was
  broken upstream, which is a far more useful signal than a missing grosz on a receipt.
- `apply_fraction` rounds **half away from zero on the magnitude**, so refunds are symmetric
  in sign and a player receives at most one grosz more than the exact half. Rounding in the
  player's favour is the defensible direction, and it is stated once rather than re-argued by
  each reader.
- `payable_from(share, card)` is the **only** implementation of the card rule, and a card can
  never produce a credit — a 15 zł allowance against a 13 zł share yields a 13 zł offset.
- **Every `Grosze` in Raketa is gross — VAT-inclusive, the number the player sees.** "38,00 zł"
  on a card is a gross figure, and the whole-złoty law applies to it. VAT decomposition is an
  invoicing concern computed from the gross price at settlement, never a second money type in
  the kernel.
- The type stays named `Grosze`. One market, stated rather than assumed. A second currency is
  a new decision, and the rename is mechanical.
- **The kernel never formats money** ([ADR-0022](0022-kernel-negative-space-and-constant-homes.md)).
  Money crosses the wire as integer minor units.

## Consequences

**Easier**

- No float touches a price, and the one place rounding happens is a function with a name and a
  test.
- The seat split cannot lose a grosz, and a property test says so rather than a comment.
- A club cannot silently invalidate the exactness proof, because the configuration screen
  refuses the price that would.
- One card rule, so a player and a club manager cannot read different numbers for one booking.

**Harder**

- **Clubs lose half-złoty pricing.** A venue wanting 89,50 zł an hour must charge 89 or 90.
  That is a real product constraint traded for a real correctness guarantee, and the first
  club to ask will need an answer rather than a shrug.
- **Gross-inclusive pricing puts VAT arithmetic at settlement,** where a rate change or a
  reclassification — sports facilities are not always charged at one rate — becomes an
  invoicing migration rather than a price edit.
- **`NewType` erases at runtime,** so nothing stops `Grosze(x)` being called directly and
  bypassing the factory. The discipline is a convention plus the mypy-as-a-test harness, not a
  runtime guarantee.
- **Arithmetic loses the brand** — adding two `Grosze` yields an `int` — so every operation
  goes through a named function. Noisier at the call site, and arguably the point.

**Neutral**

- The VAT position is a decision with tax consequences. It should be confirmed by a human who
  owns that question; nothing in the kernel changes if it is reversed, only the written
  meaning of the number.
- Whether a *net* figure is ever stored alongside the gross one is left open, and belongs with
  the context that issues invoices.
