# ADR-0079 — A category is the club's own grouping, and the price attaches to it rather than to a court

- **Status:** Accepted
- **Date:** 2026-08-21
- **Narrows:** [ADR-0035](0035-a-reservation-claims-a-court-over-an-interval.md), which named a category *"what is bought and priced"* and did not say who defines one
- **Answers:** the open item handed here by [#9](https://github.com/Raketa02/Raketa/issues/9) — *"who authors a court `category` — a club's word or the platform's"*
- **Split from:** [ADR-0078](0078-club-policy-is-eight-fields-and-two-of-them-ship-dark.md), because this lands on Courts and that lands on Clubs

## Context

[ADR-0035](0035-a-reservation-claims-a-court-over-an-interval.md) gave the category a job and no
author:

> **Category** — what is bought and priced. **The court is assigned, never chosen**, and may be
> swapped for another of the same category until shortly before play; only then is a specific court
> named to the player. This is what lets a seat price be quoted before a court exists and stay
> fixed when one is assigned.

The hold ladder then asks for *"a court of this category"* and nothing in the repo says what makes
two courts one. [#9](https://github.com/Raketa02/Raketa/issues/9) filed it and moved on.

**The v37 seed shows why the question bites, and shows the model contradicting itself.** Zabłocie
Sport (`ps`) has `ct1` and `ct2` — Padel, Mondo, indoor — and `ct3`, Padel, **Wall surface,
outdoor**, carrying `pm: 0.90`. One club, one sport, three courts, and a **per-court price
multiplier** sitting alongside a rule that says any court of the category may be swapped in.
Together those say: you may be moved onto a different court after your price was quoted, and it
costs a different amount. Both cannot be true.

## Decision

**A category is a club-scoped named group of courts, authored by the club, constrained by the
platform to exactly one sport. The price attaches to the category. `court.pm` is deleted.**

### The club authors it

**Interchangeability is a fact only the venue knows.** A platform-defined enum would be either too
coarse to be true — swapping a player from an indoor Mondo court onto an outdoor wall court because
both say *Padel* — or so fine that it is just the surface list under another name, at which point
the platform is guessing at nine venues' operational judgement from a table.

So the club groups its own courts, and the platform constrains only that **a category belongs to
exactly one sport**. That constraint is not arbitrary: a sport's player count is read from exactly
one place everywhere (`CONTEXT.md`), and a category spanning two sports would make a seat share
undefined.

**Cross-club comparability is explicitly not a category's job.** Nothing on Now compares a category
at one club against a category at another; a category is only ever resolved inside the club that
declared it. Anyone reaching for a shared vocabulary of categories is solving a problem no screen
has.

### The price attaches to the category, and `court.pm` is deleted

**A court that costs differently is, by definition, a different category.** `ps` should have been
seeded as two: `ct1`/`ct2` (Mondo, indoor) as one, `ct3` (Wall, outdoor) as another.

This is what makes ADR-0035's *"the court is assigned, never chosen"* honest rather than something
we say while the price moves underneath the player. It is the same argument ADR-0035 used to
justify quoting a seat price before a court exists: **the quote is safe precisely because every
court that could satisfy it costs the same.** A per-court multiplier withdraws that guarantee at
the moment of assignment, which is the one moment the player has no say.

The **club** multiplier `pm` survives — it multiplies the whole club's prices and cannot vary
between two courts the player might be swapped between.

### A category lives in the court catalogue

[ADR-0077](0077-a-club-is-a-record-and-history-is-a-property-of-three-facts.md) made the **court
catalogue** one of the three series whose history is kept, and fixed that *a court is retired,
never deleted* — because availability is a question asked of reservations, and a court that
vanished would make *nothing was free* unexplainable on the day it mattered.

**A category is part of that catalogue and inherits the rule: it is retired, never deleted.** A
past reservation names the court it claimed, and the price that was quoted is copied onto the match
at booking (ADR-0077) — so nothing needs to query a category as of a past instant. What retirement
buys is the same thing it buys for a court: the record still parses.

## Consequences

**The demo week reseeds.** Nine clubs' courts are grouped into categories rather than listed flat,
`ps` splits into two Padel categories, and both `court.pm` values (`0.90`, `1.33`) become category
prices. [#52](https://github.com/Raketa02/Raketa/issues/52) is the ticket that feels this, and it
is a shape change to its input, not a value change.

**`pickCourt` gets its predicate.** The domain spec flags *"`pickCourt` returns the first free
court from a scan"* as **the strongest argument for modelling Courts before Matches**. It can now
say what it scans: the free courts **of one category**, excluded by overlapping interval on the
Courts aggregate. Nothing else about ADR-0035 changes.

**A club can make its own quote unsafe, and nothing stops it.** A club that puts genuinely
non-interchangeable courts in one category has told us they are interchangeable, and the player
is swapped onto the worse one at the same price. There is no mechanical test for this — it is the
same class of judgement as ADR-0077's *three named facts*, and it is the honest cost of letting the
club author.

**A category with no courts left is possible.** Retire every court in one and it survives as a
group that can never be assigned. That is correct rather than a bug — a past reservation still
resolves — but the ladder must treat *category exists, no free court* and *category exists, no
courts at all* identically, which is `inventoryLost` in both cases.

**This does not give a category a name a player reads.** The card prints the court once assigned
(*"Court 2 · Mondo"*), and prints the category before assignment only where the two UI documents
already say it does (`Protected · {cat}`). Whether a club's category names are player-facing copy
is a club-console question, and it is not answered here.

## Alternatives considered

**A platform-defined category enum, like sports.** Refused: `CONTEXT.md`'s rule that adding a sport
is *"a code change and a release, never a row"* is right for sports because a sport's player count
is marketplace law. A category is an operational judgement about which of *this venue's* courts are
mutually acceptable, and the platform has no basis for it.

**Category as a composed tuple — (sport, indoor/outdoor, surface).** Refused: it is the surface list
wearing a schema, it makes every new surface a platform change, and it still gets `ps` wrong, since
what separates `ct3` is the combination plus a price the club chose.

**Keep `court.pm` and re-quote at assignment.** Refused outright: it breaks the one promise
ADR-0035 was written to make — that a seat price is quotable before a court exists and **stays
fixed when one is assigned**.
