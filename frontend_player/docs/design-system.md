# Raketa Player App — Design System

**Status: locked.** This is the player app's visual and interaction contract. Every
screen and component in `frontend_player/` conforms to it. Building a surface that is not
described here means extending the system deliberately (Part 15), not inventing beside it.

- **Origin:** measured out of the v34 HTML prototype
  (`raketa-player-app-prototype-v34.html`, cross-checked against
  `raketa-player-deck-v34.html`). The verbatim measurement is preserved at
  [`design-system-v34-prototype-audit.md`](design-system-v34-prototype-audit.md).
- **Relationship to that audit:** the audit is _descriptive_ — it recorded the prototype
  including its inconsistencies (its Part 20) and its accessibility gaps (its Part 21).
  This document is _prescriptive_. Where the two differ, **this document wins**, and every
  difference is listed in [Part 14](#part-14--corrections-applied-to-the-prototype).
- **The prototype is a web page; this app is not.** Part 2 of this document is about
  translating a stylesheet into React Native, and that translation is not mechanical —
  see [Part 0](#part-0--reading-a-web-prototype-as-a-native-app) first.
- **Changes made since locking** are recorded in [Part 16](#part-16--amendments-after-locking),
  never absorbed silently. Locked means changes are _visible_, not forbidden. Sections
  deleted by the 2026-08-25 reset are listed in [Part 17](#part-17--what-the-reset-removed).
- **Implementation:** the tokens are real code at
  [`../src/shared/ui/theme.ts`](../src/shared/ui/theme.ts). That file is the single source
  of colour, type, spacing, radius, elevation and motion values.
- **Scope: the player app only.** A second client would get its own design system. Two
  palettes would converge because it is one brand, but **the values are never shared** — no
  common package, no cross-import
  ([ADR-0005](../../docs/adr/0005-three-app-monorepo-ownership-boundaries.md)).
- **Cut back on 2026-08-25.** The reset reduced the repository to sign-up, sign-in and
  onboarding, and every section specifying a removed feature was removed with it — the
  match card, the fit badge, the balance bar, the seat avatar, the booking slot grid, and
  the Find / Match detail / Creating / Passport screens. **Section numbers of what survives
  are unchanged**, so the gaps are deliberate and an old citation still resolves to the
  right thing; [Part 17](#part-17--what-the-reset-removed) lists what stood where.

---

# Part 0 — Reading a web prototype as a native app

The prototype is an HTML file. Four things in it are **not part of the product**, and a
handful more need translating rather than copying. Read this before Part 1 or you will
build the harness.

## 0.1 The harness is not the app

Above 900px the prototype renders the app inside a phone frame on a dark stage, with a
scenario rail and a time bar. **None of that ships.**

| In the prototype                                                             | Status                                                                          |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `#stage` `#phone` (392×788, radius 34, `#24505E` border) — the phone picture | **Harness.** The app _is_ the phone.                                            |
| `#rail` — the 290px scenario switcher at `#071C24`                           | **Harness.** A demo tool for stepping through 32 states.                        |
| `#timebar`, `#mtop`, `#statusbar`                                            | **Harness.** The OS provides the status bar; safe-area insets provide the rest. |
| The `900px` breakpoint and the mobile drawer                                 | **Harness.** A native app has no desktop mode.                                  |
| Stage colours `#08222B` `#071C24` `#0B2B36` `#24505E`                        | **Dropped from the palette.** They exist only to frame a picture of a phone.    |

The prototype's own principle 1.6 says this in its way — _"the frame is not the app"_.
Taken to its conclusion in a real native app, the frame does not exist at all.

## 0.2 What replaces the frame

| Prototype                                        | Native app                                                                                                            |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| Fixed 392pt width; 362pt content                 | **Content width = screen width − 30** (15pt gutters). Every horizontal measurement derives from _that_, not from 362. |
| `#statusbar` 28px                                | `react-native-safe-area-context` top inset                                                                            |
| `#toast { bottom: 78px }` — clearing the tab bar | Tab-bar height + bottom safe-area inset                                                                               |
| `100dvh` / `calc(100dvh - 46px - 56px)`          | Flex layout inside `SafeAreaView`                                                                                     |
| `.mrail > * { width: 268px }`                    | **0.74 × content width** — the peek affordance is a _ratio_, not 268pt. On a 320pt phone, 268 leaves no peek at all.  |

## 0.3 What has no equivalent and must be re-specified

| Prototype                                  | Native app                                                                                                              |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| `:hover` (`.card.tap:hover`, `.btn:hover`) | **Press states.** Touch has no hover. Specified in [6.6](#66-press-states).                                             |
| `filter: brightness(1.06)`                 | Not available. Each variant declares a pressed colour.                                                                  |
| `transform: translateY(-1px)` on hover     | Dropped. A 1px lift is a pointer affordance and means nothing under a finger.                                           |
| `:focus-visible` outline                   | Not a touch concept. Replaced by the accessibility contract in [Part 13](#part-13--accessibility).                      |
| `box-shadow` with spread / negative spread | RN shadow props + `elevation`. Approximations given in [4.3](#43-elevation).                                            |
| `letter-spacing` in `em`                   | **RN `letterSpacing` is in points.** Every value is pre-converted in [3.4](#34-tracking-converted-to-points).           |
| `line-height` as a multiplier              | **RN `lineHeight` is in points.** Pre-converted in [3.5](#35-line-height-in-points).                                    |
| `font-weight` on a custom family           | **Does not work on Android.** Weight is selected by _family name_. See [3.2](#32-weights-are-family-names-not-numbers). |
| `overflow-x: auto`, `scroll-snap`          | `ScrollView horizontal`, `snapToInterval`, `pagingEnabled`                                                              |
| `z-index`                                  | `zIndex` is per-parent. Overlays use `Modal` or a single root-level portal.                                             |

## 0.4 What the prototype could not have

Two requirements exist only because this is a real app on a real device, and both are
non-negotiable:

- **Touch targets.** The prototype has 23–32px controls. Nothing tappable may be smaller
  than **44 × 44pt** of _reachable_ area — use `hitSlop` where the visual is smaller.
  See [6.5](#65-touch-targets).
- **Screen readers.** VoiceOver and TalkBack are the only way some players use the app.
  See [Part 13](#part-13--accessibility).

---

# Part 1 — Design principles

Not aspirations — each is visible in the implementation and can be checked against it.

## 1.1 Paper, not glass

The app background is `--paper` `#F4F2ED`, a warm off-white, not pure white. Cards are
`#FFFFFF` on top of it. **The contrast between surface and background is what creates
depth**, so the app needs almost no shadow: three shadows exist in the whole system, and
all three are for things that genuinely float.

A deliberate rejection of the "floating card on grey" pattern. Warm paper reads as a
physical object; a card on it reads as a piece of paper on a desk.

## 1.2 One accent, used sparingly

Coral is the only attention colour. It appears on: the primary button, the active tab,
the level mark on the band bar, the onboarding progress fill, and the hot tag.
**Nothing else.** When everything is accented, nothing is.

## 1.3 Semantic colour is never decorative

| Token   | Means                                  |
| ------- | -------------------------------------- |
| `mint`  | Settled, safe, covered, confirmed      |
| `amber` | Watch this — reversible, not yet wrong |
| `red`   | Ended badly                            |
| `info`  | Explanation, not status                |

`info` is the deep teal already in the palette rather than a new blue. **The palette does
not grow to accommodate a new meaning; a meaning is assigned to a colour already present.**

## 1.4 Numbers are monospaced, always

Money, levels, times, percentages and counts use IBM Plex Mono with tabular figures. A
column of levels lines up. **A level changing from 2,71 to 2,80 does not reflow its row.**

## 1.5 Nothing animates that does not have to

One entrance animation, one sheet animation, one popover animation, one fade. Press
feedback is 120ms. Reduced-motion disables all of it.

## 1.6 The app is the app

There is no frame, no stage, no scenario rail — see [Part 0](#part-0--reading-a-web-prototype-as-a-native-app).

---

# Part 2 — Colour

## 2.1 Surfaces and structure

| Token     | Value     | Role                                                                     |
| --------- | --------- | ------------------------------------------------------------------------ |
| `paper`   | `#F4F2ED` | App background. Warm off-white                                           |
| `paper2`  | `#EDEAE3` | Recessed surface — the situation header in a question, the popover close |
| `surface` | `#FFFFFF` | Cards, sheets, popovers, raised controls                                 |
| `ink`     | `#101B20` | Body text, selected chip                                                 |
| `night`   | `#0A3441` | Dark cards, meter fill, toast                                            |
| `night2`  | `#12495B` | Secondary dark                                                           |
| `muted`   | `#5C6D73` | Secondary text, `tiny`, eyebrows, disabled                               |
| `line`    | `#E5E1D8` | Card borders, chip borders, dividers                                     |
| `line2`   | `#F0EDE6` | Hairlines inside cards, tag backgrounds, inactive tracks                 |

> `line` **bounds a thing**; `line2` is a **fold inside one thing**. The hairline uses
> `line2` precisely so a card with two sections reads as one object, not two.

> **`surface` is used.** In the prototype it was declared and never referenced — cards
> hard-coded `#fff`. Here there is one white and it has a name.

## 2.2 Accent and semantics

Each semantic colour ships as a **triplet**: the colour, a soft background, and an ink
variant for text on that soft — plus a `line` companion for the soft's border.

| Token       | Value     | Used for                                                                                                   |
| ----------- | --------- | ---------------------------------------------------------------------------------------------------------- |
| `coral`     | `#E8482B` | The single accent. A **mark**, not a text bed                                                              |
| `coralSoft` | `#FDEBE6` | Backgrounds behind coral messaging                                                                         |
| `coralInk`  | `#B8351C` | Text on `coralSoft`; **and the fill wherever white text sits on coral**                                    |
| `coralLine` | `#F3CFC5` | Border of a coral note                                                                                     |
| `mint`      | `#0C8F6B` | Good, settled, covered. A **mark**                                                                         |
| `mintSoft`  | `#E2F3EC` | Free time slots, ok tags                                                                                   |
| `mintInk`   | `#0A7355` | Text on `mintSoft`; the fill wherever white text sits on mint                                              |
| `mintLine`  | `#CFE7DD` | Border of a mint note                                                                                      |
| `amber`     | `#8A5E09` | Caution, reversible                                                                                        |
| `amberSoft` | `#FBF0DA` | Caution backgrounds                                                                                        |
| `amberLine` | `#EFDCB8` | Border of an amber note                                                                                    |
| `red`       | `#B4392C` | Failure                                                                                                    |
| `redSoft`   | `#FBEAE7` | Failure backgrounds                                                                                        |
| `volt`      | `#D9F24B` | **A fill anywhere, a stroke only on dark.** Confidence ring, active info mark, the interest tag and button |
| `info`      | `#12495B` | Explanatory notes                                                                                          |
| `infoSoft`  | `#EAF1F4` | Explanatory backgrounds                                                                                    |
| `infoLine`  | `#C7DBE3` | Explanatory borders                                                                                        |

**Volt is a fill anywhere and a stroke only on dark.** The two uses are not the same
problem. As a **foreground** on paper volt is ~1.3:1 — a volt hairline, ring or border on
`paper` is a line nobody sees, which is the failure corrections **#14** and **#15** already
fixed once for the dashed empty seat (1.17:1) and the free-slot border (1.27:1). As a
**fill** the relationship inverts: `ink` on volt is **13.96:1** ([2.5](#25-contrast--computed)),
so a volt tag or button reads on any surface in the app. On `night`, volt as a foreground is
10.60:1.

**A volt fill carries `ink`, never white.** And an emphasis that wanted a volt stroke on
paper becomes a volt **tag** instead: a border carries no word, and a signal that has one
should say it ([Part 13](#part-13--accessibility) — never colour alone). An in-progress
state on paper is `coral`, like every other one, and not a volt ring.

### Rule C — text on a saturated fill

`coral` and `mint` are **marks, not text beds**. White on them is 3.89:1 and 4.07:1 —
below AA, and nothing in this app reaches WCAG's large-text threshold (18.66pt bold).

| You want                                                                | Use                                  |
| ----------------------------------------------------------------------- | ------------------------------------ |
| A coral or mint **mark** with no text (level mark, progress fill, dots) | `coral` / `mint`                     |
| **White text** on coral — the primary button                            | `coralInk` (white on it **5.89**)    |
| **White text** on mint — the success toast                              | `mintInk` (white on it **5.84**)     |
| **Dark text** on a coral fill — the _me_ avatar's initials              | `ink` on `coral` (**4.50**)          |
| Coral or mint **text on its own soft**                                  | `coralInk` (5.11) / `mintInk` (5.08) |

Never white on `coral`. Never white on `mint`. Never `mint` as a text colour on `mintSoft`.

## 2.3 Sport identity

| Sport     | Token             | Resolves to |
| --------- | ----------------- | ----------- |
| Padel     | `sport.padel`     | `coral`     |
| Tennis    | `sport.tennis`    | `mint`      |
| Squash    | `sport.squash`    | `night2`    |
| Badminton | `sport.badminton` | `amber`     |

Sport colours **reuse the semantic palette rather than extending it** — four more hues
would make every screen carrying a sport dot noisier, and **the dot is always accompanied
by the sport name in text**, so the colour carries recognition rather than meaning.

The consequence to be aware of: a padel dot and a hot tag are the same hue. They are
never adjacent in a way that could confuse. **A fifth sport forces a real decision.**

**That premise has been tested, not merely asserted.** It is falsifiable — it fails the
moment a sport hue is drawn with no sport name on screen — so it was checked against every
site a sport hue is drawn at in Play: the **sport chips** (the name is the chip), the
**sport tags on the player record** (name adjacent), and the **court gradient** (the court
screen carries the sport chip row). There is no surface where the colour carries the sport
alone. A new surface that draws a sport hue with no name beside it reopens this as surely
as a fifth sport does.

## 2.4 Band colours — the level bar

Four bands, each with three values. Not one value with opacity applied: the bar needs a
tint for a large fill, a deep for a small one, and an **ink** that is legible as text.

| Band        | Drawing range | `tint` (bar fill) | `deep` (bar, current) | `ink` (text, card rail) |
| ----------- | ------------- | ----------------- | --------------------- | ----------------------- |
| New         | 1,00–1,55     | `#9AA8AD`         | `#7E8C92`             | `#657075`               |
| Developing  | 1,55–2,65     | `#7FB3CC`         | `#4E8FAE`             | `#40758F`               |
| Established | 2,65–3,85     | `#6FC5A8`         | `#3FA184`             | `#307A64`               |
| Advanced    | 3,85–5,00     | `#F0A08A`         | `#D9714F`             | `#A9583E`               |

Every `ink` clears **4.5:1 on paper** (4.51–4.59) and **5:1 for white on it**. The
prototype drew band names in the deep values, which are 2.83–3.20 on paper — **below AA
for text**, and the audit did not catch it.

> **Drawing ranges are contiguous; the model's are not** (1,0–1,5 / 1,6–2,6 / 2,7–3,8 /
> 3,9–5,0). The bar draws the contiguous values so there are no gaps in the graphic; **any
> card that prints a range prints the model's `bandLo`/`bandHi`, never the drawing
> values.** These are two different numbers and confusing them is a correctness bug, not
> a styling one.

## 2.5 Contrast — computed

| Pair                                                      | Ratio     | WCAG                                |
| --------------------------------------------------------- | --------- | ----------------------------------- |
| ink on paper                                              | 15.65     | AAA                                 |
| ink on surface                                            | 17.50     | AAA                                 |
| white on night                                            | 13.29     | AAA                                 |
| ink on volt                                               | 13.96     | AAA                                 |
| white + `textOnMedia` on the squash court ground          | 13.03     | AAA                                 |
| white + `textOnMedia` on the padel court ground           | 12.87     | AAA                                 |
| white + `textOnMedia` on the badminton court ground       | 12.80     | AAA                                 |
| white + `textOnMedia` on the tennis court ground          | 12.29     | AAA                                 |
| volt on night                                             | 10.60     | AAA                                 |
| white on night2 / info                                    | 9.86      | AAA                                 |
| info on infoSoft                                          | 8.63      | AAA                                 |
| white on dark-card `tiny` (white @ .68)                   | 6.97      | AAA                                 |
| white on red                                              | 5.90      | AA                                  |
| white on coralInk                                         | 5.89      | AA                                  |
| white on mintInk                                          | 5.84      | AA                                  |
| white on amber                                            | 5.70      | AA                                  |
| muted on surface                                          | 5.40      | AA                                  |
| white + `textOnMedia` on a photograph, under `photoScrim` | 5.24      | AA                                  |
| coralInk on coralSoft                                     | 5.11      | AA                                  |
| mintInk on mintSoft                                       | 5.08      | AA                                  |
| red on redSoft                                            | 5.06      | AA                                  |
| amber on amberSoft                                        | 5.04      | AA                                  |
| white on band ink (all four)                              | 5.05–5.13 | AA                                  |
| muted on paper                                            | 4.83      | AA                                  |
| white on dark-card `eyebrow` (white @ .52)                | 4.74      | AA                                  |
| white + `textOnMedia` on a poster hue's light stop        | 4.60–4.65 | AA                                  |
| band ink on paper (all four)                              | 4.51–4.59 | AA                                  |
| muted on line2                                            | 4.62      | AA                                  |
| muted on paper2                                           | 4.49      | AA — used at 11pt+ only             |
| **ink on coral**                                          | **4.50**  | AA — the only dark-on-coral pairing |
| coral on paper (marks: level mark, progress fill)         | 3.48      | ≥3:1, meets **1.4.11**              |
| mint on surface (mint-bordered fills)                     | 4.07      | ≥3:1, meets **1.4.11**              |
| `ink` on a poster hue's dark stop                         | 3.09–3.12 | ≥3:1, meets **1.4.11**              |

Deliberately absent: _white on coral_ (3.89) and _white on mint_ (4.07) — see Rule C.

### The court ground — the one rule for text over a generated fill

Every other pair above is a **fixed** pair. The court is not: its ground is drawn from the
selected sport's hue, so the ratio behind a white label would depend on which sport a player
picked, and no fixed pair can state it. **The scrim is pinned at `.93`** (`courtScrim`, the
`night` colour at 93% — the dim matches the palette exactly as [9.1](#91-bottom-sheet)'s
does), which is what makes the four rows above finite: the hue is at most **7%** of the
ground, so the dark end of the gradient is `night` whatever the sport and the light end is
one of four known composites. Those four are the **worst** case, and they are the rows.

- **Every label over the court carries `textOnMedia`** — the seat labels _and_ the side
  labels. The ratios above are the ground's light end and a label can sit anywhere on the
  ramp; the prototype gave the shadow to the seats only, and the side labels are the
  lower-contrast of the two. **The ratios are white alone.** A text shadow is not scoreable
  by WCAG, so it sits on top of a pairing that already clears rather than counting toward
  one — which is why it is named in the rows and absent from the arithmetic.
- **The side labels stay at white `.6`.** At the pinned scrim that is **5.46** against the
  worst of the four — it already clears AA, so it is not raised. Left unrecorded this is a
  value the next reader changes back.
- The four ratios are **derived, never typed**:
  [`textOnMedia.test.ts`](../src/shared/ui/textOnMedia.test.ts) computes them from
  `theme.sport` and `theme.color.courtScrim` and fails if either moves.

### The generated poster — the second generated fill, and the first with a figure on it

The poster is the other fill nobody chose a colour for, and it is bounded by a different
mechanism: not a scrim, but a **closed set**. Its hue is one of the sixteen in `POSTER_HUES`
and its ground is a two-stop gradient on that hue, so the ratios are sixteen and not
unbounded — and because the set is designed at **one lightness per stop**, those sixteen
collapse to the two rows above.

- **Two requirements bind the pair from opposite sides.** White text over a poster — a level,
  a Sport label, a shield — needs 4.5:1 against the **light** stop, which is its worst case.
  The `ink` figure is a graphical object and not text, so 4.5 does not apply to it; it needs
  3:1 against the **dark** stop, which is its worst case. A hue that cannot satisfy both is
  dropped, and the set is sixteen **after** that dropping, not before
  ([6.9](#69-the-photo-tile-and-picker)).
- **Every label over a poster carries `textOnMedia`**, for the court's reason: the row above
  is the ground's light end and a label can sit anywhere on the ramp. **The ratio is white
  alone**, exactly as the court's four are — a text shadow is not scoreable by WCAG, so it is
  named in the row and absent from the arithmetic.
- The two ratios are **derived, never typed**:
  [`posterHues.test.ts`](../src/shared/ui/posterHues.test.ts) computes them from
  `POSTER_HUES` and fails if a hue moves, along with the 25° and 10° bounds.
- **The ramp is narrow, and that is the price of the two bounds.** They confine the whole
  ground to one band of luminance, so the light stop is at most 1,23× the dark one. A deeper
  gradient is not a tuning; it is one of the two ratios.

### A player's photograph — the third generated fill, and the one nobody generated

The competitive candidate card's **photo panel** prints a Level and a Sport over the player's
own photograph ([#309](https://github.com/Raketa02/Raketa/issues/309)). The court's ground is
at least drawn by this app; a photograph is drawn by nobody, and the set of grounds behind a
white label on one is not merely large but **unknowable** — a white wall, a floodlit court at
noon, a silhouette.

The same instrument closes it, and closes it harder. **`photoScrim` is pinned at `.70`** (the
`night` colour at 70%, exactly as the other two scrims are the `night` colour), and an
unknowable set collapses to its **worst case**: for white text that is the brightest ground
there can be, which is pure white. One composite, one ratio, and every real photograph is
darker somewhere and never lighter anywhere.

- **The floor is `.65` and the pin is above it.** At `.65` a white photograph gives **4.51** —
  a published figure with nothing left in it, and the next tuning of anything takes it under.
  Both halves are computed: the floor is derived and the pin is asserted to clear it.
- **A flat pass, never a gradient.** A gradient would put the label somewhere on a ramp and
  hand back the unbounded set the pin exists to close — the worst case would depend on where
  the text happened to sit, which is not a thing a test can hold.
- **The panel is drawn identically over the generated poster**, which is why the table above
  gains **one** row and not thirty-three: all thirty-two poster stops are darker than white, so
  they clear the same bound by construction, and
  [`textOnMedia.test.ts`](../src/shared/ui/textOnMedia.test.ts) proves it over every one of
  them rather than sampling.
- **Both labels carry `textOnMedia`**, for the court's reason: the ratio is the ground's
  brightest case, and a label can sit anywhere on a photograph.
- The ratio is **derived, never typed** — same file, same formula as the court's four and the
  poster's two.

**The scrim is lighter than the court's `.93` on purpose.** The court's ground carries no
information; a photograph is a person. `.70` is the least dim that clears AA with a margin, and
the panel's whole premise is that it can afford to be: _in this product your rating is your
face, and the photograph is scenery._

---

# Part 3 — Typography

## 3.1 Families

**Archivo** for everything, **IBM Plex Mono** for numbers. Two families.

Loaded with `expo-font` from `@expo-google-fonts/archivo` and
`@expo-google-fonts/ibm-plex-mono`, awaited in the root layout before the splash screen
hides — **a font that arrives late reflows every number on screen**.

## 3.2 Weights are family names, not numbers

**`fontWeight` is ignored on Android when a custom `fontFamily` is set.** Weight is
selected by loading a differently-named family. This is the single most common way a
React Native app silently loses its typography on one platform.

| Weight | Sans family            | Mono family               |
| ------ | ---------------------- | ------------------------- |
| 400    | `Archivo_400Regular`   | `IBMPlexMono_400Regular`  |
| 500    | `Archivo_500Medium`    | `IBMPlexMono_500Medium`   |
| 600    | `Archivo_600SemiBold`  | `IBMPlexMono_600SemiBold` |
| 700    | `Archivo_700Bold`      | —                         |
| 800    | `Archivo_800ExtraBold` | —                         |

The prototype's `650` (the question text) maps to **700**. Never write a numeric
`fontWeight` alongside a custom family.

**Mono stops at 600, and the dash in that column is the specification.**
`src/shared/lib/bootstrap/fonts.ts` loads IBM Plex Mono at 400 / 500 / 600 and nothing else,
so a display role asking for mono 700 gets **synthetic bolding** — the browser-side bug the
prototype audit found in `.num` at 800, arriving on Android instead. [3.3](#33-the-type-roles)
is written to this table, not the other way round: the display roles are **600**, and mono
700 is not loaded because nothing has ever rendered it and a weight is a bundle cost.

## 3.3 The type roles

There is no modular ratio — sizes are chosen per role. These are the roles; a size outside
them is a one-off that needs justifying.

| Role          | Size | Weight | Family | Purpose                                      |
| ------------- | ---- | ------ | ------ | -------------------------------------------- |
| `h1`          | 19   | 700    | sans   | Screen title                                 |
| `h2`          | 15   | 700    | sans   | Card and section title                       |
| `question`    | 15   | 700    | sans   | The onboarding question itself               |
| `cardTitle`   | 13   | 700    | sans   | Card title                                   |
| `inlineTitle` | 12.5 | 600    | sans   | The most common inline title                 |
| `btn`         | 12   | 700    | sans   | Button label                                 |
| `rlLabel`     | 11.5 | 400    | sans   | Row label                                    |
| `rlValue`     | 11.5 | 600    | sans   | Row value                                    |
| `tiny`        | 11   | 400    | sans   | Secondary text everywhere                    |
| `flab`        | 10.5 | 700    | sans   | **Form label** — uppercase, `night`          |
| `chip`        | 10.5 | 600    | sans   | Chip label                                   |
| `seg`         | 10.5 | 700    | sans   | Segment label ([6.3](#63-segmented-control)) |
| `eyebrow`     | 9.5  | 700    | sans   | Uppercase section label, `muted`             |
| `tag`         | 9.5  | 700    | sans   | Pill text                                    |

**Display numbers** — always mono, tracking −0.035em, **weight 600** — and **500** at
`numS` and `numXS`, which are inline figures inside running text rather than display ones:

| Role         | Size | Where                                        |
| ------------ | ---- | -------------------------------------------- |
| `levelHero`  | 40   | The estimated level on the onboarding result |
| `levelLarge` | 26   | Level on comparison cards                    |
| `numXL`      | 22   | Panel and summary numbers                    |
| `numL`       | 19   | Panel numbers                                |
| `numM`       | 17   | Row numbers                                  |
| `numS`       | 14   | Inline numbers                               |
| `numXS`      | 13   | Dense inline numbers                         |

Consolidated from the prototype: `20 → 19`, `13.5 → 13`.

### Why `seg` exists separately from `chip` and `flab`

Three roles now sit at 10.5, and the pair either side of `seg` is why it is not one of them.
It is `chip`'s size at `flab`'s weight and it takes neither's other property:

- **`chip`** — 10.5, 600. A **filter**, and its selected state is a fill inversion carrying
  the label into `surface`, so the weight is doing no work.
- **`flab`** — 10.5, 700, `+.09em`, uppercase. Labels **a control you are about to operate**,
  and the tracking is what makes an uppercase run legible.
- **`seg`** — 10.5, 700, no tracking, sentence case. Names **a view you are switching to**.

6.3 stated the value from the day it was written and nothing used it; the role arrives with
Play's segment, which is the first screen that needed one.

### Why `flab` exists separately from `eyebrow`

They look almost identical and mean different things.

- **`eyebrow`** — 9.5, `+.15em`, `muted`. Labels **a region you are reading**.
- **`flab`** — 10.5, `+.09em`, `night`. Labels **a control you are about to operate**.

A full point larger, tighter-tracked, and near-black, because _a form label has to be
findable at a glance and the muted eyebrow was not_. Keep them distinct.

## 3.4 Tracking, converted to points

RN `letterSpacing` is in points. Every em value pre-multiplied:

| Role                   | em     | **points** |
| ---------------------- | ------ | ---------- |
| `h1` (19)              | −0.030 | **−0.57**  |
| `h2` / `question` (15) | −0.025 | **−0.38**  |
| `flab` (10.5)          | +0.090 | **+0.95**  |
| `eyebrow` (9.5)        | +0.150 | **+1.43**  |
| `levelHero` (40)       | −0.035 | **−1.40**  |
| `levelLarge` (26)      | −0.035 | **−0.91**  |
| `numXL` (22)           | −0.035 | **−0.77**  |
| `numL` (19)            | −0.035 | **−0.67**  |
| `numM` (17)            | −0.035 | **−0.60**  |
| `numS` (14)            | −0.035 | **−0.49**  |
| `numXS` (13)           | −0.035 | **−0.46**  |

**Every heading carries negative tracking, tightening as the size grows.** Archivo at 19pt
with default tracking reads loose; at −0.57pt it reads set. **Body text is never tracked.**

## 3.5 Line height, in points

RN `lineHeight` is in points, not a multiplier.

| Role                            | Line height                                                 |
| ------------------------------- | ----------------------------------------------------------- |
| `tiny` and all explanatory copy | **16** (11 × 1.45)                                          |
| `h1`                            | 24                                                          |
| `h2` / `question`               | 20                                                          |
| `cardTitle` / `inlineTitle`     | 17                                                          |
| `rlLabel` / `rlValue`           | 16                                                          |
| `eyebrow` / `tag` / `flab`      | 12                                                          |
| Display numbers                 | **equal to the size** — a 40pt level must not grow its card |

## 3.6 Tabular figures

Every display number and every number in a list or table sets
`fontVariant: ['tabular-nums']`. On iOS this is honoured directly; IBM Plex Mono is
already monospaced, which is what makes the rule hold on Android too. **Mono is not
optional for numbers** — it is the mechanism, not a style choice.

---

# Part 4 — Space, radius and elevation

## 4.1 Spacing — a 3pt grid

The prototype used 5, 6, 7, 9, 10, 11, 12, 13, 14 and 15. **Every one of those is within
1pt of a multiple of 3** — the grid was already there and unnamed. It is now the scale:

```
3   6   9   12   15   18   24   30
```

Mapping: 5→6, 7→6, 10→9, 11→12, 13→12, 14→15. Maximum shift 1pt.

### The two numbers to remember

```
9pt    the gap between stacked cards, and the hairline's top margin
15pt   the horizontal page gutter — content width is screen width − 30
```

Everything else follows. A value outside the grid is a bug.

## 4.2 Radius

| Radius              | Applied to                                         |
| ------------------- | -------------------------------------------------- |
| `pill` (height ÷ 2) | The chip — the only true pill                      |
| 22 (top corners)    | Bottom sheet                                       |
| 18                  | The deck card — **not a card**, see below          |
| 15                  | Dark card                                          |
| 13                  | Card, popover                                      |
| 12                  | Toast                                              |
| 10                  | Button, note, segmented control, availability cell |
| 9                   | Info button, the court ([7.12](#712-the-court))    |
| 8                   | Sport dot backing, the balance bar                 |
| 7                   | The fit pill ([7.10](#710-the-fit-pill))           |
| 6                   | Tag, sport dot                                     |

**The pattern: the bigger the surface, the rounder.** A dark card is 15 where a light one
is 13 — the darker fill makes the corner read tighter at the same radius.

**The court reads the rule the other way, and is the one thing that does.** A card at 13 is a
surface a finger rests on; a court is a **picture inside one**, and a picture wants the
tighter corner however large its box — so `radius.court` is 9 at a 74pt mini and at a
full-width build alike. It is named for its role beside the other 9 rather than borrowing
`avatar`, because a court is not a face and the next reader must not be able to change one by
changing the other.

**`deckCard: 18` is not a card at 18.** The deck card animates in, and translates and
rotates out under the thumb: it is a **transient object being manipulated**, which is why it
is also the one paper surface that casts a shadow ([4.3](#43-elevation)). Naming it as a
card and then granting it two exceptions would have been the same change with the rule
quietly weakened. **The candidate card in the pool stays a card** — 13, no shadow — because
it does not float, and that ends a condition where two candidate surfaces were one shape at
two radii.

## 4.3 Elevation

Five shadows exist, all for things that genuinely float. **Cards never have one** — depth on
paper comes from the surface change and the 1pt `line` border, and the deck card is here
because [4.2](#42-radius) says it is not a card.

RN cannot express CSS spread, so these are calibrated approximations, with `elevation`
for Android:

| Element         | iOS                                                                | Android         |
| --------------- | ------------------------------------------------------------------ | --------------- |
| **Sheet**       | `shadowColor #0A2028`, offset `{0,−8}`, opacity `.18`, radius `20` | `elevation: 16` |
| **Popover**     | `shadowColor #0B1F2A`, offset `{0,8}`, opacity `.24`, radius `15`  | `elevation: 12` |
| **Toast**       | `shadowColor #000`, offset `{0,6}`, opacity `.24`, radius `14`     | `elevation: 10` |
| **Deck card**   | `shadowColor #0B2B33`, offset `{0,7}`, opacity `.12`, radius `20`  | `elevation: 8`  |
| **⚡Play disc** | `shadowColor coral`, offset `{0,3}`, opacity `.40`, radius `7`     | `elevation: 6`  |

The deck card is the **faintest** of the five, and the calibration is why: at
`0 18px 40px -26px` it carries the largest negative spread of any shadow in the system — 26
of 40 blur — so the offset comes down hardest and the opacity with it. It floats least, and
its `elevation` says so. It is not the _tightest_: at radius 20 its blur ties the sheet's,
because a 40px blur halves to 20 whatever is subtracted from its spread.

### The fifth is a colour, and it is calibrated, not copied

The ⚡Play disc ([10.2](#102-the-tab-bar)) is the only tinted shadow in the app: it is the one
thing in the bottom chrome that floats, and it floats in its own colour rather than in a dim.
The prototype's rule is `0 6px 14px -6px rgba(232,72,43,.7)` and **the negative spread is the
whole of the calibration** — 6 of the 14 blur never reach the paper, and RN has no way to say
so:

| CSS          | Here     | Why                                            |
| ------------ | -------- | ---------------------------------------------- |
| blur `14`    | radius 7 | the halving the other four already do          |
| offset `6`   | 3        | the spread eats the drop: 6 × (1 − 6/14) = 3,4 |
| opacity `.7` | `.40`    | and the same fraction of the ink               |

**On Android it is not a colour.** `elevation` draws the platform's own black shadow and RN
exposes no way to tint it, so the disc is raised on both platforms and glows on one. Its 6
seats it under the deck card, which is right: the bar is chrome, and every overlay passes over
it.

### One text shadow, which is not an elevation

`textOnMedia` — `textShadowColor rgba(0,0,0,.6)`, offset `{0,1}`, radius `3` — is a
different RN mechanism and the only one in the app. It belongs to **every label drawn over
a ground nobody picked a colour for**: both of the court's label sets
([2.5](#25-contrast--computed)), the generated poster, and the photo panel's Level and Sport.
It is listed here because a reader looking for a shadow looks here; it is not a fifth floating
thing.

The phone-frame shadow from the prototype does not exist — see [Part 0](#part-0--reading-a-web-prototype-as-a-native-app).

---

# Part 5 — Structural primitives

## 5.1 Card — the workhorse

```
background  surface        border  1pt line
radius      13             padding 12
marginBottom 9
```

**Pressable variant:** pressed → `borderColor: coral`. No lift, no shadow, no scale.

## 5.2 Dark card

```
background  night          color   #fff
radius      15             padding 15
marginBottom 9
```

Children repaint automatically:

- `tiny` → `rgba(255,255,255,.68)` (6.97:1)
- `eyebrow` → `rgba(255,255,255,.52)` (4.74:1)
- hairline → `rgba(255,255,255,.15)`

> **The dark card repaints its children rather than requiring every child to know it is on
> dark.** Elegant until something light sits inside it — which is exactly what happened
> with the info popover in the prototype, forcing three counter-overrides. **In this
> codebase, a popover rendered from inside a dark card renders through the overlay root,
> not as a descendant** — so the repaint never reaches it and the overrides are unnecessary.

Used for: the onboarding result and the done screen — the places the app states a finding
rather than offering a choice — and for **ADR-0094's play-intent declaration**, which is a
choice, and is on this surface because what it writes is a _fact about the player_ kept on
their profile. Its three answers are **full-width [6.1](#61-button) buttons** on the `on-dark`
variant, each with a one-line `gloss` — because a column of three near-synonyms has to say
what choosing one means. See [Part 16](#part-16--amendments-after-locking).

## 5.3 Hairline — the internal divider

```
borderTopWidth 1   borderTopColor line2   marginTop 9   paddingTop 9
```

One rule, everywhere a card needs a second section. `line2` rather than `line` **so it
reads as a fold inside one object rather than a boundary between two.**

## 5.4 Note — the message block

```
padding 12 (v) 12 (h)      borderWidth 1
borderLeftWidth 3          radius 10
marginBottom 9
title: 11.5 / 700, marginBottom 3
```

A card with a **3pt left bar carrying the semantic**. Five variants:

| Variant  | Left bar | Background  | Border      |
| -------- | -------- | ----------- | ----------- |
| _(base)_ | `night`  | `surface`   | `line`      |
| mint     | `mint`   | `mintSoft`  | `mintLine`  |
| coral    | `coral`  | `coralSoft` | `coralLine` |
| amber    | `amber`  | `amberSoft` | `amberLine` |
| info     | `info`   | `infoSoft`  | `infoLine`  |

**The info note is the only one with a glyph** — a serif italic _i_, white on an `info`
circle, 14 × 14, radius 7. A serif mark inside a sans-serif app, **because the information
mark is a symbol, not text, and the serif form is the one people recognise.** In RN this
is a `<Text>` with an explicit serif family (`Georgia` on iOS, `serif` on Android), not
the app font.

Notes carry the reasoning. They are the one place a paragraph is acceptable.

## 5.5 Row — the key-value line

```
flexDirection row   alignItems center   justifyContent space-between
gap 9               paddingVertical 6   fontSize 11.5
```

Consecutive rows are separated by a 1pt `line2` top border, **applied from the second row
onward** — so the first row has no rule above it and the last none below, automatically.
In RN: `index > 0 && styles.divider`, never a `borderBottom` on every row.

Used for every key-value list: the result screen's figures, the evidence trail's rows.

---

# Part 6 — Controls

## 6.1 Button

```
height 34   paddingHorizontal 15   radius 10   label 12 / 700
```

| Variant   | Fill                    | Label  | Pressed fill                 |
| --------- | ----------------------- | ------ | ---------------------------- |
| primary   | `coralInk`              | `#fff` | `coral`                      |
| dark      | `night`                 | `#fff` | `night2`                     |
| secondary | `surface` + 1pt `line`  | `ink`  | `line2`                      |
| settled   | `mintInk`               | `#fff` | `mint`                       |
| volt      | `volt`                  | `ink`  | `opacity: .7`                |
| on-dark   | `rgba(255,255,255,.17)` | `#fff` | `rgba(255,255,255,.26)`      |
| disabled  | —                       | —      | `opacity: .4`, not pressable |

Heights in practice: **32** (tertiary in a card), **34** (default), **40** (screen action),
**42** (the primary action on a result screen). All clear the touch minimum.

> Per Rule C the primary button is filled `coralInk` and **brightens to `coral` when
> pressed** — the inverse of the prototype, which put white 12pt text on `coral` (3.89:1).
> Coral still reads as the accent; the label is now legible.

> **`volt` is the one variant that does not have the others' shape.** Every other filled
> variant is _a fill, a white-or-`ink` label, and a second fill under the finger_. Volt is a
> **fill anywhere and a stroke only on dark** ([2.2](#22-accent-and-semantics)): as a
> foreground on paper it is invisible, but `ink` on it is 13.96:1, so filling with it inverts
> exactly the problem a volt stroke has. Its label is `ink` and **never white**. Its press is
> **`opacity: .7`** ([6.6](#66-press-states)) rather than a second fill, because volt is
> already the brightest value in the palette and has no darker companion — inventing a
> seventh hex to satisfy _the variant's pressed fill_ would be adding a colour to describe a
> press. It carries _they want you to play_, which is a fact about somebody else; `primary`
> stays the action.

> **A button may carry a `gloss` — one line of `tiny` under the label**, for a column of
> answers whose labels are near-synonyms and do not say what choosing one means. A glossed
> button **aligns both lines to the start** instead of centring them, and grows past its
> height row exactly as a wrapped label does (`minHeight`, never `height`). The gloss **adds
> no colour** ([15.2](#152-adding-a-colour)): hierarchy is the type role — `tiny` under the
> 12/700 label — and the ink is the label's own except on `on-dark`, which takes
> [5.2](#52-dark-card)'s `rgba(255,255,255,.68)`, and on `secondary`, which takes `muted`.
> It is **not** part of the accessible name: a glossed button is one element named by its
> caller, and the gloss is the sighted half of what that name already says.

> **`settled` is the button whose state is the message** — the thing it asked for has been
> obtained, and pressing it again would only obtain it a second time. Mint is this system's
> word for _settled, safe, covered_ ([1.3](#13-semantic-colour)), so it is the one colour
> that could carry it; `mintInk` rather than `mint` because Rule C forbids white on `mint`
> at 4.07:1, and it brightens to `mint` on press exactly as `primary` brightens to `coral`.
> **The fill is never the whole fact:** a control that turns green must change its words
> too ([Part 13](#part-13--accessibility) — never colour alone), and it stays a control
> rather than becoming a label, because the act it offers is still available.

## 6.2 Chip — the filter pill

```
height 27   paddingHorizontal 12   radius height/2   1pt line
background surface   label 10.5 / 600
selected: background ink, label #fff, border ink
small:    height 25, paddingHorizontal 9, label 10
```

**The only true pill in the app.** Selected is **ink-filled, not coral** — coral is
reserved for actions, and a selected filter is a state.

Optional 6pt square dot before the label, for a sport colour — **[6.4](#64-tag--the-status-pill)'s
dot, and the same square rather than a second one.** It is decoration and is hidden from
assistive technology, because the label beside it always says which sport; that is the
condition [2.3](#23-sport-identity) attaches to every surface drawing a sport hue. The dot
**does not invert with the pill**: a sport's colour is an identity rather than a state, and a
selected padel chip is still coral-dotted on `ink`.

## 6.3 Segmented control

```
track     background line2   radius 10   padding 3   gap 3
segment   flex 1  paddingVertical 6  radius 8  label 10.5 / 700  muted
selected  background surface   label ink
```

**Inset track, raised selection — the inverse of the chip.** For a two- or three-way view
switch within one screen. Nothing uses it today; it is specified so the first screen that
needs one does not invent a second shape.

## 6.4 Tag — the status pill

```
paddingVertical 3   paddingHorizontal 6   radius 6   label 9.5 / 700
background line2    label muted
```

| Variant     | Background              | Label      |
| ----------- | ----------------------- | ---------- |
| _(default)_ | `line2`                 | `muted`    |
| ok          | `mintSoft`              | `mintInk`  |
| hot         | `coralSoft`             | `coralInk` |
| warn        | `amberSoft`             | `amber`    |
| bad         | `redSoft`               | `red`      |
| volt        | `volt`                  | `ink`      |
| on-dark     | `rgba(255,255,255,.14)` | `#fff`     |

**`volt` is the one variant whose background is a base colour rather than a soft.** Volt has
no soft and needs none: it is _a fill anywhere and a stroke only on dark_
([2.2](#22-accent-and-semantics)), and `ink` on it is **13.96:1** — already in
[2.5](#25-contrast--computed), so its Rule C pair is computed rather than eyeballed. A
`voltSoft` invented to give this tag the shape of the other six is exactly what
[15.2](#152-adding-a-colour) forbids.

It carries Play's _they want you_ signal, and it is **why that signal is a tag at all**: the
2026-08-31 amendment refused the volt strokes it had been drawn with, including a border on the
interest card, and concluded that _"the card's emphasis becoming a tag is what
[Part 13](#part-13--accessibility) prefers anyway — a border carries no word and this signal
has one."_

Optional 6pt square dot for a sport colour. A long state tag **truncates with an ellipsis
rather than breaking the row** (`numberOfLines={1}`).

**Tags are never pressable.** A pressable pill is a chip.

## 6.5 Touch targets

**Nothing tappable may have a reachable area smaller than 44 × 44pt.** The prototype's
controls are visually smaller than that, which is correct — the _visual_ stays, the
_target_ grows:

| Control      | Visual height | `hitSlop`                                      |
| ------------ | ------------- | ---------------------------------------------- |
| Chip         | 27            | `{ top: 9, bottom: 9 }`                        |
| Small chip   | 25            | `{ top: 10, bottom: 10 }`                      |
| Time square  | 32            | `{ top: 6, bottom: 6 }`                        |
| Info button  | 20            | `{ top: 12, bottom: 12, left: 12, right: 12 }` |
| Segment      | 25            | `{ top: 9, bottom: 9 }`                        |
| Button (34+) | 34            | `{ top: 5, bottom: 5 }`                        |

Horizontal slop is bounded by the neighbour: in a `sqrow` with a 6pt gap, horizontal slop
is at most 3 per side or targets overlap and the wrong square is selected.

Onboarding's second part adds four targets, and three of them are built to the minimum
rather than granted it:

| Control                                                     | Visual                      | `hitSlop`                                        |
| ----------------------------------------------------------- | --------------------------- | ------------------------------------------------ |
| Availability cell ([6.8](#68-the-availability-grid))        | 44 tall, ≥ 59,5 wide        | none — the geometry _is_ the target              |
| Photo tile ([6.9](#69-the-photo-tile-and-picker))           | ≥ 90 × 120                  | none                                             |
| Photo remove control ([6.9](#69-the-photo-tile-and-picker)) | 28                          | `{ top: 8, bottom: 8, left: 8, right: 8 }`       |
| Radius slider row ([6.10](#610-the-radius-slider))          | 44 tall, full content width | none — the **row** is the surface, not the thumb |

Sign-up's age question adds a fifth, built the radius slider's way:

| Control                                  | Visual                               | `hitSlop`                                                 |
| ---------------------------------------- | ------------------------------------ | --------------------------------------------------------- |
| Tick box row ([6.11](#611-the-tick-box)) | box 20 × 20, row 44 tall, full width | none — the **row** is the surface, box and label together |

**The availability cell lost 6pt of width to its card and still clears the minimum**, at
59,5 rather than 65,5 ([6.8](#68-the-availability-grid)). The figure is in this table rather
than only in the test because it is the one target here whose margin is now small enough that
a change elsewhere — the card's padding, the gap, the label cap — could spend it.

**A `hitSlop` around the box would have been the wrong answer here**, not merely a second
one. Growing a 20pt square to 44 leaves the sentence beside it inert, so the target stops
where the words start — and the words are what a player reads before deciding. The row is
the control for the same reason the slider's is.

**The photo remove control is the case the neighbour rule would have got wrong.** Its 44pt
square is anchored _inside_ its tile rather than over the tile's corner. Tiles sit 9pt
apart, so a target overhanging the edge could take at most 4,5pt from the gap and would
land at 40,5 — and the 4,5pt it took would be the next tile's. Anchored inside, the whole
square is the tile's own, and what remains of the tile is still four times the minimum.

## 6.6 Press states

Touch has no hover. Every pressable declares its pressed appearance explicitly:

| Element                         | Pressed                                                   |
| ------------------------------- | --------------------------------------------------------- |
| Card                            | `borderColor: coral`                                      |
| Button                          | the variant's pressed fill ([6.1](#61-button))            |
| Chip / segment                  | `opacity: .7`                                             |
| Volt button ([6.1](#61-button)) | `opacity: .7` — it has no darker fill and gets no new one |
| Avatar (press-and-hold to peek) | `scale(.93)`, and while holding a 3pt `coralSoft` ring    |

Onboarding's second part adds five, and one of them takes the card's state rather than the
chip's:

| Element                                                     | Pressed                                                                  |
| ----------------------------------------------------------- | ------------------------------------------------------------------------ |
| Availability cell ([6.8](#68-the-availability-grid))        | `opacity: .7`, over either of its two states                             |
| Photo tile ([6.9](#69-the-photo-tile-and-picker))           | `opacity: .7`                                                            |
| Photo remove control ([6.9](#69-the-photo-tile-and-picker)) | `opacity: .7`                                                            |
| Photo add control ([6.9](#69-the-photo-tile-and-picker))    | `borderColor: coral` — the card's state ([5.1](#51-card--the-workhorse)) |
| Radius slider ([6.10](#610-the-radius-slider))              | **none** — the thumb moving to the finger _is_ the feedback              |

Sign-up's age question adds a sixth, and it takes the availability cell's:

| Element                                  | Pressed                                                      |
| ---------------------------------------- | ------------------------------------------------------------ |
| Tick box row ([6.11](#611-the-tick-box)) | `opacity: .7`, over either of its two states, on the **row** |

The dimming is on the row rather than on the box, because the row is the target: a box that
dimmed while the sentence beside it did not would say the two are separate things, which is
the reading 6.5 already refuses.

**The add control takes the card's press state and the photo tile does not**, though they
are the same rectangle. The add control is a pressable card-shaped surface with a border to
change; a filled tile's border is already carrying whether it is the profile photo
([6.9](#69-the-photo-tile-and-picker)), so borrowing it for a press would have one line say
two things and lose the argument at the moment both are true.

Play's tab bar adds two, and the pair is the same rule twice — **one channel per state**:

| Element                                | Pressed                                                                 |
| -------------------------------------- | ----------------------------------------------------------------------- |
| Tab column ([10.2](#102-the-tab-bar))  | `opacity: .7`, on the **column** — it is the target, and it has no fill |
| ⚡Play disc ([10.2](#102-the-tab-bar)) | `coral` — [6.1](#61-button) `primary`'s pressed fill, arriving free     |

The disc is the one column that does **not** dim, because it already has a second fill and
dimming it as well would put two channels on one press. Its ring is untouched by a press for
the same reason the shadow is: the ring says _you are here_, and a press is not that.

Feedback is immediate — use `Pressable`'s `pressed` state, not a 120ms animation. The
120ms in the prototype is a mouse-hover transition and has no touch equivalent.

---

## 6.8 The availability grid

The player's ordinary week, as seven days by three parts of the day. One cell is one
standing preference, and the grid is the only place time preference is expressed anywhere
in this product.

**6.7 is not being reused, and this is not 6.7 returning under a new number.** That
section held the slot squares — day / time / hour / range squares and their four-state
vocabulary — and it went with the booking grid in the 2026-08-25 reset
([Part 17](#part-17--what-the-reset-removed)). A slot square was _one bookable hour on one
court_, and it needed four states because a court is free, held, taken or yours. A cell
here has **two** states, names no court and no hour, and nothing can be booked from it. (The
mark below is a fact drawn on one of those two, not a third — it presses like every other
cell.)
Section numbers in this document never move, so this is 6.8 and 6.7 stays empty.

```
seven rows of three — days DOWN the page, parts of the day ACROSS
MONDAY FIRST, and the seven run Monday to Sunday
the whole thing on a card, with the footnote inside it

card         surface, radius.card, 1pt line, padding 12
column head  flab / ink, once, above the grid          MORNING · AFTERNOON · EVENING
day label    flab / ink, content-sized, capped at 0.25 x the card's inside, labelGutter 9
cell         flex 1, height 44, radius.availabilityCell, gap 6, NO border
footnote     rlLabel / muted inside the card, above it a 1pt line hairline, minHeight 32
```

**Monday first**, because that is how the week reads here — and the order is the contract's
too: `AvailabilitySlotResource` numbers days 1–7 as ISO weekdays and says the grid is
Monday-first in as many words. The three parts of the day run in the order `DayPart`
declares them, so nothing on this side sorts.

**A cell is the only thing on the grid that is pressable.** Not a day label, not a column
head, not the row or the column they name, and **there is no bulk selection at all** — no
row tap, no column tap, no _weekends_ shortcut. A shortcut is a claim about what players
want that this product has no evidence for, and describing an irregular week is the whole
reason the grid is 21 independent answers rather than three.

**Days are rows because seven columns cannot be reached.** Seven cells at the 44pt minimum
([6.5](#65-touch-targets)) want 308pt; the narrowest phone has 290pt of content
([Part 0.2](#02-what-replaces-the-frame)), and no `hitSlop` closes a deficit against
neighbours 6pt apart. **The widest phone in the population does not close it either**, so
this is a property of seven columns rather than a device to design around. Turned this way
each cell is 44 tall by its own geometry and, with the card's padding taken off and the label
column at its cap, **59,5pt** wide on that same phone — the first control in the app that
reaches the touch minimum in **both** axes without being granted anything.
`profileControlGeometry.test.ts` pins that division, because it is the kind of arithmetic
that holds on the phone an agent tests on and fails on the one a player owns.

**The card takes 24pt off that division and the margin is what is left.** It was 65,5pt of
cell before the grid sat on a surface of its own; it is 59,5 now, still 15,5 clear of the
minimum, and the test states the margin rather than only the bound so the next person adding
padding can see the room they are spending.

The grid does not scroll. The screen does ([10.1](#101-screen-structure)).

### Cell states

| State          | Fill     | Border | Content                                        |
| -------------- | -------- | ------ | ---------------------------------------------- |
| **unselected** | `paper2` | none   | empty                                          |
| **selected**   | `mint`   | none   | a 12 × 12 tick, 2pt stroke, `surface` — 4,07:1 |
| **pressed**    | —        | —      | `opacity: .7`, over either of those            |

**There is no disabled cell and no fourth state.** Every cell toggles, always, in both
directions: the grid has no floor, no ceiling, and no rule that could close one off. A
greyed cell would be the screen claiming a constraint the domain does not have.

**The selected state is a fill _and_ a tick, and the tick is the half that matters.** The
fill goes `paper2` → `mint`: 3,39:1, and a relative luminance of 0,824 against 0,208, which
is what [Part 13](#part-13--accessibility) asks of a non-text graphical object and what a
reader who sees no hue at all still reads as a dark square in a field of pale ones. But a cell
is a bare rectangle with nothing else in it, and 21 rectangles differing only in lightness is
a texture. The tick is the shape Part 13 asks for, and it is what makes a ticked week readable
as a pattern rather than as a stain. Drawn in `react-native-svg` with a round cap and join: at
2pt, butt caps make a tick read as two bars meeting at a corner.

**The tick is `surface` on `mint` at 4,07:1, and that does not cross Rule C.**
[Rule C](#22-accent-and-semantics) refuses white **type** on mint; a 2pt stroke is a
graphical object and clears the 3:1 that binds one. The distinction is the same one
[7.11](#711-the-balance-bar) already relies on.

**`mint` and not `ink`, which reverses an earlier decision here.** It was `ink` because
[Part 12](#part-12--screens)'s copy for the onboarding step says the grid is _a preference and
not a promise_, and painting it mint would have the colour contradict the sentence beside it.
That reading stands for a **status**, and this is not one: the cell says _I could play then_,
and nothing anywhere reads a green square as a booking. What decided it is the drawing — 21
`ink` rectangles with a 1pt border each, on a card, read as holes punched through the card
rather than as answers, and two softer fills at a legal ratio do not.

**No cell border.** The card bounds the grid ([2.1](#21-surfaces-and-structure): `line`
_bounds a thing_), and a line drawn around each of 21 adjacent squares inside one card is a
fold repeated 21 times inside one thing, which is what `line2` means and neither is what this
is.

### The mark a search leaves on a cell

One cell may carry a **third fact**, and a fact is not a state: _this search added this
slot, and you did not tick it_. A times rung on the pool widens the searcher's own grid by
one cell for **one** search
([ADR-0099](../../docs/adr/0099-relaxation-offers-the-searchers-own-asks.md)), and the week
the player filled in disagrees with the search that ran until the grid says which cell that
was ([#283](https://github.com/Raketa02/Raketa/issues/283)).

| Fact                      | Fill     | Mark                           |
| ------------------------- | -------- | ------------------------------ |
| **added for this search** | `paper2` | a **plus**, in `ink` — 14,57:1 |

**The cell is not filled, and that is the whole of it.** It is not part of the week the
player is asking with — the ask is unchanged and the request carries the same grid it
carried before — so a filled cell would say the opposite of what is true, under a finger
that is about to tick it. Pressing it is an ordinary tick and the mark goes with the press:
from then on the cell is the player's own answer.

**`ink` and not `volt`, though the diff variant's plus is volt.** The two land on different
beds: the diff draws its plus on a filled cell, where volt as a stroke is legal, and this one
sits on `paper2`, where volt is ~1,3:1 and simply not there
([2.2](#22-accent-and-semantics)). It is the same crossed pair at the same size — `Tick.tsx`
draws it twice for the bed, never for the meaning.

### The footnote slot

An `rlLabel` message in `muted` **inside the card**, under a 1pt `line` hairline, at most two
lines long, and **its height is reserved whether or not it has anything in it.** The hairline
is drawn only when there are words to separate; the height is not conditional on either. The
line that appears at zero slots names what an empty week costs; the line that replaces it can
name the count. Neither may move the grid, because the moment a player is most likely to tick
a second cell is immediately after ticking the first, and a grid that jumps upward under a
finger mid-tap selects the wrong cell. `minHeight` is two lines of `rlLabel` (32), which is
the longest either message may run to — a third line is an amendment, not a copy tweak.

**Inside the card rather than under it**, because the sentence is about the grid: a count of
slots floating beneath a bare block of squares belonged to whatever came next on the page as
much as to the week above it.

**The diff variant reserves nothing**, and that is this rule read rather than an exception to
it. What the reservation protects is a cell moving under a finger between two taps, and
nothing on the diff grid is pressable: it cannot gain a footnote, cannot lose one, and 44pt of
empty card is 44pt `SH.saveav` does not have — that sheet draws this grid above two buttons
and stops at 88 % of the screen ([9.1](#91-bottom-sheet)).

### The empty state

**An empty grid is a complete answer and is drawn as one:** 21 unselected cells, the
footnote carrying the consequence, and the screen's forward control enabled. Nothing is
greyed, nothing is pre-seeded, and no cell is ticked on the player's behalf — a pre-seeded
slot is a claim the player never made that silently becomes a matchmaking input. Blank
means _no preference_ and never _leave me out_.

### Accessibility

Each cell is a `checkbox` with `accessibilityState={{ checked }}`, and its label names
**its day and its part of the day** — `"Monday morning"` — because a screen reader gets no
help from the row it is in or the column it is under. The column heads are therefore
decoration to assistive technology and are hidden from it (`accessibilityElementsHidden`
/ `importantForAccessibility="no-hide-descendants"`); without that, every cell is announced
twice.

`checkbox` rather than `button` because the state is the point and the role is what carries
it: 21 buttons announce 21 identical actions, where 21 checkboxes announce 21 answers.

Dynamic Type grows the day labels, and `labelMaxRatio` is what stops them starving the
cells. At the cap the three cells still share 178,5pt inside the card on the narrowest phone.
The cells contain no text, so nothing inside one scales, and `allowFontScaling={false}` never
arises ([Part 13](#part-13--accessibility)).

### The diff variant

`SH.saveav` draws the same week with a **third fact** on each cell: the slots this search
added, and the ones it dropped. `the-words.md` §20.7 calls it _"a different control with a
third fact … not interactive"_ — which describes a second accessibility tree and **not a
second file**. It is this seven-by-three geometry exactly, and a second copy of that grid is
the drift `Tick` was extracted to prevent.

> **One component, two modes, two accessibility trees.**

| State              | Cell     | Mark                   |
| ------------------ | -------- | ---------------------- |
| **on**, unchanged  | `mint`   | the tick               |
| **added**          | `mint`   | a **plus**, in `volt`  |
| **dropped**        | `paper2` | a **dash**, in `muted` |
| **off**, unchanged | `paper2` | —                      |

**The prototype's scheme is replaced by the arrival rather than after it**, because it is a
[Part 13](#part-13--accessibility) violation twice over. New drew a **volt ring** and dropped
drew **45 % opacity** — colour as the only signal, on a sheet whose own body copy named the
colour as the mechanism (_"Green rings are new, faded ones you dropped"_, rewritten against
this table by [#277](https://github.com/Raketa02/Raketa/issues/277)) — and a volt ring on
paper is 1,3:1, so half of it was not there at all
([2.2](#22-accent-and-semantics): volt is a fill anywhere and a stroke only on dark).

**Three shapes, from the tick's own family.** One 12 × 12 box, one 2pt round-capped stroke,
and plus-and-minus is the diff idiom every reader already has;
[6.9](#69-the-photo-tile-and-picker)'s add glyph is the same crossed pair at 20 × 20, so
nothing here is a new drawing. The plus is `volt` **on `mint`** at 3,25:1 — tighter than the
10,60 it had on `ink`, and still a fill dark enough for volt to be a stroke on.

**Nothing on it is pressable**, so nothing carries `checked` and nothing offers a state a
reader could try to change. **A cell with nothing to say is hidden** rather than announced
empty: a slot that was off and stayed off tells a listener nothing, and twenty-one of those
between the ones that changed is the double announcement the column heads are hidden to avoid.
The three sentences are §20.7's — `{Day} {part}` · `{Day} {part}, newly added` ·
`{Day} {part}, dropped` — and they are the caller's, like every other word on this grid.

---

## 6.9 The photo tile and picker

Up to three photos of the player on a court, or none. The tile is the unit: it holds a
photo, or it is the control that adds one, or it is the space where a photo would go.

```
three tiles across the content width, ALWAYS three, gap 9

tile        flex 1, aspectRatio 3:4 (portrait), radius 13, 1pt border
foot strip  height 18, full tile width, bottom corners at the tile radius
remove      28pt visual at the top right, INSIDE the tile — 44pt target by hitSlop
add glyph   two crossed 2pt bars, 20 × 20, in muted
```

Radius 13 is the card's ([4.2](#42-radius)): at ≥ 90 × 120 a tile is a card-sized surface,
and the rule is that the bigger the surface the rounder. Portrait rather than square
because the subject is a person standing on a court.

**The row is always three tiles, and that is where the ceiling lives.** A filled tile shows
its photo; the first empty tile is the add control; any empty tile after it is a
placeholder. At three photos there is no add control on screen at all — **the ceiling is a
fact of the layout rather than a disabled button**, which is the same reason
[6.1](#61-button) never draws a pressable-looking control that refuses. A player who picks
more than the remaining slots is refused in words by the step
([Part 12](#part-12--screens)), because a multi-select picker can hand back more than the
row has room for and the layout cannot say so on its own.

**A placeholder is not a second add control, and it is not a surface either — it is not
drawn.** It is empty space of a tile's dimensions with the paper showing through:
borderless, glyphless, not pressable, and hidden from assistive technology. It has no fill
of its own because `line2` is _a fold inside one thing_ ([2.1](#21-surfaces-and-structure))
and a full-tile ground is not a fold, and because the honest statement is that nothing is
there. What the placeholder is for is the row's rhythm — three slots that do not move as
photos arrive — and space does that as well as a rectangle would. There is exactly one add
control, always the leftmost empty slot, so a player never has to work out which plus does
what.

| Tile is           | Fill                                | Border     | Contents                                  |
| ----------------- | ----------------------------------- | ---------- | ----------------------------------------- |
| **a photo**       | the image                           | 1pt `line` | the foot strip, if it has an occupant     |
| **the profile**   | the image                           | 1pt `ink`  | the foot strip, carrying the profile word |
| **the add**       | `paper2`                            | 1pt `line` | the crossed glyph and a `tag`-sized word  |
| **a placeholder** | not drawn — the paper shows through | none       | nothing                                   |

Every tile that can be pressed carries a 1pt border, and promoting one changes only that
border's colour — so a photo never resizes by a point when it becomes the profile photo. The
placeholder is the one tile without a border, because it is the one tile that is not an
object: a bare `line2` field reads as the space a photo would occupy rather than as a thing
sitting in it. The add control sits on
`paper2` because `paper2` is the recessed surface ([2.1](#21-surfaces-and-structure)): it is
a hole you put something into, not a card you press.

### The foot strip — one slot, three occupants

The strip is a full-width band at the tile's foot, and **at most one thing is ever in it.**

| Occupant      | Fill    | Carries                                            |
| ------------- | ------- | -------------------------------------------------- |
| **profile**   | `night` | the word, in `type.tag`, `#fff` — 13.29:1          |
| **uploading** | `night` | a 4pt bar inset 6: track `onDarkHair`, fill `#fff` |
| **failed**    | `red`   | the word, in `type.tag`, `#fff` — 5.90:1           |
| _(none)_      | —       | no strip is drawn                                  |

**A settled, non-profile photo carries nothing.** That is the whole reason the strip is one
slot and not three stacked badges: the tile that needs no explanation gets no furniture.

**The strip is a solid fill and not a floating pill, because the photo behind it is
unknown.** A translucent badge over an arbitrary image has an arbitrary contrast ratio, and
`onDarkTag` — which is what [6.4](#64-tag--the-status-pill) would otherwise reach for — is
`rgba(255,255,255,.14)`, computed against `night` and meaningless over a bright sky. On a
`night` or `red` fill the ratio is fixed no matter what the player photographed. This is
also why the progress bar lives in the strip rather than across the image: a `line2` track
([7.3](#73-meter-and-bar)) is invisible on a photograph.

**The progress fill is white, not `coral`.** [1.2](#12-one-accent-used-sparingly) names the
five places coral appears and an upload is not one of them; a fourth colour would be an
extension ([15.2](#152-adding-a-colour)) bought for a bar that exists for two seconds.
White on `night` is 13.29:1 and costs nothing.

**Failure is per tile, and the failed tile is its own retry target.** One photo's upload
failing must cost that photo and not the part, so nothing about the row changes — the other
two keep their state, and pressing the red tile retries it.

Every one of these is pressable except the placeholder, and each declares its pressed
appearance in [6.6](#66-press-states) — the tile and the remove control fade, and the add
control takes the card's coral border, because a filled tile's border is already saying
whether it is the profile photo.

### The remove control, and what is left of the tile

A 28pt visual at the tile's top right, grown to 44 × 44 by `hit.photoRemove`, **with the
whole square anchored inside the tile.** [6.5](#65-touch-targets) explains why it is not
allowed to overhang the corner.

**It is a solid `night` square carrying a white mark, at the `tag` radius, for the foot
strip's reason.** What is behind it is a photograph nobody has seen, so a translucent
control over it has an arbitrary contrast ratio — and the `line2` circle
[9.1](#91-bottom-sheet) draws a close mark on is a paper-surface object that vanishes over
a bright sky. It is inset from the tile's corner by exactly its own slop — 8 + 28 + 8 = 44
— which is what "anchored inside" means in points.

That square overlaps the tile's own press area, and RN gives the overlap to the child — so
**the tile's press area is the tile minus its top-right 44pt square**, which on the
narrowest phone is still more than four times the minimum. Pressing that remainder promotes
the photo to profile photo; pressing the square removes it. Two acts, two targets, no menu:
promotion is by tap because it is the frequent one, and it is also the one a screen reader
and a keyboard get for free.

**The promote affordance is a sentence, not a glyph.** Nothing is drawn on a non-profile
tile to advertise that pressing it promotes the photo — the step carries one line of copy
under the row saying so ([Part 12](#part-12--screens) owns the words), and every
non-profile tile carries the same thing as an `accessibilityHint`. A per-tile label would be
the same sentence up to three times, printed over the photographs it describes, inviting an
act on the one tile that already leads; and a glyph small enough to fit would be a third
44pt square in a tile that has room for two.

### The generated poster

What a player with no photos has instead of an empty box. Not a grey avatar and not a
tile-only thing — it is drawn wherever a profile photo would be, at whatever size that place
gives it.

```
ground   a POSTER_HUES pair    the light stop to the dark, on ONE hue, corner to corner
figure   ink                   one of three poses, flat, at one value
ball     volt                  one mark

react-native-svg, in viewBox units, 100 x 100, preserveAspectRatio="xMidYMid slice"
```

viewBox units and not points, so **one drawing serves a 90pt tile and a 27pt avatar** and
there is no pixel geometry to tokenise. The stroke scales with the box; nothing is measured
here because nothing here has a size. What the small case carries is a **colour** — the one
difference that survives 27pt — and a smudge of a figure.

**It draws a player, and never a likeness.** One of three poses — forehand, serve, lunge — as
a flat silhouette in a single value, `ink`, with no second value, no gradient on the figure,
no skin tone, no hair, **no face and no facial feature of any kind**. That constraint is the
line, and it is the line the older prose was pointing at when it said _never a person_: the
question a photograph answers here is _do I want to play this person_, a **face** answers it,
and a flat unfaced pictogram — the figure on a squash-court door — does not. The moment the
figure gains a face, a second value or a likeness, it is a picture of a person again and
[ADR-0134](../../docs/adr/0134-the-poster-draws-a-player-and-no-value-is-invented.md) does not
cover it. The figure holds a **racket**, which is the one prop true of every player on this
platform, and carries nothing that names a Sport.

**The pose is not a fact, and nothing may read it as one.** A player whose pose is `serve` is
not a server, and the handedness a pose appears to show is not theirs. A poster is shown and
never read — the same standing a social tag has. Somebody will ask which pose means what; the
answer is _nothing_, and it is a support answer rather than a code one.

**The composition is fixed and whole, and it is three things.** The eight framings and six
ball positions are retired: a window onto this would slice the figure, and their own argument
— that two crops of one drawing are a weaker difference than they sound — is the argument the
colour replaces them with. The line weights are heavier than a diagram's for the 27pt case,
which is the only place in the drawing where a size is paid for.

**The specification's scenery does not come across, and that is a decision.** Its floor glow,
glass wall, mullions and light streak are all marks **lighter than the light stop**, and the
light stop is the number [2.5](#25-contrast--computed) publishes as the worst case for a
white label. A poster whose real worst case is a hairline nobody tokenised is a poster whose
ratio is a guess — which is the exact failure the court's pinned scrim exists to prevent. The
`volt` ball stays because it is the one mark the record names: a 3,4-unit disc is a mark and
not a text bed, and it survives **because** `volt` is excluded from `POSTER_HUES`, so the one
mark on the poster is the one hue a poster can never be.

**The hash does not choose a hue. It chooses from `POSTER_HUES`** — sixteen designed values,
each at least **25°** from `red`, `coral`, `mint`, `amber`, `volt` and every `sport` hue, and
at least **10°** from every other poster hue. That is what dissolves the older prose's second
refusal rather than overruling it: a poster hue is not _in_ the palette, so
[1.3](#13-semantic-colour-is-never-decorative) is untouched, and no poster can claim a Sport
its player may not play, by construction rather than by hope —
[2.3](#23-sport-identity)'s premise survives a surface that draws a hue with no name beside
it. The set is published in `theme.ts` **outside `color`**, because it must not be reachable
where a semantic colour is expected.

**The gradient ramps on one hue and does not shift it.** Two stops, light to dark, corner to
corner. A 40°-warmer light stop would make a poster occupy a 40° _arc_, so the 25° bound would
have to hold at both ends and the usable space collapses; and a two-hue ground is a second
value to compute contrast against for no gain a reader would name.

**`CourtPoster` takes a colour prop, and it is the only one in this system that does.** `hue`
is a member of `POSTER_HUES` **by type**, so it is still a token and still bounded — but the
rule _a literal hex in a component is a bug_ now has exactly one named exception, and this is
it. Adding a seventeenth hue is [15.2](#152-adding-a-colour) with two extra bounds to clear;
it is not a prop somebody passes a hex to.

**Contrast is [2.5](#25-contrast--computed)'s**, and it is what fixes the lightness at both
ends: white over the light stop at 4.5:1, `ink` over the dark stop at 3:1. A hue that cannot
satisfy both is dropped before the set is counted.

**The stop pair, published.** Both stops are stated in **CIE LCh(uv)** and converted once into
the hexes `POSTER_HUES` holds:

```
light stop   L* 49,13   C 65     white over it       4,60-4,65
dark  stop   L* 43,65   C 53     ink over it         3,09-3,12
                                 the ramp between    1,21-1,23
```

**And not in sRGB HSL, which cannot supply such a pair at all.** At one HSL saturation and
lightness the sixteen would vary in luminance by a factor of three between the greens and the
blues, while the two bounds leave a band only 1,41 wide: above **17%** saturation there is no
lightness whatever at which one hue from each arc fits inside it, so every HSL pair that
clears both bounds is a grey. LCh(uv) is a space where equal lightness _is_ equal luminance,
which is what turns sixteen ratios into the two rows in [2.5](#25-contrast--computed). The 17%
is derived in [`posterHues.test.ts`](../src/shared/ui/posterHues.test.ts), not asserted —
**this is a departure from the letter of
[ADR-0134](../../docs/adr/0134-the-poster-draws-a-player-and-no-value-is-invented.md) §3 and
§5, which say the pair is one of saturation and lightness**, and it is the only reading under
which §5's own sentence — _fixed saturation and lightness is what makes the poster
computable_ — is true.

**The gradient's `<Defs>` id comes from `useId()`, and is never derived from data.** The
prototype composed it from the player id and the width, so a screen drawing the same person
twice at one size emitted duplicate ids; composing it from the id, the width _and_ the height
is the same bug one screen further out. React's own per-instance uniqueness is a fix that
cannot be re-derived wrongly.

**A poster is never checked.** It carries no `review` verdict, never enters the photo port and
is never submitted to the checker. There is nothing to check: it is not a photograph of
anybody, and a warning drawn on it would be the app doubting its own drawing.

**Determinism is the feature's, not the theme's.** The design system's contract is that the
same player id produces the same drawing; the hash, and which hue and pose an id maps to, are
the photos feature's, exactly as the confidence ring's 30% ceiling belongs to the engine and
not to `theme.ts` ([7.8](#78-the-confidence-ring)). **One id, one poster, forever, and nothing
is stored** — a stored identity hue or pose index is a choice that can be lost, and a player
whose poster changed would reasonably think their profile had.

### Accessibility

Each filled tile is a `button` whose label names **its position, whether it is the profile
photo, and what its strip says** — `"Photo 2 of 3, profile photo"`, `"Photo 1 of 3, upload
failed, double tap to retry"` — because the strip is the only carrier of those facts and
none of them is legible to a screen reader. The remove control is its own labelled button
naming which photo it removes. The add control announces how many slots remain.

The poster's label says that it is a generated court poster and not a photograph. Nobody
should have to see it to know they are not looking at the player.

---

## 6.10 The radius slider

How far out the player wants to look for other players. One number, in whole kilometres.

```
row      height 44, full content width — THE TOUCH SURFACE
track    height 4, radius 2, line2, centred in the row
fill     from the track's start to the thumb, night, radius 2
thumb    20pt disc, night, with a 3pt surface ring — 26pt overall
figure   num.xl mono, tabular, ink, in a box reserving the maximum's width
words    tiny / muted, one line beneath, height reserved
```

**The row is the control, not the thumb.** A press anywhere on the row moves the value to
that point and the pan continues from there. That is what gets the slider to 44pt without a
`hitSlop` entry ([6.5](#65-touch-targets)), and it is also the behaviour a thumb-only
slider gets wrong: the player who taps the far end of the track expects the far end of the
range, not nothing.

**The thumb is the level bar's mark in a circle** — a `night` disc inside a 3pt `surface`
ring ([7.5](#75-the-level-bar) draws a 3pt coral bar inside a 2pt surface ring for the same
reason). The fill behind it is `night` too, so **the ring is the entire reason the thumb
reads at all**; without it the thumb is the end of the fill and the control has no handle.

**The fill is `night` and not `coral`.** A filled slider portion states a value somebody
set; coral is for actions ([1.2](#12-one-accent-used-sparingly)), and the meter already
fills in `night` ([7.3](#73-meter-and-bar)) for exactly this reason. At the minimum there is
**no fill at all** — a zero-length fill is correct, because the smallest radius is the
smallest radius and not an error.

**No tick marks, and no end labels.** The step is one kilometre over a range that may run
to fifty; 49 ticks is a texture, not information. The figure states the value exactly, and
the ends of the track are reachable rather than worth printing — a number nobody has chosen
sitting under each end of a slider is two figures competing with the one that is true.

**The scale is always the full served range**, exactly as the ring's is always 0–100
([7.8](#78-the-confidence-ring)) and the level bar's always 1,00–5,00
([7.5](#75-the-level-bar)). The same radius lands in the same place on this step and in the
profile editor that later reads it.

**The minimum, the maximum, the step and the default are not values in this document and
not tokens in `theme.ts`.** They are served, with the tag vocabulary and its bounds, by
`GET /player-profile/options` — because they are product's, they are re-validated on the
write path, and they may be retuned without a client release. This is the ring's ceiling
precedent ([7.8](#78-the-confidence-ring)): the control is told its range; it does not know
why. A slider that shipped `1` and `50` compiled in would be a second, staler copy of a
rule the server already owns.

### The figure and the words

The figure is `num.xl` mono and tabular, and **its container reserves the width of the
largest value the served maximum can produce**, so dragging from 9 to 10 does not move the
text ([1.4](#14-numbers-are-monospaced-always) is about a level not reflowing its row; this
is the same rule under a finger). The plain-word line beneath is `tiny` in `muted`, one
reserved line, for the same no-reflow reason — and it exists because a number in kilometres
means nothing to a player who does not think in kilometres. Which words at which distances
is the step's copy, not this section's.

### Accessibility

`accessibilityRole="adjustable"`, `accessibilityValue={{ min, max, now, text }}`, and
`accessibilityActions` for `increment` and `decrement`, each moving exactly one step. **A
drag-only slider is unusable with a screen reader and with a hardware keyboard**, and this
is the control that most often ships that way.

`text` carries **both** the figure and the plain-word reading, as one announcement — the two
are one fact rendered twice for sighted players, and reading them as two values would say
the control has two.

No visible increment and decrement buttons are drawn. The accessibility actions are the
mechanism, and two more 44pt targets beside a slider would be a second control competing
for the same value.

**The thumb does not animate.** It tracks the finger, and the value under an accessibility
action changes at once ([1.5](#15-nothing-animates-that-does-not-have-to)). There is nothing
here for reduced motion to switch off, which is the correct amount.

**The slider has no selected state**, so it has none to carry by colour or otherwise. Its
whole state is one number, and the number is on the screen.

## 6.11 The tick box

One box and one claim beside it, for a statement a player either makes or does not.

```
row      height 44, box + label together — THE TOUCH SURFACE
box      20 x 20, radius 10, 1pt line, surface
ticked   fill ink, border ink, the 12 x 12 tick from 6.8 in surface — 17,50:1
refused  1pt red border, and only while unticked
label    rlValue / ink, flex 1 so a long claim wraps inside the row
message  tiny / red beneath, announced, absent when the answer is fine
pressed  opacity .7, over any of those
```

**It borrows 6.8's cell rather than inventing a second ticked thing.** The selected state is
a fill inversion _and_ a tick for the reason [6.8](#68-the-availability-grid) gives: the
inversion is a 17,50:1 luminance change that survives colour blindness on its own, and the
tick is the shape [Part 13](#part-13--accessibility) asks for. A box carrying its state in
fill alone is a stain rather than an answer. The tick is the same path at the same 12 × 12,
drawn from the same tokens.

**The row is the control, not the box** — the same decision the radius slider makes. A 20pt
square is well under the [44pt minimum](#65-touch-targets) on its own, and growing it with
`hitSlop` would leave the words beside it inert, which is a target that stops where the
sentence starts.

**This is not a switch and not a chip.** A switch turns something on and reads as a setting
that can be flipped back later; a chip narrows what is already on screen
([6.2](#62-chip--the-filter-pill)). This shape is for a sentence the player asserts, so the
label is written in their voice and the accessible name is that same sentence.

**There is no pre-ticked state.** The component takes `checked` and has no default for it:
a box that arrives ticked is a claim the player never made. That rule is the whole reason
the control exists — [12.1](#121-onboarding)'s data screen already records that a screen
listing what is kept is exactly where a consent checkbox gets added by someone who means
well, and this one is on the sign-up form because an account has a precondition, not because
a surface had room for a tick.

**The refused border is drawn only while the box is unticked.** Once it is ticked there is
nothing left to fix, and a red outline around a satisfied control contradicts the answer
inside it. The message beneath carries the state as words, so nothing rests on the border.

---

## 6.12 The switch

A mode a player turns on and off — the swap toggle on the interactive court is the first,
and the pattern is _a setting that can be flipped back_.

```
row     height 44, control + words together — THE TOUCH SURFACE
track   40 × 23, radius pill · line2 off · ink on
knob    18 circle, inset 2,5 · night off · surface on
travel  track − knob − two insets, and nothing else moves
pressed opacity .7, over either state
```

**Nothing already in Part 6 carries `checked` on a mode.** [6.11](#611-the-tick-box) says in
as many words that it is not a switch — it is _"a claim a player either makes or does not"_,
written in the player's voice and asserted once; [6.3](#63-segmented-control) picks one of
several; [6.2](#62-chip--the-filter-pill) narrows what is already on screen. A mode that can
be turned back off is none of the three, and `the-words.md` §20.4 fixed the role as `switch`
with `checked`, so the role and the control arrive together.

**The row is the control, not the track** — the same decision [6.11](#611-the-tick-box) and
[6.10](#610-the-radius-slider) make. A 23pt track is well under the
[44pt minimum](#65-touch-targets), and growing it with `hitSlop` would leave the words beside
it inert.

**The state is carried by the knob's position before it is carried by any fill.** That is the
shape [Part 13](#part-13--accessibility) asks for, and it is what lets the two fills be the
inversion [6.8](#68-the-availability-grid) already uses rather than a second on-colour. Mint
was refused for the fill: [2.2](#22-accent-and-semantics) means _settled, safe, covered_ by
it, and a swap mode being on is not a settled thing.

**The knob takes the value that reads on the bed it is standing on.** The prototype drew a
white knob at both ends of the travel, and against its unchecked `line` track that is
**1,30:1** — the control's only moving part invisible in half its states. `night` on `line2`
is **11,36:1** and `surface` on `ink` is **17,50:1**, so the knob clears
[1.4.11](#25-contrast--computed)'s 3:1 for a graphical object at both ends. This is Rule C's
argument applied to a mark rather than to text, and it is the only place in this system where
one object takes two values. **The three ratios are derived, never typed** —
[`Switch.test.tsx`](../src/shared/ui/Switch.test.tsx) computes them and fails if a token
moves, exactly as the court's four and the poster's two are derived.

**There is no disabled switch.** [6.1](#61-button)'s rule is that this app never draws a
pressable-looking control that refuses, and [6.9](#69-the-photo-tile-and-picker) makes its
ceiling a fact of the layout rather than a greyed button. A mode with nothing to switch is a
row that is not on screen.

**The words are the caller's, and the accessible name is the label alone.** A switch announces
its state through `checked`, so a description folded into the name would be the double
announcement 6.8 hides its column heads to avoid. The mode line beneath is drawn and merged
into the one element; what the mode _does_ is said by the controls it changes.

---

# Part 7 — Data display

## 7.3 Meter and bar

| Element | Height | Radius | Track   | Fill        |
| ------- | ------ | ------ | ------- | ----------- |
| Meter   | 5      | 3      | `line2` | `night`     |
| Bar     | 4      | 2      | `line2` | caller sets |

A bar states a fraction, so it is only for a value with a denominator somebody knows. The
questionnaire has none — see [7.9](#79-the-question-navigator).

## 7.5 The level bar

Not a styled component — a drawn object, built from Views. Its geometry is fixed:

```
row 1   (y 0,  h 6)    four band segments, radius 3, the current band at full opacity
                       and the others at .38 (light) / .42 (dark), 1pt separators in
                       the surface colour
mark    (y −3, h 12)   3pt coral bar with a 2pt surface-coloured ring
row 2   (y 13, h 8)    the likely-range bracket: 2pt centre line with 2pt end caps, in muted
row 3   (y 24)         four band names — the current one at weight 800 in its band ink,
                       the others at weight 600 in muted
legend  (optional)     a coral tick and a bracket glyph, with labels
```

> **The separation of the two rows is the whole design.** An earlier version drew the range
> on top of the bands and it hid exactly what the bands were there to show.

**The scale is always the full 1,00–5,00**, so the same value always lands in the same
place — on the result card and on a comparison card alike.

Band names use the band **ink** values ([2.4](#24-band-colours--the-level-bar)), not the
deeps. The bracket uses `muted`.

## 7.6 The anchored popover

```
width 250   background surface   1pt line   radius 13   padding 12
shadow: the popover elevation
arrow: an 11 × 11 rotated square carrying TWO of its four borders
```

**The arrow carries two borders so it reads as a continuation of the outline rather than a
floating diamond.**

Position is measured after layout (`onLayout` + `measureInWindow`) and **clamped inside
the screen's horizontal bounds** — a mark two-thirds across would otherwise lose its right
edge. The popover renders through the overlay root, never as a descendant of a dark card
(see [5.2](#52-dark-card)).

Accessibility: `accessibilityViewIsModal` on iOS, siblings hidden on Android, an explicit
close control, and focus returned to the mark that opened it.

## 7.7 The card rail

```
child width  0.74 × content width     ← NOT 268pt; see Part 0.2
card         marginBottom 0, flex 1, column
last hairline in the card: marginTop auto
```

**The peek is the entire affordance** — the next card showing by roughly a quarter is what
says "there are more". `marginTop: auto` on the last hairline pushes the footer to the
bottom **so footers align across cards of differing height.**

## 7.8 The confidence ring

Like the level bar, not a styled component but a drawn object — an arc, a track and a tick,
in `react-native-svg`. It appears **only inside a dark card**, because `volt` is legible
nowhere else ([2.2](#22-accent-and-semantics)).

```
ring     size.ring 72        stroke size.ringStroke 6, butt caps
                             starts at 12 o'clock, sweeps clockwise
track    full circle         color.onDarkHair    ← the dark card's structural line
arc      0 → value           color.volt          ← 10.60:1 on night
ceiling  at the served       size.ringTick 2, in color.volt, spanning the stroke
         ceiling (30% → 108°) and overshooting size.ringTickOvershoot 3 outward
                             — omitted entirely where none was served
value    num.numXL 22 mono 700, tabular, #fff, optically centred in the ring
label    type.eyebrow "CONFIDENCE" beneath — repainted .52 by the dark card
```

Every value above is a token. **The 30% is not** — it is the onboarding confidence ceiling,
it belongs with the engine rather than in `theme.ts`, and it is not a constant on this side
at all: the engine serves it on the result, because it is scoped to the engine version that
produced the rating and may be retuned without a client release. The ring is told where its
ceiling sits; it does not know why.

**Where no ceiling was served, no tick is drawn** and nothing on the screen names one. That
is a rating replayed from an engine version since retired — it keeps its numbers and loses
its explanation, and what a retired engine could have proved is part of that explanation. A
default tick would state a limit that did not exist when the rating was produced.

**The scale is always the full 0–100**, exactly as the level bar is always the full
1,00–5,00 ([7.5](#75-the-level-bar)) — so the same percentage always lands in the same
place, on the onboarding result and on a rating settled by fifty matches alike.

**The ceiling tick is what makes the full scale survivable.** Onboarding cannot produce
confidence above 30% — the questionnaire is the entire evidence surface — so every player
leaves it with an arc covering under a third of the circle. A bare arc that short reads as
failure. The tick turns "nearly empty" into "as far as a questionnaire can prove", and it
does so without a second component: when matches later push confidence to 75%, the same
ring means the same thing and the tick simply sits behind the arc.

**Butt caps, not round.** A round cap adds half a stroke width at each end, which on a 3%
arc is most of the arc — it would inflate the smallest values, exactly where the number is
least certain, and it would overhang the ceiling tick. The arc's drawn length is its
value.

**The tick is radial where the arc is tangential.** That is a difference in shape, not in
colour, which is what [Part 13](#part-13--accessibility) requires — the mark survives
being unable to distinguish volt from white.

**The ring is not pressable.** Its meaning is carried by the adjacent information mark and
its popover ([12.1](#121-onboarding)); do not give the ring its own press state or touch
target. Its accessibility role is `progressbar`, and its value text names both numbers —
the confidence reached and the ceiling that applies — because the tick is invisible to a
screen reader.

## 7.9 The question navigator

The questionnaire's progress indicator, and the third drawn object — Views, like the level
bar, not a styled `Bar`. It replaces the sports-measuring bar in onboarding's chrome
([12.1](#121-onboarding)).

```
a left-aligned row of fixed-width segments, growing rightward

segment    size.navigator.segmentWidth 12 × segmentHeight 4, radius 2
answered   fill color.coral                    ← one segment per answer given
unanswered fill color.line2                    ← the question being asked
standing   height currentHeight 8, radius 3    ← where the player is, whatever its fill
gap        size.navigator.gap 3
```

**It claims no total, and every other property follows from that.** An adaptive
questionnaire has no denominator: the engine decides it has heard enough only _after_ an
answer arrives. So the segments are a **fixed width** in a row that grows and never
arrives — a flex-filled track would put the last segment at the right edge and assert a
length nobody in the system knows. At the engine's ten-question ceiling the row is
`10 × 12 + 9 × 3 = 147pt` against 290pt of content on the narrowest phone, so it is
visibly short of the end at every length it can reach. **There is no segment for a question
that has not been asked**, because that segment _is_ the denominator.

**Fill and height are two independent facts.** Fill says a question has been answered;
height says where the player is standing. A player who walked back four questions stands on
a segment that is both filled and tall, and the question being asked is tall and empty.
Collapsing them into one state would mean walking back moved nothing on screen, in the one
component whose job is to say where you are. Height rather than opacity carries it, for the
reason [Part 13](#part-13--accessibility) gives and [7.5](#75-the-level-bar) already
follows: the ratio is the level bar's own mark-to-track, doubled from 4 to 8.

**The row shrinks.** A revision truncates the answers, so a step can describe less progress
than the one before it. The navigator is drawn from what the run holds _now_, never from
what it last drew — a component counting its own answers is wrong in the one direction it
cannot detect.

**It indicates; it does not navigate.** Ten segments across the content width is a 26pt
target, and [6.5](#65-touch-targets) bounds horizontal `hitSlop` by the neighbour — at most
1,5pt a side at a 3pt gap. That is a 29pt target against the 44pt minimum
[Part 13](#part-13--accessibility) locks in, and the failure mode decides it: selecting the
wrong segment would discard every answer after it, which would be the most destructive
consequence in the flow reached by the least reliable target in the app. Movement is the
screen header's back control ([10.3](#103-the-screen-header)) and the screen's own forward
control.

**One element, one label — never one per segment.** A row of rectangles is not readable at
any font size, so the label is the whole of it in words: the position, and how many answers
are behind it. It states **no total**, because there is none to state. Its role is _not_
`progressbar`: that role carries a max. `allowFontScaling` does not arise — the navigator
contains no text.

## 7.10 The fit pill

Fit, on a card. One shape, one threshold, drawn on four surfaces — the competitive card, the
social card, the deck card, and the head of the why-fit sheet.

```
pill    height 26, radius.fit 7, padding 0 × 9, row, gap 3
base    background night · label #fff        13,29:1
hi      background coral · label ink          4,50:1   ← Rule C
glyph   ✦, drawn and never spoken
number  num.xs, mono, TABULAR
```

**This is not the deleted 7.1 returning under its old number.**
[Part 17](#part-17--what-the-reset-removed) removed the fit badge because the Match Fit engine
it drew was removed, and it warns about this section in particular: the badge's _"90 threshold
named a scale the deleted engine defined."_ The engine ships again and the component comes
back — at a new number, because a section number in this document never moves — and it
**states the scale it is against** rather than inheriting one.

> **Fit is out of 100**, and `hi` is Fit ≥ 90 — the top tenth of that scale.

[`CONTEXT.md`](../../CONTEXT.md) defines Fit as _"how good the game would be, printed on the
card as one number out of a hundred"_, which is where the denominator comes from, and
`the-words.md` §20.3 rules against §E6's _"out of 99"_ on the same sentence. The step is a
**step in a fill and not a fourth meaning**: [15.2](#152-adding-a-colour) forbids inventing one
of those, and `coral` is the app's one accent used exactly as [1.2](#12-one-accent-used-sparingly)
describes — sparingly, on the tenth of cards that earn it.

**`ink` on the coral, never white.** The prototype drew `#fff` on `var(--coral)`, which is
3,89:1 and the one pairing [Rule C](#rule-c--text-on-a-saturated-fill) refuses outright.

**26 tall, which is what every call site drew.** UI §G1 records the class defaults being
overridden inline at all five of them — _"the class defaults are used nowhere"_ — so the
arrival takes the used values and the unused ones stop existing. The number inside is
`num.xs`, the nearest mono role to the 12pt those same sites wrote: a seventh size step for
one pill is what [15.3](#153-adding-a-size-or-a-spacing-step) says not to add.

**The pill is not its own accessibility element.** `the-words.md` §20.3 merges it into the
card body's label — `Fit {n} out of 100` — and the ✦ _"is hidden by the merge rather than by a
separate rule"_, so there is no rule here either.

## 7.11 The balance bar

Two segments in one track, saying **which side** a game leans to.

```
bar     height 16 / 18 / 24, radius.balanceBar 8, overflow hidden
yours   night          — on a dark card: surface, with the label in night
theirs  ok mintInk · warn amber · bad red        ← Rule C: white sits on all three
labels  tag, centred, drawn at 18 and 24 and absent at 16
```

**This is not the deleted 7.2 returning under its old number**, for 7.10's reason and by the
same rule.

### One fixed scale, because three clamps were the defect

The prototype computed the left segment as _fifty, plus the difference between the two side
strengths times thirty-four_ — and then clamped it to **22–78** on the forecast card and
**20–80** on the pool header and the candidate card. One formula, three clamps, so the same
gap landed in a different place on two screens. That is precisely what
[7.5](#75-the-level-bar) and [7.8](#78-the-confidence-ring) exist to prevent: _a value must
land in the same place everywhere or the component means different things on different
screens._

Drawing the raw shares instead would be honest and invisible — 2,71 against 2,83 is 48,9
against 51,1, a difference nobody can see at 24pt.

> **The amplification ships as one fixed scale: one mapping, one constant of 34, one clamp at
> 20–80.** A steep scale is still a fixed scale. What was wrong was three of them.

The scale lives in the component, exactly as the level bar's fixed 1,00–5,00 does;
`theme.size.balanceBar` holds the geometry and nothing else.

**The printed evenness percentage stays the server's and is never derived from the strengths**
(`the-play-screens.md` §11.3 — _no forecast arithmetic on the client_). The bar and the number
are two different facts: the number says _how even_, the bar says _which side_.

**The word beside the bar carries the meaning**, which [Part 13](#part-13--accessibility)'s
_never colour alone_ already forces, and `the-words.md` §20.4 makes the bar one `image`
element whose name is that word and its figure.

**The on-dark repaint is a repaint, not a second scheme.** The pool header draws this bar
inside a dark card, where a `night` segment against a `night` card is one segment — so the two
sides swap which of them is the dark one, and the label on _your_ side goes to `night` with
it. React Native has no colour cascade, which is why this is a `variant` rather than something
the card does to its children; [7.5](#75-the-level-bar) took the same repaint for the same
reason. **The tone, the scale and the clamp are untouched by it.**

**Three sizes, and the size decides whether there is a label.** #219 B4 put the type floor at
9,5pt, so the prototype's 8 / 8,5 / 9,5 segment labels collapse to one role. At 24 and 18 a
`tag` line fits beside the fold; at 16 it does not, and the smallest bar draws none rather
than drawing one under the floor.

**The tone is exported, because two other things are painted with it.** `BALANCE_INK` and
`BALANCE_SOFT` sit beside the component — the ink for a surface that prints a tinted figure
rather than drawing the bar, the soft for one that tints a **box**, and the forecast card's
_their side_ panel does both. The bar's own rule is _one value lands in the same place
everywhere_; this is that rule about the colour rather than about the fold, and it is what
stops a panel four lines under the bar picking a different amber from it. **The two sides are
deliberately not a pair**: the bar paints _yours_ `night` and only _theirs_ carries a tone, so
a panel over the same split takes `line2` on your half and the tone's soft on theirs.

**One thing recorded rather than fixed.** §B9's word breaks at 85 / 70 / 55 and its colour
breaks at 70 / 55, so _Very even_ and _Fairly even_ share one green. That is **correct**: Part
13 is satisfied by the word, and a fourth tone would need a fourth _meaning_, which
[15.2](#152-adding-a-colour) forbids inventing. Left unwritten, somebody tidies it into four
colours.

## 7.12 The court

The court a game is played on, with the players standing where they will stand. The fifth
drawn object — after the level bar, the confidence ring, the question navigator and the
generated poster — and the one whose numbers cannot be derived.

```
ground   a 150° gradient from the Sport hue to `night`, under one `courtScrim` pass
chrome   ONE white at four weights — boundary .30/1,6 · net .85/1,8 over a .35/5 glow
         · inner lines .24/1,1 · squash's front wall, a .16 band
caption  eyebrow over a gradient to `courtScrim`, with `textOnMedia`
sides    eyebrow at white .6, with `textOnMedia`      ← 5,46 against the worst ground (2.5)
seat     THREE characters of the handle, no ellipsis, and the level beside it on one line
         — `tag` + `num.xs` tabular, both white with `textOnMedia`, in a box inset -9
         past the face on each side
box      100 × 132 drawing units — the 1,32 aspect IS those two numbers
radius   radius.court 9
seats    POSITIONS. The caller supplies what stands in each one.
build    196 — the width at which a seat is 46. The interactive court, always.
thumb    54 — the court as a picture BESIDE a sentence, never as a surface
header   84 — the court INSIDE a card about it. Above 72, so the seat is the ratio
         rather than the floor, and the faces sit in the ground instead of on it
```

> **`Court` takes a Sport and a box, renders the ground, the chrome and the seat _positions_,
> and takes children in seat order.**

```tsx
<Court sport={sport} width={w} summary={…}>
  {seats.map(…)}          // children in seat order; the court places them
</Court>
```

**Two other shapes were refused and both fail the same way.** A `renderSeat(index, position)`
callback is this with an indirection. A `useCourtGeometry(sport, width)` hook **returns** the
coordinates, and geometry that is returned is geometry that gets adjusted at one call site and
not the other — the drift this Part exists to prevent, arriving through the door the rule was
written to close. With children the positions never leave the module, and the interface is
testable through itself: hand it two children, assert two positions, per Sport.

**The seat count is the Sport** — padel and badminton four, tennis and squash two — and it is
read off the coordinates rather than stated twice.

**H-25 is why the coordinates cannot be derived.** Squash has **no net and no two sides** —
its pair share one playing area, where the other three put a seat on each side of a net. So
_seat 3_ is not where seat 3 is in padel, and reflecting the near side about the middle draws
three Sports correctly and one wrongly with nothing to see. They are
`theme.size.court.seats`, per Sport, **in seat order — your side first**, which is the order
`the-words.md` §20.4 reads `{side}` off.

**The seat's caption is three characters and a figure, and it announces no cut.** Sixty-four
characters under a 46pt face is about four, so the drawn label was never the handle and could
not be; what changed is that it no longer spends one of the four saying so. A tail ellipsis on
a caption whose only job is to tell four faces apart is a character of apology pointing at
something the player cannot go and read from here — and the level, which used to sit on a
second line, joins it on the first, because _Pau 3,23_ reads as one identifier where a word
over a number reads as a paragraph under a dot. **A fixed count rather than the seat's own
width**: a caption that measured itself would draw three letters on one phone and five on
another. The pair is wider than the seat, so its box is inset negatively past the face on both
sides — it is absolutely positioned and bounds nothing. The whole handle is unchanged in both
sentences and in the spoken name.

**The interactive court is a fixed width, and the width is chosen by the seat.** Every rule in
this section about a seat is stated about a **46pt** one — the three-character caption, and
the clear badge's 44pt target inset into a 46pt face — so `build` is
`46 / seatRatio` and the court is centred in the content column rather than stretched across
it. Sized by the content width instead, that seat is 81pt on a large phone and every one of
those arguments is being made about a court nobody draws.

**A court may also be drawn as a thumbnail, and `thumb` is the one width that is.** _Find a
game_'s way onto the court draws one beside a line of prose, to say what shape the court is
and which seat is yours before a search has run. It sits under the width at which the seat
share clears its floor, so **every seat on it is the floor face** — which is the point: a
thumbnail states a shape, and a picture that tried to state faces at 54pt would be stating
them at a dot. It is a fixed number rather than a share of the content width, because a court
that grew with the phone would stop being a thumbnail on a large one.

**The seat face is a share of the court with a floor** below which a face is a dot. Its
**radius and its ring are not here**: the court owns where a seat goes and how big its box is,
and the seat owns what is drawn in it. That is why `CandidatePhoto`'s _33 % of its own box_
lives with `CandidatePhoto` and not in `theme.size.court` — a rule about a face, held beside
the thing that draws faces.

**The read-only court and the interactive one are not a flag on this component.** They share
every number and no behaviour, so they are two feature components over one drawn object:
read-only faces and pressable seats are _different children_. The court owns geometry and
knows nothing about players; a seat owns its label, its ring, its badge and its taps.

**The seat-clear badge is not a new component.** [6.9](#69-the-photo-tile-and-picker)'s remove
control already is one — a solid `night` square with a white mark at the `tag` radius, a 44pt
target, inset by its own slop — and §20.4's _`Remove {name} from {side}`_ is 6.9's own rule
that a remove control _"names which photo it removes"_ applied. The prototype's 18px circle at
radius 9 is dropped.

**Padel's second boundary pass is dropped** — a 5pt white at `.12`, the glass wall — on
[6.9](#69-the-photo-tile-and-picker)'s argument for dropping the poster's: it is a mark
lighter than the ground it sits on, drawn over a boundary that is already there. **Squash's
out-line takes the net's weight and none of its glow**: the glow is a net's depth, and squash
has no net.

**Padel's inner lines join the .24 the other three draw.** The prototype drew them at `.28`,
which is the same kind of variance §G2 exists to close; one line weight across four courts is
half the reason this is one component.

**Every label over the court carries `textOnMedia`**, and the gradient id comes from `useId()`
— the pool draws a court in its header and another in a card, and an id composed from the
Sport and the width emits duplicates the moment a screen draws two of the same Sport
([6.9](#69-the-photo-tile-and-picker) closed exactly that bug).

**This file holds no copy.** The caption, the two side labels and the summary a screen reader
hears first all arrive as props. The summary is an element of its own **preceding the seats**
rather than the court's own label — a container carrying one would swallow the seats, which
are the elements the screen is navigated by — and the caption and side labels are hidden,
because the summary already names the Sport and each seat names its own side.

---

# Part 8 — Scrolling patterns

Two horizontal patterns with different jobs.

| Pattern        | Behaviour                                                                              | Used for                              |
| -------------- | -------------------------------------------------------------------------------------- | ------------------------------------- |
| **Square row** | Free scroll, content-sized children, gap 6, no scrollbar                               | Chips, sport squares                  |
| **Strip**      | Snapping carousel, full-content-width children, gap 9, **bleeding to the screen edge** | Where one item at a time is the point |

```
Square row  horizontal, showsHorizontalScrollIndicator={false},
            contentContainerStyle: { gap: 6 }

Strip       horizontal, snapToInterval = contentWidth + 9, decelerationRate="fast",
            style: { marginHorizontal: -15 },
            contentContainerStyle: { paddingHorizontal: 15, gap: 9 }
```

**The strip's negative margin is what lets it bleed to the screen edge** while its content
still aligns to the 15pt gutter.

**Scroll position must survive a re-render.** The prototype preserves `scrollLeft` on every
rail because the screen re-renders on every interaction; in RN the equivalent is keeping
the rail's data identity stable and never remounting the `ScrollView` — a rail that snaps
back to the start on every tap is the bug this prevents.

**Pager dots:** 5pt dots, the active one widened to 14pt and coloured `coral`.

---

# Part 9 — Overlays

## 9.1 Bottom sheet

```
scrim   rgba(10,52,65,.45)          ← the night colour at 45%, not black
sheet   bottom 0, maxHeight 88%, radius 22 22 0 0
grab    36 × 4, line, radius 2, centred, marginBottom 9
close   28 circle, line2 background, top-right
```

**The scrim is the night colour, not black — the dim matches the palette.**

The sheet is a real modal: it traps focus, hides its siblings from screen readers, and
closes on back-gesture (Android hardware back must dismiss it).

**The body scrolls, and the head does not.** `maxHeight: 88%` is a cap, and a cap without a
scroll under it does not bound a sheet — it **truncates** one: the children keep their
heights, the column overflows, and whatever is last in it goes off the bottom of the screen.
On a sheet that is always the controls, because a sheet reads statement first and answer last.
So the grab, the title and the close control stay put and everything below them is in a
`ScrollView` that **shrinks**; the sheet's bottom padding travels onto the scrolled content,
or the last control sits against the screen edge at full scroll.

**Nothing is pinned**, and that is a refusal rather than an omission. A footer slot holding
the controls outside the scroll is the other way to guarantee they are reachable, and it is a
bigger claim than this component can make for every caller: three of the four sheets in the
app end in something that is not a control, and a slot that pinned the last child would move
a sentence away from the paragraph it belongs to.

## 9.2 Toast

```
position  left 15, right 15, above the tab bar + bottom safe-area inset, clear by 9
tst       background night, #fff, radius 12, padding 12 × 15, 12 / 600
ok        background mintInk        ← Rule C, was mint (4.07:1)
bad       background red
```

`pointerEvents: 'none'` on the container **so a toast never blocks a tap.** Every toast
announces itself — the prototype had no live region, and a toast a screen-reader user cannot
hear is a toast that did not happen.

### The queue, the live region and the dismiss

Specified above and unbuilt until #260. What was missing is the three things §G3 #7 asks for.

**One host, mounted once, at [9.3](#93-layer-order)'s overlay root.** `zIndex` is scoped to
the parent in React Native, so a toast raised from inside a card renders inside that card;
`ToastHost` is a sibling of the route tree in `src/app/_layout.tsx`, exactly as the
environment badge is. The queue behind it is `shared/store/toast.store.ts` and not a feature's,
because a queue living in a feature is that feature owning every other feature's toasts.

**A queue, not a stack.** The prototype appended toasts to a column and let three sit there at
once. The announcement is queued (Part 13, below), and a screen showing three sentences while
a listener is being read one is the two channels disagreeing about what just happened —
nineteen toasts fire from the Play tab alone, so the case is real.

**The one interrupting message jumps the queue as well as the voice.** Part 13's exception is
that the send confirmation _does not queue behind anything_, and that is two things rather than
one: it is spoken with `queue: false`, **and** it is placed in front of everything not yet
shown. A politeness flag alone would still leave it waiting two holds — 5,2 seconds — on a
destination that is a placeholder with nothing else on it to say the challenge went. **The
message already on screen keeps its place**, because pulling a sentence out from under a reader
is the interruption the amendment exists to stop.

**The dismiss is the hold, and there is no close control.** `pointerEvents: 'none'` is the
rule above, and a control inside the toast is a tap the toast has to eat. So the head of the
queue is shown for `motion.hold.toast` — 2,6 seconds, the read time of the longest sentence
this app fires — and then the next one takes its place.

**Nothing about it animates.** [1.5](#15-nothing-animates-that-does-not-have-to) is the rule,
and the message has already been spoken by the time a 240ms rise would have finished arriving.
That also means there is no reduced-motion branch to get wrong: a hold is not an animation.

**The live region is an announcement, not `accessibilityLiveRegion`.** Android's attribute has
no iOS equivalent and fires on re-render rather than on arrival, which on a host that swaps one
message for another is the wrong event. The host announces the head as it _becomes_ the head —
a sentence spoken while three others are ahead of it is a sentence about a screen the player is
not on — and the drawn toast is hidden from assistive technology, because it has already been
spoken and a reader that walked into it would hear the sentence 2,6 seconds late.

## 9.3 Layer order

| Layer   | Order |
| ------- | ----- |
| Sheet   | 20    |
| Toast   | 40    |
| Popover | 60    |

`zIndex` in RN is scoped to the parent, so overlays render from a **single root-level
overlay host**, not from wherever they were triggered. That is also what keeps a popover
out of a dark card's repaint.

---

# Part 10 — The app shell

## 10.1 Screen structure

```
SafeAreaView
  ScreenHeader        eyebrow + h1, optional back, optional right slot
  ScrollView          paddingHorizontal 15, paddingBottom 15
  CTA                 conditional, pinned above the tab bar
  TabBar              equal columns, one per top-level destination
```

> **Confirmed for Play**, against a UI specification that proposed the opposite
> ([#227](https://github.com/Raketa02/Raketa/issues/227)). The header **pins** above the
> scroller and does not scroll away — both shipped layouts already build it that way, and the
> counter-argument is a viewport budget computed against a 392 × 788 phone with **no safe
> areas at all**, so its own number gets worse on a real device rather than better. The CTA
> and the tab bar are **flex siblings** below the scroller, never fixed elements.
>
> **The tab bar owns the bottom safe-area inset and the CTA owns none.** The CTA sits above
> the bar, so an inset applied twice is 34pt of nothing on a notched device — and applied to
> the wrong one it is a CTA under the home indicator.

## 10.2 The tab bar

```
equal columns, one per top-level destination
paddingTop 6, paddingBottom = 12 + bottom safe-area inset
icon 16 × 16, gap 3, label `tag`
centre column: a 30pt disc, radius 11, 6.1 `primary`, shadow.fab
active Play:   a 2pt `coral` ring, 2pt clear of the disc, ABSOLUTELY POSITIONED
```

**Five columns** — `Now · Around · ⚡Play · Chats · You`. The centre one is raised, and it is
both an action and a destination: pressing it always opens Play's entry, and the four screens
that entry leads to are somewhere a player can be for a whole flow. That is what the ring is
for.

### The disc is [6.1](#61-button) `primary` in a squircle

Not a new colour treatment, and this is the one exception the bar looked like it needed and
does not have. The prototype's disc was **white on `coral` at 3.89:1** — the exact pairing
[2.2](#22-accent-and-semantics)'s Rule C refuses outright, on the grounds that nothing in this
app reaches the large-text threshold. `primary` already answers it: fill `coralInk`, white
mark, brightening to `coral` on press. The press state arrives free and no colour is added.

Radius 11 rather than the avatar rule's `round(30 × 0.33)` = 10: the disc is not a face, and
11 is the measured value.

### The active state is a ring, in coral, and it is out of the layout

**2pt, `coral`, set 2pt clear of the disc.** The gap is the bar's own `surface`, so there is
no collar to token and coral reads **3.89:1 on both edges** of the stroke — clearing 3:1 for a
non-text indicator. Volt cleared it on neither: **1.25:1** against the bar and **2.86:1**
against the disc, which is [2.2](#22-accent-and-semantics) as amended — _a fill anywhere, a
stroke only on dark_ — measured rather than asserted.

**Absolutely positioned, and the bar's height never changes.** A bar that grew 8pt on arriving
in Play would move the four things that did not change in order to announce the one that did.
The 4pt the ring needs above the disc comes out of the 6pt top padding, leaving 2pt of
clearance to the hairline.

**The bar carries no badge.** A count that is not filtered the way the surface it labels is
filtered would be an unfiltered number on permanent chrome, on a tab whose own rule is that it
always opens somewhere else. Counts belong to the screen they describe.

### Feather, and selection in tone alone

The glyph set is **Feather from `@expo/vector-icons`**, declared in `package.json` rather than
inherited transitively, and the inventory is these five
([ADR-0135](../../docs/adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md)):

| Tab      | Glyph            | Box                              |
| -------- | ---------------- | -------------------------------- |
| `now`    | `home`           | 16pt                             |
| `around` | `map-pin`        | 16pt                             |
| `play`   | `zap`            | **15pt**, white, inside the disc |
| `chats`  | `message-circle` | 16pt                             |
| `you`    | `user`           | 16pt                             |

**Selection changes tone and never shape**: `ink` selected, `muted` resting — 3.25:1, and a
_lightness_ difference rather than a hue one, so it survives greyscale and a red-green
deficiency. Feather has one weight and no filled counterparts, and that costs nothing here for
exactly that reason: a family with outline/filled pairs would put a second state channel on
top of a sufficient one, which is the same thing the ring refuses about the shadow.

**The ⚡ is `zap` and never the character.** `U+26A1` carries `Emoji_Presentation=Yes`, so a
bare `<Text>⚡</Text>` requests colour-emoji presentation and a `color` style has nothing to
apply to — the one mark in the bar whose colour this app would not control, on the disc whose
whole argument is a white mark.

**Every glyph name is typed against its own family's `glyphMap`,** so a name the package does
not ship is a compile error rather than a blank column nobody notices at 16pt.

### The label is `tag`, under a derived cap

`tag` — 9,5/700 and **flat**. A tab label is a _name_, and `eyebrow`, the other member of the
9,5 pair, is tracked: 1,43pt per character spends **8,6pt** of a 64pt column on air.

[Part 13](#part-13--accessibility) names this bar as the fixed-height exception **and** permits
`allowFontScaling={false}` only inside the level bar, so a bounded `maxFontSizeMultiplier` is
the only mechanism left. **Its value is derived, never chosen** — from the longest shipped
label, at `tag`'s size, in the narrowest phone's column, with the grid's smallest step held on
each side. `theme.size.tabBar.labelMaxScale` carries the answer and
[`tabBarLabelCap.test.ts`](../src/shared/ui/tabBarLabelCap.test.ts) re-derives it from the real
Archivo Bold metrics, so a sixth tab or a longer word goes red rather than truncating on
somebody's phone.

**The bar's height is fixed against _state_, not against the OS text size**, and the two claims
on this page are not the same claim. Nothing about being in Play changes the height — that is
what the absolute ring is for. The label, however, scales: at the cap one line of `tag` goes
12 → 20,4pt and the bar grows with it, which is [Part 13](#part-13--accessibility) working
rather than failing. The 44pt figure below is a **minimum**, met at 1× and only exceeded from
there.

Every tab needs an `accessibilityRole="tab"`, an `accessibilityLabel` and
`accessibilityState={{ selected }}`. The visible label is not enough on its own. The glyph is
**hidden** from the reader on every column, the bolt included — the label already names the
tab, and the disc's own visible _Play_ is what announces the control.

The column reaches the 44pt minimum by its own geometry — 30 + 3 + 12 inside the bar's
padding — so there is no hit-slop to arrange.

## 10.3 The screen header

```
eyebrow above, h1 below
optional back chevron, 20pt, muted, 44 × 44 target
optional right slot for a segmented control
```

---

# Part 12 — Screens

Specified at the level the design system owns — order and composition, not copy.

## 12.1 Onboarding

Steps: welcome → sports → adaptive questions → **review → calculating** → result → done →
data. Chrome is a header, and — on the questionnaire — the question navigator
([7.9](#79-the-question-navigator)) beneath it.

**Done is the end of the first part, not the end of onboarding.** A player who has not yet
committed a Player profile takes the second part's six steps between done and data — the
summary is the screen they enter it from. The order is a product decision rather than a
design one and lives in the app's `CLAUDE.md`; what it fixes here is that _done_ is a screen
two different flows continue from, so its action bar carries one control whose label names
whichever of the two it is about.

**The questionnaire stopping and the rating existing are two moments, and the review sits
between them** ([ADR-0020](../../docs/adr/0020-revisable-assessment-answers.md)). Every
player passes through both new screens, including the beginner who answered one question:
one question screen, one review, one result is one rule, and skipping the review for a short
run earns nothing.

**The eyebrow is the sole carrier of which Sport of how many.** A `coral` bar under the
header used to say it too. It measured Sports, which meant it did not move for the eight
questions a player spends the longest on, and the words were always the half readable at
any font size. One carrier, in the eyebrow: `Padel · Rating 1 of 2`.

**That step list is exhaustive. The app has one question screen.** The prototype showed a
separate _gate_ screen ("have you played this sport?") and a _history_ screen (the layoff
question); neither is a screen here. Both are ordinary questions in the engine's bank,
served through the same adaptive loop as every other question, because the engine decides
what to ask next and the client does not get a vote. Building either as its own screen
would put the engine's question order into the navigator, where it cannot be changed
without shipping an app.

**Cut from the prototype's history screen, and not to be rebuilt from it:** cross-sport
transfer, format links, external ratings, coach assessments, and verified results. These
are not deferred — they are out of the onboarding evidence surface entirely, which is why
onboarding cannot exceed 30% confidence. Anyone reading the prototype later will find
these screens in it; they are listed here so the answer is already written down.

### The question screen

**The reading order is fixed and deliberate: category → progress → situation → question →
answers.**

```
Match execution                          ← h1 is the CATEGORY, not the question
Padel · Rating 1 of 1                    ← eyebrow

Question 3     [discriminating]
┌─ card ────────────────────────────────────────┐
│ ── PICTURE THIS ──────────── paper2 header ──  │
│ A deep lob pushes you off the net             │  13 / 600
│ ─────────────────────────────────────────────  │
│ How often do you play a controlled overhead   │  15 / 700 / −0.38
│ and recover position, instead of going for a  │
│ winner?                                       │
│ A normal match against players at your level  │  tiny
└───────────────────────────────────────────────┘
[ Almost never ]      ← five pressable cards — selection only, never submission
[ Next ]              ← primary button, present from the start, disabled until selected
```

**The situation is a shaded header inside the same card as the question** — on `paper2`
with a 1pt bottom border. **The question is never the page title**, because a title is read
last on a screen the eye scans top-down.

Difficulty is a tag: basic / standard / **discriminating** (hot).

**Tapping an answer selects it; it does not submit.** Submission is the `Next` button —
the deliberate giving of one answer, which is why a mis-tap costs nothing and no timed undo
window is needed.

**A player may walk back over the questions they have answered, and it costs nothing.**
That is a domain rule, not a styling one
([ADR-0020](../../docs/adr/0020-revisable-assessment-answers.md), which supersedes the
irreversibility rule of [ADR-0017](../../docs/adr/0017-rating-context-event-sourced.md) and
leaves the rest of it standing). The whole run is served with every step, so moving issues
no request; an answered question is drawn with the recorded option **selected**; and the
way back is the header's back chevron ([10.3](#103-the-screen-header)), never the navigator,
which is not a target ([7.9](#79-the-question-navigator)).

**Changing an answer discards every answer after it**, because each was pitched at a
difficulty chosen from the estimate as it then stood — so a change is put in front of the
player, with what it costs, before it happens rather than after.

**Leaving is not going back.** The close control in the header's right slot is the way
_out_ of the flow; the back control in the left slot is the way back _through_ it. Two
doors, two sides of one header, and they are not interchangeable.

**The button label never changes.** The engine decides it has enough information _after_
the answer arrives, so the client cannot know which question is the last one — and it no
longer matters that it cannot, because answering never creates the rating. The label was a
compromise and is now simply correct. The review arrives without a countdown, which suits a
flow that never asks the player to brace for a verdict.

**Where the questionnaire has stopped, the forward control leads to the review** and says
so, because there is no next question to promise. It is the same move — one step towards
the end of the run — and the only place on this screen that could name a screen the run
cannot produce.

### The review screen

The last look before the rating exists, and the first time the player sees the whole account
of themselves rather than one question at a time.

```
Check your answers                       ← h1
Padel · Rating 1 of 2                    ← eyebrow — the Sport it belongs to

This is everything your Padel level …    ← tiny, muted
┌─ pressable card ──────────────────────────────┐
│ QUESTION 1                                    │  eyebrow
│ Have you played padel before?                 │  question
│ ─────────────────────────────────────────────  │  the fold
│ YOUR ANSWER                                   │  eyebrow
│ I play most weeks                             │  h2
└───────────────────────────────────────────────┘  … one per answer, in order
[ Get my Padel level ]   ← screen action, the one control that creates the rating
```

**No Level, likely range or Confidence appears anywhere on it.** The no-running-estimate
rule ([Part 16](#part-16--amendments-after-locking), 2026-08-13) applies here exactly as it
applies to a question, and with more force: every answer on this screen is still editable,
so a number on it is an invitation to tune answers until it reads the way the player wants.

**The whole card is the control**, and it opens that question in the questionnaire rather
than editing anything here. A change costs later answers, and what it costs is named by the
question screen's own confirmation — a second place to change an answer is a second place
the cost can be misstated.

**The header carries the way out and not a way back.** The right slot is the close control,
identical to the questionnaire's, because reaching the end must not be the one screen with
no exit. The left slot is empty: there is no question behind this screen, and every answer
is reachable from the list.

### The calculating screen

One indicator, one short line naming the Sport, no chrome and no controls.

**It is held for a minimum time** (`theme.motion.hold.calculating`) and is the one thing in
this system that reduced motion does not skip — nothing moves except the indicator, and a
held screen is not an animation. Completion is one round trip over fast arithmetic, so
without the floor this appears and leaves inside a frame, which reads as a glitch rather
than as the moment a Level came into existence.

**The copy and the duration are one decision.** A sentence a player cannot finish before the
screen leaves is worse than no sentence, so the line stays one short line; lengthening
either means revisiting both.

**Nothing can be left from here.** No close control and no back: the rating is already being
created, and a control that appeared to cancel it would be a promise this screen cannot
keep.

### The result screen

**Upper half — the verdict.** A dark card with the level at `levelHero`, the likely range,
a confidence ring ([7.8](#78-the-confidence-ring)), the level bar with labels and legend
([7.5](#75-the-level-bar)), and a band/status/questions row. Then a light card whose **3pt
left border is the band's own ink** — the only place a band colour appears outside the bar.

Three information marks, three anchored popovers.

**Lower half — the evidence trail.** The verdict alone is a number without an account of
itself, and the rating is never only a number. The trail is **two lists, and they stay
apart**, because they answer different questions:

```
WHAT MOVED THE LEVEL      each kind of evidence, fused on its own, and where
                          that sits relative to the estimate given
                          → direction is a shape and a word, never colour alone

WHAT WIDENED THE RANGE    a layoff, a contradiction, an uneven profile — each
                          reporting how much uncertainty it actually added
                          → never drawn as an up or a down
```

**Nothing appears in both lists, and the second list has no direction.** Something that
widened the range did not move the level, and drawing it with an arrow would describe a
different rating than the one produced. Where a contributor sits is computed by comparing
it against the estimate; the confidence reason is whichever thing widened the range most.
**No copy in this app decides either** — retuning a constant moves the explanation with it,
which is the whole point ([`CONTEXT.md`](../../CONTEXT.md)).

Where calibration priority is raised, it is stated as a property of the _estimate_ — it
changes who the player is matched with, never where they sit — and it is never phrased as a
judgement of the player.

Each contributor is a row ([5.5](#55-row--the-key-value-line)); the two lists are separated by a
hairline, not by two cards, because they are one account with two halves.

**The action is rate the next sport, or stop.** Where more than one sport was chosen the
primary control **names** the next one — `Rate Tennis`, never `Next sport` — with
`Done for now` beneath it as a secondary. Where nothing is queued behind this rating there
is one control and it leads to the summary: an offer to continue, with nothing to continue
to, is a choice the player does not have. Both paths go through the done screen, because a
player who stopped after one rating is owed the same account of the run as one who finished.

### The done screen

One card per sport. The sport's identity colour is its **3pt left rail** — the same rail
the note ([5.4](#54-note--the-message-block)) and the result screen's band card use —
with the sport's name beside it, because a rail is not readable and no state is carried by
colour alone.

Inside each card, as rows ([5.5](#55-row--the-key-value-line)): Level, likely range,
Confidence, Rating status. **Every figure is mono and tabular.** That is not the general
rule being restated — several cards sit one under another here, and a column of levels that
shifts as its digits change is the exact thing tabular figures exist to stop.

Then one `tiny` line per card saying **which of two things held the Confidence where it
is**: the questionnaire's own ceiling, or the evidence. Everybody leaves at or below the
ceiling, but a rating the ceiling bound and a rating its own answers bound are not the same
rating, and one sentence for both would tell half of these players something untrue about
themselves.

**No progress bar.** The bar measures which sport is being rated, and none is; a full bar
for a player who stopped after the first of two would be the one dishonest thing this
screen could say about their run.

Under the cards, the note that frames all of them: these are **hypotheses, not verdicts**,
and real matches are what narrow them.

### The data screen

Four cards — the closing counterpart to welcome's three, and deliberately the same shape:
what is kept, what is never done with it, that **no one, including staff, can hand-edit a
Level**, and that any sport can be rated again later. Brief, final, and the last thing
onboarding says.

**It reads nothing and writes nothing.** No endpoint, no cache, no state — the screen is
copy and one control.

**It is not a consent form and must never become one.** Nothing here is recorded and there
is no control that means yes. The match-proposals opt-in is its own explicit, skippable
step whenever it arrives; folding it into a screen the player passes through on the way out
would collect an agreement nobody read.

---

# Part 13 — Accessibility

The prototype's Part 21 recorded what was present and what was missing. **Everything in
the missing column is a requirement here.**

**Locked in:**

- **Contrast.** Every pair in [2.5](#25-contrast--computed) is AA or better at the size it
  is used. The prototype's `tiny` at 3.9:1 is fixed by the `muted` change.
- **Touch targets.** 44 × 44pt minimum reachable area ([6.5](#65-touch-targets)).
- **Reduced motion.** `AccessibilityInfo.isReduceMotionEnabled` disables every animation
  and press transform, checked once and held in context.
- **Tabular numerals** everywhere numbers are compared.
- **Live announcements.** Every toast announces, **queued** —
  `announceForAccessibilityWithOptions` with `queue`, and **one exception**. The bare call
  _interrupts_ on both platforms, and this requirement was written against onboarding, which
  has one toast at a time; nineteen fire from the Play tab, and one landing mid-card cuts a
  listener off in the middle of what they were listening to. The requirement keeps its force
  and names its mechanism precisely — an amendment, not an exception.
  **The send confirmation interrupts, and earns it**: [#227](https://github.com/Raketa02/Raketa/issues/227)
  made the send discard the Play stack to a placeholder, so the toast is the _entire_
  confirmation that the one irreversible act in the feature succeeded, and it fires after the
  destination mounts so the platform's own screen-change notification does not clobber it.
  A second exception is an amendment, never a call-site decision (`the-words.md` §20.10).
  `queue` is honoured on iOS and is not a thing on Android, where the interrupting call is
  what a queued announcement falls back to.
- **Modal semantics.** The sheet and the popover set `accessibilityViewIsModal` (iOS) and
  hide siblings (Android), and return focus to the trigger on close.
- **Names on everything tappable.** Tabs, info marks, the popover close, answer options,
  the question navigator's dots. **A control's label is its content _and_ its state** —
  a navigator dot reads "question 3, answered" — because colour is not available to a
  screen reader.
- **State, not just style.** `accessibilityState` for selected chips, tabs and segments.
- **Dynamic Type.** Text scales with the OS setting; layouts use `flex` and wrapping rather
  than fixed heights, except where a fixed height is the design (the tab bar).
  **`allowFontScaling={false}` is permitted only inside the level bar's drawn geometry**,
  where a scaled label would break the alignment of the bar it labels.

**Never:** colour as the only signal. Every state carries a word or a shape — that is what
the tag variants and the navigator's filled-versus-hollow dots are for.

---

# Part 14 — Corrections applied to the prototype

The [prototype audit](design-system-v34-prototype-audit.md) recorded eight inconsistencies
and five accessibility gaps. All are resolved here. **This table is the diff.**

> **Kept verbatim through the 2026-08-25 reset.** Some rows correct components the reset
> then removed — the match card, the fit badge, the empty-seat avatar. The rows stay because
> this table is a _record of what was decided and why_, not a description of the current
> tree, and the reasoning in the right-hand column is what a rebuilt component would be
> argued from. Editing it to match today's tree would delete the evidence.

| #   | Prototype                                                                                                            | Locked here                                                                                                           | Why                                                                                       |
| --- | -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 1   | `--surface` declared, never used; cards hard-code `#fff`                                                             | `surface` is the one white and every card uses it                                                                     | A token nothing references is a lie about the system                                      |
| 2   | `--paper2` used before it was defined                                                                                | Declared once in `theme.ts`                                                                                           | Ordering hazards do not survive into a typed object                                       |
| 3   | Sport colours alias semantic colours                                                                                 | Kept, but resolved through the semantic tokens rather than duplicated hexes                                           | The aliasing is deliberate; the duplication was not                                       |
| 4   | Band drawing ranges contiguous, model ranges not                                                                     | Kept, and stated: the bar draws the contiguous values, **any printed range comes from the model's `bandLo`/`bandHi`** | Two different numbers; confusing them is a correctness bug                                |
| 5   | No spacing scale — 5, 6, 7, 9, 10, 11, 12, 13, 14, 15                                                                | **A 3pt grid: 3, 6, 9, 12, 15, 18, 24, 30.** Every prototype value is within 1pt                                      | The grid was already there and unnamed                                                    |
| 6   | No icon set — `currentColor` squares                                                                                 | Kept as an honest placeholder; the 16pt box and position are specified, the glyph set is a separate recorded decision | Specifying a glyph we do not have would be worse than a square                            |
| 7   | Two "open seat" casings                                                                                              | **"Open seat" as a label, "the open seat" in prose.** Both were right; the rule was missing                           |                                                                                           |
| 8   | The deck maintains a parallel implementation of the match card, band bar and popover, kept in sync by hand           | **One implementation.** These are components in `src/shared/ui/`, used everywhere                                     | The prototype says they have drifted before                                               |
| 9   | `--muted` `#6E7F85` — `tiny` at 11pt is **3.73:1** on paper                                                          | **`#5C6D73`** — 4.83 paper / 5.40 surface / 4.62 line2                                                                | The audit's own headline accessibility failure                                            |
| 10  | `--amber` `#9A6A0B` — 4.18 on its soft                                                                               | **`#8A5E09`** — 5.04                                                                                                  | The warn tag is 9.5pt                                                                     |
| 11  | mint on mintSoft — 3.54                                                                                              | **`mintInk` `#0A7355`** — 5.08                                                                                        | The ok tag is 9.5pt                                                                       |
| 12  | White on `coral` (3.89) and `mint` (4.07): primary button, high fit badge, success toast, _me_ avatar                | **Rule C** — `coralInk` / `mintInk` fills; `ink` is the only dark permitted on coral                                  | Nothing in this app reaches WCAG's large-text threshold, so "AA-large only" means "fails" |
| 13  | Band names drawn in the deep values — **2.83–3.20 on paper**                                                         | **Band `ink` values** — 4.51–4.59                                                                                     | Not recorded in the audit; found by computation                                           |
| 14  | Empty-seat avatar: 1.5pt dashed border in `--line` — **1.17:1**                                                      | Dashed border in `muted` — 4.83:1                                                                                     | The only dashed element in the app, carrying real meaning, and it was invisible           |
| 15  | Free slot border `#BFE0D2` — **1.27:1 on white**                                                                     | Border in `mint` — 4.07:1                                                                                             | A pale fill on a white card needs a visible border or the control disappears              |
| 16  | Likely-range bracket `#5C6B70`, an untokenised near-duplicate of muted                                               | `muted`                                                                                                               | Two colours 1 hex apart is one colour                                                     |
| 17  | No live region for the toast; no focus trap in the sheet or popover; tab icons unnamed; rails not keyboard-reachable | All required — [Part 13](#part-13--accessibility)                                                                     |                                                                                           |
| 18  | Stage, rail, phone frame, time bar, and their four hard-coded colours                                                | **Not product** — [Part 0](#part-0--reading-a-web-prototype-as-a-native-app)                                          | The harness is not the app                                                                |
| 19  | Three counter-overrides so the popover survives inside a dark card                                                   | The popover renders through the overlay root                                                                          | Fix the containment, not the symptom                                                      |

**Row 6 is retired.** The separate recorded decision it was waiting for is
[ADR-0135](../../docs/adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md): the family
is Feather, the five names are fixed, and [10.2](#102-the-tab-bar) draws them. The row stays
in the table for the reason every row here stays — it is the record of what was decided and
why, and _"specifying a glyph we do not have would be worse than a square"_ is still the
argument that kept the placeholder honest for as long as there was no bar to draw on.

Every ratio quoted was computed against WCAG 2.1, not estimated.

---

# Part 15 — Extension guide

## 15.1 Adding a component

1. **Is it one of the existing primitives?** card · dark card · note · row · tag · chip ·
   button. If yes, use it.
2. **Colour:** pick the _meaning_, then the token. Never a hex. Check Rule C if white text
   will sit on it.
3. **Space:** from the 3pt grid. 9 between cards, 15 at the gutter.
4. **Radius:** bigger surface, rounder — from the radius list.
5. **Type:** from the roles. Secondary text is always `tiny`. Numbers are always mono.
6. **Touch:** 44 × 44pt reachable, `hitSlop` if the visual is smaller.
7. **Press state:** declare it. There is no hover to fall back on.
8. **Accessibility:** a name, a role, and a state. Never colour alone.

## 15.2 Adding a colour

Only if it carries a meaning none of the existing semantics carries. It needs a base, a
`Soft`, an `Ink` if text sits on either, a `Line` if the soft gets a border, **computed**
contrast against paper, surface and its own soft, and an entry in [Part 2](#part-2--colour)
and in `theme.ts`.

## 15.3 Adding a size or a spacing step

Don't, first. If a surface genuinely needs one, change `theme.ts` and this document in the
same commit. **A local `fontSize: 12` is a bug**, not an extension.

## 15.4 Dark mode

**There is no dark mode.** The app is paper-only, and the dark card is a _component_, not a
theme. Adding one is a new ADR, not a styling change — every semantic soft background and
every `Ink` would need a second computed value.

---

# Part 16 — Amendments after locking

[Part 14](#part-14--corrections-applied-to-the-prototype) is the diff against the
prototype. This is the diff against **this document**, for changes made after it was locked
by [ADR-0012](../../docs/adr/0012-player-app-design-system.md). A locked document is not an
unchangeable one; it is one whose changes are recorded rather than absorbed.

| Date       | Section                                                                                               | Was                                                                                                                                                                                                             | Is                                                                                                                                                                                                                                                                                                                                                                                                                                                | Why                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ---------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-08-13 | [12.1](#121-onboarding) question screen                                                               | The header row carried the running estimate: `Question 3  [discriminating]  [3,17 so far]`                                                                                                                      | The estimate is removed. The tag stays                                                                                                                                                                                                                                                                                                                                                                                                            | A live number reframes the questionnaire from _describe yourself accurately_ to _make this number go up_. A player who answers honestly, watches 3,4 fall to 2,9 and feels the drop has been taught mid-flow that honesty is expensive — which corrupts the only evidence the engine has. It is also the least explained number in the app, in a screen whose final figures each earn an information mark and a popover because _"none is self-explanatory"_. The difficulty tag survives because three coarse values read as _we think you can handle a hard one_, not as a score                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 2026-08-13 | [12.1](#121-onboarding) question screen                                                               | Five pressable cards, tap to answer                                                                                                                                                                             | Five cards select; a `Next` button submits                                                                                                                                                                                                                                                                                                                                                                                                        | Answers are irreversible ([ADR-0017](../../docs/adr/0017-rating-context-event-sourced.md)), and taking a reflex tap and making it permanent is a bad bargain. The confirm is the moment the player accepts finality, and it makes a timed undo window unnecessary                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| 2026-08-14 | [7.8](#78-the-confidence-ring)                                                                        | The confidence ring was named in [2.2](#22-accent-and-semantics) and required by [12.1](#121-onboarding), but never specified as a component — no diameter, stroke, track, cap or ceiling treatment             | **Specified**: 72 × 72, stroke 6, butt caps, track `onDarkHair`, arc `volt`, a 2pt radial ceiling tick at 30%, value in `numXL` inside and an `eyebrow` label beneath                                                                                                                                                                                                                                                                             | An agent building it would have been inventing design rather than implementing it. Added through [15.1](#151-adding-a-component); the stroke matches the level bar's band segments and the diameter is on the 3pt grid                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 2026-08-14 | [7.8](#78-the-confidence-ring)                                                                        | —                                                                                                                                                                                                               | The ring's scale is **always the full 0–100**, with the 30% onboarding ceiling marked on the track                                                                                                                                                                                                                                                                                                                                                | The same reasoning as the level bar's fixed 1,00–5,00 scale: a value must land in the same place everywhere or the component means different things on different screens. Every player leaves onboarding at or below 30%, so a bare arc would read as failure; the tick makes the short arc legible as _as far as a questionnaire can prove_, and keeps the component honest when matches later push confidence to 75%                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 2026-08-14 | [12.1](#121-onboarding) result screen                                                                 | The lower half stopped at the band-meaning card                                                                                                                                                                 | The **evidence trail** is recorded as specified composition: two lists — what moved the level, what widened the range — kept apart, the second carrying no direction                                                                                                                                                                                                                                                                              | The source specification calls the trail critical, and the engine already supplies it as structured data. Leaving it unspecified invited each implementer to invent a layout for the one part of the screen that explains the rest                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 2026-08-14 | [12.1](#121-onboarding)                                                                               | The step list was correct but silent about the prototype's _gate_ and _history_ screens                                                                                                                         | A note: both are engine questions, not screens — **the app has one question screen** — and the rest of the history screen is listed as cut content                                                                                                                                                                                                                                                                                                | The step list being correct was not the same as it being unambiguous. Someone reading the prototype later would have found two screens with no record of why they are absent, and rebuilt them                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 2026-08-14 | [7.5](#75-the-level-bar)                                                                              | The bar's geometry lived only in this section's prose, while the ring's lived in `theme.ts`                                                                                                                     | The same numbers are now `size.levelBar` tokens, as `size.ring*` already were. **No value moved** — the y coordinates are kept as coordinates so the token block reads against the spec line by line                                                                                                                                                                                                                                              | Appendix A says this document and `theme.ts` are one contract. Half a drawn object in each was how a value gets changed in one place; the ring had already set the pattern                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 2026-08-14 | [7.5](#75-the-level-bar)                                                                              | The bar's colours assumed paper: bracket in `muted`, band names in the band `ink` values                                                                                                                        | An **on-dark repaint** ([5.2](#52-dark-card)): bracket and unselected names in `onDarkTiny`, the current name in white, separators and the mark's ring in the card colour. `ink` and `tint` are untouched on paper                                                                                                                                                                                                                                | [12.1](#121-onboarding) puts this bar inside the dark card, where `muted` is about 1,6:1 and the band inks about 2,4:1 — [Part 13](#part-13--accessibility) permits neither at any size. The band `tint` values would have passed, but they are the bar's and never text's; band identity is carried by the segment, and the current name by weight 800 against 600, so nothing rests on colour                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 2026-08-14 | [12.1](#121-onboarding) result screen                                                                 | "Each contributor is a row", of both lists                                                                                                                                                                      | Contributions are rows; **range-wideners are notes**, carrying the server's own label, detail and the σ each added                                                                                                                                                                                                                                                                                                                                | A widener carries a sentence and a row is a line. Drawing the wideners as rows meant either dropping the detail the engine authors for each of them or letting a key-value line wrap to three lines. The two lists still share one card and one fold, which is what "one account with two halves" was protecting                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 2026-08-14 | [12.1](#121-onboarding) done screen                                                                   | The step list named the screen; nothing said what is on it                                                                                                                                                      | **Specified composition**: a card per sport with the sport's colour as its 3pt rail, four rows of figures in tabular mono, a line saying whether the ceiling or the evidence held the Confidence, and the hypotheses note. No progress bar                                                                                                                                                                                                        | The screen a player leaves onboarding through was the one with no composition at all, so every implementer would have invented one. The line about the Confidence is the part that could not be left to an implementer: it is the difference between _a questionnaire cannot prove more_ and _your answers left something unsettled_, and choosing one sentence for both tells half of these players something untrue about themselves                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 2026-08-14 | [12.1](#121-onboarding) data screen                                                                   | Named in the step list only                                                                                                                                                                                     | **Specified composition**: four cards mirroring welcome's three, and the two properties that are not layout — it reads and writes nothing, and it is **not a consent form**                                                                                                                                                                                                                                                                       | Same gap as the done screen, with one addition worth writing down rather than remembering: a screen listing what is kept, sitting one tap before the app, is exactly where a consent checkbox gets added by someone who means well. Saying it is out of scope in a PRD lasts one slice; saying it here lasts                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| 2026-08-14 | [12.1](#121-onboarding) result screen                                                                 | The result screen's action was unspecified                                                                                                                                                                      | The primary control **names** the next chosen sport, with `Done for now` beside it; with nothing queued there is one control and it leads to the summary                                                                                                                                                                                                                                                                                          | Multi-sport is in the step list and the result screen is where a run either continues or ends, so its action carries the whole of it. Naming the sport is the part that is easy to lose: `Next sport` asks a player to remember what they chose several minutes ago                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 2026-08-14 | [7.8](#78-the-confidence-ring)                                                                        | The ceiling tick is drawn at 30%, always                                                                                                                                                                        | The tick is drawn at the ceiling the **response** carries, and is **omitted** where none was carried                                                                                                                                                                                                                                                                                                                                              | 30% was a client-side copy of a number only the engine can keep honest: it is scoped to an engine version, so a retune desynchronised the tick, the ring's accessible name and the "held by the ceiling or by your own answers" sentence from the Confidence they describe — silently, in builds already on phones. Serving it removes the copy. Omission is the case the copy hid: a rating replayed from a retired engine keeps its numbers and loses its explanation, and a default tick would state a limit that did not exist when it was produced. No rendered change today — the served ceiling is 30                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| 2026-08-15 | [12.1](#121-onboarding) question screen                                                               | _"it is irreversible — there is no back control anywhere in the questionnaire"_, citing [ADR-0017](../../docs/adr/0017-rating-context-event-sourced.md)                                                         | **Removed**, and replaced by the revision rule of [ADR-0020](../../docs/adr/0020-revisable-assessment-answers.md): a player may walk back over the questions they have answered, and changing one discards every answer after it                                                                                                                                                                                                                  | ADR-0020 supersedes exactly that rule of ADR-0017 and leaves every other decision in it standing. The cost ADR-0017 named and accepted in writing — _"it costs the player the ability to change their mind two questions later"_ — lands on the first thing anybody does in this app, in the flow that is the **entire** evidence surface for the rating, so a mis-tap on question three is a permanent distortion of a Level every later feature reads. The confirm survives and its reasoning survives with it; what it earns is now one deliberate answer rather than the finality of the run                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 2026-08-15 | [12.1](#121-onboarding) question screen                                                               | The button label never changes, _because the client cannot know which question is the last one_                                                                                                                 | The rule stands; the reason is that it no longer matters. Answering never creates the rating                                                                                                                                                                                                                                                                                                                                                      | The client still cannot predict the last question. Leaving only that argument would leave the strongest one unstated — with the commitment moved off the last answer, the identical label stopped being a compromise and became simply correct. A wart retired rather than inherited                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 2026-08-15 | [12.1](#121-onboarding), [7.3](#73-meter-and-bar)                                                     | Chrome is a header plus a `coral` progress bar measuring **Sports**, repeating the eyebrow's `Rating 1 of 2`                                                                                                    | The bar is gone from onboarding. The eyebrow is the **sole** carrier of Sport position, and the questionnaire draws the navigator ([7.9](#79-the-question-navigator)) instead                                                                                                                                                                                                                                                                     | The bar measured the one denominator the player chose, which is honest and useless: rating two Sports, it moves once, so the screen a player spends the longest on showed no movement for eight questions. Two carriers of one fact was also how a Sport denominator would come back to a bar that no longer counts Sports — recording the eyebrow as the only one is what stops that. `Bar` itself is untouched for every other use                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 2026-08-15 | [7.9](#79-the-question-navigator)                                                                     | —                                                                                                                                                                                                               | **New section.** The question navigator: fixed-width segments in a left-aligned row, `coral` where answered and `line2` where not, double height where the player is standing, no total, and not a touch target                                                                                                                                                                                                                                   | The bar's replacement needed specifying before it was built or every implementer would invent it, the way the confidence ring did. Two decisions in it are load-bearing and neither is taste: **no segment for an unasked question**, because that segment is the denominator the engine does not have; and **indicates rather than navigates**, because ten segments across the content width is a 29pt target against Part 13's 44pt minimum, and the tap it would get wrong is the one that discards answers                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 2026-08-15 | [10.3](#103-the-screen-header)                                                                        | The back chevron was specified and forbidden — no screen in onboarding could use it                                                                                                                             | Unchanged as a component, and now **used**: it is the questionnaire's way back through the run                                                                                                                                                                                                                                                                                                                                                    | It needed no design, only permission. Worth a row because the control existing all along is what made "the navigator indicates rather than navigates" cost nothing: the movement had a home before the indicator did                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 2026-08-15 | [12.1](#121-onboarding)                                                                               | The step list ended the questionnaire at the result screen, because answering the last question created the rating                                                                                              | **Two screens added**: the step list is welcome → sports → questions → **review → calculating** → result → done → data, each with its own specified composition                                                                                                                                                                                                                                                                                   | Stopping and completing are two moments now, and the screen between them had nowhere to be described. Both are visual surfaces with no composition at all, which is the gap the done and data screens were amended to close on 2026-08-14 — an implementer would otherwise invent one. Every player passes through both, the beginner with one answer included: one question screen, one review, one result is one rule, and exempting short runs is a second rule that earns nothing                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 2026-08-15 | [12.1](#121-onboarding) review screen                                                                 | —                                                                                                                                                                                                               | **New section.** A pressable card per answer — question above the fold, the option chosen below it — in the order asked, the Sport in the eyebrow, one screen action that creates the rating, and the questionnaire's own close control                                                                                                                                                                                                           | The load-bearing rule is the one that looks like an omission: **no Level, range or Confidence anywhere**. This is the only screen in the app that shows a player their whole evidence while they can still change it, so a number on it turns the questionnaire from _describe yourself_ into _make this read higher_ — the same argument that removed the running estimate, at the point it would bite hardest. The card opening the question rather than editing in place keeps one place a change can happen, which is the place that names what it costs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| 2026-08-15 | [12.1](#121-onboarding) calculating screen                                                            | —                                                                                                                                                                                                               | **New section.** An indicator and one short line naming the Sport, no chrome and no way out, **held for a minimum duration** and not skipped under reduced motion                                                                                                                                                                                                                                                                                 | The duration is the specification, not decoration: the request is one round trip over fast arithmetic, so unheld this screen appears and leaves inside a frame and reads as a glitch at the exact moment a Level comes into existence. Recording it here is what couples it to its copy — one short line, because a sentence a player cannot finish before the screen leaves is worse than none. `theme.motion.hold` lands with it, nested so the motion block keeps its one-line contract (_the four things reduced motion skips_)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 2026-08-15 | [12.1](#121-onboarding) question screen                                                               | The forward control over answered questions read `Next question` everywhere                                                                                                                                     | At the end of a **stopped** run it reads that it leads back to the answers, because there is no next question                                                                                                                                                                                                                                                                                                                                     | The same move, and the one place this screen could name a screen the run cannot produce. It appeared with the review: before the stop existed, walking forward always arrived at a question                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| 2026-08-25 | [6.2](#62-chip--the-filter-pill)                                                                      | Specified since the document was locked and never built. The app shipped the tag, which is deliberately never pressable, so _a pressable pill is a chip_ had nothing to point at                                | Unchanged as a component, and now **used**: the Social tags step selects from eighteen of them, and the profile editor will reuse the same control                                                                                                                                                                                                                                                                                                | It needed no design, only a use — the same shape as the back chevron's row above, and worth a row for the same reason. The chip is the one of these four that was already specified, and recording it here is what stops the step that needs it re-specifying a control that has sat in 6.2 since locking. Its selected treatment was re-read against _never colour alone_ and stands: inverting to `ink` is a 17,50:1 **luminance** change rather than a change of hue, and [Part 13](#part-13--accessibility) already requires `accessibilityState` on it                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| 2026-08-25 | [6.8](#68-the-availability-grid)                                                                      | —                                                                                                                                                                                                               | **New section.** The availability grid: seven rows of three, Monday first, days down and parts of the day across, cells 44 tall and ≥ 65 wide with no `hitSlop` to grant, two states carried by an `ink` inversion **and** a tick, a reserved two-line footnote slot, and an empty grid drawn as the complete answer it is. Registered in [6.5](#65-touch-targets) and [6.6](#66-press-states)                                                    | The precedent [7.8](#78-the-confidence-ring) and [7.9](#79-the-question-navigator) set: an agent building this would have been inventing design rather than implementing it. Two decisions in it are load-bearing and neither is taste. **Days are rows**, because seven columns want 7 × 44 = 308pt against the 290pt of content the narrowest phone has, and no hit-slop closes a 2,6pt-per-cell deficit against neighbours 6pt apart — `profileControlGeometry.test.ts` pins that division, because it is the kind of arithmetic that holds on the phone an agent tests on and fails on the one a player owns. And **6.7 is not reused**: the deleted slot squares were four states deep because a court is free, held, taken or yours, where a cell here has two and can book nothing, and a section number in this document never moves ([Part 17](#part-17--what-the-reset-removed))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 2026-08-25 | [6.9](#69-the-photo-tile-and-picker)                                                                  | —                                                                                                                                                                                                               | **New section.** The photo tile and picker: three 3:4 tiles across the content width always, the ceiling as a fact of the layout rather than a disabled button, one foot strip with three mutually exclusive occupants — profile, uploading, failed — a 44pt remove square anchored inside the tile, promotion by pressing what remains of it, and the generated court poster. Registered in [6.5](#65-touch-targets) and [6.6](#66-press-states) | The same gap, with two parts that could not be left to an implementer. **The foot strip**, because every other way of marking a photo puts a translucent badge over an image nobody has seen — `onDarkTag` is computed against `night` and means nothing over a bright sky, and a `line2` progress track is invisible on a photograph. One solid strip fixes the ratio whatever the player photographed, and being one slot rather than three stacked badges is what leaves the settled tile undecorated. **The poster**, because the two ways to get it wrong are both attractive: a drawing that varied in colour would assign meaning to a hash in a palette where every colour already means something, and the four `sport` colours would have it claim a sport the player may not play; a drawing that gestured at a person is one somebody mistakes for a photograph, in the one place a photograph answers a question a drawing cannot                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 2026-08-25 | [6.9](#69-the-photo-tile-and-picker)                                                                  | The remove control had a size, a target, a position and a press state, and no fill or mark                                                                                                                      | **Specified**: a solid `night` square with a white mark at the `tag` radius, inset from the tile's corner by its own 8pt slop                                                                                                                                                                                                                                                                                                                     | Found while building the section. Every other object on the tile states what it is drawn on and this one did not, and the two obvious fills are both wrong for the reason the strip's own paragraph gives — a translucent scrim over an unknown photograph has an unknown ratio, and [9.1](#91-bottom-sheet)'s `line2` close circle is a paper-surface object that disappears over a bright sky                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 2026-08-25 | [6.10](#610-the-radius-slider)                                                                        | —                                                                                                                                                                                                               | **New section.** The radius slider: the 44pt **row** is the touch surface rather than the thumb, a `line2` track with a `night` fill and a `night` thumb inside a 3pt `surface` ring, the figure in a width-reserved box and the plain words beneath it, no ticks and no end labels, and `adjustable` with increment and decrement. Registered in [6.5](#65-touch-targets) and [6.6](#66-press-states)                                            | The load-bearing rule is the one that reads as an omission: **the minimum, the maximum, the step and the default are not in this document and not in `theme.ts`**. They are served by `GET /player-profile/options`, they are re-validated on the write path, and they are product's to retune — so a slider shipping `1` and `50` compiled in would be a second, staler copy of a rule the server already owns, in builds already on phones. That is the ceiling precedent of [7.8](#78-the-confidence-ring), and the reason the scale is the full **served** range rather than a fixed one. The row rather than the thumb being the touch surface is what gets the control to 44pt without a `hitSlop` entry; `adjustable` with increment and decrement is the part sliders universally ship without, and a drag-only slider is unusable with a screen reader                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 2026-08-26 | [6.1](#61-button)                                                                                     | Three variants: `primary`, `dark`, `secondary`                                                                                                                                                                  | A fourth, **`settled`** — `mintInk` filled, white label, brightening to `mint` on press                                                                                                                                                                                                                                                                                                                                                           | The location step needed a control whose **state is the message**: the area has been read, and pressing again would only read it a second time. Every existing variant says something else — `primary` claims the accent a screen may only spend once ([1.2](#12-the-one-accent-rule)), `secondary` reads as the lesser of two actions, and `dark` is a filled action with no meaning attached. Mint is this system's word for _settled, safe, covered_ ([1.3](#13-semantic-colour)), so it is the only colour that could carry it, and Rule C picks `mintInk` over `mint` at 4.07:1. It brightens on press exactly as `primary` does, with the same momentary exception. **Its label changes with its fill**, which is what keeps it inside _never colour alone_ ([Part 13](#part-13--accessibility)) — the variant is half of a state and the screen owns the other half                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 2026-08-27 | [6.11](#611-the-tick-box)                                                                             | There was no tick box, and no specified control for a claim a player either makes or does not                                                                                                                   | **Specified**: 6.8's cell at 20pt with 6.8's own tick, the whole row as the touch surface, no pre-ticked state, and a refused border drawn only while unticked. Registered in [6.5](#65-touch-targets) and [6.6](#66-press-states)                                                                                                                                                                                                                | The sign-up form has to ask whether the player is an adult ([ADR-0124](../../docs/adr/0124-the-matcher-gates-account-state-never-age.md)), and Part 6 specified exactly one ticked thing — a grid cell. Left unrecorded, the form would have invented a second idea of what _ticked_ looks like beside the one that exists, which is what [15.1](#151-adding-a-component) is for. Added through it: no new colour, no new radius, and the one new size is 6.8's cell brought down to the height a line of text wants                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 2026-08-31 | [2.2](#22-accent-and-semantics)                                                                       | _"Volt never appears on paper. It is illegible there (~1.3:1) and is never used there."_                                                                                                                        | **Volt is a fill anywhere and a stroke only on dark.** A volt fill carries `ink`; an emphasis that wanted a volt stroke on paper becomes a volt tag, and an in-progress state on paper is `coral`                                                                                                                                                                                                                                                 | Play's entire _they want you_ signal is volt, and it used volt on paper in four places that are two different kinds of use. The **fills** — the interest tag, the _even it out_ button — carry `ink` at **13.96:1**, which [2.5](#25-contrast--computed) already listed as AAA: they violated the sentence and nothing else. The **strokes** — a 2pt border on the interest card, the search ring, the ring on a newly added slot — are ~1.3:1 and are the bug corrections **#14** and **#15** already fixed once. So the argument is upheld and the sentence narrowed to what the argument actually covers: volt's problem on paper is contrast as a **foreground**, and a fill inverts that. A `voltLine` companion dark enough to read on paper was refused — that is no longer volt; moving interest to `coral` was refused — coral is the action colour, and _they want you_ is a fact about somebody else. The card's emphasis becoming a tag is what [Part 13](#part-13--accessibility) prefers anyway: a border carries no word and this signal has one                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 2026-08-31 | [2.3](#23-sport-identity)                                                                             | The aliasing was defended by a stated premise — _"the dot is always accompanied by the sport name in text"_ — and a stated trip-wire                                                                            | The same decision, with the premise recorded as **tested**: checked against every Play site that draws a sport hue — sport chips, sport tags on the player record, the court gradient — and the three named in the section. The trip-wire is unchanged                                                                                                                                                                                            | The UI spec asked for four dedicated sport hues and called it _the single highest-value colour change in the feature_, which is a proposal to overturn a stated argument rather than a token collision. The premise is falsifiable, so it was tested rather than re-asserted: there is no Play surface where a sport hue appears with no sport name on screen, and the objection is stated as purity without ever producing a screen where the aliasing misleads. Play's real adjacency risk — a coral padel court beside a coral primary button — is answered by the court's scrim, not by four new hues. The next feature inherits evidence instead of a claim, and a fifth sport still reopens it                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 2026-08-31 | [2.5](#25-contrast--computed)                                                                         | Every pair in the table is a **fixed** pair. There was no rule at all for text over a **generated** fill                                                                                                        | Four rows for white plus `textOnMedia` on the court ground, one per sport, and a subsection stating the rule: the scrim is pinned, every label over the court carries the shadow, the side labels stay at white `.6` on the arithmetic, and the four ratios are derived by [`textOnMedia.test.ts`](../src/shared/ui/textOnMedia.test.ts) rather than typed                                                                                        | The one contrast risk this document did not answer. The court's ground is drawn **from the selected sport's hue**, so the ratio behind a white label depended on which sport a player picked and no fixed pair could state it. Pinning the scrim is what makes it finite: the hue is at most 7% of the ground, so the dark end is `night` whatever the sport and the light end is one of four known composites — four ratios rather than an unbounded set. The `.6` side labels were expected to need raising and do not: **5.46** against the worst of the four, which is recorded precisely because a value left alone on evidence is one the next reader changes back. Derived rather than published, for the reason `bandEdges.test.ts` gives — a number two documents restate is a number that drifts in one of them                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 2026-08-31 | [`theme.ts`](../src/shared/ui/theme.ts) · [12.1](#121-onboarding)'s precedent                         | `motion.hold` held one duration a screen is **shown** for, `calculating`                                                                                                                                        | **`motion.hold.pool: 1100`** and **`motion.hold.fill: 650`** — the Play tab's two minimum-display floors, nested with `calculating` and `toast` rather than added flat                                                                                                                                                                                                                                                                            | The same argument `calculating` was added on, at two more screens: a floor exists _so a fast answer does not flash past_, which is **legibility rather than motion**, so reduced motion does not skip it — the player who asked the OS to calm things down is the last one who should get a flash. The engine fill's timing **splits** here: this number is the held half of its `650 plus 550 per seat`, and the 550-per-seat stagger is motion, collapses to zero under either collapse condition, and lands every seat together after this same beat. The stagger is not a token because it belongs to the court that draws it; both floors are, because two screens share them and a floor typed twice is a floor that drifts                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| 2026-08-31 | [3.2](#32-weights-are-family-names-not-numbers) · [3.3](#33-the-type-roles)                           | _"Display numbers — always mono, weight 700"_, while [3.2](#32-weights-are-family-names-not-numbers)'s family table carried no mono 700 row                                                                     | **Weight 600** — and 500 at `numS` / `numXS`. [3.2](#32-weights-are-family-names-not-numbers) states that mono stops at 600 and that the dash is the specification                                                                                                                                                                                                                                                                                | Three parties disagreed and **the code was the only one that was right**. The UI spec found the prototype's real bug — `.num` requests 800, IBM Plex Mono ships 400/500/600, so every mono figure was synthetically bolded — and prescribed _load mono 700_. `fonts.ts` loads 400/500/600 and `theme.ts` uses `mono[600]` for every display role, so the app never had the bug: the prose carried it and the code did not. A 700 mono is a bundle cost for a weight this system has never rendered, so the prescription is refused and the prose corrected instead. The diagnosis was right; the app had already satisfied it by a cheaper route                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 2026-08-31 | [4.2](#42-radius)                                                                                     | The radius list stopped at 15 (dark card) and 22 (sheet)                                                                                                                                                        | **`deckCard: 18`**, with the paragraph that says it is not a card                                                                                                                                                                                                                                                                                                                                                                                 | Radius 18 is the one radius in Play the list did not already cover — every other value the prototype used was inside 1pt of a token, including the photo's 14 → 13. It is named for the surface rather than added to the card family because the deck card is a transient object being manipulated, and the competitive candidate card in the pool stays a card at 13. That ends a condition where two candidate surfaces were one shape at two radii                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 2026-08-31 | [4.3](#43-elevation)                                                                                  | _"Three shadows exist. **Cards never have one**"_                                                                                                                                                               | A **fourth**, for the deck card, and the sentence intact — it applies to cards, and [4.2](#42-radius) says the deck card is not one                                                                                                                                                                                                                                                                                                               | The deck card animates in, and translates and rotates out under the thumb; real swipe is proposed on the grounds that the animation already implies it. That makes it a fourth member of the floating family rather than a fifth exception to a rule about cards, and naming what the rule applies to is what lets the rule survive whole. Calibrated for RN the way the other three are: it has the largest negative spread of any shadow here — 26 of 40 blur — so it is the tightest and the faintest, and it floats least                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| 2026-08-31 | [6.1](#61-button)                                                                                     | Four variants: `primary`, `dark`, `secondary`, `settled`                                                                                                                                                        | A fifth, **`volt`** — filled `volt`, label `ink`, pressed `opacity: .7`                                                                                                                                                                                                                                                                                                                                                                           | Play needs a control for _they want you to play_ and every existing variant says something else: `primary` claims the accent a screen may only spend once ([1.2](#12-one-accent-used-sparingly)), `secondary` reads as the lesser of two actions, `dark` is a filled action with no meaning attached, and `settled` is mint's. It is the one variant that does not have the others' shape — its label is `ink` rather than white, and its press is an opacity rather than a fill. Both follow from volt itself: `ink` on volt is 13.96:1 and white on it is not readable, and volt is already the brightest value in the palette with no darker companion to press to                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 2026-08-31 | [6.6](#66-press-states)                                                                               | The volt button had no registered press                                                                                                                                                                         | `opacity: .7`, over its one fill                                                                                                                                                                                                                                                                                                                                                                                                                  | The system's existing answer for a pressed surface with no second fill — the chip, the segment, the availability cell, the photo tile and the tick-box row all take it. A seventh hex invented to satisfy _the variant's pressed fill_ would be a colour added to describe a press, which [15.2](#152-adding-a-colour) refuses on its face: it carries no meaning nothing else carries. Registered here rather than left in [6.1](#61-button), because this table is where a build session looks for what a finger does                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 2026-08-31 | [2.5](#25-contrast--computed) · [4.3](#43-elevation)                                                  | —                                                                                                                                                                                                               | **Two new tokens.** `color.courtScrim` — the `night` colour at **`.93`** — and `shadow.textOnMedia`, a `textShadow` rather than an elevation                                                                                                                                                                                                                                                                                                      | The prototype's two court call sites disagreed at `.92` (read-only) and `.94` (interactive), and a scrim that is not one number is a ground whose worst case cannot be computed at all; pinning it is what turns an unbounded set of ratios into four. It is the `night` colour rather than the prototype's `rgba(6,26,33,·)` for the reason [9.1](#91-bottom-sheet)'s scrim is: the dim matches the palette, and that hex carries no meaning the palette does not already have ([15.2](#152-adding-a-colour)). `textOnMedia` is lifted from the seat labels' own `0 1px 3px rgba(0,0,0,.6)` and applied to **both** label sets — the prototype gave it to the seats and not to the side labels, which are the lower-contrast of the two. The generated poster inherits it and sets its own lightness floor separately, its hue being player-derived rather than one of four                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| 2026-08-31 | [4.3](#43-elevation)                                                                                  | Four shadows, none of them tinted                                                                                                                                                                               | A **fifth**, the ⚡Play disc's, in `coral` — and the calibration table that turns the prototype's `-6px` spread into a radius, an offset and an opacity RN can actually express                                                                                                                                                                                                                                                                   | The one thing in the bottom chrome that floats, and it floats in its own colour. Stated with the Android caveat, because `elevation` cannot be tinted and half the platform gets a dim instead                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 2026-08-31 | [6.6](#66-press-states)                                                                               | The tab bar had no registered press at all                                                                                                                                                                      | Two: `opacity: .7` on a tab **column**, and [6.1](#61-button) `primary`'s `coral` on the ⚡Play disc — which does **not** also dim                                                                                                                                                                                                                                                                                                                | One channel per state. The disc has a second fill and the flanks do not, so each takes the answer its own surface allows                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 2026-08-31 | [10.1](#101-screen-structure)                                                                         | The structure, stated and never confirmed against a specification that proposed the opposite                                                                                                                    | The same structure, recorded as **confirmed for Play**: the header pins above the scroller, the CTA and the bar are flex siblings below it, and the **bar owns the bottom inset**                                                                                                                                                                                                                                                                 | The counter-argument is a viewport budget computed against a phone with no safe areas, so it gets worse on a real device. An inset applied twice is 34pt of nothing                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 2026-08-31 | [10.2](#102-the-tab-bar)                                                                              | Geometry for a bar nobody had built: paddings, a 16pt box, `currentColor` squares, and no label role at all                                                                                                     | The whole bar. Five columns, a 30pt disc at radius 11 in [6.1](#61-button) `primary` with `shadow.fab`, a 2pt `coral` ring **absolutely positioned**, `tag` labels under a **derived** `maxFontSizeMultiplier`, Feather and its five names, no badge — and [Part 14](#part-14--corrections-applied-to-the-prototype) row 6 retired                                                                                                                | The bar ships, so every question it was holding open is now due. Volt lost the ring by measurement (1.25:1) and the disc lost white-on-`coral` to Rule C; the cap is derived because a guessed one fails on one word, on one phone, at one OS setting                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 2026-08-31 | [4.3](#43-elevation) · [10.2](#102-the-tab-bar)                                                       | —                                                                                                                                                                                                               | **Four new values in `theme.ts`.** `size.fab` **28 → 30**, `radius.fab: 11`, a `size.tabBar` block holding the bolt, the ring's gap and stroke and the derived label cap, and `shadow.fab`                                                                                                                                                                                                                                                        | `size.fab` was unreferenced and off the 3pt grid at both values; 30 is what the bar draws. The ring is kept as its two stated numbers rather than a pre-added 38, and the bar does the arithmetic                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| 2026-08-31 | [6.9](#69-the-photo-tile-and-picker)                                                                  | _"It is never a person. No face, no silhouette, no initials"_ and _"it varies in geometry and never in colour"_ — a singles court in three colours, cropped by a hash into eight framings by six ball positions | **The poster draws a player.** One of three poses — forehand, serve, lunge — flat, in `ink`, with **no face and no likeness of any kind**, holding a racket, over a two-stop gradient on one of sixteen `POSTER_HUES`. The composition is fixed and whole and the **crops are retired**; the ball is `volt`; the `<Defs>` id comes from `useId()`                                                                                                 | Both refusals are **dissolved rather than overruled** ([ADR-0134](../../docs/adr/0134-the-poster-draws-a-player-and-no-value-is-invented.md)). The first was protecting one sentence — _the poster must not appear to answer do I want to play this person_ — which a **face** answers and a flat unfaced pictogram does not, so the line moves to no likeness and the constraint becomes the rule. The second was protecting [2.3](#23-sport-identity)'s Sport aliasing, which a `hash % 360` would have broken on the very surface it had just been checked against — so the hash picks from a **designed set** instead, and no poster can claim a Sport by construction. The crops go because their own file conceded the case against them: forty-eight crops of one court is a deck where every card is the same picture, and at 27pt a crop of a court carries no identity at all                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 2026-08-31 | [2.5](#25-contrast--computed)                                                                         | _"The generated poster is not covered here"_ — one line deferring it to [6.9](#69-the-photo-tile-and-picker)                                                                                                    | **Two rows and a subsection.** White + `textOnMedia` on a poster hue's light stop at **4,60–4,65**, `ink` on its dark stop at **3,09–3,12**, both derived in `posterHues.test.ts`                                                                                                                                                                                                                                                                 | The poster is the second generated fill and the first with a foreground requirement of its own, so it stops being a forward reference. Two requirements bind the stop pair from opposite ends — 4.5:1 for white at the light end, 3:1 for the `ink` figure at the dark — and what makes sixteen hues into two rows is that the set is designed at **one lightness per stop**. It also records what that costs: the two bounds confine the ground to one band, so the ramp can never exceed 1,23×                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 2026-08-31 | [6.9](#69-the-photo-tile-and-picker)                                                                  | `CourtPoster` took a framing and no colour; `theme.ts` had no poster values                                                                                                                                     | **`POSTER_HUES` in `theme.ts`, outside `color`** — sixteen hues, one lightness-and-chroma pair per stop — and a `hue` prop on `CourtPoster` typed as a member of it                                                                                                                                                                                                                                                                               | It is **not a semantic colour**: [1.3](#13-semantic-colour-is-never-decorative) picks colour by meaning and this one is picked by a hash, so it must not be reachable where a semantic colour is expected. The prop is the **first place in this system where a component takes a colour it did not get from `theme.color`**, so _a literal hex in a component is a bug_ now has one named exception, and it is bounded by a type rather than by a convention. The pair is fixed in **CIE LCh(uv)** and not in sRGB HSL: sixteen hues at one HSL `S`/`L` vary in luminance by a factor of three between the greens and the blues, and every such pair that clears both bounds is grey                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 2026-08-31 | [6.8](#68-the-availability-grid)                                                                      | The grid had one mode: twenty-one `checkbox` cells with two states between them                                                                                                                                 | A **diff variant** — the same seven-by-three geometry, not interactive, with a third fact per cell: added and dropped                                                                                                                                                                                                                                                                                                                             | `the-words.md` §20.7 calls the diff grid _"a different control with a third fact … not interactive"_, which describes a second **accessibility tree** and not a second file. It is 6.8's geometry exactly, and a second copy of that grid is the drift `Tick` was extracted to prevent. The prototype's scheme is replaced by the arrival rather than after it: _new_ drew a volt ring and _dropped_ drew 45% opacity — colour as the only signal twice over, on a sheet whose own body copy names the colour as the mechanism — and a volt ring on paper is 1,3:1. The three facts are three **shapes** from the tick's own family, and `Tick.tsx` gains `Plus` and `Dash`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| 2026-09-01 | [3.3](#33-the-type-roles) · [6.3](#63-segmented-control)                                              | 6.3 stated `label 10.5 / 700` and 3.3 carried no role at that pair                                                                                                                                              | **New type role, `seg`.** 10.5 / 700, no tracking, sentence case — plus the subsection saying why it is neither `chip` nor `flab`                                                                                                                                                                                                                                                                                                                 | 6.3 closes with _"nothing uses it today; it is specified so the first screen that needs one does not invent a second shape"_, and Play's two ways through the tab are that screen. The **value** was specified from the day the document was locked; what was missing was a **role** to read it from, and a component reaching for `chip` (600, a filter) or `flab` (uppercase, tracked, a control you operate) would have been the second shape 6.3 exists to prevent. Three roles now sit at 10.5, which is why the subsection states what separates them rather than leaving the next reader to guess                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 2026-08-31 | [6.12](#612-the-switch)                                                                               | —                                                                                                                                                                                                               | **New section.** The switch: a 40 × 23 track at the pill radius, an 18pt knob, the 44pt **row** as the touch surface, and `switch` with `checked`                                                                                                                                                                                                                                                                                                 | Nothing in Part 6 carried `checked` on a **mode** — [6.11](#611-the-tick-box) says outright that it is not a switch, 6.3 picks one of several and 6.2 narrows what is on screen — and `the-words.md` §20.4 fixed the swap toggle's role as `switch`. The knob takes **two values**, which is the one object in this system that does: `surface` on the unchecked track is 1,2:1, so the prototype's white knob was invisible in half its states                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 2026-08-31 | [7.10](#710-the-fit-pill)                                                                             | Deleted with the Match Fit engine in the reset, as **7.1**, with [Part 17](#part-17--what-the-reset-removed) warning that its 90 threshold _"named a scale the deleted engine defined"_                         | **New section**, at a new number. The fit pill: 26 tall at `radius.fit`, `night` by default and `coral` with `ink` on it at Fit ≥ 90 — and the scale **restated**: Fit is out of 100                                                                                                                                                                                                                                                              | A returning component does not reclaim its old number; the gaps are the record ([6.8](#68-the-availability-grid)'s own row settled that). The threshold is **re-argued rather than inherited**: `CONTEXT.md` defines Fit as one number out of a hundred, and 90 is the top tenth of that scale rather than a fourth meaning [15.2](#152-adding-a-colour) would forbid. `ink` on the coral and not `#fff`, which is 3,89:1 and the pairing Rule C refuses; 26 tall and not 23, because UI §G1 records the class defaults being used at none of the five call sites                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| 2026-08-31 | [7.11](#711-the-balance-bar)                                                                          | Deleted with the pairing / balance-forecast engine in the reset, as **7.2**                                                                                                                                     | **New section**, at a new number. The balance bar: three heights, one mapping, one amplification constant of 34 and **one** clamp at 20–80                                                                                                                                                                                                                                                                                                        | The prototype had one formula and **three clamps** — 22–78 on the forecast card, 20–80 on two others — so the same gap landed in a different place on two screens, which is the defect [7.5](#75-the-level-bar) and [7.8](#78-the-confidence-ring) exist to prevent. Drawing the raw shares would be honest and invisible. A steep scale is still a fixed scale; what was wrong was three of them. The tones are the `*Ink` values, per Rule C, and the segment labels are `tag` at the two larger sizes and absent at the smallest — #219 B4's floor, not a smaller step. It also takes [7.5](#75-the-level-bar)'s **on-dark repaint**, because the pool header draws it inside a dark card and React Native has no colour cascade                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 2026-08-31 | [7.12](#712-the-court)                                                                                | The court was drawn twice in the prototype and specified nowhere                                                                                                                                                | **New section.** The court: a Sport and a box in, the ground and the chrome and the seat **positions** out, and **children in seat order**                                                                                                                                                                                                                                                                                                        | A `useCourtGeometry` hook **returns** the coordinates, and returned geometry gets adjusted at one call site and not the other — the drift this Part exists to prevent, through the door the rule was written to close. With children the positions never leave the module. **H-25 is why they cannot be derived**: squash has no net and no two sides, so a reflection about the middle draws three Sports right and one wrong. Padel's glass wall and its `.28` inner lines go — a lighter mark over a boundary already there, and one line weight across four courts                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 2026-08-31 | [4.2](#42-radius) · [`theme.ts`](../src/shared/ui/theme.ts)                                           | —                                                                                                                                                                                                               | **`radius.court: 9`**, `size.switch`, `size.court` (including the per-Sport seat coordinates), `size.balanceBar` as three heights, `size.fit` 23 → **26**, and `motion.hold.toast`                                                                                                                                                                                                                                                                | Appendix A's contract: the document and `theme.ts` change in one commit. The seat coordinates are tokens on [7.5](#75-the-level-bar)'s precedent — half a drawn object in each file is how a value gets changed in one place. The court's chrome is **opacities of one white** rather than five rgba values, because a generated ground's lines are one colour at a set of weights and five near-identical whites in a palette that picks by meaning are five colours that mean nothing                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 2026-08-31 | [9.2](#92-toast) · [9.3](#93-layer-order)                                                             | Specified and unbuilt: a position, three fills and _every toast announces_                                                                                                                                      | **Built** — the queue, the live region and the dismiss, mounted **once** at the overlay host                                                                                                                                                                                                                                                                                                                                                      | 9.3 requires a single root-level overlay host and this is its first occupant; the queue is `shared/store/` and not a feature's, because a queue inside a feature is that feature owning every other feature's toasts. A **queue and not a stack**, because the announcement is queued and three sentences on screen while a listener is read one is the two channels disagreeing. The interrupting message takes the **head** as well as `queue: false` — a flag alone would leave the send confirmation waiting two holds to be spoken at all. The dismiss is the **hold**: `pointerEvents: 'none'` is 9.2's own rule and a close control is a tap the toast has to eat. Nothing animates ([1.5](#15-nothing-animates-that-does-not-have-to)), so there is no reduced-motion branch                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 2026-08-31 | [Part 13](#part-13--accessibility)                                                                    | _"Live announcements. Every toast calls `announceForAccessibility`."_                                                                                                                                           | Every toast announces, **queued** — `announceForAccessibilityWithOptions` with `queue` — with the **send confirmation** as the single interrupting exception                                                                                                                                                                                                                                                                                      | The bare call interrupts on both platforms, and the requirement was written against onboarding, which has one toast at a time. Nineteen fire from the Play tab and one landing mid-card cuts a listener off. The requirement keeps its force and names its mechanism precisely — an **amendment, not an exception**. The send confirmation earns the one interruption because [#227](https://github.com/Raketa02/Raketa/issues/227) made the send discard the stack to a placeholder, so the toast is the entire confirmation that the one irreversible act succeeded (`the-words.md` §20.10)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| 2026-08-31 | [10.2](#102-the-tab-bar)                                                                              | The bar's height existed only as the sum of five tokens in its own stylesheet                                                                                                                                   | **`TAB_BAR_HEIGHT`**, derived from those same five, exported                                                                                                                                                                                                                                                                                                                                                                                      | [9.2](#92-toast) positions the toast _above the tab bar_, and the alternative was the toast holding a second copy of the bar's paddings, its hairline, the ⚡Play disc and its label. It is the height at the **default** text size and says so: `labelMaxScale` grows the labels, so it is the floor 9.2 asks for rather than a promise                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 2026-09-01 | [6.8](#68-the-availability-grid)                                                                      | Two cell states and nothing else on the editor grid: ticked, or not                                                                                                                                             | A **third fact** on an editor cell — _added for this search_, drawn as the diff variant's plus in `ink` on the **unfilled** cell — and `Tick.tsx` gains a second plus for that bed                                                                                                                                                                                                                                                                | A times rung adds one slot to the searcher's own grid for one search, and until the grid marks that cell the week the player just filled in disagrees with the search that ran, with nothing on any screen to say so ([#283](https://github.com/Raketa02/Raketa/issues/283), [#223](https://github.com/Raketa02/Raketa/issues/223) §8). It is a **fact and not a state**, which is what keeps the two paragraphs above it true: the cell is unselected, reports itself unchecked, and toggles like its neighbours — pressing it is how a player makes the widening their own. The fill is what could not be borrowed from the diff variant: an inverted cell would say the slot is part of the ask, and the ask is exactly what a rung does not change. `volt` could not be borrowed either, for the bed rather than for the meaning                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 2026-09-01 | [Part 13](#part-13--accessibility) · [6.6](#66-press-states)                                          | Press-and-hold appeared as a press _state_ (6.6's avatar peek) and nowhere as an interaction rule                                                                                                               | **A hold is a fallback and never the only way to reach anything.** There is no long-press gesture in the accessibility API, so every destination a hold reaches must also be reachable by a control a listener can navigate to. 6.6's peek row is unchanged; the court's seat takes no ring, because it already dims on press-in and _one channel per state_ is 6.6's own rule                                                                    | The Play court had a 430 ms holding ring inherited from the prototype, feeding two sheets K-7 removed. Deciding where the gesture lands ([#278](https://github.com/Raketa02/Raketa/issues/278)) needed a rule about holds rather than one more hold: the app's only implemented one is the deck card's, on the platform default and with no feedback at all                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| 2026-09-02 | [7.12](#712-the-court) · [`theme.ts`](../src/shared/ui/theme.ts)                                      | The court took a width from its caller and every caller passed the content width                                                                                                                                | `size.court.build` **196** — the width at which a seat is the 46pt the section's own rules are written against — and `size.court.thumb` **54**, the court drawn as a picture beside a sentence                                                                                                                                                                                                                                                    | Two of this section's rules quote a 46pt seat and neither was true of anything on screen: at the content width the seat is 81pt on a large phone. A drawn object with rules about its parts is sized by the part                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 2026-09-02 | [Part 4](#part-4--space-radius-and-elevation) · [`theme.ts`](../src/shared/ui/theme.ts)               | `motion` was four transitions and _"nothing else moves"_                                                                                                                                                        | A fifth, `ripple` **1400** — one expanding ring, the only **looping** animation in the app, and `size.ripple` / `size.rippleStroke` for its box                                                                                                                                                                                                                                                                                                   | The engine seating a court is the one open-ended wait in the product, and it is now drawn under the court rather than over the screen. A spinner says _loading_; a ring says _something is being looked for_, which is what is happening. Skipped under reduced motion like the four above it, and there the ring is drawn at rest                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 2026-09-02 | [6.8](#68-the-availability-grid) · [6.5](#65-touch-targets) · [`theme.ts`](../src/shared/ui/theme.ts) | The grid was a bare block of squares on the page, cells `surface` with a 1pt `line` border and `ink` when ticked, and the footnote floating beneath it                                                          | **The week gets a card**: `surface`, `radius.card`, 12pt padding, with the footnote **inside** it under a 1pt hairline. Cells lose their borders and take `paper2` unticked and `mint` ticked; the heads and day labels go `flab` / `ink`; the footnote goes `rlLabel` / `muted`. The layout is unchanged — **days are still rows**                                                                                                               | The grid is the only control in the app whose subject is a **pattern**, and 21 bordered squares floating on paper read as a table of fields rather than as a week. A card is what makes it one object, and the footnote belongs inside it because the sentence is about the grid — floating beneath, it belonged to whatever came next on the page as much as to the week above it. **The turn to seven day columns was built and reverted**: it reads better and it cannot be touched — 7 × 44 = 308 against 290pt of content, missed on the widest phone in the population too, so it is a property of seven columns rather than a device to design around. The card costs 6pt of cell width and the cell still clears the minimum at 59,5; `profileControlGeometry.test.ts` now states that **margin** as well as the bound, because it is small enough that padding added elsewhere could spend it                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 2026-09-02 | [6.8](#68-the-availability-grid)                                                                      | The selected cell was an `ink` fill with a 1pt `ink` border, and `ink` was argued for against `mint` on the grounds that the grid is _a preference and not a promise_                                           | **`paper2` unticked and `mint` ticked**, no border, and the 12 × 12 tick unchanged on top of it                                                                                                                                                                                                                                                                                                                                                   | The _preference and not a promise_ reading held for a **status**, and this is not one: the cell says _I could play then_, and nothing reads a green square as a booking. What decided it is the drawing — 21 `ink` rectangles on a card read as holes punched through it. The pair is legal on its own at **3,39:1**, a luminance step of 0,824 → 0,208, which is what [Part 13](#part-13--accessibility) asks of a non-text graphical object — and the tick **stays**, because 21 rectangles differing only in lightness are a texture and that argument is about lightness rather than about which two fills. The tick is `surface` on `mint` at 4,07:1: a 2pt stroke is a graphical object and clears 3:1, which is not the white **type** [Rule C](#22-accent-and-semantics) refuses                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 2026-09-02 | [6.2](#62-chip--the-filter-pill)                                                                      | The chip was a label and nothing else; [6.4](#64-tag--the-status-pill)'s optional sport dot had no equivalent on the pressable pill                                                                             | An optional **6pt square dot** before the label, in a sport's identity colour, hidden from assistive technology and **not inverted** by the selected fill                                                                                                                                                                                                                                                                                         | Play's sport row is four names a player picks between on every search, and four names read word by word is the one row on that screen with nothing to pick it out by. It is 6.4's square rather than a second dot shape — [15.1](#151-adding-a-component) — with no new colour, no new size and no new radius. Not inverting it is the load-bearing half: a sport's hue is an **identity** and the chip's fill is a **state**, and a dot that changed with the selection would make two facts share one channel. It stays decoration, which is the condition [2.3](#23-sport-identity) attaches to every surface drawing a sport hue                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 2026-09-02 | [6.3](#63-segmented-control) · [12](#part-12--screens) Find a game                                    | _What kind of game_ was two `Button`s side by side, `dark` for the chosen one and `secondary` for the other                                                                                                     | The **segmented control**, competitive and for fun as its two halves                                                                                                                                                                                                                                                                                                                                                                              | A button is an act and these are two views of one search: the screen runs nothing until the court card is pressed, so two filled buttons were offering an act twice and performing neither. 6.3 is _"for a two- or three-way view switch within one screen"_ and this is the second one on the same screen, under [`PlaySegment`](#63-segmented-control). It also stops the mode being carried by a **fill** where the sport chips beside it already carry selection that way — the raised half on an inset track is a surface step, which is the chip's shape inverted and reads as a different kind of choice                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 2026-09-02 | [9.1](#91-bottom-sheet) · [6.8](#68-the-availability-grid)                                            | `maxHeight: 88%` on a column with no scroll under it, and a footnote slot reserved on both variants of the grid                                                                                                 | **The sheet's body scrolls** — head fixed, children in a shrinking `ScrollView`, the bottom padding moved onto the scrolled content — and the **diff** grid reserves no footnote slot                                                                                                                                                                                                                                                             | Found the way these are found: `SH.saveav`'s two answer controls were **not on the screen**. A cap with no scroll under it does not bound a sheet, it truncates one, and what a sheet truncates is always its controls — it reads statement first and answer last. Every control was still _rendered_, so nothing failed and no screen-level suite could see it; `BottomSheet.test.tsx` now asserts the two structural facts that carry it, because `flexShrink` is the half that looks right in a diff when it is missing. The grid's slot is the same rule read rather than an exception: the reservation protects a cell moving between two taps, and nothing on the diff can be tapped. **Pinning the controls outside the scroll was refused** — three of the four sheets end in something that is not a control                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 2026-09-03 | [7.12](#712-the-court)                                                                                | The seat drew the whole handle truncated to the face's width with a **tail ellipsis**, and the level on a second line under it                                                                                  | **Three characters, hard, with no ellipsis — and the level beside them on the same line**, in a box inset -9 past the face on each side                                                                                                                                                                                                                                                                                                           | A caption whose only job is telling four faces apart had four characters and spent one of them on an apology: `Pau…` and `Pav…` are two characters of signal and a mark pointing at something the player cannot go and read from here. Three letters and no mark is the same identifier with the punctuation spent on a letter, and a **fixed count** rather than the seat's own width is why it is three on every phone rather than three on one and five on another. The level joins the first line because _Pau 3,23_ reads as one identifier where a word over a figure reads as a paragraph under a dot — which costs more width than a 46pt seat has, and the caption was already absolutely positioned and bounding nothing. The whole handle is untouched in both sentences and in the spoken name, so ADR-0107 is where it was                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 2026-09-03 | [7.11](#711-the-balance-bar) · [12](#part-12--screens) the forecast card                              | _Your side_ and _their side_ were two [5.5](#55-row--the-key-value-line) rows of faces and handles under a hairline, and the card ended on a sentence saying nobody was out of their depth                      | Two **tinted panels** side by side with `vs` between them — heading, faces drawn at `minTouch`, the joined **stems** on one line and the side's strength — `line2` on your half and `BALANCE_SOFT`'s tone on theirs; the split row above them keeps its three figures and **drops both names**; and two of the five reason lines are gone                                                                                                         | A row is a key and a value, and a side of a court is neither: it is a group of people with a number attached, which is a **block**. Making it one moved the strength inside the box it is a strength of and gave the two halves a shape you compare rather than two lines you read down. The bed is the bar's own colour rather than a new one — 7.11 already paints _yours_ neutral and _theirs_ toned, so `BALANCE_SOFT` joins `BALANCE_INK` and one place decides which amber. The face **is** the target rather than a small picture centred in one, because [6.5](#65-touch-targets) bounds horizontal slop by the neighbour and two faces in a row share the gap between them: centring a 27pt face in a 44pt box solves the touch and draws a person at the size of a dot, with most of their own control blank around them. Two panels are one **height** whatever is written in them, and the name is cut at its first word break to one line — a half that wrapped stopped being comparable, and the comparison is what the panel is for. The stem is a prefix of a handle somebody typed rather than a first name nobody gave, and every sentence still carries all sixty-four characters (`handleStem`). Everything that is not a face is **drawn and hidden**: the split row above states the same facts as one element. The two removed sentences are the two that **grade the answer** — _nobody is out of their depth_, _the best all-round fit_ — printed under four figures saying exactly how matched these people are; the three that stay name which criterion the engine went looking for, which no figure carries |
| 2026-09-03 | [5.2](#52-dark-card) · [6.1](#61-button)                                                              | The dark card was for _"the two places the app states a finding rather than offering a choice"_; 6.1's **on-dark** variant was specified and unbuilt; and a button's label was one line                         | The dark card also carries **ADR-0094's play-intent declaration**, and 6.1 gains the built `onDark` variant plus an optional **`gloss`** — one `tiny` line under the label, both lines aligned to the start                                                                                                                                                                                                                                       | The declaration is a **fact about the player**, kept on their profile and read by other people's searches — and it was drawn as a [5.4](#54-note--the-message-block) note, which is the surface this app carries _reasoning_ on. On Find a game the note sat as a sibling of the mode segment, same width and same rhythm, so proximity grouped a search's toggle with a profile's answer and _"looks like the user is selecting options for the same thing"_ was the correct reading of it. The render order took the pair apart; the surface says which of the two the remaining control is. The three answers are **buttons**, not a shape copied into the feature: `theme.ts` already names the two on-dark tokens _the on-dark button_, and re-declaring a fill, a pressed fill and a blocked opacity beside them is the second copy of a primitive `src/shared/ui/README.md` exists to prevent. The gloss is what a column of near-synonyms needs and what 6.1's one-line label could not carry. The failure stays on paper as a coral note **above** the card: the repaint has no on-dark coral, and a white line inside would be a failure carried by wording alone next to a screen that draws every other one in coral                                                                                                                                                                                                                                                                                                                                                                                                         |
| 2026-09-03 | [12](#part-12--screens) Find a game                                                                   | The mode section, the week grid, the radius and the court card were drawn on every rated sport, with the declaration note beneath the mode section and the card greyed under _Say what kind of game first_      | On an **undeclared** sport the declaration is the whole of the screen under the sport chips; the form is drawn only where the standing is `searchable`. The mode section takes an **eyebrow** — _This search only_ — over a `flab` heading now reading _What kind of game tonight_                                                                                                                                                                | `play_intent_not_declared` refuses the search either way, so the declaration is a **precondition for the form existing** rather than a field on it, and two controls that never co-occur cannot be mistaken for each other. The two headings differed by two words and a question mark, and the segment was already sitting on an answer to the question the note below it was still asking. The visible words now carry the lifetime the accessible names have carried since the interstitial shipped — _this search_ against _your usual_ — and [3.3](#33-the-type-roles)'s split does the work rather than a third size: the eyebrow labels the region, the `flab` labels the segment. The greyed card goes with it, on [6.1](#61-button)'s own rule that this app never draws a pressable-looking control that refuses                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 2026-09-03 | [12](#part-12--screens) Find a game · [2.1](#21-surfaces-and-structure)                               | Once answered, the declaration had no representation on any screen: the mode segment stood alone under its heading, and the only way to change what other people read was to trip the five-search drift sheet   | A **standing line under the segment**, on the recessed `paper2` ground with the sentence `tiny` in `muted` and the declaration itself in `ink`, carrying a `sm` [6.1](#61-button) `secondary` control. It has **two states in one slot**: _Your usual at Padel is Competitive_ · _Change_, and — the moment the segment moves off it — _Just this search. Players still find you as Competitive at Padel._ · _Update_                             | The value other people's searches read had nowhere to be seen, which taught players the question had been a hurdle rather than a setting they own. It is **not a card**: [5.1](#51-card) makes a second object on a page whose subject is one question, where `paper2` is the recessed surface and this is a fact set **into** the section it is about. The two states are one slot because the disagreement is a state and not an event — moving the switch writes nothing, and the player watches the durable fact hold still while the control moves, which no sheet appearing afterwards can demonstrate. The register is deliberately the quietest in the system: `muted` on `paper2` is 4.49:1 and legal at the 11pt `tiny` is drawn at, and the one word that is not `muted` is the one word the line is about. Both accessible names carry the **lifetime** rather than the heading above them, because _Competitive_ is on this screen twice and only _your usual_ against _just this search_ tells the two apart                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 2026-09-03 | [12](#part-12--screens) You                                                                           | The tab was one citation line plus the account panel, and nothing on it was editable                                                                                                                            | The first of the three facts it cites arrives: **what other players see** — a [5.1](#51-card) card of [5.5](#55-row--the-key-value-line) rows, one per rated sport, each opening into the three answers as full-width `secondary` [6.1](#61-button) buttons with their glosses                                                                                                                                                                    | A per-sport declaration whose only home was the search form will keep reading as a search setting however it is worded there. The rows are 5.5's shape rather than a list of controls because each is a **key and a value** — the sport and what was answered for it — and the answers open in place rather than in [5.2](#52-dark-card)'s card, which is the shape reserved for the question that **gates** a search rather than one that edits an answer already given. A rated sport with no answer reads _Not set_ and never a blank: it is the first place a player can discover that a search there would be refused. The citation line stays, because the radius and the week are still owed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 2026-09-03 | [12](#part-12--screens) Match me                                                                      | The deck drew the sport chips and then the deck, with nothing on it saying what the deal was ranked against                                                                                                     | The **standing line** joins it, under the chips rather than under a segment, and in **one state**: _Dealing Competitive games at Padel — your usual_ · _Change_                                                                                                                                                                                                                                                                                   | Same object, different anchor, and the anchor is the argument. `SearchEnvelope.mode` is null on a deal, so this is the one surface in the product where the durable answer **is** what the search runs on — there is nothing here for it to disagree with, so the drift state is unreachable and the sentence can say the thing plainly that Find a game has to say in two states. It sits under the chips because on this screen the chip is the control it is about: choosing a sport is what chooses which declaration is being read. _Either suits me_ takes a frame of its own — _Dealing on your usual at Padel_ — because the deal inherits a for-fun vector from an answer that named no kind, and printing _dealing for fun games — your usual_ would report the inheritance back as the player's own answer                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 2026-09-03 | [12](#part-12--screens) Find a game · [5.1](#51-card--the-workhorse) the court card                   | An **eyebrow** — _This search only_ — over _What kind of game tonight_; a line under the radius heading; a court card of two rows — title beside a hot tag, picture beside a sentence — and a footnote under it | The heading alone, _What kind of game_; the radius section is its heading and the slider; and the card is a **centred column** of three things about one court — _Build a doubles_ / _Build a singles_, what the court is for, and the court                                                                                                                                                                                                      | The lifetime the eyebrow labelled the region with is already on the control that has it — `modeControlLabel` says _this search_, and the standing line under the segment says the durable answer — so the region label was the one copy of it a player could not act on, and _tonight_ was a metaphor for a lifetime the section no longer states. The tag said what the picture beside it already draws — _padel is doubles_ next to four drawn seats — or, on a singles court, nothing about the sport at all. The sentence beside the picture said the shape a second time, and the fact worth keeping in it is said where sending is offered rather than three screens early: [9.1](#91-bottom-sheet)'s pre-send sheet draws _nobody is contacted until you send it_ over the control that contacts somebody. What is left is a title, a sentence and a picture, so nothing is drawn beside anything and the column is centred on the axis the court is drawn on. The title names the **game** rather than the furniture: _Build the four_ against _Set up the match_ was one sentence in two registers, where _doubles_ against _singles_ is the sport's own pair and one word apart                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 2026-09-05 | [2.5](#25-contrast--computed)                                                                         | Two grounds nobody picked a colour for — the court's four composites and the poster's two stops — each closed by a bound of its own                                                                             | A **third**, and the one that cannot be enumerated at all: the competitive card's photo panel prints a Level and a Sport over a player's own photograph. `photoScrim` is pinned at `.70` and the unknowable set collapses to its **worst case** — pure white — at **5.24:1**                                                                                                                                                                      | [#309](https://github.com/Raketa02/Raketa/issues/309) put text over a photograph, which is a contrast problem this system had never had: every other pair in 2.5 is a fixed pair, and even the court's ground is at least _generated_. Pinning is the instrument that already worked twice, and it works harder here — a worst case is one row rather than four. The floor is derived as well as the pin (`.65` gives 4.51, a figure with nothing left in it), so lightening the scrim goes red instead of going unnoticed. A gradient was refused for the reason the unpinned court ground was: it would put the label somewhere on a ramp and hand back the unbounded set                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| 2026-09-05 | [6.4](#64-tag--the-status-pill)                                                                       | Six variants, all of them a `Soft` background under an `Ink` label                                                                                                                                              | A seventh, `volt` — background `volt`, label `ink`, the one variant whose background is a base colour                                                                                                                                                                                                                                                                                                                                             | The 2026-08-31 amendment ended with _the card's emphasis becoming a tag_, and named no tag. This is it. Volt has no soft and needs none: `ink` on volt is 13.96:1 and 2.5 has listed it as AAA since the document was locked, so the pair is computed rather than eyeballed — and a `voltSoft` invented to give this tag the shape of the other six is what [15.2](#152-adding-a-colour) forbids                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 2026-09-05 | [5.1](#51-card--the-workhorse) · [1.2](#12-one-accent-used-sparingly)                                 | —                                                                                                                                                                                                               | **A card's border is never an accent.** The designs' coral border on every competitive card and green border on a lifted one are both refused, and the refusals are recorded rather than re-argued                                                                                                                                                                                                                                                | Coral on a card is 5.1's **pressed** state, so a permanent one is every row in a scrolling list drawn as though a finger were on it — and 1.2 is _when everything is accented, nothing is_. The green one is volt, which is **1,25:1** on `surface` and **1,12:1** on `paper`: the 2026-08-31 amendment already refused a 2pt border on the interest card by name, refused a darker `voltLine` companion (_that is no longer volt_), and refused moving the signal to coral. `CourtEntryCard` had refused the same coral outline one screen earlier. What carries the fact is the tag, which carries a word                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |

# Part 17 — What the reset removed

On **2026-08-25** the repository was cut back to sign-up, sign-in and onboarding. The
sections below specified features that no longer exist and were deleted rather than left
standing as a specification nobody is building to.

**Numbering of the surviving sections did not change.** A design system is cited by section
number — 72 internal cross-references, plus the ADRs and `architecture.md` — and renumbering
to close the gaps would silently repoint every one of them. The gaps are the record.

| Was      | Specified                                                                                          | Why it went                                                                                                                                                                                                                                                                                                                                                                                                                              |
| -------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 6.7      | Slot squares — day / time / hour / range squares and their four-state vocabulary                   | The booking time grid. Courts and Bookings were never modelled and the contexts are gone.                                                                                                                                                                                                                                                                                                                                                |
| 7.1      | Fit badge — dark pill, coral at a score of 90+                                                     | The Match Fit engine was deleted. A badge with no number behind it is a shape, not a component.                                                                                                                                                                                                                                                                                                                                          |
| 7.2      | Balance bar — two flex-weighted children labelled with the predicted shares                        | The pairing / balance-forecast engine was deleted.                                                                                                                                                                                                                                                                                                                                                                                       |
| 7.4      | Seat avatar — filled, dashed-empty, and the coral _me_ variant                                     | Matches and seats were never modelled. This carried the app's only dashed border.                                                                                                                                                                                                                                                                                                                                                        |
| 11 (all) | Cross-screen patterns — the sport bar, the match card, the state card                              | All three are compositions of removed domain nouns. The state card's 32-context table went with the Matches context.                                                                                                                                                                                                                                                                                                                     |
| 12.2     | Find — the Games / Courts tabs, the fit-ordered list, the club cards                               |                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 12.3     | Match detail — the state card, the five numbers, the seat row, the deadline strip, the money block |                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 12.4     | Creating — the two-mode choice, the calendar, the overlap block                                    |                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 12.5     | Passport, Wallet, Score                                                                            | Wallet was the money ledger and Score the player score, both removed. **Passport was the per-sport ratings view** — the one entry here with a live subject, since ratings survive. It is deleted rather than kept because it specified a per-format block, and `CONTEXT.md` is explicit that **there is no `Format`**: one rating per sport. A screen for reading ratings is a fresh design against the vocabulary that actually exists. |

**Do not restore any of these from the v34 prototype or the audit.** They were measured off
a design for a product this repository no longer implements, and several are already known
to contradict the current domain — the per-format block above, and the fit badge's 90
threshold, which named a scale the deleted engine defined. Rebuilding one is an amendment
under [Part 15](#part-15--extension-guide), recorded in
[Part 16](#part-16--amendments-after-locking).

**Two of them have come back, and neither reclaimed its number.** The Match Fit engine and the
balance-forecast engine both ship again, so the fit badge and the balance bar return — as
[7.10](#710-the-fit-pill) and [7.11](#711-the-balance-bar), leaving 7.1 and 7.2 empty. That is
[6.8](#68-the-availability-grid)'s rule applied a second time: a section number in this
document never moves, and the gaps are the record. The warning above did its work on the way
past — 7.10 **restates** the scale its threshold is against rather than inheriting one.

---

# Appendix A — The token contract

The authoritative values live in
[`../src/shared/ui/theme.ts`](../src/shared/ui/theme.ts). That file and this document
change together, in the same commit.

# Appendix B — Quick reference card

```
COLOUR      coral = the one accent · mint = settled · amber = reversible · red = ended badly
            info = explanation, not status · volt FILLS anywhere, STROKES only on dark
            white text needs *Ink fills (Rule C) · ink is the only dark on coral
SURFACE     paper background · white cards · NO shadow on cards (the deck card is not one)
            line BOUNDS a thing · line2 is a FOLD inside one
TYPE        Archivo everywhere · IBM Plex Mono for every number
            weight = family name, never fontWeight · tracking in POINTS, not em
            h1 19 · h2 15 · tiny 11/16 · eyebrow 9.5 · flab labels a CONTROL
SPACE       a 3pt grid · 9 between cards · 15 at the gutter
            content width = screen − 30 · rail card = 0.74 × content
RADIUS      bigger surface, rounder · dark card 15, light card 13
TOUCH       44 × 44pt minimum reachable · hitSlop when the visual is smaller
            no hover — every pressable declares its pressed state
NUMBERS     mono + tabular · weight 600, never 700 — mono 700 is not loaded
            comma decimals · 2,71 · 65% · 60 min · 18:30
STATE       every state has a word or a shape, never colour alone
NEVER       the phone frame, the stage, the scenario rail — the harness is not the app
```
