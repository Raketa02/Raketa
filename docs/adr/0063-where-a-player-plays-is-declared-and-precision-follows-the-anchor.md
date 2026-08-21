# ADR-0063 — Where a player plays is declared, never observed, and a distance is only as precise as the anchor

- **Status:** Accepted
- **Date:** 2026-08-21
- **Overrides:** `rakieta-now-section-ui-spec.md` §B18's rule *"Travel is expressed in
  minutes, not kilometres, on both cards"*, and its §G4 gap-table entry naming the header's
  source as *"profile + geolocation/home club"*. This is the first time this map overrides a
  **UI authority** on a value it states; the reason is below and it is deliberately narrow.
- **Discharges:** [ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md)'s
  open item *"the ladder needs a player location and there is none"*, for every player who
  gives an anchor.

## Context

Three separate things reached for a player's location and found nothing there: the header
eyebrow drawn as `Kraków · Saturday · 14:30`, the offer copy's *"20 min away"*, and rung 6 of
the invitation ladder — *nearby reliable players inside the level range* — which without a
source ships as *everyone in the band, anywhere*.

**Nobody has ever been asked anything about how they want to play.** Signing up today is: pick
your sports, answer the rating questions, read a privacy note, start playing. There is no
price ceiling, no days, no hours, no distance. A location question is not the fourth ask on an
existing profile step; it is the first, and it arrives alone.

**The scoring already holds a limit with nothing to measure it against.**
`PlayerProfile.travel_radius` is a declared number of minutes; `ClubSnapshot.travel_minutes` is
*"how long **this player** would travel to it, resolved by the assembler against wherever they
are"* — and there is no *wherever they are*. Every travel figure on screen today is a
prototype fixture (6–19 minutes), and every club in the fixture is in Kraków.

**The screen spec chose minutes with the kilometre figure sitting next to it.** Each prototype
club carries both, and `UI` §B18 states the choice as a rule. That was not an oversight, so
reversing it needs a reason the spec did not have.

**Two candidates were considered and refused.**

- **The phone.** It is precise about the wrong moment: at 08:00 on Monday it measures from a
  desk 8 km away to a Tuesday-evening match a player will drive to from home, 3 km away. It
  also costs the second permission dialog of an onboarding that already spends one on push.
- **The club they play at most.** Zero-cost, and wrong for a brand-new player — who is exactly
  the person rung 6 exists to reach — and wrong again for anybody who plays at two clubs on
  opposite sides of a city.

**Deriving a city from the device timezone was rejected earlier**: `Europe/Warsaw` is not a
city a player told us about.

## Decision

**We will ask a player where they play, in their own words, and never observe it.**

### Two facts, not one

A place a player **belongs to** and a place we **measure from** are different facts with
different jobs, different audiences and different precision. They stop competing to be one
field.

| | Asked | Precision | Seen by others | Job |
|---|---|---|---|---|
| **City** (with country) | Compulsory, on its own screen, before Now first opens | A market | **Yes** | Filters what the app shows; printed in the header eyebrow |
| **Area or postcode** | Optional, inside the optional profile step | A district, or a few streets | **Never** | The only thing a distance is ever measured from |

**The city is not a preference and is not skippable.** It is which market the player is in —
structurally the same question as the sports picker, which is also unskippable — and the feed
cannot be composed without it. It is therefore asked **outside** the optional profile step.

**It is a field from the first day, never a constant.** Hard-coding Kraków while it is the only
market would let every downstream reader assume there is only one, which is the assumption
this product most needs not to bake in: a player who has *moved* to Kraków for two months is
the case the city switch exists for.

**Switching city is a later feature.** The field is shaped for it now so that nothing has to be
migrated when it arrives.

### The origin is declared, never observed

**No location permission is asked, ever, for this.** The phone is not the source of record.

The reason is not privacy — it is that the two questions have different answers. An observation
tells us where a player *is*; the declaration tells us **where they play from**, which is what
every consumer of this actually wanted. A statement of intent cannot be wrong at 08:00 on a
Monday.

A *"use my current location"* button may later fill the field in. It fills a declaration; it
never becomes one, and what is stored afterwards is still the player's answer.

**Search gets its own location field when Search is built.** The profile's anchor is the
default, not the only one — a player looking for a game near their parents' house is asking a
different question from the one their profile answers.

### Kilometres, everywhere, permanently

A radius is declared as **3 / 5 / 10 / 25 km / anywhere**. The card reads `{club} · ~{n} km`,
the lock screen reads *"A padel seat is free — Tue 19:00, about 4 km away."* The scoring
compares kilometres against kilometres.

