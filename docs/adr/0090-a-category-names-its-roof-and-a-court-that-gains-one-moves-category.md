# ADR-0090 — A category names its roof, and a court that gains one moves category

- **Status:** Accepted
- **Date:** 2026-08-23
- **Resolves:** [`Raketa02/Raketa#98`](https://github.com/Raketa02/Raketa/issues/98)
- **Narrows:** [ADR-0079](0079-a-category-is-club-authored-and-it-is-the-priced-unit.md) — the
  platform constrained exactly one thing about a category, its sport. It now constrains two.

## Context

[ADR-0073](0073-a-card-counts-money-and-counts-down-to-what-happens-anyway.md) put
indoor-or-outdoor **on the spine of every card**, and gave the reason:

> It behaves like place, not like state, and leaving it on six situations fails the player at
> the exact moment they are choosing: in November in Kraków it is the most important fact about
> a padel court, and it is absent from every shelf.

[`#73`](https://github.com/Raketa02/Raketa/issues/73) shipped the wire shape — `Cover` as a
required field of `PlaceResponse`, on every match card. **Nothing in the system could answer
it.** A match names a `category_id`; a `CourtCategory` carried a name, a sport, a rate and a
retirement, and whether there was a roof lived inside the *name*: `Padel · indoor`,
`Padel · Wall, outdoor`, `Tennis · outdoor`. A convention in a display string is not a fact.

That is a required field with no producer, and it is the shape this repository is least able to
tolerate: `#73` composed no cards, so nothing was wrong on the day it shipped, and the bill
arrived four tickets later. It has blocked [`#74`](https://github.com/Raketa02/Raketa/issues/74)
and [`#75`](https://github.com/Raketa02/Raketa/issues/75) — the enrolled strip and the ranked
funnel, which are the first two things that compose a match card — and through them
[`#77`](https://github.com/Raketa02/Raketa/issues/77),
[`#79`](https://github.com/Raketa02/Raketa/issues/79),
[`#80`](https://github.com/Raketa02/Raketa/issues/80) and
[`#81`](https://github.com/Raketa02/Raketa/issues/81), each of which embeds the same spine.
Four consecutive commits have reported it as standing and worked around it.

Three facts bound the answer, and each removes an option.

**The specific court is not assigned until fifteen minutes before play.** `kernel.court_named_at`
is the moment, and ADR-0035 is the reason — *"a caller asks for a category and a window, never
for a court"*. A card composed on Monday for a match on Thursday has no court to read a roof
off, so `Court` cannot carry the fact even though it is where the fact is most precisely true.

**A category is already the unit of interchangeability, and the price already attaches to it
for exactly this reason.** ADR-0079: *"a court that costs differently is, by definition, a
different category"*, and that is what makes ADR-0035's *"the court is assigned, never chosen"*
honest rather than something we say while the terms move under the player.

**The court's catalogue is already an effective-dated series** (ADR-0077) — *this court existed,
in this category, between these instants* — and moving a court between categories closes the row
in force and opens a new one.

## Decision

**We will put the roof on the category, keep `Cover` two-valued, and give a court that gains a
roof no operation of its own — it moves category, and the catalogue series records that it did.**

### `CourtCategory.cover`, required, with no default

A fourth field beside name, sport and rate. **Required at construction and with no default**, for
the reason `ClubSnapshot` gives for a price and a zone: a default of *outdoor* is a fabricated
observation, and the assembler that forgot one would be silently wrong rather than fail to
compile.

The objection is real and worth writing down: **a club could group a covered and an uncovered
court into one category**, and then the fact is wrong for one of them. The answer is that such a
category is already mis-authored under ADR-0079, because a roof is precisely the kind of
difference that makes two courts *not* interchangeable — a player swapped onto the other one in
November has been sold something else. Putting the field here **states** that rule where ADR-0079
left it implicit, and it is the same argument that put the price here rather than on a court.

**The platform now constrains two things about a club-authored category** — its sport, and
whether it has a roof — and both are constrained for the same kind of reason: a category
spanning two sports makes a seat share undefined, and one spanning two roofs makes the card lie.
Everything else about a category stays the club's.

### `Cover` moves into the kernel

It was declared in `app/modules/now/domain/vocabulary.py`, which was right while Now was the
only reader. Clubs now **authors** it and Now **renders** it, and a closed set two contexts read
verbatim is ADR-0022's own test for the innermost ring: *a second implementation of it would be
a defect*. It goes in `app/kernel/courts.py`, beside the other vocabularies three contexts share,
with the count pinned the way `CAUSE_COUNT` and `OUTCOME_COUNT` are.

The **schema** is untouched: same name, same two values, same required field on
`PlaceResponse`, and `Cover: "indoor" | "outdoor"` is the same line in the player client's
generated types. What does move is the enum's `description`, because the description *is* the
docstring and the docstring now records this decision — so `openapi.player.json` and
`frontend_player/src/generated/schema.d.ts` gain a JSDoc paragraph and nothing else.
`openapi.club.json` and `frontend_club/` are byte-identical. There is no client work.

### Two values in v1, and a roof is `indoor`

*Covered but open-sided* is a real padel configuration and reads as neither. It stays out, and
the mapping is stated rather than left to whoever seeds the first one: **a roof is `indoor`**.

The question the card answers is *will I be rained on*, and a canopy answers it the same way a
wall does. What a canopy does not answer is *will I be cold*, and that is a real loss — but a
third value is an additive enum member **and a client release for its copy**, and no document in
the specification set has asked for one. ADR-0071 has just refused a field with no reader; a
value with no author is the same refusal.

### A court that gains a roof moves category. There is no operation to re-roof one

`reprice_category` exists because a price change is **a club's decision about the same courts**.
A roof is a change to the court itself, and the model already has the operation for it:
`move_court` closes the court's catalogue row and opens a new one under the new category. #98
asked whether changing a category's cover should close a row and open a new one, and the answer
is that **the category's cover never changes** — so nothing has to be versioned, no new series is
invented, and *a court that gained a roof in October* reads back off the series ADR-0077 already
built.

**So no `CourtCategory` history, and this is not an omission.** ADR-0077 gave a club exactly
three history-bearing facts, and the catalogue's own doctrine is that *"the price quoted is
copied onto the match at booking, so nothing has to query a category as of a past instant."*

Note that cover, unlike the rate, is **read live and never copied onto the match**, and the two
treatments are both correct for the same reason: the price was agreed when the match was posted,
and the roof is a fact about the evening the player is about to walk into.

### The backfill parses the name, once, in the migration

#98 named a third option *"worth naming before it is dismissed"* — that the category is already
the answer and what is missing is only that it is spelled in prose. It is not dismissed; it is
what ships. Parsing a name **on the compose path** would be deriving a domain fact from copy on
the busiest read in the product; parsing it **once, in a migration, in a diff somebody reviewed**
is how prose becomes a fact.

A name containing *indoor* becomes `indoor`; **everything else becomes `outdoor`**. That default
is not a coin toss: telling a player a court is outdoor when it has a roof costs them a match
they would have wanted, and telling them it is indoor when it has none costs them a soaking in
ADR-0073's own November. The answer that never claims shelter a club did not declare is the one
that goes in.

## Consequences

**Easier**

- **Every match card can be composed.** The five tickets blocked on this are unblocked, and the
  fact reaches the spine through the `category_id` a match already names — one read the compose
  path was already making.
- **A category's identity is now stated rather than implied.** Two padel categories at one club
  differ in price *and* in roof, and both differences are fields.
- **The history question answered itself.** `move_court` was already the right operation, and
  the series ADR-0077 built already records it.

**Harder**

- **A club that roofs a court must move it**, and moving it is a different gesture from editing
  it. A console that offers *edit this category* will want to offer a cover field, and the honest
  answer will be that it cannot — which is a conversation, not a bug.
- **A category spanning two roofs is now wrong rather than merely unwise**, and nothing refuses
  it: the constraint is stated here and in the field, and no index or invariant enforces that a
  club authored honestly. It cannot be enforced — only the venue knows.
- **`Cover` in the kernel is a third vocabulary Clubs must import from the innermost ring**, and
  the kernel grows by one module for one enum. The alternative was Clubs and Now each declaring
  two-valued cover and a mapper between them, which is the defect the ring exists to refuse.
- **The two-value decision will be revisited by the first club with a canopy**, and it will be
  revisited as a client release rather than a backend one.

**Neutral**

- **The contract does not move.** `Cover` was already on the wire with these two values; this
  record gives it an author, not a shape.
- The root `CONTEXT.md`'s context table lists indoor/outdoor under **Courts**. The catalogue has
  lived in Clubs since ADR-0079, and this record puts the fact where the catalogue is; the table
  describes intent from before the code and is corrected rather than followed.
- No production data exists — only `local` runs (`docs/environments.md`) — so the backfill is
  exact for every row that exists today, all of which the seeds author.
