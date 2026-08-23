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
  never absorbed silently. Locked means changes are _visible_, not forbidden.
- **Implementation:** the tokens are real code at
  [`../src/shared/ui/theme.ts`](../src/shared/ui/theme.ts). That file is the single source
  of colour, type, spacing, radius, elevation and motion values.
- **Scope: the player app only.** The club console (`frontend_club/`) has its own design
  system. The two palettes converge because it is one brand, but **the values are never
  shared** — no common package, no cross-import
  ([ADR-0005](../../docs/adr/0005-three-app-monorepo-ownership-boundaries.md)).

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
the level mark on the band bar, the FAB, the onboarding progress fill, the hot tag, and
the _me_ avatar. **Nothing else.** When everything is accented, nothing is.

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
column of prices lines up. **A level changing from 2,71 to 2,80 does not reflow its row.**

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
| `ink`     | `#101B20` | Body text, selected chip, selected slot square                           |
| `night`   | `#0A3441` | Dark cards, avatars, fit badge, meter fill, toast                        |
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

| Token       | Value     | Used for                                                                |
| ----------- | --------- | ----------------------------------------------------------------------- |
| `coral`     | `#E8482B` | The single accent. A **mark**, not a text bed                           |
| `coralSoft` | `#FDEBE6` | Backgrounds behind coral messaging                                      |
| `coralInk`  | `#B8351C` | Text on `coralSoft`; **and the fill wherever white text sits on coral** |
| `coralLine` | `#F3CFC5` | Border of a coral note                                                  |
| `mint`      | `#0C8F6B` | Good, settled, covered. A **mark**                                      |
| `mintSoft`  | `#E2F3EC` | Free time slots, ok tags                                                |
| `mintInk`   | `#0A7355` | Text on `mintSoft`; the fill wherever white text sits on mint           |
| `mintLine`  | `#CFE7DD` | Border of a mint note                                                   |
| `amber`     | `#8A5E09` | Caution, reversible                                                     |
| `amberSoft` | `#FBF0DA` | Caution backgrounds                                                     |
| `amberLine` | `#EFDCB8` | Border of an amber note                                                 |
| `red`       | `#B4392C` | Failure                                                                 |
| `redSoft`   | `#FBEAE7` | Failure backgrounds                                                     |
| `volt`      | `#D9F24B` | **Only on dark.** Confidence ring, active info mark                     |
| `info`      | `#12495B` | Explanatory notes                                                       |
| `infoSoft`  | `#EAF1F4` | Explanatory backgrounds                                                 |
| `infoLine`  | `#C7DBE3` | Explanatory borders                                                     |

**Volt never appears on paper.** It is illegible there (~1.3:1) and is never used there.
On `night` it is 10.60:1.

### Rule C — text on a saturated fill

`coral` and `mint` are **marks, not text beds**. White on them is 3.89:1 and 4.07:1 —
below AA, and nothing in this app reaches WCAG's large-text threshold (18.66pt bold).

| You want                                                                                | Use                                  |
| --------------------------------------------------------------------------------------- | ------------------------------------ |
| A coral or mint **mark** with no text (FAB, level mark, progress fill, seat ring, dots) | `coral` / `mint`                     |
| **White text** on coral — the primary button, the high fit badge                        | `coralInk` (white on it **5.89**)    |
| **White text** on mint — the success toast                                              | `mintInk` (white on it **5.84**)     |
| **Dark text** on a coral fill — the _me_ avatar's initials                              | `ink` on `coral` (**4.50**)          |
| Coral or mint **text on its own soft**                                                  | `coralInk` (5.11) / `mintInk` (5.08) |

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

| Pair                                              | Ratio     | WCAG                                |
| ------------------------------------------------- | --------- | ----------------------------------- |
| ink on paper                                      | 15.65     | AAA                                 |
| ink on surface                                    | 17.50     | AAA                                 |
| white on night                                    | 13.29     | AAA                                 |
| ink on volt                                       | 13.96     | AAA                                 |
| volt on night                                     | 10.60     | AAA                                 |
| white on night2 / info                            | 9.86      | AAA                                 |
| info on infoSoft                                  | 8.63      | AAA                                 |
| white on dark-card `tiny` (white @ .68)           | 6.97      | AAA                                 |
| white on red                                      | 5.90      | AA                                  |
| white on coralInk                                 | 5.89      | AA                                  |
| white on mintInk                                  | 5.84      | AA                                  |
| white on amber                                    | 5.70      | AA                                  |
| muted on surface                                  | 5.40      | AA                                  |
| coralInk on coralSoft                             | 5.11      | AA                                  |
| mintInk on mintSoft                               | 5.08      | AA                                  |
| red on redSoft                                    | 5.06      | AA                                  |
| amber on amberSoft                                | 5.04      | AA                                  |
| white on band ink (all four)                      | 5.05–5.13 | AA                                  |
| muted on paper                                    | 4.83      | AA                                  |
| white on dark-card `eyebrow` (white @ .52)        | 4.74      | AA                                  |
| band ink on paper (all four)                      | 4.51–4.59 | AA                                  |
| muted on line2                                    | 4.62      | AA                                  |
| muted on paper2                                   | 4.49      | AA — used at 11pt+ only             |
| **ink on coral**                                  | **4.50**  | AA — the only dark-on-coral pairing |
| coral on paper (marks: FAB, level mark, progress) | 3.48      | ≥3:1, meets **1.4.11**              |
| mint on surface (free-slot border)                | 4.07      | ≥3:1, meets **1.4.11**              |

