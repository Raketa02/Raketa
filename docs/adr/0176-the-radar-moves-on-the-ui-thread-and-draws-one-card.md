# ADR-0176 — The radar moves on the UI thread, and draws one card at a time

- **Status:** Accepted — **§2's *the rubber band at the reach's edge* narrowed 2026-09-17 by
  ADR-0177 §1** to the
  drag: the pinch is held at the edge, and the drag is anchored on the recogniser's
  translation rather than the fingers' position. **§2's *one transform carrying the lot, every
  tile counter-scaled* replaced 2026-09-17** (§2, amended): every tile places itself on the UI
  thread from the same three values, and nothing is scaled — an iPhone simulator at the floor
  showed every tile as a blur of a few pixels. Everything else stands.
- **Date:** 2026-09-16
- **Supersedes, by named sentence:**
  - [ADR-0174](0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md) §7's *"**Built
    with** raw touches and the native driver, SVG for the rings; no gesture or animation
    library. If a device shows stutter, that is its own decision"* — two devices showed more
    than stutter, and this is that decision (§2). Its *"at 5,4 and below, the card"* and *"A
    selected player keeps their card when the view zooms back out"* — **the card is the
    selection's alone, at every width** (§3). Its *"land at the 3 km stop"* — **or at the
    width already held, where that is narrower** (§3).
  - `the-radar.md` §7.3's third state, §7.4's *"Nearer
    players are drawn above farther ones"* read as a rule about cards, §7.5's flight width, and
    the whole of §7.9. The spec is amended in place, and the amendments cite this record.
  - The locked mocks **3, 9 and 10**, where they draw several cards at once. ADR-0174 locked the
    mocks with *"where a mock and a record disagree, the record is amended"*; here the mock is
    what a device disproved, and the author's own ruling on the device is what amends it. The
    card itself — mocks 10–14, line for line — stands.
- **Narrows** ADR-0165
  §6's *"with neither `react-native-gesture-handler` nor `reanimated` added"* to **the swipe
  row, the deck's drag and the radius slider stay on `PanResponder`**; the two libraries are in
  the app now, for one surface, and the argument for keeping the others where they are is
  restated in §2. Narrows the client's architecture record's *"a feature never adds a global
  provider"* by one root view that is the touch system's and not a feature's (§2).
- **Leaves standing** everything else ADR-0174 decided: the reading, the drawn spot, the five
  gates, the two windows, the chip, the cold-start location, the ladder, the rings, the footer,
  the sheet's foot. Nothing on the wire changes. **A client change only.**
- Grilled 2026-09-16 at the repo root, from two devices — an iPhone simulator and an Android
  phone — and one screenshot each.

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** The radar's field is gone, and §3 and §4 with it. §2's adoption stands without the radar: `react-native-gesture-handler` and `react-native-reanimated` stay — the week grid, the undo toast, a group's sport filter and the record's details use them — `GestureHandlerRootView` stays outermost in the root layout, and the router harness still runs real reanimated. Of the three surfaces §2 kept on `PanResponder`, only the deck's drag is still drawn, as the Games deck's `DeckStage`; the swipe row and the radius slider have no caller.

## Context

The radar landed on 2026-09-16 unseen on a device, as its record said, and ADR-0174 §7 ended
with a sentence written for this day: *if a device shows stutter, that is its own decision*.
The first look, on two devices, found five things, and only one of them was stutter.

**On the iPhone every face grew with the pinch.** At 30 km across a 24 pt face was drawn at
about 45; at 10 km across, at 150 — the screenshots are unambiguous. The field lays every tile
out once and carries the lot on one scaled transform, and each tile counter-scales about a
**0 × 0 anchor** at its point so it stays 24 or 30 pt. The counter-scale never reached the
screen. The cause is in React Native itself, verified in the source the app builds against:
`BaseViewProps::resolveTransform` returns the **identity for any view whose width and height
are both zero**, on the new architecture, on iOS. Android's view manager has no such rule, which
is why the Android phone drew every face at its size.

