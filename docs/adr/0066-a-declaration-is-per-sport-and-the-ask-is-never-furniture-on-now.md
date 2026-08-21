# ADR-0066 — A declaration is one set per sport with two readers, and the ask for it is never furniture on Now

- **Status:** Accepted
- **Date:** 2026-08-21

> **Scope note.** [ADR-0084](0084-the-sport-bar-is-five-fixed-chips-and-an-unrated-sport-is-a-door.md)
> narrows this ADR in three places, none of them superseded. The caption's *"currently
> filtered sport"* gains its missing `All` case — silent, except where a sport the player
> holds a rating at has **nothing** declared. The onboarding tail
> `result → city → editor → opt-in → done` becomes `result → editor → back` for a sport
> **added after onboarding**, since city and the opt-in are answered once per player. And
> *"one card per declared sport, in sport-picker order"* is **not implementable as
> written** — the sports picker's selection is never persisted, so the only durable order
> is the one the ratings came to exist in.

## Context

[ADR-0063](0063-where-a-player-plays-is-declared-and-precision-follows-the-anchor.md)
established, in passing, that an **optional, skippable profile step** exists at the end of
onboarding holding eight declarations — play days · hours · matches per week · how far ahead
they will commit · distance anchor and travel radius · price per seat · competitive or social —
and promised **a completion card on Now with a progress ring**. Neither the step's screens nor
the card's behaviour were settled there, deliberately: a screen's furniture should not be
decided inside a decision about kilometres.

Six facts, gathered before any of it was designed, moved almost every premise.

- **v37 already draws this screen, and does not put it on Now.** `V.intentedit` — *"When I want
  to play"* — is **one scrolling form** in captioned sections, each caption stating what leaving
  the field blank does, with a ring in the header reading *n of 10 filled in*. `V.you` prepends
  the nudge **above the *Playing* section on You**. There is no completion card on Now anywhere
  in the prototype.
- **[ADR-0050](0050-now-below-the-strip-is-shelves.md) had already refused it**, one day earlier
  and against exactly this kind of addition: *"Nothing is added to fill the gap: no first-run
  shelf and no dismissible banner, because everything on Now is either a thing the player is in
  or a thing they could join, and a banner is neither."*
- **It is not one profile.** `S.intent` is an **array** and `profilePct()` **averages** across
  it, while root `CONTEXT.md` says *"One declaration, read by every engine that needs it."*
- **Ten fields, not eight — and three are answered before the step exists.** Sport (the
  compulsory picker), Level band (*"never typed, not by you, not by a club"*) and **Opt in to
  proposals** (its own screen, §7.3, *"skipping is not consent"*). On v37's arithmetic a player
  who has answered nothing is already at **30 %**.
- **`iComplete` · `profilePct` is marked *"Yes (contract)"*** in the v37 documentation's Part 13
  — shared with the club console's intent engine. The denominator is not a UI ornament.
- **ADR-0063's *answered-or-declined* rule cannot be implemented in the meter.** v37 counts
  `ceil: i.ceil != null`, and *"No limit"* **is** `null`. The honest answer is stored identically
  to never-asked, so the ring sits below 100 forever — the exact defect the rule was written to
  close, and it is a storage defect, not an arithmetic one.

A seventh fact arrived from `ACT.intentnew` and reframed the whole object: a v37 declaration
carries a **`clubs` array** and a **narrowed level band** (`[lv−0,25, lv+0,25]`) that ADR-0063
never listed, a player may create **several**, and Part V37's own header says what they are for —
*"what the intent pool needs from this app"*, the club console's engine. The eight fields are
identical to the Player profile's eight. So two things were wearing one name.

## Decision

**We will treat the eight declarations as one set per sport with two readers, and we will refuse
to put the ask for them on Now as furniture.**

### The object

- **One set of declarations, two readers.** Raketa's own ranking reads it unconditionally; the
  club console's intent pool reads it **only behind the opt-in**. Two objects would mean two
  screens on which a player states their hours, and a guaranteed drift between them.