Deliberately absent: _white on coral_ (3.89) and _white on mint_ (4.07) — see Rule C.

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

## 3.3 The type roles

There is no modular ratio — sizes are chosen per role. These are the roles; a size outside
them is a one-off that needs justifying.

| Role          | Size | Weight | Family | Purpose                             |
| ------------- | ---- | ------ | ------ | ----------------------------------- |
| `h1`          | 19   | 700    | sans   | Screen title                        |
| `h2`          | 15   | 700    | sans   | Card and section title              |
| `question`    | 15   | 700    | sans   | The onboarding question itself      |
| `cardTitle`   | 13   | 700    | sans   | Card title                          |
| `inlineTitle` | 12.5 | 600    | sans   | The most common inline title        |
| `btn`         | 12   | 700    | sans   | Button label                        |
| `rlLabel`     | 11.5 | 400    | sans   | Row label                           |
| `rlValue`     | 11.5 | 600    | sans   | Row value                           |
| `tiny`        | 11   | 400    | sans   | Secondary text everywhere           |
| `flab`        | 10.5 | 700    | sans   | **Form label** — uppercase, `night` |
| `chip`        | 10.5 | 600    | sans   | Chip label                          |
| `eyebrow`     | 9.5  | 700    | sans   | Uppercase section label, `muted`    |
| `tag`         | 9.5  | 700    | sans   | Pill text                           |

**Display numbers** — always mono, weight 700, tracking −0.035em:

| Role         | Size | Where                                        |
| ------------ | ---- | -------------------------------------------- |
| `levelHero`  | 40   | The estimated level on the onboarding result |
| `levelLarge` | 26   | Level on comparison cards                    |
| `numXL`      | 22   | Panel and summary numbers                    |
| `numL`       | 19   | Panel numbers                                |
| `numM`       | 17   | Prices and row numbers                       |
| `numS`       | 14   | Inline numbers                               |
| `numXS`      | 13   | Dense inline numbers                         |

Consolidated from the prototype: `20 → 19`, `13.5 → 13`.

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

| Radius              | Applied to                                     |
| ------------------- | ---------------------------------------------- |
| `pill` (height ÷ 2) | The chip — the only true pill                  |
| 22 (top corners)    | Bottom sheet                                   |
| 15                  | Dark card                                      |
| 13                  | Card, popover                                  |
| 12                  | Toast                                          |
| 10                  | Button, note, day square, segmented control    |
| 9                   | Range square, hour square, avatar, info button |
| 8                   | Time square, balance bar, sport dot backing    |
| 7                   | Fit badge                                      |
| 6                   | Tag, sport dot                                 |

**The pattern: the bigger the surface, the rounder.** A dark card is 15 where a light one
is 13 — the darker fill makes the corner read tighter at the same radius.

## 4.3 Elevation

Three shadows exist. **Cards never have one** — depth on paper comes from the surface
change and the 1pt `line` border.

RN cannot express CSS spread, so these are calibrated approximations, with `elevation`
for Android:

| Element     | iOS                                                                | Android         |
| ----------- | ------------------------------------------------------------------ | --------------- |
| **Sheet**   | `shadowColor #0A2028`, offset `{0,−8}`, opacity `.18`, radius `20` | `elevation: 16` |
| **Popover** | `shadowColor #0B1F2A`, offset `{0,8}`, opacity `.24`, radius `15`  | `elevation: 12` |
| **Toast**   | `shadowColor #000`, offset `{0,6}`, opacity `.24`, radius `14`     | `elevation: 10` |

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

Used for: the onboarding result, the state card on a match, the level card on the passport.

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

Used for every key-value list: price breakdowns, passport stats, wallet lines.

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
| on-dark   | `rgba(255,255,255,.17)` | `#fff` | `rgba(255,255,255,.26)`      |
| disabled  | —                       | —      | `opacity: .4`, not pressable |

