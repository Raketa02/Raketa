# ADR-0134 — The generated poster draws a player, and every value it varies comes from a designed set

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

A player with no photograph is not left with an empty box: they get a **generated court
poster**, derived from their identity so it is stable across devices
([`CONTEXT.md`](../../CONTEXT.md)). It exists today as
`frontend_player/src/shared/ui/CourtPoster.tsx` and design-system
[§6.9](../../frontend_player/docs/design-system.md#69-the-photo-tile-and-picker), and it
draws a singles court seen from above — outer lines, net, service lines, centre line, one
ball — in three colours, cropped by a hash of the player id.

The Play tab's UI specification draws a different poster: a coloured gradient derived from
the player's identity, a floor glow, a glass wall, mullions, a light streak, a ball — and
**a human figure**, one of three poses (forehand, serve, lunge), chosen by the same hash.

The two documents do not merely differ. **The incumbent refuses both new things, in
writing, for two different reasons**, and only one of the two documents can be this
repository's:

> **It is never a person.** No face, no silhouette, no initials. A poster that gestured at a
> human is one somebody mistakes for a photograph, in the single place a photograph answers
> a question a drawing cannot — *do I want to play this person?*

> **It varies in geometry and never in colour.** […] there is no prop that changes one.
> Every colour in the system already means something, so a hue chosen by a hash would be
> assigning meaning to a hash — and the four sport colours would have a poster claim a sport
> its player may not play.

### What has changed since those sentences were written

**The deck is a stack of posters.** Play's `deck` screen shows one candidate at a time as
360 × 210 of media, and the pool shows 360 × 150. The seeded development cohort carries no
photographs at all, so in development *every* card draws a poster — the exact surface the
first refusal is about. That cuts both ways, and the second cut is the one nobody had made:
a deck of forty-eight crops of one court, in the same three colours, is a deck where every
card is the same picture. `courtPosterFraming.ts` already concedes the point about its own
mechanism — *"two crops of the same size at different offsets look like one drawing that
slid, which is a weaker difference than it sounds"* — and answered it by multiplying eight
windows by six ball positions. Colour is the difference geometry was standing in for.

**The 27pt case was never solved, only asserted.** §6.9's claim is that one drawing serves a
90pt tile and a 27pt avatar. At 27pt a crop of a court is four hairlines; it is legible and
it carries no identity whatever. Whatever the small poster is for, the crop is not doing it.

**The product now draws a visible line around photographs.**
[ADR-0129](0129-the-photo-check-is-a-sidecar-the-backend-asks.md) put a checker on the
upload path and [ADR-0133](0133-the-verdict-crosses-on-the-upload-and-the-warning-may-be-wrong.md)
made its verdict cross the wire and show a warning. A photograph is now a thing the platform
has looked at and has an opinion about. A poster is on the other side of that line by
construction, and the line is visible.

**The accessibility contract already carries the risk the first refusal names.**
`CourtPosterProps.accessibilityLabel` is required, has no default, and *"must say the
picture is generated"* — a mechanism that does not depend on what the drawing contains.

### What the first refusal was actually protecting

Its operative sentence is not *no human shape*. It is *the poster must not appear to answer*
***do I want to play this person?*** That is right, and it survives this record untouched.
What does not survive is the belief that a silhouette answers it. A **face** answers it. A
flat, single-value, unfaced pictogram — the figure on a squash-court door — is not mistaken
for a photograph by anyone, and the specification that proposes it says so in its own
parameters: filled and stroked in one dark value, at one opacity, with no facial feature.

### What the second refusal was actually protecting

Design-system [1.3](../../frontend_player/docs/design-system.md#13-semantic-colour-is-never-decorative)
— *semantic colour is never decorative* — and
[2.3](../../frontend_player/docs/design-system.md#23-sport-identity)'s sport aliasing, which
[#219](https://github.com/Raketa02/Raketa/issues/219) has just **upheld** on a premise it
checked rather than asserted: a sport hue never appears without the sport's name in text.
A poster hue taken as `hash % 360` breaks that premise on the one surface where it was
checked — a coral-grounded poster on a card whose own sport tag says Tennis. It also makes
white text over the poster uncomputable, which is UI §E5's third finding and the thing #219
fixed for the court by pinning its scrim at `.93`. Both are real. Neither is an argument
against colour; they are arguments against **a hash inventing a value**.

The framings never invented anything. Eight windows, designed and enumerated, and the hash
picks one. That is the discipline the hue was missing.

## Decision

We will adopt the UI specification's poster — **the figure and the colour** — under
constraints that keep both refusals' actual protections intact, and we will re-draw the
line where the original arguments were pointing rather than where their sentences fell.

**1 — The poster draws a player, and never a likeness.** One of three poses — forehand,
serve, lunge — as a **flat silhouette in a single value**, `ink`, with no second value, no
gradient on the figure, no skin tone, no hair, **no face and no facial feature of any
kind**. That constraint *is* the new line: the moment the figure gains a face, a second
value or a likeness, it is a picture of a person again and this record does not cover it.
The figure holds a racket, which is the one prop true of every player on this platform, and
carries nothing that names a sport.

**2 — The pose is not a fact, and nothing may read it as one.** It is chosen by a hash: a
player whose pose is *serve* is not a server, and the handedness a pose appears to show is
not theirs. A poster is shown and never read — the same standing a social tag has under
[ADR-0115](0115-a-tag-about-the-person-may-be-shown-never-scored.md). No engine, no term and
no gate may take an input from it.

**3 — The hash does not choose a hue. It chooses from `POSTER_HUES`** — a closed set of
**sixteen designed hues at one fixed saturation-and-lightness pair**, published in
`theme.ts` under its own name and **not inside `color`**, because it is not a semantic
colour and must not be reachable where one is expected. Each hue is at least **25° from
`red`, `coral`, `mint`, `amber`, `volt` and every `sport` value**, and at least **10° from
every other poster hue**.

This dissolves both halves of the second refusal rather than overruling either: a poster hue
is not *in* the palette, so 1.3 is untouched; and no poster can claim a sport, by
construction rather than by hope.

The constraint is satisfiable, and was checked rather than assumed. The named hues sit at
6° (`red`), 9° (`coral`, `sport.padel`), 40° (`amber`, `sport.badminton`), 69° (`volt`),
163° (`mint`, `sport.tennis`) and 195° (`night2`, `sport.squash`, `info`). At ±25° they
exclude two arcs — 341°→94° and 138°→220° — leaving **44° and 121° usable, 165° in all**,
which holds sixteen hues at 10° spacing with room over.

**4 — The gradient ramps saturation and lightness on one hue, and does not shift hue.** This
is the one parameter of §A5.3 we do not adopt. A 40°-warmer light stop makes a poster occupy
a 40° *arc*, so the bound in (3) would have to hold at both ends and the usable space
collapses; and a two-hue ground is a second value to compute contrast against for no gain a
reader would name. One hue, two stops.

**5 — Fixed saturation and lightness is what makes the poster computable, and two
requirements bind it from opposite sides.** White text drawn on the poster — the level, the
sport label, the shield — needs **4.5:1 against the lightest stop**, with the `textOnMedia`
shadow #219 created. The `ink` figure is a graphical object and not text, so 4.5:1 does not
apply to it; it needs **3:1 against the darkest stop**. §6.9 publishes the stop pair that
clears both, and §2.5 tables the resulting ratios. **A hue that cannot satisfy both is
dropped, and the set is sixteen after that dropping, not before.** If sixteen do not survive
inside the usable arcs, that is a finding that reopens this record rather than a number to
quietly lower.

**6 — The crops are retired.** The composition is fixed and whole; a window onto it would
slice the figure. `CourtPosterFraming`, `COURT_POSTER_FRAMINGS` and the eight-by-six set go,
and `courtPosterFor(playerId)` returns the hue and the pose instead of a view and a ball.
`COURT_POSTER_COUNT` stays a tested constant and **must not fall below its present 48** —
sixteen hues by three poses is exactly 48.

What survives from the incumbent, verbatim and deliberately: **nothing here has a size**;
viewBox units, `preserveAspectRatio="xMidYMid slice"`; one accessible node carrying one
label; the label required with no default and saying the picture is generated; and
**determinism is the feature's, not the theme's**.

**7 — One id, one poster, forever, and nothing is stored.** §A5.3's *stored identity hue*
and *stored pose index* are refused. `courtPosterFraming.ts`'s existing argument is upheld
and extended to the two new dimensions: *"a stored choice is a choice that can be lost, and
a player whose poster changed would reasonably think their profile had."* The hue and the
pose are taken from **different parts of the hash**, for the reason that file already
records — dividing one number twice by two small sets ties the choices together and cuts the
count.

**The player card already carries the player id, so this record changes no contract.**
`openapi.player.json` is untouched, no field is added to the profile surface, and nothing is
backfilled. That is a consequence of (7), not a coincidence.

**8 — A gradient's `<Defs>` id is a per-instance value, and is never derived from data.**
The poster's id comes from React's `useId()` (React 18.3.1). UI §G6 bug #3 records the
prototype composing it from the player id and the width, so the pool — which draws the same
person in a candidate card and in the header court — emits duplicates. Composing it from the
id, the width *and* the height is the same bug one screen further out. The rule is the fix.

**9 — A poster is never checked.** It carries no `review` verdict, never enters the photo
port ([ADR-0091](0091-photo-storage-behind-a-port.md)) and is never submitted to the checker
([ADR-0129](0129-the-photo-check-is-a-sidecar-the-backend-asks.md),
[ADR-0133](0133-the-verdict-crosses-on-the-upload-and-the-warning-may-be-wrong.md)). There
is nothing to check: it is not a photograph of anybody, and a warning drawn on it would be
the app doubting its own drawing.

### Standing of ADR-0012

**[ADR-0012](0012-player-app-design-system.md) is neither superseded nor amended, and that
is not a formality.** §6.9 does not exist in its text: the section was added by a Part 16
amendment row on 2026-08-25, thirteen days after ADR-0012 was accepted. ADR-0012 locked the
system and supplied Part 15 and Part 16 as the mechanism for changing it; this record is
that mechanism being used at the threshold Part 15 sets — an ADR is required precisely where
a change **overturns a stated argument**, which is the line #219 also drew and did not
reach. Nothing ADR-0012 argued for is reversed here.

Everything below lands as `design-system.md` Part 16 rows with `theme.ts` changed in the
same commit, per Part 15.3.

## Consequences

**Easier**

- Two players' posters differ in **colour**, which is the only difference that survives a
  27pt avatar. The small poster gains an identity it has never had; the deck stops being
  forty-eight renderings of one picture.
- Text over the poster becomes **sixteen computable ratios** instead of an unbounded set —
  the same conversion #219 made for the court by pinning its scrim. The poster is the second
  generated fill in the system and the first with a foreground requirement of its own.
- No contract change, no migration, no profile field, no backfill. The client already has
  the player id, and a pure function of it is the whole input.
- The gradient-id defect is closed by a rule that cannot be re-derived wrongly, rather than
  by a naming convention that is correct until the next caller.
- §2.3's sport-alias premise — *a sport hue never appears without its name in text* —
  survives Play intact, having been the thing this decision was shaped around rather than
  the thing it broke.

**Harder**

- **§6.9 has to do real work before it can publish.** Sixteen hues must be designed inside
  two arcs, at one saturation-and-lightness pair, and each must clear 4.5:1 for white and
  3:1 for `ink` at opposite ends of its own gradient. That is a genuine constraint-satisfaction
  problem and it may not have sixteen solutions.
- **Ten degrees is a weak separation.** Two players can land on adjacent poster hues and read
  as nearly the same colour. The pose multiplies them back to 48 combinations, but the
  colour difference alone is not always a strong one.
- **Three vector poses have to be drawn**, and drawn to a constraint — flat, one value, no
  face, a racket, no sport-specific gear — that no existing asset in this repo meets. The UI
  spec's own handover note says the pose paths are *"best copied across verbatim"*; they
  cannot be, because the constraint in (1) is this record's and not the prototype's.
- **`§6.9`'s headline claim gets narrower.** One drawing still serves every size, but what it
  carries at 27pt is a colour and a smudge. Anyone reading *"enough for the shape to be
  recognised at 27pt"* about the court will find that sentence no longer the point.
- **`CourtPoster` gains a colour prop, and §6.9 gains a fill rule** — the first place in this
  design system where a component takes a colour it did not get from `theme.color`. It is
  bounded (a member of `POSTER_HUES`, by type) and it is still a token, but the shape of the
  rule *"a literal hex in a component is a bug"* now has a named exception to explain.
- **The figure will be over-read.** Somebody will ask which pose means what, and the answer
  is *nothing* (2). That is a support answer and a copy answer, not a code one.

**Neutral**

- [`CONTEXT.md`](../../CONTEXT.md) is unchanged. *A generated court poster, derived from
  their identity so it is stable across devices* is still exactly true — it is still a court,
  and the derivation is still the point. The change is presentational and the glossary is
  not where presentation lives.
- The volt ball of §A5.3 is adopted and the incumbent's `onDarkTiny` ball goes. It survives
  **because** volt is excluded from `POSTER_HUES` by (3): the one mark on the poster is the
  one hue a poster can never be.
- The eight framings and six ball positions are deleted rather than kept for a smaller
  variant. Their argument — that geometry alone is a weak difference — is the argument this
  record is built on, and keeping the mechanism that made it would be keeping the evidence
  for the case against it.