**On the Android phone a drag came apart** — the small squares moved and the field did not
move with them as one thing. The field kept a `live` view in React state beside its three
native-driven values and wrote it on **every frame** of a gesture, so the whole field
re-rendered per frame; and a re-render of an `Animated.View` swaps its animated-props node,
which restores the old node's transform to the identity and re-pushes the new one on the
*next* frame. On iOS the two land in one pass; on Android they do not, and a drag is a
transform reset sixty times a second.

**Neither is fixable inside the design.** The design was *the JavaScript thread narrates a
transform the native driver animates*: three `Animated.Value`s set per frame from a
`PanResponder`, a shared `Animated.divide(1, scale)` on every anchor, a state write per frame
for the rings and the words. Every one of those is a frame of work on the JavaScript thread
racing the finger, and the two platform faults are two of its seams. A one-point anchor would
mend the iOS fault; nothing mends the per-frame re-render but not doing it.

**Cards at 5,4 km were a field nobody could use.** The mocks draw the closest width as a
field of cards — one per player, ~190 pt each, top-left at the spot — and on a device with the
seed's population the cards lay on one another and no tap reached the one wanted. The author
ruled, on the device: *the card should be visible only by tapping the player, and one at a
time*.

**The population is the seed's, not the radar's.** The fifth finding — everybody drawn in a
few clumps due north — is the seed: every member of a distance ring shares **one cell on the
centre's meridian** (`seeds/cohort.py`, `Ring.north`, `longitude = centre.longitude`), by
design, so the relaxation ladder finds somebody new at each rung by construction. The drawn
spot scatters each of them inside that one cell and no further, exactly as ADR-0174 §2
promised. It is named here so the next reader does not look for it in the radar.

## Decision

### 1. The two faults are named, and the second is the design's

The iOS fault is React Native's rule about zero-sized views and is recorded in the field's own
note so the next 0 × 0 anchor anybody writes is written with a size. The Android fault is the
JavaScript-thread design's, and is what §2 replaces.

### 2. The field moves on the UI thread: `react-native-gesture-handler` and `react-native-reanimated`

We add the two libraries, at the versions the Expo SDK pins, **for the radar's field**. The
field keeps its shape — every tile laid out once at the home view, one transform carrying the
lot, every tile counter-scaled — but the three values of the transform are **shared values**,
written by the pan and the pinch and the flight **on the UI thread** and read there by every
tile's counter-scale, by every ring's centre and radius, and by a reaction that tells
JavaScript **only when a sentence would change**: the width to a tenth of a kilometre, or the
count of points in view. No frame of a drag, a pinch or a flight passes through React. The
anchor is one point square, for §1's reason.

**Amended 2026-09-17 — placed, not carried.** The one scaled transform went. At the floor on
the iPhone simulator every tile was a blur: the container is some 4 700 points wide at 1,5 km
across, and iOS rasterised it at its unscaled resolution and stretched the few pixels each
34-point face had become — a plain white card included, so it was never the posters. The
three shared values are the same, the gestures and the flight write them as before, and
**every tile's anchor reads them itself**: an animated style recovers the view from them
(`viewFromTransform`) and translates the one-point anchor to where `toScreen` puts the tile's
spot, exactly as a ring's centre already did. No layer is ever scaled, so a face is 24 or 30 pt
because it is drawn so and not because a counter-scale undoes a scale; §1's one point stands,
since iOS drops a translation on a sizeless view as readily as a scale. The cost is forty
animated styles a frame where there were forty-one; the tiles are still laid out once, and
nothing passes through React. The same day's look also moved the **zoom state** to the UI
thread: it is decided per frame with its dead-band and spoken with the width, so a face changes
state at the threshold and never at a release — JavaScript no longer derives it from a width it
heard to a tenth.

The gestures are the library's pan and pinch, **simultaneous**: the pan claims nothing until
the intent distance, the pinch needs two fingers, so a tap still reaches a face, a card or the
empty ground — they are doors, as they were. Everything the spec says about motion holds
unchanged: no inertia, the rubber band at the reach's edge, the pinch around the fingers, the
next ± snapping from wherever the pinch left off, the flight's 400 ms `easeDecel`, nothing at
all under reduced motion.

**The other three surfaces stay on `PanResponder`** — the swipe row, the deck's drag, the
radius slider. ADR-0165 §6's argument was never that the libraries are bad; it was that a
one-axis reveal does not need them, and it still does not. A surface moves to the UI thread
when a device shows it has to, and this record is what that looks like.