- **The opt-in is therefore not a field at all — it is a permission on the second reader.** It
  keeps its own screen and its table of what changes either way, it is asked once, and it is
  **never metered and never nagged**. A progress ring that rises when you consent is a ring that
  pays you to consent.
- **One declaration per sport, in v1.** `CONTEXT.md`'s *"One declaration"* is **corrected**: a
  padel player's hours and price are not a tennis player's, and ADR-0050 filters every shelf by
  sport, so a single profile would be a claim about no sport in particular on a screen that is
  about exactly one. **Never averaged** — any percentage shown is one sport's.
- **The create-several shape and its two extras are the intent pool's, not this map's.** The
  `clubs` list and the narrowed band are **club-console surface** and are ruled out of scope
  here; the several-declarations-per-sport shape returns when that effort needs it.
- **Adding a sport creates its empty declaration.** Declarations exist for exactly the sports the
  player picked — no more, no fewer — so there is no sport without a declaration, only one at
  0 %.

### The meter

- **The denominator is the eight the step asks**, not v37's ten. Sport and Level band are not
  asks: one is compulsory elsewhere, the other is derived and never typed. A ring that opens at
  30 % is the same dishonesty as one that sticks at 87 %, pointed the other way — it claims
  credit for a sport picker.
- **A constraint term becomes three-valued: `undeclared | none | <value>`.** `none` and
  `undeclared` **score identically** — both *no limit*, full marks, weight kept in the
  denominator — and **count differently** in the meter. Without this, ADR-0063's
  *answered-or-declined* rule is unimplementable.
- **The distinction lives in the profile record only. The engine snapshot collapses both to *no
  limit*.** A distinction that reaches a component with no reason to read it is one that drifts,
  and the drift here reintroduces the **absence never flatters** invariant's failure. The
  collapse happens once, at the mapping.
- **All eight are declinable, and where blank currently means an *assumption*, the explicit
  decline replaces the assumption with nothing.** Five carry *no limit* semantics already — days,
  hours, price, radius, and the anchor's city-only third case. Three do not: appetite
  (*"assumed one"*), the commitment horizon (*"assumed a fortnight"*) and competitive-or-social
  (*"a weight, not a filter"*). *No preference* on appetite tells the ranking policy to **stop
  assuming one game a week**; it does not mean one game a week. This is
  [ADR-0064](0064-a-radius-orders-now-and-bounds-only-a-search.md)'s own principle — *an
  unmeasurable distance is missing evidence, not an absent limit* — applied to the other three,
  and it is what makes 100 % reachable for a player who genuinely has no view.
- **`profilePct` is dropped from the published contract; `iComplete` stays.** The average existed
  only to collapse the list into one number for a card no longer drawn that way. Part 13 names
  both, so the removal is recorded here rather than left to be discovered.

### The two surfaces

- **Nothing new is added to Now.** ADR-0050's line holds: a row that is neither a thing the
  player is in nor a thing they could join is furniture, and *"Your profile is 40 % complete"*
  never appears on Now at any percentage.
- **The *Best fit for you* shelf may carry a one-line caption** stating the basis of its own
  order — which [ADR-0051](0051-now-is-ordered-not-drawn.md) already requires every shelf to be
  able to do. It is not a banner and not a new row.
- **The caption is not driven by the percentage.** It fires only when one of the terms the
  ranking **actually reads** is undeclared — hours, price, radius-and-anchor, competitive or
  social — because those are the ones genuinely degrading the order in front of the player.
  Appetite and the horizon are the ranking policy's and no term reads them, so they never raise
  it. **A player who declined all four sees nothing on Now, forever, at whatever percentage.**
- **It reads the currently filtered sport's declaration.** Switching the sport bar to tennis is
  what surfaces that tennis was never filled in — the moment it starts mattering, and not
  before.
