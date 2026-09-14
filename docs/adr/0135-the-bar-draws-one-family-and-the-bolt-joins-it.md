# ADR-0135 — The tab bar draws one family, and the bolt joins it

- **Status:** Accepted — ***`map-pin` for Around* superseded 2026-09-14 by [ADR-0169](0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)** §1: the
  tab is **Players** and draws `users`. One family, and `radar` still not drawn, stand.
- **Date:** 2026-08-29
- **Closes:** [ADR-0012](0012-player-app-design-system.md)'s one deliberately-open item — *"The glyph set for tab icons is deliberately still open. The system specifies the 16pt box and the position; `@expo/vector-icons` ships with Expo and is the likely answer, but choosing it is a separate decision"*
- **Answers:** [#238](https://github.com/Raketa02/Raketa/issues/238) — *Five glyphs, and the set they come from*, on [#217](https://github.com/Raketa02/Raketa/issues/217)
- **Builds on:** [#227](https://github.com/Raketa02/Raketa/issues/227) (the five-tab shell), [#219](https://github.com/Raketa02/Raketa/issues/219) (the 9.5 type floor), [#221](https://github.com/Raketa02/Raketa/issues/221) (a chat opens on the first acceptance)
- **Evidence:** branch [`prototype/play-tab-glyphs`](https://github.com/Raketa02/Raketa/tree/prototype/play-tab-glyphs) — three families × three glyph slates × four treatments of the bolt × two state channels, drawn in #227's own bar over its own back stack, and looked at

## Context

`design-system.md` §10.2 draws the five tab icons as 16pt `currentColor` squares and says
why: *"an honest placeholder that specifies shape and position but not glyph … picking the
glyph set is a separate, recorded decision."* Part 16 row 6 holds the same line. ADR-0012
declined to choose and left the question named, with `@expo/vector-icons` attached to it as
the likely answer.

**A square that was honest over an unbuilt bar is not honest in the app's real bottom
chrome.** [#227](https://github.com/Raketa02/Raketa/issues/227) built the bar — five
columns `Now · Around · ⚡Play · Chats · You`, §10.2's geometry, `tag` labels, a 30pt
`coralInk` disc with a 2pt `coral` ring when Play is active — so the decision is now due.

### This was decided once, and the record was deleted

ADR-0082 (2026-08-22, merged as [#58](https://github.com/Raketa02/Raketa/pull/58)) chose
Feather and five glyphs, and was removed by the 2026-08-25 reset along with **0030–0088**.
Its numbers are not reusable and the index's own rule governs: *anything rebuilt gets a
fresh ADR at the next free number, argued from the code that exists then.* Its prototype
survives on [`prototype/tabbar-glyphs`](https://github.com/Raketa02/Raketa/tree/prototype/tabbar-glyphs)
and its text on [`docs/adr-0082-tab-bar-glyphs`](https://github.com/Raketa02/Raketa/tree/docs/adr-0082-tab-bar-glyphs).

**It is precedent to argue with, not an answer to copy, because three of its premises are
gone:**

1. **The five acts are different.** It named `Now · Find · Create · Inbox · You`. Two of
   those tabs have since changed what they *are* — `Around` is proximity rather than a
   query, and `Chats` is a conversation that opens on the first acceptance
   ([#221](https://github.com/Raketa02/Raketa/issues/221)) rather than a mailbox that
   receives.
2. **The centre is no longer a create button.** 0082 explicitly *declined to raise the
   control out of the bar*; #227 raised it, and made it both an action and a destination.
3. **The selected tone changed, and that dissolves 0082's one accepted failure.** It
   carried selection in `coral` against `muted` — **1.39:1**, two colours within a hair of
   the same lightness — and knowingly accepted a WCAG **1.4.1** failure on the app's
   primary navigation, recording a 3pt coral dot as the pre-costed remedy. #227's bar
   carries `ink` against `muted`: **3.25:1**, and a *lightness* difference rather than a
   hue one, so it survives greyscale and a red-green deficiency. **The failure is not
   fixed here; it never arises.** The remedy is not inherited either.

### What was built

Three families and the shipping squares, each with three complete four-glyph slates,
switchable live in the real bar with the real back stack, real insets and real `theme.ts`.
The slates disagree about the only two tabs whose glyph is genuinely open: whether **Now**
is a place, a calendar or a clock, and whether **Around** is a point, a direction or a
sweep. A fourth axis varied the bolt and a fifth varied whether selection changes the
glyph's shape or only its tone.

Every glyph name is typed against its own family's `glyphMap`, so a name absent from
`@expo/vector-icons@14.0.4` is a compile error rather than a blank column nobody notices at
16pt. All 27 resolve. *(Three of them — the bolts — sat behind a cast and were unchecked
for two commits, which is exactly how a verdict gets given on a glyph that does not
exist.)*

## Decision

**We will draw the tab bar with Feather from `@expo/vector-icons`, at §10.2's 16pt box, and
the ⚡ becomes a member of that family rather than a text glyph.**

### The five

| Tab | Glyph | Box |
|---|---|---|
| `now` | `home` | 16pt |
| `around` | `map-pin` | 16pt |
| `play` | `zap` | 15pt, white, inside the 30pt disc |
| `chats` | `message-circle` | 16pt |
| `you` | `user` | 16pt |

**The family is fixed and the inventory is these five.** A sixth glyph on a sixth surface is
a fresh question that inherits the family and nothing else — never a licence to sprinkle.
The removed record made the same reservation, and it is worth making twice.

### Feather, and the limitation that costs nothing here

Feather is a **font with one weight and no filled counterparts** — no `strokeWidth`, no fill,
no optical size. That is a real limitation, and on 0082's bar it was the binding one: with no
second shape available, selection could only be colour, which is how that record ended up
accepting a 1.4.1 failure.

**On #227's bar it costs nothing**, because the state channel is already a lightness
difference that does not depend on hue. Ionicons and MaterialCommunity both offer
outline/filled pairs, and both would therefore put a **second state channel on top of a
sufficient one** — which is the thing #227 already refused once in writing, for the disc:
*the ring carries the state, not the shadow.* A bar whose glyph and whose tone both announce
selection is two things saying one thing, and the second is free to disagree.

So the family's single weakness is not exercised, and its strength — one weight, one
geometry, no per-glyph decisions left to make — is what a five-column bar wants.

### The place read, over the calendar and the clock

**`home` for Now, and `map-pin` for Around.**

Now's competing slates drew a calendar and a clock. Both **over-promise**: #227 fixed Now's
own placeholder as *"What is happening today and next — not built yet"*, and a calendar
glyph on a tab with no plans, no bookings and no courts announces a scheduling surface that
[#217](https://github.com/Raketa02/Raketa/issues/217) has explicitly ruled out of scope.
`home` claims nothing that is not built, and Now is where a sent challenge lands.

Around drew a compass, a globe and — in MaterialCommunity, which is the only family that has
it — `radar`. `radar` is the most specific glyph available anywhere and that is the argument
against it: it draws an **active scan**, on a tab that is a placeholder. `map-pin` says
*near here* and stops.

### The bolt joins the family, and stops being a text glyph

**Feather `zap`, 15pt, white, inside the disc, and still hidden from the reader** — §E6's
*"the FAB's visible 'Play' label already suffices"* is unchanged, and #236 already routed
what the control announces.

One family means one family, and ⚡ was the only mark in the bar not drawn from a set. But
the stronger reason is structural rather than aesthetic: **U+26A1 carries
`Emoji_Presentation=Yes`**, so a bare `<Text>⚡</Text>` requests *colour emoji* presentation,
and a `color` style then has nothing to apply to. The mark's colour stops being the design
system's to decide. §6.1 `primary` requires a **white** mark on the `coralInk` disc, and
#227's whole disc argument rests on that white — so the one glyph in the bar that is not
from a family is also the one whose colour the app does not control.

Feather `zap` is a font icon: `color` is a real prop, and white is white.

> **Stated as prediction, not observation.** The Unicode property is a fact; what iOS and
> Android actually drew was not checked by the author of this record.
> **`research/tab-shell` almost certainly carries this defect** — it draws a bare `⚡` under
> `color: theme.color.surface` — and the build ticket should expect #227's "white mark" to
> be unachieved on that branch rather than assume it renders.

### Selection changes tone, and never shape

`ink` selected, `muted` resting, exactly as #227's bar draws it. The glyph is the same glyph
in both states. This is the same rule as the ring and the disc: **one channel per state**,
and the channel that already works is the one that carries it.

### The dependency gets declared

**`@expo/vector-icons` is added to `frontend_player/package.json`** at the version Expo
resolves for SDK 52 (`14.0.4`), via `npx expo install`.

It is present today only as a **transitive** dependency of `expo` — in `pnpm-lock.yaml`, with
no line in the manifest. The removed record found the same thing and called it *"costs
nothing … we are not paying for what we already have,"* and stopped there. That is true about
the install and false about the risk: after this ADR the app's **primary navigation** renders
through a package the app does not declare, which an SDK bump can move or drop with no signal
in this app's own manifest. The remedy is one line and Expo's own documented practice. Taking
it is the difference between a dependency we have and a dependency we rely on.

### What this hands the build

Not written by this map — [#217](https://github.com/Raketa02/Raketa/issues/217) plans and does
not build, and #227 routed its own design-system edits the same way:

| File | Change |
|---|---|
| `design-system.md` §10.2 | The family, the five glyph names, and `zap` at 15pt in the disc. The 16pt box and every other value are unchanged. |
| `design-system.md` Part 16 | **Row 6 retires** — the placeholder it records is answered. Its replacement states the family and cites this ADR. |
| `package.json` | `@expo/vector-icons` declared, via `npx expo install`. |
| `theme.ts` | **Nothing.** `size.tabIcon: 16` needed no change; Feather scales to it. |

## Consequences

**Easier**

- **A build session can render the bar with nothing left to choose** — family, five names,
  both box sizes, the mark's colour, and the state channel are all fixed, and every one of
  them resolves against a package that is already installed.
- **No commissioned icon set**: no SVG pipeline for this surface, no asset licence, no
  designer in the loop. `react-native-svg` is a direct dependency and a drawn set was on the
  table and built; it lost on being a maintenance surface the app has no second use for, not
  on being unaffordable. That is a better reason than 0082 had.
- The one accessibility exposure the deleted record accepted **does not exist here**, and no
  remedy is owed.

**Harder**

- **Feather forecloses tuning.** §A5.2 recommended a 1.75/24 stroke; Feather draws 2/24 and
  it is not adjustable. A future surface genuinely needing a filled or heavier glyph needs a
  second family or a drawn one, and **this ADR authorises neither** — it would have to argue
  with the one-family finding above.
- **Selection now depends on `ink` and `muted` staying apart in lightness.** They are 3.25:1.
  Anyone re-tuning either token is re-tuning the tab bar's only state channel, and nothing
  mechanical says so. This is the same class of coupling 0082 recorded, at a safer distance.
- **The bolt claim is unverified on device.** The Unicode property is certain; the rendering
  is inferred from it. If both platforms happen to draw U+26A1 monochrome under an explicit
  `color`, the structural argument for `zap` still stands but its sharpest evidence does not.

**Neutral**

- Ionicons and MaterialCommunity stay on the prototype branch, with working outline/filled
  selection. If the tone-only channel ever proves insufficient in use, **switching family is
  the other way to fix it**, and the branch holds a running version of both.
- `radar` exists in MaterialCommunity and in neither other family. If Around ever becomes an
  active scan rather than a placeholder, the glyph question reopens as a family question.
- The family chosen here is the family the deleted record chose, and **two of the five glyphs
  moved — exactly the two acts that moved.** That the answer converged from different
  premises is worth recording: it is a re-derivation, not a copy.
