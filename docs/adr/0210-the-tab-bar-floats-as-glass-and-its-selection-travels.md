# ADR-0210 — The tab bar floats as glass, and its selection travels

- **Status:** Accepted. **§7 was completed on 2026-11-25** by the A32 spike,
  [#880](https://github.com/Raketa02/Raketa/issues/880), in a dated amendment: **Android draws no
  glass**, so its dock is opaque `surface`. The slide's stutter while a tab mounts was confirmed, and
  its named remedy is [#886](https://github.com/Raketa02/Raketa/issues/886), to be decided there.
- **Date:** 2026-11-25
- **Amends the player app's [design system](../../frontend_player/docs/design-system.md)
  §1.1, *Paper, not glass*,** with one exception: the tab bar is the one glass surface (§2).
- **Amends §1.2, *One accent, used sparingly*,** with a third line. A `coralSoft` fill means
  *where you are*, on the bar only. The coral list stays at six, because the marker *is* the
  active-tab entry (§4).
- **Reverses §10.1's flex sibling.** The bar floats over the screen and owns no layout. Screens end
  at its **reach**, and the bottom inset is the lift's (§3).
- **Supersedes [ADR-0135](0135-the-bar-draws-one-family-and-the-bolt-joins-it.md) for the bar
  only.** The bar draws Ionicons, and its selection changes marker, shape and tone (§5). Feather
  stays everywhere else.
- **Retires the ⚡Play disc**, with its ring, its white bolt, their size tokens and `shadow.fab`.
  `shadow.dock` takes `fab`'s slot, so the shadow inventory stays at seven (§6).
- **Adds the app's first spring**, with a stretch that follows the motion (§8). The motion list's
  *"Nothing else moves"* gains one entry.
- **Leaves standing:**
  - the shell's one stack and its reset ([#227](https://github.com/Raketa02/Raketa/issues/227)):
    what each tab opens and how a press navigates;
  - the URL as the only source of the lit tab;
  - the chat's stand-down (§10.1, [#400](https://github.com/Raketa02/Raketa/issues/400));
  - [ADR-0198](0198-the-player-app-is-not-built-for-screen-readers-for-now.md): the name is the
    whole job, and the bar's names don't change;
  - [ADR-0012](0012-player-app-design-system.md)'s rule on dependencies that own styling.
    `expo-blur`, the one new dependency, owns none;
  - from ADR-0135: one family on the bar, every glyph name typed against its family's `glyphMap`,
    the ⚡ never drawn as the character, and `@expo/vector-icons` declared rather than transitive.
- **Settles PRD [#878](https://github.com/Raketa02/Raketa/issues/878).** Decided in the dock
  grilling on 2026-11-24 (Q1–Q26) and written by [#879](https://github.com/Raketa02/Raketa/issues/879).
  The brief, the decision log and the mocks are in
  [`docs/specs/tab-bar-dock/`](../specs/tab-bar-dock/README.md). Built by:
  - [#880](https://github.com/Raketa02/Raketa/issues/880), the A32 spike: the blur, the mount
    during the slide, the shadow, and the blur's strength;
  - [#881](https://github.com/Raketa02/Raketa/issues/881), the bar floating with today's look, and
    every tab screen ending at the reach;
  - [#882](https://github.com/Raketa02/Raketa/issues/882), Android's keyboard stand-down;
  - [#883](https://github.com/Raketa02/Raketa/issues/883), the glass dock with the marker standing
    still;
  - [#884](https://github.com/Raketa02/Raketa/issues/884), the marker's motion;
  - [#885](https://github.com/Raketa02/Raketa/issues/885), the phone walk.

## Context

**Today the tab bar ends the screen.** It is a flat `surface` strip with a 1pt `line` top border,
a flex sibling below the shell's one stack. It is 64pt tall plus the bottom inset
(`TAB_BAR_HEIGHT` = 1 + 6 + 30 + 3 + 12 + 12), and the 30pt Play disc sets that height. Nothing
shows past it.

- **Home and You** draw Feather at 16pt. **Selection is tone alone**: `ink` selected and `muted`
  at rest, the same glyph in both states (ADR-0135).
- **Play** is a raised 30pt `coralInk` disc with a white Feather `zap`, casting `shadow.fab`,
  coral-tinted on iOS. When Play is lit, a 2pt `coral` ring sits 2pt clear of it. **The disc looks
  like a button to press even when you are already in Play**, and its *you are here* is a thin ring.
- **Nothing animates on a tab change.** The highlight blinks from one column to the next.

**The product owner's brief and three mocks redraw it** as a floating piece of frosted glass:
- a rounded slab 54 tall, 12 in from each side, lifted 10 off the bottom, radius 22;
- translucent white at about two-thirds, with a strong blur;
- three equal tabs, each an icon over a label;
- the selected tab filled, coral, and held in a soft coral pill 76 × 42, coral at 13%;
- content running underneath;
- the pill *travelling* to the tapped tab on a 460 ms spring, stretching like a bubble and
  overshooting, with the new tab colouring in 140 ms after it sets off.

The brief sets two rules over itself:
- *"The design from the mock references is priority so if you have to create new adr or update
  then do it."*
- *"Do not take decisions based on mocked data and mock sizes. Any decision is based on real
  evidences."*

**It runs into six locked rules:**

1. **§1.1, *Paper, not glass*:** *"A deliberate rejection of the 'floating card on grey'
   pattern."*
2. **§1.2:** *"a coral stroke is where you are … a `coralInk` fill is a thing to attend to."* The
   marker is a coral **fill** that means *where you are*.
3. **§10.1:** *"The CTA and the tab bar are flex siblings below the scroller, never fixed
   elements,"* and *"The tab bar owns the bottom safe-area inset."*
4. **ADR-0135 and §10.2:** Feather, and *"selection changes tone, and never shape."* Also: *"a
   future surface genuinely needing a filled … glyph needs a second family or a drawn one, and this
   ADR authorises neither."*
5. **The motion list in `theme.ts`:** *"Nothing else moves."* There is no spring anywhere in
   `src/`.
6. **The shadow inventory is closed at seven** (`theme.ts`, the agent rules file).

**It also meets four facts about the platform:**

- **No blur library is installed.** By `expo-blur`'s documentation (not yet checked in the
  package, which isn't installed):
  - **Android's blur on SDK 52 is the experimental `dimezisBlurView`.** It redraws the window
    behind it into a bitmap whenever anything under it or on it changes.
  - **iOS's is the native `UIVisualEffectView`.**
- **The A32 is already near its frame budget** (measured 2026-11-24):
  - the RenderThread redraws the whole scroll viewport on every animation frame, at **14–18 ms a
    frame**;
  - about **150 ms** passes from touch-end to views inserted, on debug native;
  - a tree mounting mid-motion once cost a **204 ms** frame (the splash);
  - **no local release APK can be built**, because of the path length.
- **SDK 52 doesn't draw edge to edge on Android**, so the A32's bottom inset is 0.
- **Android's `softwareKeyboardLayoutMode` defaults to `resize`.** Today's bar is a flex sibling,
  so it rides up above the keyboard and the scroller shrinks above it. A floating dock shrinks
  nothing.

**The evidence moved five of the brief's numbers.** The user agreed each in the grilling:

| The brief | Decided | Why |
| --- | --- | --- |
| lifted 10 | **12, or the bottom inset if larger** | 10 is off the 3pt grid. 12 equals the side inset, so Android gets an even margin on three sides |
| pill 76 wide | **75** | 76 is off the grid |
| about two-thirds white | **88%** | idle words must hold 4.5:1 over Home's dark game card (§2) |
| coral at 13% | **opaque `coralSoft`** | as an alpha it turns a murky brown-red over a dark card (§4) |
| coral label | **`coralInk`** | `coral` on `coralSoft` is 3.38:1, below 4.5:1 for a 9.5pt word (§4) |

## Decision

### 1. It stays *the tab bar*, and its coral capsule is *the selection marker*

**"Floating glass dock" describes the bar's look and is not its name.** *Dock* is used freely
below as a description.
- "Bottom menu" would collide with **the tab's menu**, `TabMenu`, the picker that folds out of a
  group page's Games or Friends tab.
- "Tab bar" is the name in §10.2, in `TabBar` and in both glossaries.

**The capsule is *the selection marker*,** the brief's own phrase. "Pill" is taken three times:
`radius.pill`, `SportPill` and FOR YOU's count pill.

### 2. The bar is the one glass surface — §1.1's exception

**Geometry:**

| Part | Value |
| --- | --- |
| Height | **54** |
| Side inset | **12** each side (`space.md`) |
| Lift off the bottom | **the larger of 12 and the bottom inset** |
| Corner radius | **22**, a new `radius.dock` beside `radius.sheet`'s 22 (top corners only) |
| Columns | **three equal**, (screen − 24) ÷ 3: 98.7 on a 320 phone, 120 on the A32. The Administrator's bar has two |

- **On a notched iPhone the dock rests on the safe-area line**, as iOS's own bars do.
- **On Android, with an inset of 0,** it stands 12 clear of three edges.

**Material:**
- **The glass:** a new `color.glass`, white at **.88**, over a blur wherever the platform draws
  glass. Otherwise the fill is `surface`.
- **An inner rim:** 1pt `surface`, the bright edge of the glass. It disappears on an opaque dock,
  which is harmless.
- **An outer hairline:** 1pt `line`, the border that *bounds a thing*.
- **The shadow:** `shadow.dock` (§6).

**Why 88%.** Idle words must hold 4.5:1 over the dark ground that passes under the dock most
often: Home's game card, `night` `#0A3441`. Computed with WCAG 2.1 from the theme's hex values,
with idle drawn as `ink` at 62% alpha:

| Glass white | Idle over paper | Idle over `night` | Idle over `ink` | Idle over black |
| --- | --- | --- | --- | --- |
| 67% (the brief) | ~4.7 ✓ | **3.76** ✗ | | |
| 85% | 4.89 ✓ | 4.42 ✗ | 4.38 ✗ | 4.32 ✗ |
| **88%** | 4.90 ✓ | **4.53** ✓ | 4.49 ✗ | 4.44 ✗ |
| 90% | 4.90 ✓ | 4.60 ✓ | 4.57 ✓ | 4.53 ✓ |

**`night` is not the darkest thing that can pass under the dock.** The grilling took it as the
darkest, but an `ink`-filled control or a dark player photograph is darker. Over those, 88% falls a
hair short: 4.49 over `ink` and 4.44 over black, computed as above.
- **The blur works in its favour.** It averages what passes under it, so a dark area smaller than
  the blur's reach never shows at its own darkness.
- **That has not been measured.** The spike (#880) and the phone walk (#885) look at the glass over
  dark content, and 90% is the figure that clears black.
- **88% stands as decided.** Whether to move to 90% is a call for the product owner to check (see
  *Neutral*).

**Idle is `ink` at 62%** (a new `color.tabIdle`), not `muted`. An alpha ink darkens along with the
ground under it, and a fixed `muted` doesn't: on 67% glass over `night` it reads 2.77.

**Why this is an exception and not the end of §1.1.** Nothing else becomes glass.
- Paper is still the ground, and cards still cast no shadow.
- The bar is the one thing that floats over *every* main screen, and the brief asks that it
  *belong* to the screen it is on. Paper can't do that.

The next surface that wants to be glass argues with §1.1, not with this record.

### 3. The bar floats over the screen and owns no layout — §10.1 reversed

**Screens inside the tabs draw to the bottom of the phone, and the dock floats over them.** Rows
slide beneath the glass as they scroll.

**The reach is the room the dock takes at the bottom:** lift + 54 while it is drawn, and nothing
while it stands down.
- It replaces `TAB_BAR_HEIGHT` plus the inset. Everything at the bottom is placed by it, except the
  toast, which is placed by the **full reach**: lift + 54 from the insets alone, whether or not the
  dock is drawn.
- **66 on the A32**, against today's bar at 64. **88 on a notched iPhone**, against 98. So the
  deck's room barely changes.
- **It is a followed value that the shell writes and screens follow,** the pattern `shared/ui`'s
  `onScreen.ts` already uses. Unlike the page's band, **the reach is drawn**: it sets paddings and
  where a screen ends. So a reader redraws when it changes, at the keyboard's stand-down and
  return (§9). A reader that took it once at mount would keep a band the dock no longer takes.
- **The Administrator's area draws the same dock** (Q16), and its shell, `AreaShell`, does what
  the player's shell does: it writes the reach and stands its dock down for the Android keyboard.
  Its lists and forms clear the dock the same way. #881's and #882's bodies name the player's
  shell only, and this sentence adds the Administrator's.
- **The bottom inset is the lift's.** The dock no longer pads itself with it.

**Everything placed against the bar is placed against the reach, and each keeps its own gap:**

| What | Where |
| --- | --- |
| A scroller's end | padding of reach + 15, today's gap above the bar. Its last row scrolls clear of the dock |
| The Games deck's ✕ · i · ✓ | reach + 15, the brief's *fixed clearance*. The stage fills what's left, as today, and keeps #865's least height and scroll |
| The group page's Post a game | reach + the gutter (15) |
| A screen with a pinned button (`action=`) | the layout ends at the reach, so the button sits above the dock in flow. Content ends at the button and nothing runs under the dock there |
| The toast | 9 above the **full reach** on every screen, as today it sits 9 above the full bar on every screen. In the chat it still clears the composer |
| The Undo toast | reach + 9 while the dock is drawn, and the bottom inset + 9 while it stands down, as it follows the bar today |

**Where the dock is absent:**
- **The chat** doesn't render it, as today. The chat takes the bottom inset on its own
  `SafeAreaView`.
- **On Android, while the keyboard is up,** the dock stands down too (§9).
- **The rule for both:** the dock is **not rendered**, rather than hidden, and nothing animates it
  away (§1.5).
- ***It's a game!***, sheets, popovers, toasts and the launch splash are drawn above it, as today.

### 4. A `coralSoft` fill means *where you are*, on the bar only — §1.2's third line

**The selection marker:** opaque `coralSoft` (`#FDEBE6`), 75 × 42, at `radius.pill`, centred in
its column. It sits on the glass, under the icons and labels.

**It is opaque.** The brief's *coral at 13%* would be `#FCE7E3` over white, a hair away from
`coralSoft`. As an alpha it would turn a murky brown-red over a dark card. Opaque, it looks the
same over anything.

**The selected tab's colours are split by what they carry:**
- **Its icon is `coral`**: a mark, 3.38:1 on `coralSoft`, clearing 3:1 for a graphical object.
- **Its label is `coralInk`**: words, 5.11:1 on `coralSoft`. `coral` would be 3.38, failing 4.5:1
  for 9.5pt `tag`. This is Rule C's spirit, and the tab's menu tick already took `coralInk`
  ([#861](https://github.com/Raketa02/Raketa/issues/861)).
- Mock 3 draws the label in bright coral. That is illustration.

**§1.2 gains a third line beside its two.** It already says *a coral stroke is where you are* and
*a `coralInk` fill is a thing to attend to*. It now adds: **a `coralSoft` fill is where you are, on
the bar.**
- **The coral list stays at six.** The marker *is* the active-tab entry, redrawn. With the ring
  gone (§6), the stroke line keeps the game card's ringed cell as its example.
- **Home's badge stays `coralInk`, with a white digit.** The brief's *"the selected tab is the only
  coloured thing on the dock"* is read as *the only coloured thing that means selected*.
  *Something needs you* and *you are here* are kept apart by fill.
- **Rankings' own row is already tinted `coralSoft`** for *where you are* in a list
  ([#775](https://github.com/Raketa02/Raketa/issues/775)), recorded as a meaning above. It stays
  what it is. The third line names the bar and licenses no further surface.

### 5. The bar draws Ionicons, and selection changes marker, shape and tone — ADR-0135 superseded for the bar

| Tab | Idle | Selected |
| --- | --- | --- |
| Home | `home-outline` | `home` |
| Play | **`flash`**, filled in both states | `flash` |
| You | `person-outline` | `person` |
| Groups (the Administrator's) | `people-outline` | `people` |

- **The icon box is 18**, with a gap of 3 to the label. The label is `tag`, and its 1.6
  `maxFontSizeMultiplier` cap is kept.
- **Idle:** icon and label in `color.tabIdle`.
- **Selected:** icon `coral` and label `coralInk`, over the marker.
- **Every name in the table is in the installed `@expo/vector-icons@14.0.4` Ionicons glyph map**,
  checked in the package. Every name is typed against `Ionicons.glyphMap`, as today's are against
  Feather's, so a missing name fails to compile.

**Why 18.** It is the largest box that keeps icon + 3 + the label's line inside the 42 marker at
the 1.6 cap, where `tag`'s 12pt line becomes 19.2:
- **16** → 38.2 ✓;
- **18** → **40.2** ✓;
- **20** → 42.2 ✗.

16 is the fallback if 18 looks crowded on the phone (#885).

The decision log's §4 gives 39.4, 41.4 and 43.4. Those take the line at the cap as 20.4, which is
the old 1.7 cap's figure, still printed in §10.2. The verdict is the same, and these are the
figures to test against.

**So the dock is 54 tall on every screen, in every state and at every text size.** Today the bar
grows with the label at the cap (§10.2). The cap is now what holds the label inside the marker.

**Why a second channel is right now, when ADR-0135 refused one.** 0135 argued that `ink` against
`muted` (3.25:1) was a sufficient state channel. On that view an outline/filled pair would be *"two
things saying one thing, and the second is free to disagree"*.
- **The premise moved:** the PRD's problem statement is that the tab you are on is hard to see. The
  product owner's design, which the brief puts first, asks for a marker, a fill and a colour.
- **The channels can't disagree.** All three are drawn from one value, the lit tab read from the
  URL. The tab left goes idle at once, so the dock never shows two selected tabs. The colour-in's
  140 ms lag (§8) is a transition, not a second state.
- **WCAG 1.4.1 is met by more than colour.** Selection is a filled shape and a capsule as well as
  a hue, so it survives greyscale and a red-green deficiency.
- **Play has no outline**, because the brief draws the bolt filled always: it is the brand's mark,
  not a pictogram. Play's selection is the marker and the colour. That is one reason the marker
  is not optional.

**Why Ionicons.**
- **Feather has no filled counterparts**, so the outline → filled change can't be drawn in it.
  ADR-0135 named this limitation itself, under *Harder*.
- **Ionicons ships in the package the app already declares**, so the bar needs no new dependency.
- **A drawn SVG set** lost in ADR-0135 as a maintenance surface with no second use, and still does.
- **MaterialCommunityIcons** has the glyphs too and was not chosen (Q4).

**What stands of ADR-0135:**
- **one family on the bar**, never mixed: now Ionicons;
- **Feather on every other surface**, including Home's header beside the bar;
- typed glyph names;
- the ⚡ never drawn as the character;
- the declared dependency.

**The cost:** Ionicons' outline stroke is finer than Feather's 2/24, so the bar reads a touch
lighter than the header above it. The user accepted that (Q4).

**Unchanged on the column:**
- **Press:** the column's icon and label dim to 0.7 while the finger is down, as today. The marker
  ignores the press, and the slide starts at the lift.
- **No haptics** (Q26). The marker's landing is the feedback, and the app's one success haptic
  stays *It's a game!*'s.
- **Accessibility:**
  - role `tab`, the column's name and its selected state;
  - icons hidden from the reader;
  - Home's count spoken in Home's name: *Home, 2 games waiting on you*.

**Home's badge** keeps today's mark and geometry:
- 18 minimum, `num.xs` tabular;
- rises 4 above the icon box and sits 3 back over its right edge.

Its old ground was the ring's 4pt taken out of the bar's 6pt top padding, and that went with the
ring. The 4 stays as the badge's own number. Inside a 54 dock with the content centred, the badge's
top is **6.5** inside the dock's top edge at 1× and **2.9** at the cap (the log's 2.3 is the 1.7
cap's). The font-fit tests hold it there (#883).

### 6. The ⚡Play disc retires, and `shadow.dock` takes `fab`'s slot

**What retires:**
- the 30pt `coralInk` disc;
- the 2pt `coral` ring;
- the white `zap` at 15pt;
- the disc's own `size.fab` (30) and `radius.fab` (11), which only the bar draws;
- `size.tabBar.bolt`, `ringGap` and `ringStroke`;
- `shadow.fab`.

**Play becomes an ordinary column.** What pressing Play does is unchanged. A raised disc reads as a
button you are being pushed to press, even while you are in Play. Mock 3 draws Play as one of three
equal places.

**`shadow.dock` takes the freed slot, so the inventory stays at seven.**
- **It borrows `shadow.deckCard`'s values:** `#0B2B33`, offset 0/7, radius 20, opacity .12,
  elevation 8. That is the faintest of the shadows for things that float: `theme.ts` says it
  *floats least of the four*. The club result's and FOR YOU's open line's are fainter, but they
  are the two named amendments for things on the page, not things over it.
- **The ⚡Play disc's coral tint on iOS was the only tinted shadow.** It retires with the disc.
- **Android's `elevation` shadow shows through a translucent fill.** If Android keeps the glass
  (§7), the dock's shadow is drawn with React Native 0.76's `boxShadow` instead, clipped outside
  the dock.

### 7. Android's material is decided on the A32 — *open*

**iPhone draws the glass, always.** Android draws it **only if the spike's blur test passes**.

**Otherwise Android's dock is opaque `surface`** (Q18). It keeps the same shape, lift, radius,
rim, hairline, shadow and marker. Two in-between options were rejected:
- **translucency without blur**, because sharp text behind the labels shows through;
- **near-opaque (about 95%)**, because it needs a new token for almost nothing.

**The spike** ([#880](https://github.com/Raketa02/Raketa/issues/880)) runs before the dock is
built:
- **The build:** the debug native build with JavaScript in production mode, through the
  shared-prefs switch. It is the only build that can be made locally.
- **The tool:** the atrace A/B harness from the 2026-11-24 performance work.
- **The prototype:** a throwaway, never merged.

| Test | What runs | Passes if |
| --- | --- | --- |
| **T1 — the blur** | Blur on against blur off, in one build, over (1) a scroll on Home with the dark game card passing under the dock and (2) the marker's slide, several runs each | **the blur adds no frame over 16.7 ms to either.** The debug overhead cancels out in an A/B, so the verdict is fair on this build. The A32's own scroll already draws frames at 14–18 ms, so a single run can differ from the next by a frame. The verdict is read across the runs, and #880 records the run counts beside it |
| **T2 — the mount during the slide** | Real presses Home → You, Home → Play and You → Home, with the new screen mounting while the marker travels | **no frame is over 33 ms during the 460 ms** |
| **T3 — the shadow** (only if T1 passes) | The dock's shadow drawn with `boxShadow` | it is clipped outside the dock, and nothing shows through the glass |

- **T1 decides the material.** Pass → Android draws the glass. Fail → Android's dock is opaque
  `surface`.
- **A T2 fail on this build is inconclusive**, because debug native can fail on overhead alone.
  The product owner confirms it on a release or preview build they make, since builds are
  human-only.
- **The remedy for a confirmed fail is named here and not chosen: keep the three tab roots
  mounted, so a press mounts nothing.**
  - It would change the shell's lay-it-down-fresh model (#227), in which You and Play are laid
    down fresh on every press.
  - It opens as a new issue on that evidence, and is decided there, not here.
- **The blur's strength is chosen by eye.** Two or three strengths are shown over Home's dark card
  and over a list of white rows, and the product owner picks one.
- **The brief's *touch more saturation* is judged on the phone.** iOS's materials carry their own
  saturation; Android's blur has none.

**The outcome is recorded in one place in code:** a single theme-level switch saying whether
Android draws the glass. #880 completes this section with a dated amendment: **Android draws the
glass, yes or no.** It also adds the blur's strength and the measured numbers.

> **Amended 2026-11-25 — Android draws the glass: no.** The A32 spike
> ([#880](https://github.com/Raketa02/Raketa/issues/880)) measured a throwaway prototype dock on a
> local branch that was never merged: `expo-blur`'s `dimezisBlurView` under 88% white, and the
> 460 ms spring. The numbers, the builds and the run counts are in the spec folder's
> [`a32_spike.md`](../specs/tab-bar-dock/a32_spike.md).
>
> - **T1 fails, so Android's dock is opaque `surface`.** The blur redraws everything behind the
>   dock on the UI thread whenever anything under or on the dock changes.
>   - Over You's rows of icons and dark controls, it added frames over 16.7 ms on both builds: 17 →
>     26 on debug native and 6 → 16 on release, over six scrolls an arm.
>   - On release, it also added them to the slide: 19 → 28 over twenty slides.
>   - Over Play's plain white rows it added none.
>   - The pass mark was *no frame added to either*. The dock keeps its shape, lift, radius, rim,
>     hairline, shadow and marker. **The theme-level switch that #883 writes is off on Android.**
>     The iPhone draws the glass.
> - **T2 fails, and the fail is confirmed.**
>   - With the blur off, 16 of 16 slides on debug native and 14 of 16 on release had a frame over
>     33 ms.
>   - The worst is Home → Play, up to 176 ms on release: Fabric creating Play's views on the UI
>     thread mid-slide.
>   - The slide also starts late. A real press draws nothing for 104–208 ms (release medians) while
>     the new tab is rendered in JavaScript, against about 47 ms with no navigation.
>   - **The named remedy, keeping the three tab roots mounted, is
>     [#886](https://github.com/Raketa02/Raketa/issues/886)**, `needs-triage`, and is decided there.
> - **The confirming build was made locally.** The Context's *no local release APK can be built* no
>   longer holds: a checkout at a short path builds one. The product owner accepted that release
>   build as T2's confirmation.
> - **T3 passes, though Android no longer needs it.**
>   - `boxShadow` drew the shadow outside the dock, and nothing showed through 88% or even 50%
>     glass.
>   - §6's worry about `elevation` didn't materialise on this dock: the blur's opaque copy of what's
>     behind covers the shadow.
>   - On the opaque Android dock, `shadow.dock`'s `elevation` draws as it is.
> - **The blur's strength is intensity 100**, the brief's *strong blur*.
>   - Under 88% white, 20, 60 and 100 look almost the same over Home's dark card and over white
>     rows. 100 is the cleanest of the three: Android's blur draws the dock's own icons into its
>     bitmap, and 100 is the one that leaves no grey ghosts of them.
>   - The product owner has no iPhone at hand, and took the iPhone's value from the A32. **It
>     hasn't been seen on an iPhone**, which #885 checks if one is available.
>   - The brief's *touch more saturation* stays the iPhone's own material's.
> - **The ticket's scroll couldn't run on Home.** Once the dock floats, Home doesn't scroll for the
>   populated seed player, and its dark game card ends far above the dock. So the scroll ran on You
>   and Play, and the strength renders lifted the dock over the card.
> - **For #884:** Reanimated 3.16's `withSpring` takes `{ duration: 460, dampingRatio: 0.75 }`, so
>   §8's fallback configuration isn't needed.

### 8. The selection marker travels — the app's first spring

**The marker slides whenever the lit tab changes after the dock is first drawn:**
- a press on the bar;
- a landing that lays down another tab's stack, after a rating pass or a notice;
- **a group opened from Home's *Groups heating up***. It lives under Play (`/play/group/{id}`), so
  the marker slides Home → Play, and back slides it home. Today's bar already lights Play there;
- back from any of these.

**It doesn't move:**
- **on the dock's first draw, or when the dock comes back** after the chat or the keyboard. It is
  simply there under the lit tab (Q25);
- **inside a branch**: a booked game from Home, a group from Play, game details from a group;
- **on a press of the lit tab.** There is no slide, bounce or pulse. Navigation is as today: at the
  tab's start nothing happens, and from deeper in the stack resets to the start (Q14).

**The slide is a spring: 460 ms, damping ratio 0.75.** Every trip takes 460 ms, whatever the
distance, so the far jump moves faster. The overshoot is `e^(−ζπ/√(1−ζ²))` of the trip, about 2.8%:

| ζ | one column (A32, 120) | two columns (240) | one column (320 phone, 98.7) |
| --- | --- | --- | --- |
| 0.70 | 5.5 | 11 | 4.5 |
| **0.75** | **3.4** | **6.8** | **2.8** |
| 0.80 | 1.8 | 3.6 | 1.5 |

**Why a spring, in an app with none.** The brief asks for one: *"a spring curve, not a straight
ease-out"*. A spring also does what a timed curve can't: a press mid-flight **retargets** it. A new
spring starts from the marker's current place and speed. It never finishes the first trip first,
and never snaps.

**The stretch follows the marker's motion, not its share of the trip** (Q10).
- **The motion:** the marker widens and flattens as it speeds up, and narrows and heightens as it
  brakes.
- **The calibration:** a two-column trip (Home → You, the brief's frame-by-frame) reaches about
  **1.30 wide × 0.84 tall near 35%** of the way and recoils to about **0.94 × 1.06 near 70%**. It
  rests at exactly 1.
- **A one-column trip stretches about half as much.**
- **The speed is measured in columns, not points.** So a two-column trip reaches 1.30 × 0.84 on
  every phone, and a wide phone doesn't stretch more than a narrow one.
  - Measured in points, every trip still takes 460 ms. A wider phone's trip would then be faster,
    and it would stretch past the brief's numbers.
  - The PRD didn't name the unit, so this is a call made while writing (see *Neutral*).
- **At its peak the marker is 75 × 1.30 = 97.5 wide**, against a 320 phone's 98.7 column, measured
  on the dock's outer edge. That margin is under a point and the borders take part of it, so the
  fit tests measure it against the column as built.
- **Why not keyframes tied to the trip:** they couldn't meet both the brief's fixed numbers and its
  *"the far jump stretches a little more"*. A retarget would also restart the trip and snap the
  shape. Tied to the motion, the shape stays continuous through a retarget.

**The colour-in:**
- The pressed tab's icon goes outline → filled and `tabIdle` → `coral`, and its label `tabIdle` →
  `coralInk`.
- It runs **300 ms on `easeDecel`, starting 140 ms after the slide begins**, so the tab seems to
  light up because the marker arrived.
- It is a cross-fade between two stacked layers per tab, idle and selected, so only opacity moves.
- **The tab left goes idle at once.**
- **The screen behind changes at 0 ms.** The reset runs on the press, and the motion never slows a
  player down (Q12).

**Per frame, only `transform` and `opacity` move, on the UI thread.** This is the app's Reanimated
rule, and it keeps the motion independent of the JavaScript thread mounting the new screen.
- **The travel is a translate, and the stretch is a scale on the marker's own layer.**
- **The layers, bottom to top:** glass → marker → icons and labels → badge.
- **No glyph or word is ever deformed.** The scaled layer holds no word or glyph, so iOS's
  rasterising of a scaled layer (the app's rule against scaling a layer to move things) has nothing
  to blur. The caps go slightly oval at the peak. That is the bubble.

**Reduce motion:** the marker is placed under the new tab, and the colours switch at once. There is
no slide, stretch or cross-fade. It is not one of Part 13's exceptions, because nothing moves.

**One token, `motion.tabMarker`,** holds the slide, the damping ratio, the colour-in and its delay.
The motion list's header gains the entry.
- If Reanimated 3.16's spring doesn't take a duration and a damping ratio, the build uses the
  stiffness and damping that give the same settle and overshoot.
- The table above is the acceptance.

### 9. On Android, the bar stands down while the keyboard is up

**Why:** a floating dock doesn't shrink the scroller. A field focused just above the keyboard
could sit under the glass: Intro, Name, a new group, editing a group, posting a game, and the
Administrator's forms (§3).

**What happens:**
- **On Android, while the soft keyboard is up,** the shell stops rendering the dock and sets the
  reach to nothing, with no animation. Its reserved space goes with it, so no empty band sits above
  the keyboard.
- **When the keyboard closes, the dock comes back**, with the marker in place (§8).
- **iPhone ignores the keyboard**, which already covers the dock there.

**The keyboard's platform module reports whether the soft keyboard is up.**
- **It already exists:** `shared/lib/platform/keyboard.ts` is the keyboard's chokepoint today
  (`KEYBOARD_AVOIDANCE`, `windowResizesForKeyboard`, `dismissKeyboard`). The reading joins it there,
  not in a second module. Native code hides behind a narrow interface in `shared/lib/platform/`,
  one chokepoint per capability, as the player app's
  [architecture](../../frontend_player/docs/architecture.md) Part 13 asks.
- **It is the app's only listener for the keyboard's show and hide**, and nothing else subscribes
  to them today. A caller can follow it.
- **It gets a fake** beside the platform fakes in `test-support`.
- **This corrects the PRD and #882**, which call it a new port.

### 10. Where each change is written

**This record and #879 change the documents only.** No code changes, and no `theme.ts`.

**The design system's text changes with the code that ships it**, together with `theme.ts`, per
the locked rule. Until then, §1.1, §1.2, §10.1 and §10.2 carry a note: *decided by ADR-0210, not
yet built*.

| Ticket | Writes |
| --- | --- |
| #879 | this record; ADR-0135's status line; the index; the spec folder; the glossary's *selection marker* and *The shell*'s note; the four *not yet built* notes |
| #880 | §7's amendment, and the spike's numbers in the spec folder |
| #881 | §10.1 rewritten for the floating structure; the shell's feature record; the Administrator's area ending at the reach too (§3) |
| #882 | §10.1's keyboard stand-down beside the chat's, in both shells; `keyboard.ts` named in the player app's `CLAUDE.md` port list |
| #883 | `theme.ts`'s new and retired tokens (all but `motion.tabMarker`); §1.1, §1.2 and §10.2 rewritten; the Part 16 rows; Appendix B if it names the bar; the agent rules file (the disc's tinted shadow and the coral list's wording); `CLAUDE.md`'s *every mark is drawn or is Feather*, which gains Ionicons on the bar |
| #884 | `motion.tabMarker`; §10.2's motion paragraph; Part 13; their Part 16 rows; the player app's `CLAUDE.md` rule *never scale a layer to move things*, which gains the marker as a scale on a layer that holds no word or glyph (the log's §14) |

**The tokens:**
- **Added:** `color.glass`, `color.tabIdle`, `radius.dock`, the bar's size tokens (height, inset,
  lift, marker, icon), `shadow.dock`, `motion.tabMarker`, and the Android-glass switch.
- **Retired:** `size.fab`, `radius.fab`, `size.tabBar.bolt`, `ringGap`, `ringStroke` and
  `shadow.fab`.
- **The names are calls made while writing**, for the product owner to check. The values are the
  grilling's.

**The historical records are not rewritten.** That covers this record's predecessors and the
earlier decision logs. Other mentions of the bar's look, or of the flex sibling, get notes in
place from the tickets that change them.

## Consequences

**Easier**

- **Where you are is visible across a room.** The marker, the fill and the colour say it together,
  and it holds without hue.
- **Play reads as a place**, not a button to press while you are already in it.
- **Every main screen uses its whole height,** and the page shows around and under the dock.
- **One measure places everything at the bottom.** Today the two toasts add `TAB_BAR_HEIGHT` and
  the inset, while the deck, Post a game and every scroller clear the bar only because it is a
  flex sibling. Now they all read the reach, or the toast its full reach: the same sum, without
  the stand-down.
- **A tab change has a direction.** The eye follows the marker from where you were to where you
  went.

**Harder**

- **A glass surface in a paper system.** The exception has to stay one. The next request to make
  something glass argues with §1.1, not with this record.
- **Every tab screen now owns its bottom edge.** The flex sibling made it impossible to get wrong;
  now only the router-harness tests guard it.
  - A new scroller that forgets reach + 15 leaves its last row under the glass.
  - A pinned button that forgets the reach sits under the dock.
- **A spring and a speed-driven stretch are harder to pin than a timed curve.** The numbers live in
  a pure module, and the tests read poses with `getAnimatedStyle` under fake timers. The feel is
  judged only on the phone (#885).
- **The two platforms may draw two materials.** If T1 fails, Android's dock is opaque white while
  iPhone's is glass. §10.2 describes a fork, and every visual check needs both platforms.
- **The A32 has little headroom for any of this.**
  - On Android, blur redraws the window behind the dock.
  - The slide may stutter while a tab's root mounts.
  - If T2's fail is confirmed, the remedy changes #227's model for every tab press. That is a
    larger decision, taken later.
- **On Android, the bar disappears while a player types.** One more platform port exists for it.
  Navigation is one dismissal of the keyboard away.
- **Two icon families in one app.** Feather everywhere and Ionicons on the bar, fenced by surface.
  The bar reads a touch lighter than Home's header beside it.
- **§1.2's list keeps growing in words, if not in entries.** `coralSoft` now means *where you are*
  twice: on the bar, and on Rankings' own row. Each is fenced to its surface.
- **The toast keeps the dock's full clearance in the chat**, where there is no dock: 9 above an
  empty band. That is the price of never covering the composer. It is a call made while writing the
  PRD, for the product owner to check.

**Neutral**

- **The deck's room barely changes:** the reach is 66 on the A32 against 64 today, and 88 on a
  notched iPhone against 98.
- **The group page's own tabs and `TabMenu` are a separate system** and don't change.
- **Not asked for, and not built:**
  - scroll-to-top on a lit-tab press;
  - hiding the dock on scroll;
  - haptics;
  - a dark mode;
  - iPhone keyboard handling.
- **Rejected in the grilling**, with reasons in the decision log:
  - "bottom menu" and "dock" as names;
  - 67% and 85% glass, and `muted` for idle;
  - an alpha coral marker and a `coral` label;
  - keeping Feather, MaterialCommunityIcons, or a drawn icon set;
  - icons at 20;
  - keeping the disc;
  - dropping Home's badge;
  - the brief's 10 and 76;
  - a stretch keyed to the trip;
  - damping 0.70 or 0.80;
  - changing the screen after the marker lands;
  - keeping the tab roots mounted *now*;
  - Home staying lit for a group opened from Home;
  - a slide on first draw;
  - translucency without blur, or near-opaque, on Android.
- **Calls made while writing, for the product owner to check:**
  - the token names;
  - `easeDecel` for the colour-in, instead of the brief's *plain ease*;
  - the stretch stated as behaviour and two calibration points, rather than a formula;
  - the spring's fallback configuration;
  - the spec folder's name;
  - the toast's clearance in the chat.
- **Calls made writing this record, for the product owner to check:**
  - **88% or 90% glass.** 88% holds 4.5:1 over `night` but not over `ink` or a dark photograph
    (§2). Whether the blur's averaging closes the gap is for the spike and the phone walk to show.
  - **The stretch measured in columns** (§8), so every phone stretches alike.
  - **The Administrator's shell writing the reach and standing down for the keyboard** (§3, §9),
    which follows from Q16 but isn't in #881's or #882's body.
  - **The keyboard reading joining `keyboard.ts`** rather than a new port (§9).