**Why this overrides `UI` §B18.** That rule was written for a product that had a travel
*time*. With a declared, coarse origin and no routing integration, a figure in minutes is a
guess wearing a measurement's clothes — and the one thing the whole spec is built on is that
what the card says is true. The override is to that single value and to nothing else in the
document.

**The glossary's objection does not apply.** `CONTEXT.md` forbade a radius in kilometres
compared against a club in minutes, *"because that would mean inventing a speed"*. The
prohibition is on the **mixture**. Both sides in kilometres invents nothing, so this is a case
the rule never covered rather than a rule being broken.

**The declaration stays in kilometres even after routing exists.** A standing statement a
player made once is not re-asked because our tooling improved, and converting *"5 km"* into
minutes on their behalf is exactly the invented speed the glossary was guarding against. When
travel times become real, minutes arrive as something the card may **also** show.

**What this costs, stated plainly.** A player chooses on time, not on distance. Five kilometres
across the river with one bridge is twenty-five minutes; nine kilometres down a tram line is
fourteen. A kilometre figure never lies and can still send somebody to the wrong match. We are
choosing honesty because we cannot yet deliver the thing they care about — not because
kilometres are better. The trigger to revisit is a routing integration, and nothing else.

### Precision follows the anchor

- **City only → no distance anywhere.** No figure on the card, and **no travel clause on the
  lock screen** — *"A padel seat is free — Tue 19:00"* and nothing more.
- **Area or postcode → rounded to the kilometre and marked approximate** — `~4 km`, *"about
  4 km away"*. **Never a decimal.** A district is around three kilometres across, so `4.2 km`
  claims an accuracy the anchor cannot support; the imprecision belongs in the presentation
  rather than hidden behind it.

**City-only is the majority state at launch**, because the profile step is skippable and most
people skip.

### What another player sees

**City and country only.** The area and the postcode are never shown to another player; the
postcode is roughly street-level and is the most precise thing this product stores about where
somebody lives.

**Nothing spends this permission yet.** The only surface on Now that shows another player is the
*New on Raketa* shelf — a face, a name, a Level — and it does **not** change. In a one-city
product the same city line would sit under every face, which is decoration that teaches people
to stop reading the card. The rule is recorded now because a privacy commitment is cheap to
make and expensive to change; the surface that exercises it is the profile screen, which
[ADR-0050](0050-now-below-the-strip-is-shelves.md)'s effort ruled out of this map.

## Consequences

**Easier**

- **Rung 6 gets its source.** *Nearby* becomes an ordering over a declared anchor rather than a
  clause with nothing behind it, for every player who gave one.
- **The header eyebrow stops being hardcoded** and becomes a fact about the player — and the
  same fact that quietly steers which seats they hear about, which is worth showing back to
  them.
- **Onboarding keeps exactly one permission dialog.** The push explanation
  ([ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md)) stays the only one.
- **`matchFit`'s travel term gets a real input** and the 6–19 minute fixture retires.
- **One field, three granularities.** A player who wants better matching can give a postcode
  without everybody being asked for one.

**Harder**

- **A UI authority is overridden on a value it states — the first time on this map.** The rule
  that `rakieta-now-section-ui-spec.md` is final has an exception now, and the exception's
  shape matters: the value was chosen under an assumption (that a real travel time would be
  available) that does not hold. Anyone reading `UI` §B18 in future will find it correct about
  its own reasoning and wrong about ours.
- **Four shipped places change unit.** `PlayerProfile.travel_radius`,
  `ClubSnapshot.travel_minutes`, `TravelFact`, and `Constants.travel_decay_span` (20 minutes
  becomes a span in kilometres). None is difficult; all of them are cheaper now than after the
  scoring is wired to real data.
- **Clubs must carry a location.** Kilometres cannot be computed without coordinates on a club,
  and Clubs and Courts are still unmodelled. This places a requirement on a context this map
  does not own.
- **Most players see no distance at all.** The lock screen's travel clause is the thing standing
  in for the venue name, and it is absent for everyone who skipped the step.
- **A declared origin goes stale silently.** Somebody who moves house and does not update it
  gets quietly worse ordering, and there is nothing for them to notice.

**Neutral**

- Switching city, and a search-time location field, are both later features. Both are shaped
  for now so neither needs a migration.
- A player who declares a city they do not live in gets exactly what they asked for. That is
  the point of a declaration, not a defect in it.