The gesture system needs its root view around the whole app. It goes at the very top of the
root layout, outside every provider, because it is the touch system and not a provider a
feature composes — the one exception to *a feature never adds a global provider*, and the
reason it is not one.

**Under test, the libraries are real.** Reanimated's own jest setup runs every worklet on the
JavaScript thread and its timing on the fake clock; the gesture library's fires a gesture
through its own utilities. `expo-router`'s testing library quietly replaces reanimated with an
inert mock the moment it is imported, after anything a test could hoist; the mock's module name
is mapped back to the real module so the router harness and the radar's tests are the same
harness.

### 3. The card is the selection's alone

At every width, **one player at most is a card: the one tapped**. The closest width draws the
same face-with-level the closer width does, for everybody who is not selected. A tap on a face
flies to them and selects them — at the 3 km stop, **or at the width already held where that
is narrower**, so a tap at 1,5 km across never zooms out to show a card. The selected card is
kept through a zoom in as through a zoom out, drawn above every face; a tap on empty ground
deselects; ◉ homes and deselects; a sport switch clears it. The hint at the closest widths
says what a tap earns there: *Tap anybody for their card, and the card for the full profile
and the two answers.*

The card itself does not change — mocks 10–14, line for line, the sheet behind it, the two
answers, the answered last line.

### 4. What the seed draws is the seed's to change

The clumps are a seed decision (the Context's fifth finding) and this record does not change
it. Scattering the members around their rings at the same distances is a backend change to
`seeds/cohort.py` with the ladder's assertions to keep, and is left to a ticket of its own.

## Consequences

- **Two native dependencies.** `react-native-gesture-handler` and `react-native-reanimated`
  are in the app, with a pod install and a prebuild on the next native build, a Babel plugin
  the Expo preset adds on its own, and two lines in the jest setup. Both are the SDK's own
  picks and the SDK's own versions; the app depends on nothing that is not.
- **A second gesture system beside the first.** The radar's field is the library's; every
  other gesture is React Native's. A reader has to know which is which, and the rule is one
  sentence: *the radar, and nothing else, until a device says otherwise*.
- **The domain's geometry carries `'worklet'` directives.** They are the one word Reanimated's
  compiler needs to carry a pure function to the UI thread; the functions stay pure, import
  nothing, and are tested as before. It is still a build fact written into a domain module.
- **The router harness runs real reanimated in every test**, not only the radar's, because the
  mock is mapped away for the whole configuration. Every worklet runs on the JavaScript
  thread there and every timing on the fake clock; a suite that never touches an animated view
  pays nothing, and one that does now tests what ships.
- **The tests fire gestures the library's way.** The old harness drove the responder's own
  handlers at the field; the new one fires the pan and the pinch through the library's
  utilities, which know nothing about a press — so *never claims the press* is pinned as the
  pan's intent distance rather than driven as a touch.
- **Three mocks are amended by a ruling and not by a mock.** The locked set has its first
  exception, argued from a device; the next one has to be too.
- **Nothing here has been seen on a device.** The two faults were diagnosed from screenshots
  and the source, the rebuild is tested through the harness, and the author looks on both
  devices — the drag on Android, the pinch on iOS, one card at a time on both. *(The look came
  on 2026-09-17: the pinch on iOS showed the blur §2's amendment answers, and the pinch on
  Android the hand-off ADR-0177 §1's amendment answers. Both were seen fixed on the same two
  devices.)*
- **Reanimated in the tree breaks every `Modal` on Android.** Under the New Architecture a
  modal's content is laid out at 0 × 0 until the dialog's size arrives as native state, and
  Reanimated 3.16 loses that update whenever any animated style is mounted — a 1 × 1
  `useAnimatedStyle` view on the deck pane collapsed the deck's own sheet. This record put the
  first animated style in the app, and the radar's sheet was the first casualty: a sliver of
  padding at the top-left of a window that still slid in, and — sized by hand — one nothing in
  could be pressed. [ADR-0178](0178-an-overlay-on-android-is-a-layer-in-the-tree-not-a-native-window.md)
  takes every overlay on Android off the native window and into a layer at the root.
