# ADR-0064 — A travel radius orders Now and bounds only a search, and an unmeasurable distance is missing evidence

- **Status:** Accepted
- **Date:** 2026-08-21
- **Narrows:** [ADR-0027](0027-fit-and-certainty-are-separate-ranking-is-policy.md)'s
  *"distance, price and level are never exclusions"* — by naming the one surface on which a
  distance may exclude, and why that surface is different in kind.
- **Extends:** [ADR-0063](0063-where-a-player-plays-is-declared-and-precision-follows-the-anchor.md),
  which creates the anchor this radius is measured from.

## Context

[ADR-0027](0027-fit-and-certainty-are-separate-ranking-is-policy.md) fixed that candidate
generation excludes on **facts**, never on preferences, and named distance first among the
three that are never exclusions. `matchfit`'s own module states the same thing in its own
words: *nothing is ever excluded on distance*. [ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md)
carried the rule into the seat offer, and
[Raketa02/Raketa#30](https://github.com/Raketa02/Raketa/issues/30) confirmed it there
explicitly: being far away must never stop a player hearing that a seat has opened.

**But a declared radius reads naturally as a search bound.** *"Search within 5 km of the
selected location"* is a wall, and a wall is an exclusion. The two readings are not a matter of
emphasis — they differ for a real case. Ania declares Podgórze and 5 km. On Tuesday there is a
match at Ogrody 33, 8 km away: her exact level, her usual hour, three people she has played
with before, one seat left. Under one reading she sees it ranked lower; under the other it
does not exist and she never learns it did.

**A second gap arrives with the same field.** ADR-0063 makes the distance printable only when
the player gave an area or a postcode. A player who gave only a city has **declared a limit
against a club nobody can measure** — and the scoring has no way to say so. `ClubSnapshot`'s
distance is a required field with no representation for *unknown*, and the glossary's
constraint-term rule covers a missing *declaration*, not a missing *measurement*.

## Decision

**We will let a radius bound a question the player asked, and never a screen we composed.**

### The same number, two jobs, decided by who asked

- **The profile radius is a preference.** It steers ranking on Now and orders rung 6 of the
  invitation ladder. It **never removes** a match, a shelf card, or a person from an offer.
- **The search radius is a bound.** When the player types a location and a distance into
  Search — a field ADR-0063 gives Search when Search is built — the result is narrowed,
  because narrowing is what they asked for.

**The distinction is not the number, it is the author of the question.** Hiding a match on Now
is the app deciding on a player's behalf, and a bound leaves nothing to soften it with: there
is no *"3 more just outside your range"* line available, because a bound means those candidates
were never retrieved. A search result, by contrast, is an answer to a question with a stated
scope, and a scope that quietly widened would be the defect.

**This is why ADR-0027 is narrowed rather than contradicted.** Its rule protects a player from a
preference being used as a gate on something they did not ask to have gated. A search is the
case where they did.

### An unmeasurable distance is missing evidence, not an absent limit

Three cases, not two:

| The player | The club | The travel term |
|---|---|---|
| Declared no radius | Measurable | **Full marks, weight kept.** No limit means no problem — the existing constraint rule, unchanged. |
| Declared a radius | Measurable | Scored, decaying past the radius. |
| Declared a radius | **Not measurable** (city-only anchor) | **Dropped.** Its weight leaves the denominator and Coverage reports the shortfall. |

**The third row is new, and it is not the first row.** Treating an unmeasurable club as *no
limit* would score every match full marks on travel for the majority of players, so a 91 on a
skipper's screen and a 91 on their neighbour's would not be the same claim — the inflation
`absence never flatters` exists to prevent. Scoring it at nothing would dock a player eight
points for using a skip button we deliberately gave them.

**Travel does not change kind.** It remains a **constraint** term whenever it can be computed.
The constraint rule is about the absence of the player's *declaration*; this is the absence of
the *club side* of the comparison, which the rule was never written about. A term that cannot
be computed is dropped, whichever kind it is.

**This requires a model change:** the club's distance becomes **optional**, and every reader
handles its absence.

## Consequences

**Easier**

- **Both halves of the location model stay true.** A radius that bounds a search and orders a
  feed is one rule, not a rule and an exception to it.
- **A great match 8 km away still reaches the player**, on the screen where they did not ask
  for it to be hidden.
- **Scores stay comparable between players.** Nobody's score is inflated by what we could not
  measure, and the app can say which part it could not measure.
- **The invitation ladder's rung 6 is now fully specified**: it orders, it never filters, and
  its input exists.

**Harder**

- **One number means two things, and nothing on the screen explains it.** A player who set
  5 km and sees a 9 km match on Now may reasonably feel their setting was ignored; no shelf
  title says *"we do not hide far matches"*.
- **Coverage reads low across most of the launch cohort.** The city-only player is the majority,
  and every one of their scores is missing the travel weight. That is the mechanism working, and
  it will look like a defect on any dashboard that plots coverage without splitting by anchor.
- **An optional distance is a new absence for every reader to handle**, including the assembler,
  the card, the reason line and the offer copy.
- **Half of this decision is written for a surface nobody can test.** Search does not exist, so
  the bound half is a commitment made in advance and unexercised until it is built.

**Neutral**

- The radius **default** matters more under this rule than it would under a bound, since it
  never removes anything and only tilts an order. Not fixed here.
- `anywhere` remains a real option and means exactly what it says: the term scores full marks
  and keeps its weight, the same as an undeclared limit.