- **The caption is composed by the server, as shelf metadata alongside the title.** Its trigger
  is a rule, and [ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md) fixes that the
  phone holds none; ADR-0050 independently makes shelf presentation server-owned so it can change
  without a client release. Both point the same way. The client receives a shelf that either
  carries a caption or does not, and evaluates nothing.
- **The card on You is v37's, unchanged in behaviour: shown while below 100 %, not dismissible,
  gone at 100 %** — and **one card per declared sport**, in sport-picker order, so the majority
  who pick one sport see exactly what v37 draws. You is a surface the player chose to open, so a
  card there is inventory rather than a nag, and §7.4's *"no repeated prompting"* is satisfied by
  not putting it anywhere they did not ask to be.
- **The route into the editor does not depend on the card.** v37 prepends the card **above** a
  *Playing* section that is always present, so when the ring reaches 100 % and the card
  disappears, the way to change your hours survives beneath it. A card-only route would strand
  every finished player.

### The step

- **The step is the editor, entered from onboarding with a Skip** — one surface, built once,
  reached from two places. v37's `V.intentedit` is the UI authority for it and it is **a form,
  not a one-question-per-screen wizard**, with each section captioned by what leaving it blank
  does. A second parallel wizard would be two screens that must agree forever about eight fields.
- **The onboarding tail is `result → city → editor (skippable) → opt-in → done`.** Nothing here
  is built — the repo holds `welcome · sports · question · review · result · done`, with no city
  screen and no opt-in screen — so the order was free. City is first because the opt-in's own
  copy talks about clubs that can reach you, and that sentence is meaningless before a market is
  named ([ADR-0063](0063-where-a-player-plays-is-declared-and-precision-follows-the-anchor.md)).
  The opt-in keeps v37's position as the final screen and its copy — *"One last thing"* —
  unchanged, because that screen was written to be last. A skip on the editor jumps straight to
  the consent.

## Consequences

**Easier**

- **The `answered-or-declined` rule becomes implementable**, and 100 % is genuinely reachable by
  every player including one with no view on anything — which is what stops the meter teaching
  people to ignore it.
- **The ask is where its consequence is.** A player learns that Now is ordered by what they told
  us, on the screen whose order it changes, rather than in a percentage on a home screen.
- **The caption's four terms are re-tunable server-side.** When the fit engine's constraint terms
  change, the trigger follows without an app release.
- **ADR-0050 survives intact** rather than being amended three days after it was accepted by the
  first feature that found it inconvenient.
- **One editor, two entrances.** Onboarding and You cannot drift about what the eight fields are.

**Harder**

- **The three-valued term costs every constraint field a wider type**, in the record, in the
  onboarding payload and in the editor's state — for a distinction only the meter reads. It is
  cheapest now, before any real declaration exists, and it is unrecoverable once players have
  declared under a two-valued field: *never asked* and *no limit* cannot be told apart
  retroactively.
- **`profilePct` leaves a published contract.** Part 13 marked it shared, so anything on the club
  side that read the average must move to `iComplete` per declaration.
- **A MultiSport player's You grows a card per sport**, which is the honest rendering and is also
  more furniture on You than v37 had. The one-sport majority is unaffected.
- **The caption is a new server-composed shelf field** in a list-builder that ADR-0051 had
  finished specifying, and it is the first piece of shelf metadata that depends on the *viewer's
  profile* rather than on the matches.
- **We have overridden a UI authority's placement**, not just its arithmetic
  ([ADR-0036](0036-a-ui-document-is-final-on-the-screen-not-on-the-arithmetic.md)): v37 shows a
  single averaged card and we show one per sport. The override is narrow — the component and its
  behaviour are v37's — but it is an override.

**Neutral**

- **Nothing on Now's composition changes.** Offers block, strip, five shelves, exactly as
  ADR-0050 left it. The first run is still three shelves and a finished screen.
- **No line of `backend/app/engines/` changes.** The collapse to *no limit* happens in the
  mapping to the snapshot, and the constraint terms read what they always read.