Heights in practice: **32** (tertiary in a card), **34** (default), **40** (screen action),
**42** (the primary action on a result screen). All clear the touch minimum.

> Per Rule C the primary button is filled `coralInk` and **brightens to `coral` when
> pressed** — the inverse of the prototype, which put white 12pt text on `coral` (3.89:1).
> Coral still reads as the accent; the label is now legible.

## 6.2 Chip — the filter pill

```
height 27   paddingHorizontal 12   radius height/2   1pt line
background surface   label 10.5 / 600
selected: background ink, label #fff, border ink
small:    height 25, paddingHorizontal 9, label 10
```

**The only true pill in the app.** Selected is **ink-filled, not coral** — coral is
reserved for actions, and a selected filter is a state.

## 6.3 Segmented control

```
track     background line2   radius 10   padding 3   gap 3
segment   flex 1  paddingVertical 6  radius 8  label 10.5 / 700  muted
selected  background surface   label ink
```

**Inset track, raised selection — the inverse of the chip.** Used for Games/Courts and for
time-of-day.

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
| on-dark     | `rgba(255,255,255,.14)` | `#fff`     |

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

## 6.6 Press states

Touch has no hover. Every pressable declares its pressed appearance explicitly:

| Element                         | Pressed                                                |
| ------------------------------- | ------------------------------------------------------ |
| Card                            | `borderColor: coral`                                   |
| Button                          | the variant's pressed fill ([6.1](#61-button))         |
| Chip / segment / slot square    | `opacity: .7`                                          |
| Avatar (press-and-hold to peek) | `scale(.93)`, and while holding a 3pt `coralSoft` ring |

Feedback is immediate — use `Pressable`'s `pressed` state, not a 120ms animation. The
120ms in the prototype is a mouse-hover transition and has no touch equivalent.

## 6.7 Slot squares

Three siblings for the three kinds of time selector, plus the range square:

| Element      | Shape                                         |
| ------------ | --------------------------------------------- |
| Day square   | radius 10, padding 6 × 9, centred, 1pt border |
| Time square  | radius 8, height 32, mono 11.5 / 700          |
| Hour square  | radius 9, padding 6 × 9, mono 11.5 / 700      |
| Range square | radius 9, padding 6 × 9, centred, 1pt border  |

The time and range squares share a **four-state vocabulary**:

| State         | Background | Border      | Text    |
| ------------- | ---------- | ----------- | ------- |
| free          | `mintSoft` | `mint`      | `ink`   |
| off / taken   | `line2`    | transparent | `muted` |
| on / selected | `ink`      | `ink`       | `#fff`  |
| end           | `surface`  | `ink`       | `ink`   |

**`end` is the hollow square marking where a booking finishes** — the same border as
selected, the opposite fill.

> The free square's border is `mint` (4.07:1 on surface), not the prototype's `#BFE0D2`
> (1.27:1). A pale fill on a white card needs a border that is actually visible, or a free
> slot is indistinguishable from the card behind it.

---

# Part 7 — Data display

## 7.1 Fit badge

```
height 23   paddingHorizontal 9   radius 7
background night   label #fff 11 / 700
high (score ≥ 90): background coralInk
```

Dark by default, **coral at 90 or above**, so _a very good match is the only thing on a
Find card that competes with the accent_. The threshold lives in the domain layer, not in
the component.

## 7.2 Balance bar

```
height 24   radius 8   overflow hidden   background line2
two children, flex-weighted to the predicted shares
labels inside the bar: #fff, 9.5 / 700, italic
```

Percentages sit **inside** the bar. Each child's fill must come from the AA-safe set
(`night`, `night2`, `mintInk`, `coralInk`, `red`) — white text sits on it.

## 7.3 Meter and bar

| Element | Height | Radius | Track   | Fill        |
| ------- | ------ | ------ | ------- | ----------- |
| Meter   | 5      | 3      | `line2` | `night`     |
| Bar     | 4      | 2      | `line2` | caller sets |

A bar states a fraction, so it is only for a value with a denominator somebody knows. The
questionnaire has none — see [7.9](#79-the-question-navigator).

## 7.4 Seat avatar

```
27 × 27   radius 9   background night   initials #fff 9.5 / 700
empty:  no fill, 1.5pt dashed border in muted, label muted
me:     background coral, initials ink        ← Rule C
```

**A dashed border for an empty seat is the only dashed element in the app, and it means
one thing: a place that could be filled.** Its border is `muted` (4.83:1 on paper), not
`line` (1.17:1) — a dashed border nobody can see does not communicate an open seat.

Press-and-hold peeks at the player: the avatar scales to .93 and gains a 3pt `coralSoft`
ring.

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
place — on the passport, on the result card and on a comparison card alike.

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

---

# Part 8 — Scrolling patterns

Two horizontal patterns with different jobs.

| Pattern        | Behaviour                                                                              | Used for                              |
| -------------- | -------------------------------------------------------------------------------------- | ------------------------------------- |
| **Square row** | Free scroll, content-sized children, gap 6, no scrollbar                               | Day squares, chips, the match rail    |
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

**The strip's peek is `gutter − gap`, and it is a consequence rather than a number.** The
child is the whole content width, so the next card shows by the difference between the
gutter and the gap — **15 − 9 = 6pt, identical at 320pt and at 430pt**. It does not depend
on the card width at all, which is why it survives the narrowest phone untouched while a
ratio-sized rail does not.

`docs/specs/now/deltas/native-kit.md` §2 writes that number as **5**, computing `15 − 10`
from the prototype's CSS gap. Part 0.2 normalised the prototype's 5,6,7,9,10,…,15 onto the
3pt grid when this system was written, and 10 became `space.sm` = 9; the delta's own
instruction is that the peek _"is a consequence of the gutter and the gap rather than a
number of its own"_, and the consequence of **this** grid is 6. Recorded here rather than
resolved by putting an off-grid 10 back into a locked system.

**`size.railCardRatio` (0,74) is the rail's and must not be applied to a strip.** On a strip
it produces a child ~94pt narrower than the column at 430pt, showing a quarter of the _next
card's contents_ — its alert box, its fact lines — which reads as two cards rather than as a
peek. Now's enrolled strip is a strip; Now's shelves are rails and do take the ratio.

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

## 9.2 Toast

```
position  left 15, right 15, above the tab bar + bottom safe-area inset
tst       background night, #fff, radius 12, padding 12 × 15, 12 / 600
ok        background mintInk        ← Rule C, was mint (4.07:1)
bad       background red
```

`pointerEvents: 'none'` on the container **so a toast never blocks a tap.** Every toast
announces itself with `AccessibilityInfo.announceForAccessibility` — the prototype had no
live region, and a toast a screen-reader user cannot hear is a toast that did not happen.

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
  TabBar              5 columns
```

## 10.2 The tab bar

```
5 equal columns, paddingTop 6, paddingBottom = 12 + bottom safe-area inset
icon 16 × 16
FAB (centre): 28 × 28, radius 10, background coral, lifted 3 above the row
```

> **The prototype ships no icon set** — its tab icons are `currentColor` squares, an honest
> placeholder that specifies shape and position but not glyph. Real icons come from
> `@expo/vector-icons` (already available through Expo). **The design system specifies the
> 16pt box and the position; picking the glyph set is a separate, recorded decision.**
> Until then, squares are correct — a placeholder that looks like a placeholder.

Every tab needs an `accessibilityRole="tab"`, an `accessibilityLabel` and
`accessibilityState={{ selected }}`. The visible label is not enough on its own.

## 10.3 The screen header

```
eyebrow above, h1 below
optional back chevron, 20pt, muted, 44 × 44 target
optional right slot for a segmented control
```

---

# Part 11 — Cross-screen patterns

These appear in three or more places and are specified once.

## 11.1 The sport bar

A square row of chips — one per sport plus "All", each with a 6pt sport-coloured square.
Persistent across Find, Courts and Create.

## 11.2 The match card

The canonical representation of a **joinable** match, used on Home, Find, the waitlist and
the creation overlap rail.

```
┌────────────────────────────────────────────┐
│ Sat · 18:30  [Promotion]          ╭─────╮  │
│ Zabłocie Sport · 14 min           │glyph│  │
│ [●Padel] [Doubles] [Counts]       ╰─────╯  │
│                                      3/4   │
├────────────────────────────────────────────┤
│ [✦ 93] [●Forming]        38,00 zł · 0 fee  │
├────────────────────────────────────────────┤
│ optional footer line                       │
└────────────────────────────────────────────┘
```

**Left column:** mono time, optional badge, club + distance in `tiny`, then a row of tags.
**Right column:** the sport glyph with seat occupancy, and `filled/n` in mono.
Then a hairline carrying the fit badge, the state tag, and the price — **struck through
when a club card applies.**

The optional footer adds a second hairline. It exists for the creation flow, which needs
to say the category and the target level — **the two things a Find card cannot know to
say.**

## 11.3 The state card

The canonical representation of a match you are **in**: a dark card carrying the state tag,
a context line, the group facet, the court facet, and up to four lines each with a tick or
a circle marker.

**Driven entirely by a state table, so the visual is identical across all 32 contexts and
only the content changes.** This is a design property worth protecting: a bespoke state
card for one context is how 32 contexts become 32 layouts.

---

# Part 12 — Screens

Specified at the level the design system owns — order and composition, not copy.

## 12.1 Onboarding

Steps: welcome → sports → adaptive questions → **review → calculating** → result → done →
data. Chrome is a header, and — on the questionnaire — the question navigator
([7.9](#79-the-question-navigator)) beneath it.

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
the note ([5.4](#54-note--the-explanation-block)) and the result screen's band card use —
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

## 12.2 Find

Two tabs via the segmented control.

**Games** — sport bar, day chips, a filter chip with a count badge, then a match card per
match ordered by fit. The empty state is a bold line, a `tiny` explanation and a
clear-filters button. **The copy is explicit that an empty list is a true answer**, not a
failure.

**Courts** — club cards with name, distance, a "from" price and a row of hour squares.
Sorted by soonest / cheapest / nearest.

## 12.3 Match detail

The longest screen in the app. The order is part of the design:

1. State card
2. The five numbers — balance, fit, at stake, target, price
3. Balance bar with the predicted split
4. The seat row — one avatar per seat, dashed for empty, coral for me
5. Court certainty — which court, held or not, and why
6. The deadline strip — three markers on a bar
7. Money — share, card, payable
8. The pinned join/leave action

## 12.4 Creating

**Step 1** is the mode choice as two tall pressable cards with a four-row comparison each.
**Step 2** is one scrolling screen: sport → club → category → calendar → overlap → price →
rules → create.

### The calendar

A square row of day squares — weekday, date, count of free starts, and a **coral count
badge** top-right when open matches already exist that day. Then three eyebrow-labelled
grids of time squares (Morning / Afternoon / Evening), four columns.

### The overlap block

**The frame is a note plus cards, not a card containing cards.** Note tone escalates with
severity: info → coral (tight) → amber (busy) → coral (saturated).

## 12.5 Passport, Wallet, Score

- **Passport** — a dark card with the level and band bar, a per-sport row list, a
  per-format block where a sport has two, and the calibration explanation.
- **Wallet** — three totals (held / committed / settled) then a ledger of rows, each with a
  label, a reference in `tiny`, and a **signed** mono amount. Held lines carry a warn tag,
  pending refunds an ok tag.
- **Score** — a large display number, a meter, the gate threshold marked, and record rows.

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
- **Live announcements.** Every toast calls `announceForAccessibility`.
- **Modal semantics.** The sheet and the popover set `accessibilityViewIsModal` (iOS) and
  hide siblings (Android), and return focus to the trigger on close.
- **Names on everything tappable.** Tabs, info marks, the popover close, avatars, slot
  squares. A slot square's label is its time _and_ its state — "18:30, free" — because
  colour is not available to a screen reader.
- **State, not just style.** `accessibilityState` for selected chips, tabs and segments.
- **Dynamic Type.** Text scales with the OS setting; layouts use `flex` and wrapping rather
  than fixed heights, except where a fixed height is the design (slot grids, the tab bar).
  **`allowFontScaling={false}` is permitted only inside the level bar's drawn geometry**,
  where a scaled label would break the alignment of the bar it labels.

**Never:** colour as the only signal. Every state carries a word or a shape — that is what
tags, the dashed empty seat and the hollow `end` square are for.

---

# Part 14 — Corrections applied to the prototype

The [prototype audit](design-system-v34-prototype-audit.md) recorded eight inconsistencies
and five accessibility gaps. All are resolved here. **This table is the diff.**

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

Every ratio quoted was computed against WCAG 2.1, not estimated.

---

# Part 15 — Extension guide

## 15.1 Adding a component

1. **Is it one of the existing primitives?** card · dark card · note · row · tag · chip ·
   button · slot square. If yes, use it.
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

| Date       | Section                                           | Was                                                                                                                                                                                                 | Is                                                                                                                                                                                                                                         | Why                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ---------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 2026-08-13 | [12.1](#121-onboarding) question screen           | The header row carried the running estimate: `Question 3  [discriminating]  [3,17 so far]`                                                                                                          | The estimate is removed. The tag stays                                                                                                                                                                                                     | A live number reframes the questionnaire from _describe yourself accurately_ to _make this number go up_. A player who answers honestly, watches 3,4 fall to 2,9 and feels the drop has been taught mid-flow that honesty is expensive — which corrupts the only evidence the engine has. It is also the least explained number in the app, in a screen whose final figures each earn an information mark and a popover because _"none is self-explanatory"_. The difficulty tag survives because three coarse values read as _we think you can handle a hard one_, not as a score                           |
| 2026-08-13 | [12.1](#121-onboarding) question screen           | Five pressable cards, tap to answer                                                                                                                                                                 | Five cards select; a `Next` button submits                                                                                                                                                                                                 | Answers are irreversible ([ADR-0017](../../docs/adr/0017-rating-context-event-sourced.md)), and taking a reflex tap and making it permanent is a bad bargain. The confirm is the moment the player accepts finality, and it makes a timed undo window unnecessary                                                                                                                                                                                                                                                                                                                                            |
| 2026-08-14 | [7.8](#78-the-confidence-ring)                    | The confidence ring was named in [2.2](#22-accent-and-semantics) and required by [12.1](#121-onboarding), but never specified as a component — no diameter, stroke, track, cap or ceiling treatment | **Specified**: 72 × 72, stroke 6, butt caps, track `onDarkHair`, arc `volt`, a 2pt radial ceiling tick at 30%, value in `numXL` inside and an `eyebrow` label beneath                                                                      | An agent building it would have been inventing design rather than implementing it. Added through [15.1](#151-adding-a-component); the stroke matches the level bar's band segments and the diameter is on the 3pt grid                                                                                                                                                                                                                                                                                                                                                                                       |
| 2026-08-14 | [7.8](#78-the-confidence-ring)                    | —                                                                                                                                                                                                   | The ring's scale is **always the full 0–100**, with the 30% onboarding ceiling marked on the track                                                                                                                                         | The same reasoning as the level bar's fixed 1,00–5,00 scale: a value must land in the same place everywhere or the component means different things on different screens. Every player leaves onboarding at or below 30%, so a bare arc would read as failure; the tick makes the short arc legible as _as far as a questionnaire can prove_, and keeps the component honest when matches later push confidence to 75%                                                                                                                                                                                       |
| 2026-08-14 | [12.1](#121-onboarding) result screen             | The lower half stopped at the band-meaning card                                                                                                                                                     | The **evidence trail** is recorded as specified composition: two lists — what moved the level, what widened the range — kept apart, the second carrying no direction                                                                       | The source specification calls the trail critical, and the engine already supplies it as structured data. Leaving it unspecified invited each implementer to invent a layout for the one part of the screen that explains the rest                                                                                                                                                                                                                                                                                                                                                                           |
| 2026-08-14 | [12.1](#121-onboarding)                           | The step list was correct but silent about the prototype's _gate_ and _history_ screens                                                                                                             | A note: both are engine questions, not screens — **the app has one question screen** — and the rest of the history screen is listed as cut content                                                                                         | The step list being correct was not the same as it being unambiguous. Someone reading the prototype later would have found two screens with no record of why they are absent, and rebuilt them                                                                                                                                                                                                                                                                                                                                                                                                               |
| 2026-08-14 | [7.5](#75-the-level-bar)                          | The bar's geometry lived only in this section's prose, while the ring's lived in `theme.ts`                                                                                                         | The same numbers are now `size.levelBar` tokens, as `size.ring*` already were. **No value moved** — the y coordinates are kept as coordinates so the token block reads against the spec line by line                                       | Appendix A says this document and `theme.ts` are one contract. Half a drawn object in each was how a value gets changed in one place; the ring had already set the pattern                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 2026-08-14 | [7.5](#75-the-level-bar)                          | The bar's colours assumed paper: bracket in `muted`, band names in the band `ink` values                                                                                                            | An **on-dark repaint** ([5.2](#52-dark-card)): bracket and unselected names in `onDarkTiny`, the current name in white, separators and the mark's ring in the card colour. `ink` and `tint` are untouched on paper                         | [12.1](#121-onboarding) puts this bar inside the dark card, where `muted` is about 1,6:1 and the band inks about 2,4:1 — [Part 13](#part-13--accessibility) permits neither at any size. The band `tint` values would have passed, but they are the bar's and never text's; band identity is carried by the segment, and the current name by weight 800 against 600, so nothing rests on colour                                                                                                                                                                                                              |
| 2026-08-14 | [12.1](#121-onboarding) result screen             | "Each contributor is a row", of both lists                                                                                                                                                          | Contributions are rows; **range-wideners are notes**, carrying the server's own label, detail and the σ each added                                                                                                                         | A widener carries a sentence and a row is a line. Drawing the wideners as rows meant either dropping the detail the engine authors for each of them or letting a key-value line wrap to three lines. The two lists still share one card and one fold, which is what "one account with two halves" was protecting                                                                                                                                                                                                                                                                                             |
| 2026-08-14 | [12.1](#121-onboarding) done screen               | The step list named the screen; nothing said what is on it                                                                                                                                          | **Specified composition**: a card per sport with the sport's colour as its 3pt rail, four rows of figures in tabular mono, a line saying whether the ceiling or the evidence held the Confidence, and the hypotheses note. No progress bar | The screen a player leaves onboarding through was the one with no composition at all, so every implementer would have invented one. The line about the Confidence is the part that could not be left to an implementer: it is the difference between _a questionnaire cannot prove more_ and _your answers left something unsettled_, and choosing one sentence for both tells half of these players something untrue about themselves                                                                                                                                                                       |
| 2026-08-14 | [12.1](#121-onboarding) data screen               | Named in the step list only                                                                                                                                                                         | **Specified composition**: four cards mirroring welcome's three, and the two properties that are not layout — it reads and writes nothing, and it is **not a consent form**                                                                | Same gap as the done screen, with one addition worth writing down rather than remembering: a screen listing what is kept, sitting one tap before the app, is exactly where a consent checkbox gets added by someone who means well. Saying it is out of scope in a PRD lasts one slice; saying it here lasts                                                                                                                                                                                                                                                                                                 |
| 2026-08-14 | [12.1](#121-onboarding) result screen             | The result screen's action was unspecified                                                                                                                                                          | The primary control **names** the next chosen sport, with `Done for now` beside it; with nothing queued there is one control and it leads to the summary                                                                                   | Multi-sport is in the step list and the result screen is where a run either continues or ends, so its action carries the whole of it. Naming the sport is the part that is easy to lose: `Next sport` asks a player to remember what they chose several minutes ago                                                                                                                                                                                                                                                                                                                                          |
| 2026-08-14 | [7.8](#78-the-confidence-ring)                    | The ceiling tick is drawn at 30%, always                                                                                                                                                            | The tick is drawn at the ceiling the **response** carries, and is **omitted** where none was carried                                                                                                                                       | 30% was a client-side copy of a number only the engine can keep honest: it is scoped to an engine version, so a retune desynchronised the tick, the ring's accessible name and the "held by the ceiling or by your own answers" sentence from the Confidence they describe — silently, in builds already on phones. Serving it removes the copy. Omission is the case the copy hid: a rating replayed from a retired engine keeps its numbers and loses its explanation, and a default tick would state a limit that did not exist when it was produced. No rendered change today — the served ceiling is 30 |
| 2026-08-15 | [12.1](#121-onboarding) question screen           | _"it is irreversible — there is no back control anywhere in the questionnaire"_, citing [ADR-0017](../../docs/adr/0017-rating-context-event-sourced.md)                                             | **Removed**, and replaced by the revision rule of [ADR-0020](../../docs/adr/0020-revisable-assessment-answers.md): a player may walk back over the questions they have answered, and changing one discards every answer after it           | ADR-0020 supersedes exactly that rule of ADR-0017 and leaves every other decision in it standing. The cost ADR-0017 named and accepted in writing — _"it costs the player the ability to change their mind two questions later"_ — lands on the first thing anybody does in this app, in the flow that is the **entire** evidence surface for the rating, so a mis-tap on question three is a permanent distortion of a Level every later feature reads. The confirm survives and its reasoning survives with it; what it earns is now one deliberate answer rather than the finality of the run             |
| 2026-08-15 | [12.1](#121-onboarding) question screen           | The button label never changes, _because the client cannot know which question is the last one_                                                                                                     | The rule stands; the reason is that it no longer matters. Answering never creates the rating                                                                                                                                               | The client still cannot predict the last question. Leaving only that argument would leave the strongest one unstated — with the commitment moved off the last answer, the identical label stopped being a compromise and became simply correct. A wart retired rather than inherited                                                                                                                                                                                                                                                                                                                         |
| 2026-08-15 | [12.1](#121-onboarding), [7.3](#73-meter-and-bar) | Chrome is a header plus a `coral` progress bar measuring **Sports**, repeating the eyebrow's `Rating 1 of 2`                                                                                        | The bar is gone from onboarding. The eyebrow is the **sole** carrier of Sport position, and the questionnaire draws the navigator ([7.9](#79-the-question-navigator)) instead                                                              | The bar measured the one denominator the player chose, which is honest and useless: rating two Sports, it moves once, so the screen a player spends the longest on showed no movement for eight questions. Two carriers of one fact was also how a Sport denominator would come back to a bar that no longer counts Sports — recording the eyebrow as the only one is what stops that. `Bar` itself is untouched for every other use                                                                                                                                                                         |
| 2026-08-15 | [7.9](#79-the-question-navigator)                 | —                                                                                                                                                                                                   | **New section.** The question navigator: fixed-width segments in a left-aligned row, `coral` where answered and `line2` where not, double height where the player is standing, no total, and not a touch target                            | The bar's replacement needed specifying before it was built or every implementer would invent it, the way the confidence ring did. Two decisions in it are load-bearing and neither is taste: **no segment for an unasked question**, because that segment is the denominator the engine does not have; and **indicates rather than navigates**, because ten segments across the content width is a 29pt target against Part 13's 44pt minimum, and the tap it would get wrong is the one that discards answers                                                                                              |
| 2026-08-15 | [10.3](#103-the-screen-header)                    | The back chevron was specified and forbidden — no screen in onboarding could use it                                                                                                                 | Unchanged as a component, and now **used**: it is the questionnaire's way back through the run                                                                                                                                             | It needed no design, only permission. Worth a row because the control existing all along is what made "the navigator indicates rather than navigates" cost nothing: the movement had a home before the indicator did                                                                                                                                                                                                                                                                                                                                                                                         |
| 2026-08-15 | [12.1](#121-onboarding)                           | The step list ended the questionnaire at the result screen, because answering the last question created the rating                                                                                  | **Two screens added**: the step list is welcome → sports → questions → **review → calculating** → result → done → data, each with its own specified composition                                                                            | Stopping and completing are two moments now, and the screen between them had nowhere to be described. Both are visual surfaces with no composition at all, which is the gap the done and data screens were amended to close on 2026-08-14 — an implementer would otherwise invent one. Every player passes through both, the beginner with one answer included: one question screen, one review, one result is one rule, and exempting short runs is a second rule that earns nothing                                                                                                                        |
| 2026-08-15 | [12.1](#121-onboarding) review screen             | —                                                                                                                                                                                                   | **New section.** A pressable card per answer — question above the fold, the option chosen below it — in the order asked, the Sport in the eyebrow, one screen action that creates the rating, and the questionnaire's own close control    | The load-bearing rule is the one that looks like an omission: **no Level, range or Confidence anywhere**. This is the only screen in the app that shows a player their whole evidence while they can still change it, so a number on it turns the questionnaire from _describe yourself_ into _make this read higher_ — the same argument that removed the running estimate, at the point it would bite hardest. The card opening the question rather than editing in place keeps one place a change can happen, which is the place that names what it costs                                                 |
| 2026-08-15 | [12.1](#121-onboarding) calculating screen        | —                                                                                                                                                                                                   | **New section.** An indicator and one short line naming the Sport, no chrome and no way out, **held for a minimum duration** and not skipped under reduced motion                                                                          | The duration is the specification, not decoration: the request is one round trip over fast arithmetic, so unheld this screen appears and leaves inside a frame and reads as a glitch at the exact moment a Level comes into existence. Recording it here is what couples it to its copy — one short line, because a sentence a player cannot finish before the screen leaves is worse than none. `theme.motion.hold` lands with it, nested so the motion block keeps its one-line contract (_the four things reduced motion skips_)                                                                          |
| 2026-08-15 | [12.1](#121-onboarding) question screen           | The forward control over answered questions read `Next question` everywhere                                                                                                                         | At the end of a **stopped** run it reads that it leads back to the answers, because there is no next question                                                                                                                              | The same move, and the one place this screen could name a screen the run cannot produce. It appeared with the review: before the stop existed, walking forward always arrived at a question                                                                                                                                                                                                                                                                                                                                                                                                                  |

# Appendix A — The token contract

The authoritative values live in
[`../src/shared/ui/theme.ts`](../src/shared/ui/theme.ts). That file and this document
change together, in the same commit.

# Appendix B — Quick reference card

```
COLOUR      coral = the one accent · mint = settled · amber = reversible · red = ended badly
            info = explanation, not status · volt on DARK only
            white text needs *Ink fills (Rule C) · ink is the only dark on coral
SURFACE     paper background · white cards · NO shadow on cards
            line BOUNDS a thing · line2 is a FOLD inside one
TYPE        Archivo everywhere · IBM Plex Mono for every number
            weight = family name, never fontWeight · tracking in POINTS, not em
            h1 19 · h2 15 · tiny 11/16 · eyebrow 9.5 · flab labels a CONTROL
SPACE       a 3pt grid · 9 between cards · 15 at the gutter
            content width = screen − 30 · rail card = 0.74 × content
RADIUS      bigger surface, rounder · dark card 15, light card 13
TOUCH       44 × 44pt minimum reachable · hitSlop when the visual is smaller
            no hover — every pressable declares its pressed state
NUMBERS     mono + tabular · comma decimals · 2,71 · 38,00 zł · 65% · 18:30
STATE       every state has a word or a shape, never colour alone
NEVER       the phone frame, the stage, the scenario rail — the harness is not the app
```
