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

| Pair                                                | Ratio     | WCAG                                |
| --------------------------------------------------- | --------- | ----------------------------------- |
| ink on paper                                        | 15.65     | AAA                                 |
| ink on surface                                      | 17.50     | AAA                                 |
| white on night                                      | 13.29     | AAA                                 |
| ink on volt                                         | 13.96     | AAA                                 |
| white + `textOnMedia` on the squash court ground    | 13.03     | AAA                                 |
| white + `textOnMedia` on the padel court ground     | 12.87     | AAA                                 |
| white + `textOnMedia` on the badminton court ground | 12.80     | AAA                                 |
| white + `textOnMedia` on the tennis court ground    | 12.29     | AAA                                 |
| volt on night                                       | 10.60     | AAA                                 |
| white on night2 / info                              | 9.86      | AAA                                 |
| info on infoSoft                                    | 8.63      | AAA                                 |
| white on dark-card `tiny` (white @ .68)             | 6.97      | AAA                                 |
| white on red                                        | 5.90      | AA                                  |
| white on coralInk                                   | 5.89      | AA                                  |
| white on mintInk                                    | 5.84      | AA                                  |
| white on amber                                      | 5.70      | AA                                  |
| muted on surface                                    | 5.40      | AA                                  |
| coralInk on coralSoft                               | 5.11      | AA                                  |
| mintInk on mintSoft                                 | 5.08      | AA                                  |
| red on redSoft                                      | 5.06      | AA                                  |
| amber on amberSoft                                  | 5.04      | AA                                  |
| white on band ink (all four)                        | 5.05–5.13 | AA                                  |
| muted on paper                                      | 4.83      | AA                                  |
| white on dark-card `eyebrow` (white @ .52)          | 4.74      | AA                                  |
| band ink on paper (all four)                        | 4.51–4.59 | AA                                  |
| muted on line2                                      | 4.62      | AA                                  |
| muted on paper2                                     | 4.49      | AA — used at 11pt+ only             |
| **ink on coral**                                    | **4.50**  | AA — the only dark-on-coral pairing |
| coral on paper (marks: level mark, progress fill)   | 3.48      | ≥3:1, meets **1.4.11**              |
| mint on surface (mint-bordered fills)               | 4.07      | ≥3:1, meets **1.4.11**              |

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
- **The generated poster is not covered here.** Its hue is player-derived rather than one
  of four, so it inherits `textOnMedia` and sets its own floor
  ([6.9](#69-the-photo-tile-and-picker)).

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
| 9                   | Info button                                        |
| 8                   | Sport dot backing                                  |
| 6                   | Tag, sport dot                                     |

**The pattern: the bigger the surface, the rounder.** A dark card is 15 where a light one
is 13 — the darker fill makes the corner read tighter at the same radius.

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
a generated fill**: both of the court's label sets ([2.5](#25-contrast--computed)) and the
generated poster. It is listed here because a reader looking for a shadow looks here; it is
not a fifth floating thing.

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

Used for: the onboarding result and the done screen — the two places the app states a
finding rather than offering a choice.

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

Onboarding's second part adds four targets, and three of them are built to the minimum
rather than granted it:

| Control                                                     | Visual                      | `hitSlop`                                        |
| ----------------------------------------------------------- | --------------------------- | ------------------------------------------------ |
| Availability cell ([6.8](#68-the-availability-grid))        | 44 tall, ≥ 65 wide          | none — the geometry _is_ the target              |
| Photo tile ([6.9](#69-the-photo-tile-and-picker))           | ≥ 90 × 120                  | none                                             |
| Photo remove control ([6.9](#69-the-photo-tile-and-picker)) | 28                          | `{ top: 8, bottom: 8, left: 8, right: 8 }`       |
| Radius slider row ([6.10](#610-the-radius-slider))          | 44 tall, full content width | none — the **row** is the surface, not the thumb |

Sign-up's age question adds a fifth, built the radius slider's way:

| Control                                  | Visual                               | `hitSlop`                                                 |
| ---------------------------------------- | ------------------------------------ | --------------------------------------------------------- |
| Tick box row ([6.11](#611-the-tick-box)) | box 20 × 20, row 44 tall, full width | none — the **row** is the surface, box and label together |

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
here has **two** states, names no court and no hour, and nothing can be booked from it.
Section numbers in this document never move, so this is 6.8 and 6.7 stays empty.

```
seven rows of three — days DOWN the page, parts of the day ACROSS
MONDAY FIRST, and the seven run Monday to Sunday

column head  eyebrow, once, above the grid          MORNING · AFTERNOON · EVENING
day label    flab, content-sized, capped at 0.25 × content width, labelGutter 9
cell         flex 1, height 44, radius.availabilityCell, gap 6
footnote     tiny / muted beneath the grid, minHeight 32 — always laid out
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
([Part 0.2](#02-what-replaces-the-frame)), and no `hitSlop` closes a deficit of 2,6pt per
cell against neighbours 6pt apart. Turned the other way each cell is 44 tall by its own
geometry and, with the label column at its cap, 65,5pt wide on that same phone — **the
first control in the app that reaches the touch minimum without being granted anything.**
`profileControlGeometry.test.ts` pins that division, because it is the kind of arithmetic
that holds on the phone an agent tests on and fails on the one a player owns.

The grid does not scroll. The screen does ([10.1](#101-screen-structure)).

### Cell states

| State          | Fill      | Border     | Content                                      |
| -------------- | --------- | ---------- | -------------------------------------------- |
| **unselected** | `surface` | 1pt `line` | empty                                        |
| **selected**   | `ink`     | 1pt `ink`  | a 12 × 12 tick, 2pt stroke, `#fff` — 17.50:1 |
| **pressed**    | —         | —          | `opacity: .7`, over either of those          |

**There is no disabled cell and no fourth state.** Every cell toggles, always, in both
directions: the grid has no floor, no ceiling, and no rule that could close one off. A
greyed cell would be the screen claiming a constraint the domain does not have.

**The selected state is a fill inversion _and_ a tick, and the tick is the half that
matters.** Inverting to `ink` is a 17,50:1 luminance change rather than a change of hue, so
it survives colour blindness on its own — but a cell is a bare rectangle with nothing else
in it, and 21 rectangles differing only in lightness is a texture. The tick is the shape
[Part 13](#part-13--accessibility) asks for, and it is what makes a ticked week readable as
a pattern rather than as a stain. Drawn in `react-native-svg` with a round cap and join: at
2pt, butt caps make a tick read as two bars meeting at a corner.

Selected is `ink` and not `mint`, though "I can play then" sounds exactly like _settled,
safe, covered_. It is not: [Part 12](#part-12--screens)'s copy for this step says in as many
words that the grid is **a preference and not a promise**, and painting it mint would have
the colour contradict the sentence beside it. `ink` is what [6.2](#62-chip--the-filter-pill)
already fills a selected chip with, and a ticked cell is the same act.

### The footnote slot

A `tiny` message in `muted` under the grid, at most two lines long, and **its height is
reserved whether or not it has anything in it.** The line that appears at zero slots names what an empty week costs;
the line that replaces it can name the count. Neither may move the grid, because the moment
a player is most likely to tick a second cell is immediately after ticking the first, and a
grid that jumps 16pt upward under a finger mid-tap selects the wrong cell. `minHeight` is
two lines of `tiny` (32), which is the longest either message may run to — a third line is
an amendment, not a copy tweak.

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
cells. At the cap the three cells still share 196,5pt on the narrowest phone. The cells
contain no text, so nothing inside one scales, and `allowFontScaling={false}` never arises
([Part 13](#part-13--accessibility)).

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

What a player with no photos has instead of an empty box. Not a silhouette, not a grey
avatar, and not a tile-only thing — it is drawn wherever a profile photo would be, at
whatever size that place gives it.

```
ground   night           the surface
court    onDarkHair      the lines — the same structural line the dark card uses
ball     onDarkTiny      one mark

react-native-svg, in viewBox units, preserveAspectRatio="xMidYMid slice"
```

viewBox units and not points, so **one drawing serves a 90pt tile and a 27pt avatar** and
there is no pixel geometry to tokenise. The stroke scales with the box; nothing is measured
here because nothing here has a size.

**It varies in geometry and never in colour.** The hash chooses the court's framing and
where the ball sits. It does not choose a hue, because every colour in this palette already
means something ([1.3](#13-semantic-colour-is-never-decorative)) — a player-coloured poster
would be assigning meaning to a hash, and the four `sport` colours in particular would have
it claim a sport the player may not play.

**It is never a person.** No face, no silhouette, no initials. A poster that gestures at a
human is a poster somebody mistakes for a photograph, and the one question a photo answers
here is _do I want to play this person_ — which a drawing cannot answer and must not appear
to.

**Determinism is the feature's, not the theme's.** The design system's contract is that the
same player id produces the same drawing; the hash and the framing set are the photos
feature's, exactly as the confidence ring's 30% ceiling belongs to the engine and not to
`theme.ts` ([7.8](#78-the-confidence-ring)).

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
- **Live announcements.** Every toast calls `announceForAccessibility`.
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

| Date       | Section                                                                     | Was                                                                                                                                                                                                 | Is                                                                                                                                                                                                                                                                                                                                                                                                                                                | Why                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ---------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-08-13 | [12.1](#121-onboarding) question screen                                     | The header row carried the running estimate: `Question 3  [discriminating]  [3,17 so far]`                                                                                                          | The estimate is removed. The tag stays                                                                                                                                                                                                                                                                                                                                                                                                            | A live number reframes the questionnaire from _describe yourself accurately_ to _make this number go up_. A player who answers honestly, watches 3,4 fall to 2,9 and feels the drop has been taught mid-flow that honesty is expensive — which corrupts the only evidence the engine has. It is also the least explained number in the app, in a screen whose final figures each earn an information mark and a popover because _"none is self-explanatory"_. The difficulty tag survives because three coarse values read as _we think you can handle a hard one_, not as a score                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| 2026-08-13 | [12.1](#121-onboarding) question screen                                     | Five pressable cards, tap to answer                                                                                                                                                                 | Five cards select; a `Next` button submits                                                                                                                                                                                                                                                                                                                                                                                                        | Answers are irreversible ([ADR-0017](../../docs/adr/0017-rating-context-event-sourced.md)), and taking a reflex tap and making it permanent is a bad bargain. The confirm is the moment the player accepts finality, and it makes a timed undo window unnecessary                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 2026-08-14 | [7.8](#78-the-confidence-ring)                                              | The confidence ring was named in [2.2](#22-accent-and-semantics) and required by [12.1](#121-onboarding), but never specified as a component — no diameter, stroke, track, cap or ceiling treatment | **Specified**: 72 × 72, stroke 6, butt caps, track `onDarkHair`, arc `volt`, a 2pt radial ceiling tick at 30%, value in `numXL` inside and an `eyebrow` label beneath                                                                                                                                                                                                                                                                             | An agent building it would have been inventing design rather than implementing it. Added through [15.1](#151-adding-a-component); the stroke matches the level bar's band segments and the diameter is on the 3pt grid                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 2026-08-14 | [7.8](#78-the-confidence-ring)                                              | —                                                                                                                                                                                                   | The ring's scale is **always the full 0–100**, with the 30% onboarding ceiling marked on the track                                                                                                                                                                                                                                                                                                                                                | The same reasoning as the level bar's fixed 1,00–5,00 scale: a value must land in the same place everywhere or the component means different things on different screens. Every player leaves onboarding at or below 30%, so a bare arc would read as failure; the tick makes the short arc legible as _as far as a questionnaire can prove_, and keeps the component honest when matches later push confidence to 75%                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 2026-08-14 | [12.1](#121-onboarding) result screen                                       | The lower half stopped at the band-meaning card                                                                                                                                                     | The **evidence trail** is recorded as specified composition: two lists — what moved the level, what widened the range — kept apart, the second carrying no direction                                                                                                                                                                                                                                                                              | The source specification calls the trail critical, and the engine already supplies it as structured data. Leaving it unspecified invited each implementer to invent a layout for the one part of the screen that explains the rest                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| 2026-08-14 | [12.1](#121-onboarding)                                                     | The step list was correct but silent about the prototype's _gate_ and _history_ screens                                                                                                             | A note: both are engine questions, not screens — **the app has one question screen** — and the rest of the history screen is listed as cut content                                                                                                                                                                                                                                                                                                | The step list being correct was not the same as it being unambiguous. Someone reading the prototype later would have found two screens with no record of why they are absent, and rebuilt them                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 2026-08-14 | [7.5](#75-the-level-bar)                                                    | The bar's geometry lived only in this section's prose, while the ring's lived in `theme.ts`                                                                                                         | The same numbers are now `size.levelBar` tokens, as `size.ring*` already were. **No value moved** — the y coordinates are kept as coordinates so the token block reads against the spec line by line                                                                                                                                                                                                                                              | Appendix A says this document and `theme.ts` are one contract. Half a drawn object in each was how a value gets changed in one place; the ring had already set the pattern                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 2026-08-14 | [7.5](#75-the-level-bar)                                                    | The bar's colours assumed paper: bracket in `muted`, band names in the band `ink` values                                                                                                            | An **on-dark repaint** ([5.2](#52-dark-card)): bracket and unselected names in `onDarkTiny`, the current name in white, separators and the mark's ring in the card colour. `ink` and `tint` are untouched on paper                                                                                                                                                                                                                                | [12.1](#121-onboarding) puts this bar inside the dark card, where `muted` is about 1,6:1 and the band inks about 2,4:1 — [Part 13](#part-13--accessibility) permits neither at any size. The band `tint` values would have passed, but they are the bar's and never text's; band identity is carried by the segment, and the current name by weight 800 against 600, so nothing rests on colour                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 2026-08-14 | [12.1](#121-onboarding) result screen                                       | "Each contributor is a row", of both lists                                                                                                                                                          | Contributions are rows; **range-wideners are notes**, carrying the server's own label, detail and the σ each added                                                                                                                                                                                                                                                                                                                                | A widener carries a sentence and a row is a line. Drawing the wideners as rows meant either dropping the detail the engine authors for each of them or letting a key-value line wrap to three lines. The two lists still share one card and one fold, which is what "one account with two halves" was protecting                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 2026-08-14 | [12.1](#121-onboarding) done screen                                         | The step list named the screen; nothing said what is on it                                                                                                                                          | **Specified composition**: a card per sport with the sport's colour as its 3pt rail, four rows of figures in tabular mono, a line saying whether the ceiling or the evidence held the Confidence, and the hypotheses note. No progress bar                                                                                                                                                                                                        | The screen a player leaves onboarding through was the one with no composition at all, so every implementer would have invented one. The line about the Confidence is the part that could not be left to an implementer: it is the difference between _a questionnaire cannot prove more_ and _your answers left something unsettled_, and choosing one sentence for both tells half of these players something untrue about themselves                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 2026-08-14 | [12.1](#121-onboarding) data screen                                         | Named in the step list only                                                                                                                                                                         | **Specified composition**: four cards mirroring welcome's three, and the two properties that are not layout — it reads and writes nothing, and it is **not a consent form**                                                                                                                                                                                                                                                                       | Same gap as the done screen, with one addition worth writing down rather than remembering: a screen listing what is kept, sitting one tap before the app, is exactly where a consent checkbox gets added by someone who means well. Saying it is out of scope in a PRD lasts one slice; saying it here lasts                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 2026-08-14 | [12.1](#121-onboarding) result screen                                       | The result screen's action was unspecified                                                                                                                                                          | The primary control **names** the next chosen sport, with `Done for now` beside it; with nothing queued there is one control and it leads to the summary                                                                                                                                                                                                                                                                                          | Multi-sport is in the step list and the result screen is where a run either continues or ends, so its action carries the whole of it. Naming the sport is the part that is easy to lose: `Next sport` asks a player to remember what they chose several minutes ago                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| 2026-08-14 | [7.8](#78-the-confidence-ring)                                              | The ceiling tick is drawn at 30%, always                                                                                                                                                            | The tick is drawn at the ceiling the **response** carries, and is **omitted** where none was carried                                                                                                                                                                                                                                                                                                                                              | 30% was a client-side copy of a number only the engine can keep honest: it is scoped to an engine version, so a retune desynchronised the tick, the ring's accessible name and the "held by the ceiling or by your own answers" sentence from the Confidence they describe — silently, in builds already on phones. Serving it removes the copy. Omission is the case the copy hid: a rating replayed from a retired engine keeps its numbers and loses its explanation, and a default tick would state a limit that did not exist when it was produced. No rendered change today — the served ceiling is 30                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 2026-08-15 | [12.1](#121-onboarding) question screen                                     | _"it is irreversible — there is no back control anywhere in the questionnaire"_, citing [ADR-0017](../../docs/adr/0017-rating-context-event-sourced.md)                                             | **Removed**, and replaced by the revision rule of [ADR-0020](../../docs/adr/0020-revisable-assessment-answers.md): a player may walk back over the questions they have answered, and changing one discards every answer after it                                                                                                                                                                                                                  | ADR-0020 supersedes exactly that rule of ADR-0017 and leaves every other decision in it standing. The cost ADR-0017 named and accepted in writing — _"it costs the player the ability to change their mind two questions later"_ — lands on the first thing anybody does in this app, in the flow that is the **entire** evidence surface for the rating, so a mis-tap on question three is a permanent distortion of a Level every later feature reads. The confirm survives and its reasoning survives with it; what it earns is now one deliberate answer rather than the finality of the run                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 2026-08-15 | [12.1](#121-onboarding) question screen                                     | The button label never changes, _because the client cannot know which question is the last one_                                                                                                     | The rule stands; the reason is that it no longer matters. Answering never creates the rating                                                                                                                                                                                                                                                                                                                                                      | The client still cannot predict the last question. Leaving only that argument would leave the strongest one unstated — with the commitment moved off the last answer, the identical label stopped being a compromise and became simply correct. A wart retired rather than inherited                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| 2026-08-15 | [12.1](#121-onboarding), [7.3](#73-meter-and-bar)                           | Chrome is a header plus a `coral` progress bar measuring **Sports**, repeating the eyebrow's `Rating 1 of 2`                                                                                        | The bar is gone from onboarding. The eyebrow is the **sole** carrier of Sport position, and the questionnaire draws the navigator ([7.9](#79-the-question-navigator)) instead                                                                                                                                                                                                                                                                     | The bar measured the one denominator the player chose, which is honest and useless: rating two Sports, it moves once, so the screen a player spends the longest on showed no movement for eight questions. Two carriers of one fact was also how a Sport denominator would come back to a bar that no longer counts Sports — recording the eyebrow as the only one is what stops that. `Bar` itself is untouched for every other use                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| 2026-08-15 | [7.9](#79-the-question-navigator)                                           | —                                                                                                                                                                                                   | **New section.** The question navigator: fixed-width segments in a left-aligned row, `coral` where answered and `line2` where not, double height where the player is standing, no total, and not a touch target                                                                                                                                                                                                                                   | The bar's replacement needed specifying before it was built or every implementer would invent it, the way the confidence ring did. Two decisions in it are load-bearing and neither is taste: **no segment for an unasked question**, because that segment is the denominator the engine does not have; and **indicates rather than navigates**, because ten segments across the content width is a 29pt target against Part 13's 44pt minimum, and the tap it would get wrong is the one that discards answers                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 2026-08-15 | [10.3](#103-the-screen-header)                                              | The back chevron was specified and forbidden — no screen in onboarding could use it                                                                                                                 | Unchanged as a component, and now **used**: it is the questionnaire's way back through the run                                                                                                                                                                                                                                                                                                                                                    | It needed no design, only permission. Worth a row because the control existing all along is what made "the navigator indicates rather than navigates" cost nothing: the movement had a home before the indicator did                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| 2026-08-15 | [12.1](#121-onboarding)                                                     | The step list ended the questionnaire at the result screen, because answering the last question created the rating                                                                                  | **Two screens added**: the step list is welcome → sports → questions → **review → calculating** → result → done → data, each with its own specified composition                                                                                                                                                                                                                                                                                   | Stopping and completing are two moments now, and the screen between them had nowhere to be described. Both are visual surfaces with no composition at all, which is the gap the done and data screens were amended to close on 2026-08-14 — an implementer would otherwise invent one. Every player passes through both, the beginner with one answer included: one question screen, one review, one result is one rule, and exempting short runs is a second rule that earns nothing                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 2026-08-15 | [12.1](#121-onboarding) review screen                                       | —                                                                                                                                                                                                   | **New section.** A pressable card per answer — question above the fold, the option chosen below it — in the order asked, the Sport in the eyebrow, one screen action that creates the rating, and the questionnaire's own close control                                                                                                                                                                                                           | The load-bearing rule is the one that looks like an omission: **no Level, range or Confidence anywhere**. This is the only screen in the app that shows a player their whole evidence while they can still change it, so a number on it turns the questionnaire from _describe yourself_ into _make this read higher_ — the same argument that removed the running estimate, at the point it would bite hardest. The card opening the question rather than editing in place keeps one place a change can happen, which is the place that names what it costs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 2026-08-15 | [12.1](#121-onboarding) calculating screen                                  | —                                                                                                                                                                                                   | **New section.** An indicator and one short line naming the Sport, no chrome and no way out, **held for a minimum duration** and not skipped under reduced motion                                                                                                                                                                                                                                                                                 | The duration is the specification, not decoration: the request is one round trip over fast arithmetic, so unheld this screen appears and leaves inside a frame and reads as a glitch at the exact moment a Level comes into existence. Recording it here is what couples it to its copy — one short line, because a sentence a player cannot finish before the screen leaves is worse than none. `theme.motion.hold` lands with it, nested so the motion block keeps its one-line contract (_the four things reduced motion skips_)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| 2026-08-15 | [12.1](#121-onboarding) question screen                                     | The forward control over answered questions read `Next question` everywhere                                                                                                                         | At the end of a **stopped** run it reads that it leads back to the answers, because there is no next question                                                                                                                                                                                                                                                                                                                                     | The same move, and the one place this screen could name a screen the run cannot produce. It appeared with the review: before the stop existed, walking forward always arrived at a question                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 2026-08-25 | [6.2](#62-chip--the-filter-pill)                                            | Specified since the document was locked and never built. The app shipped the tag, which is deliberately never pressable, so _a pressable pill is a chip_ had nothing to point at                    | Unchanged as a component, and now **used**: the Social tags step selects from eighteen of them, and the profile editor will reuse the same control                                                                                                                                                                                                                                                                                                | It needed no design, only a use — the same shape as the back chevron's row above, and worth a row for the same reason. The chip is the one of these four that was already specified, and recording it here is what stops the step that needs it re-specifying a control that has sat in 6.2 since locking. Its selected treatment was re-read against _never colour alone_ and stands: inverting to `ink` is a 17,50:1 **luminance** change rather than a change of hue, and [Part 13](#part-13--accessibility) already requires `accessibilityState` on it                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 2026-08-25 | [6.8](#68-the-availability-grid)                                            | —                                                                                                                                                                                                   | **New section.** The availability grid: seven rows of three, Monday first, days down and parts of the day across, cells 44 tall and ≥ 65 wide with no `hitSlop` to grant, two states carried by an `ink` inversion **and** a tick, a reserved two-line footnote slot, and an empty grid drawn as the complete answer it is. Registered in [6.5](#65-touch-targets) and [6.6](#66-press-states)                                                    | The precedent [7.8](#78-the-confidence-ring) and [7.9](#79-the-question-navigator) set: an agent building this would have been inventing design rather than implementing it. Two decisions in it are load-bearing and neither is taste. **Days are rows**, because seven columns want 7 × 44 = 308pt against the 290pt of content the narrowest phone has, and no hit-slop closes a 2,6pt-per-cell deficit against neighbours 6pt apart — `profileControlGeometry.test.ts` pins that division, because it is the kind of arithmetic that holds on the phone an agent tests on and fails on the one a player owns. And **6.7 is not reused**: the deleted slot squares were four states deep because a court is free, held, taken or yours, where a cell here has two and can book nothing, and a section number in this document never moves ([Part 17](#part-17--what-the-reset-removed))                                                                                                                                                                      |
| 2026-08-25 | [6.9](#69-the-photo-tile-and-picker)                                        | —                                                                                                                                                                                                   | **New section.** The photo tile and picker: three 3:4 tiles across the content width always, the ceiling as a fact of the layout rather than a disabled button, one foot strip with three mutually exclusive occupants — profile, uploading, failed — a 44pt remove square anchored inside the tile, promotion by pressing what remains of it, and the generated court poster. Registered in [6.5](#65-touch-targets) and [6.6](#66-press-states) | The same gap, with two parts that could not be left to an implementer. **The foot strip**, because every other way of marking a photo puts a translucent badge over an image nobody has seen — `onDarkTag` is computed against `night` and means nothing over a bright sky, and a `line2` progress track is invisible on a photograph. One solid strip fixes the ratio whatever the player photographed, and being one slot rather than three stacked badges is what leaves the settled tile undecorated. **The poster**, because the two ways to get it wrong are both attractive: a drawing that varied in colour would assign meaning to a hash in a palette where every colour already means something, and the four `sport` colours would have it claim a sport the player may not play; a drawing that gestured at a person is one somebody mistakes for a photograph, in the one place a photograph answers a question a drawing cannot                                                                                                                  |
| 2026-08-25 | [6.9](#69-the-photo-tile-and-picker)                                        | The remove control had a size, a target, a position and a press state, and no fill or mark                                                                                                          | **Specified**: a solid `night` square with a white mark at the `tag` radius, inset from the tile's corner by its own 8pt slop                                                                                                                                                                                                                                                                                                                     | Found while building the section. Every other object on the tile states what it is drawn on and this one did not, and the two obvious fills are both wrong for the reason the strip's own paragraph gives — a translucent scrim over an unknown photograph has an unknown ratio, and [9.1](#91-bottom-sheet)'s `line2` close circle is a paper-surface object that disappears over a bright sky                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 2026-08-25 | [6.10](#610-the-radius-slider)                                              | —                                                                                                                                                                                                   | **New section.** The radius slider: the 44pt **row** is the touch surface rather than the thumb, a `line2` track with a `night` fill and a `night` thumb inside a 3pt `surface` ring, the figure in a width-reserved box and the plain words beneath it, no ticks and no end labels, and `adjustable` with increment and decrement. Registered in [6.5](#65-touch-targets) and [6.6](#66-press-states)                                            | The load-bearing rule is the one that reads as an omission: **the minimum, the maximum, the step and the default are not in this document and not in `theme.ts`**. They are served by `GET /player-profile/options`, they are re-validated on the write path, and they are product's to retune — so a slider shipping `1` and `50` compiled in would be a second, staler copy of a rule the server already owns, in builds already on phones. That is the ceiling precedent of [7.8](#78-the-confidence-ring), and the reason the scale is the full **served** range rather than a fixed one. The row rather than the thumb being the touch surface is what gets the control to 44pt without a `hitSlop` entry; `adjustable` with increment and decrement is the part sliders universally ship without, and a drag-only slider is unusable with a screen reader                                                                                                                                                                                                 |
| 2026-08-26 | [6.1](#61-button)                                                           | Three variants: `primary`, `dark`, `secondary`                                                                                                                                                      | A fourth, **`settled`** — `mintInk` filled, white label, brightening to `mint` on press                                                                                                                                                                                                                                                                                                                                                           | The location step needed a control whose **state is the message**: the area has been read, and pressing again would only read it a second time. Every existing variant says something else — `primary` claims the accent a screen may only spend once ([1.2](#12-the-one-accent-rule)), `secondary` reads as the lesser of two actions, and `dark` is a filled action with no meaning attached. Mint is this system's word for _settled, safe, covered_ ([1.3](#13-semantic-colour)), so it is the only colour that could carry it, and Rule C picks `mintInk` over `mint` at 4.07:1. It brightens on press exactly as `primary` does, with the same momentary exception. **Its label changes with its fill**, which is what keeps it inside _never colour alone_ ([Part 13](#part-13--accessibility)) — the variant is half of a state and the screen owns the other half                                                                                                                                                                                      |
| 2026-08-27 | [6.11](#611-the-tick-box)                                                   | There was no tick box, and no specified control for a claim a player either makes or does not                                                                                                       | **Specified**: 6.8's cell at 20pt with 6.8's own tick, the whole row as the touch surface, no pre-ticked state, and a refused border drawn only while unticked. Registered in [6.5](#65-touch-targets) and [6.6](#66-press-states)                                                                                                                                                                                                                | The sign-up form has to ask whether the player is an adult ([ADR-0124](../../docs/adr/0124-the-matcher-gates-account-state-never-age.md)), and Part 6 specified exactly one ticked thing — a grid cell. Left unrecorded, the form would have invented a second idea of what _ticked_ looks like beside the one that exists, which is what [15.1](#151-adding-a-component) is for. Added through it: no new colour, no new radius, and the one new size is 6.8's cell brought down to the height a line of text wants                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| 2026-08-31 | [2.2](#22-accent-and-semantics)                                             | _"Volt never appears on paper. It is illegible there (~1.3:1) and is never used there."_                                                                                                            | **Volt is a fill anywhere and a stroke only on dark.** A volt fill carries `ink`; an emphasis that wanted a volt stroke on paper becomes a volt tag, and an in-progress state on paper is `coral`                                                                                                                                                                                                                                                 | Play's entire _they want you_ signal is volt, and it used volt on paper in four places that are two different kinds of use. The **fills** — the interest tag, the _even it out_ button — carry `ink` at **13.96:1**, which [2.5](#25-contrast--computed) already listed as AAA: they violated the sentence and nothing else. The **strokes** — a 2pt border on the interest card, the search ring, the ring on a newly added slot — are ~1.3:1 and are the bug corrections **#14** and **#15** already fixed once. So the argument is upheld and the sentence narrowed to what the argument actually covers: volt's problem on paper is contrast as a **foreground**, and a fill inverts that. A `voltLine` companion dark enough to read on paper was refused — that is no longer volt; moving interest to `coral` was refused — coral is the action colour, and _they want you_ is a fact about somebody else. The card's emphasis becoming a tag is what [Part 13](#part-13--accessibility) prefers anyway: a border carries no word and this signal has one |
| 2026-08-31 | [2.3](#23-sport-identity)                                                   | The aliasing was defended by a stated premise — _"the dot is always accompanied by the sport name in text"_ — and a stated trip-wire                                                                | The same decision, with the premise recorded as **tested**: checked against every Play site that draws a sport hue — sport chips, sport tags on the player record, the court gradient — and the three named in the section. The trip-wire is unchanged                                                                                                                                                                                            | The UI spec asked for four dedicated sport hues and called it _the single highest-value colour change in the feature_, which is a proposal to overturn a stated argument rather than a token collision. The premise is falsifiable, so it was tested rather than re-asserted: there is no Play surface where a sport hue appears with no sport name on screen, and the objection is stated as purity without ever producing a screen where the aliasing misleads. Play's real adjacency risk — a coral padel court beside a coral primary button — is answered by the court's scrim, not by four new hues. The next feature inherits evidence instead of a claim, and a fifth sport still reopens it                                                                                                                                                                                                                                                                                                                                                            |
| 2026-08-31 | [2.5](#25-contrast--computed)                                               | Every pair in the table is a **fixed** pair. There was no rule at all for text over a **generated** fill                                                                                            | Four rows for white plus `textOnMedia` on the court ground, one per sport, and a subsection stating the rule: the scrim is pinned, every label over the court carries the shadow, the side labels stay at white `.6` on the arithmetic, and the four ratios are derived by [`textOnMedia.test.ts`](../src/shared/ui/textOnMedia.test.ts) rather than typed                                                                                        | The one contrast risk this document did not answer. The court's ground is drawn **from the selected sport's hue**, so the ratio behind a white label depended on which sport a player picked and no fixed pair could state it. Pinning the scrim is what makes it finite: the hue is at most 7% of the ground, so the dark end is `night` whatever the sport and the light end is one of four known composites — four ratios rather than an unbounded set. The `.6` side labels were expected to need raising and do not: **5.46** against the worst of the four, which is recorded precisely because a value left alone on evidence is one the next reader changes back. Derived rather than published, for the reason `bandEdges.test.ts` gives — a number two documents restate is a number that drifts in one of them                                                                                                                                                                                                                                       |
| 2026-08-31 | [3.2](#32-weights-are-family-names-not-numbers) · [3.3](#33-the-type-roles) | _"Display numbers — always mono, weight 700"_, while [3.2](#32-weights-are-family-names-not-numbers)'s family table carried no mono 700 row                                                         | **Weight 600** — and 500 at `numS` / `numXS`. [3.2](#32-weights-are-family-names-not-numbers) states that mono stops at 600 and that the dash is the specification                                                                                                                                                                                                                                                                                | Three parties disagreed and **the code was the only one that was right**. The UI spec found the prototype's real bug — `.num` requests 800, IBM Plex Mono ships 400/500/600, so every mono figure was synthetically bolded — and prescribed _load mono 700_. `fonts.ts` loads 400/500/600 and `theme.ts` uses `mono[600]` for every display role, so the app never had the bug: the prose carried it and the code did not. A 700 mono is a bundle cost for a weight this system has never rendered, so the prescription is refused and the prose corrected instead. The diagnosis was right; the app had already satisfied it by a cheaper route                                                                                                                                                                                                                                                                                                                                                                                                                |
| 2026-08-31 | [4.2](#42-radius)                                                           | The radius list stopped at 15 (dark card) and 22 (sheet)                                                                                                                                            | **`deckCard: 18`**, with the paragraph that says it is not a card                                                                                                                                                                                                                                                                                                                                                                                 | Radius 18 is the one radius in Play the list did not already cover — every other value the prototype used was inside 1pt of a token, including the photo's 14 → 13. It is named for the surface rather than added to the card family because the deck card is a transient object being manipulated, and the competitive candidate card in the pool stays a card at 13. That ends a condition where two candidate surfaces were one shape at two radii                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 2026-08-31 | [4.3](#43-elevation)                                                        | _"Three shadows exist. **Cards never have one**"_                                                                                                                                                   | A **fourth**, for the deck card, and the sentence intact — it applies to cards, and [4.2](#42-radius) says the deck card is not one                                                                                                                                                                                                                                                                                                               | The deck card animates in, and translates and rotates out under the thumb; real swipe is proposed on the grounds that the animation already implies it. That makes it a fourth member of the floating family rather than a fifth exception to a rule about cards, and naming what the rule applies to is what lets the rule survive whole. Calibrated for RN the way the other three are: it has the largest negative spread of any shadow here — 26 of 40 blur — so it is the tightest and the faintest, and it floats least                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 2026-08-31 | [6.1](#61-button)                                                           | Four variants: `primary`, `dark`, `secondary`, `settled`                                                                                                                                            | A fifth, **`volt`** — filled `volt`, label `ink`, pressed `opacity: .7`                                                                                                                                                                                                                                                                                                                                                                           | Play needs a control for _they want you to play_ and every existing variant says something else: `primary` claims the accent a screen may only spend once ([1.2](#12-one-accent-used-sparingly)), `secondary` reads as the lesser of two actions, `dark` is a filled action with no meaning attached, and `settled` is mint's. It is the one variant that does not have the others' shape — its label is `ink` rather than white, and its press is an opacity rather than a fill. Both follow from volt itself: `ink` on volt is 13.96:1 and white on it is not readable, and volt is already the brightest value in the palette with no darker companion to press to                                                                                                                                                                                                                                                                                                                                                                                           |
| 2026-08-31 | [6.6](#66-press-states)                                                     | The volt button had no registered press                                                                                                                                                             | `opacity: .7`, over its one fill                                                                                                                                                                                                                                                                                                                                                                                                                  | The system's existing answer for a pressed surface with no second fill — the chip, the segment, the availability cell, the photo tile and the tick-box row all take it. A seventh hex invented to satisfy _the variant's pressed fill_ would be a colour added to describe a press, which [15.2](#152-adding-a-colour) refuses on its face: it carries no meaning nothing else carries. Registered here rather than left in [6.1](#61-button), because this table is where a build session looks for what a finger does                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 2026-08-31 | [2.5](#25-contrast--computed) · [4.3](#43-elevation)                        | —                                                                                                                                                                                                   | **Two new tokens.** `color.courtScrim` — the `night` colour at **`.93`** — and `shadow.textOnMedia`, a `textShadow` rather than an elevation                                                                                                                                                                                                                                                                                                      | The prototype's two court call sites disagreed at `.92` (read-only) and `.94` (interactive), and a scrim that is not one number is a ground whose worst case cannot be computed at all; pinning it is what turns an unbounded set of ratios into four. It is the `night` colour rather than the prototype's `rgba(6,26,33,·)` for the reason [9.1](#91-bottom-sheet)'s scrim is: the dim matches the palette, and that hex carries no meaning the palette does not already have ([15.2](#152-adding-a-colour)). `textOnMedia` is lifted from the seat labels' own `0 1px 3px rgba(0,0,0,.6)` and applied to **both** label sets — the prototype gave it to the seats and not to the side labels, which are the lower-contrast of the two. The generated poster inherits it and sets its own lightness floor separately, its hue being player-derived rather than one of four                                                                                                                                                                                    |
| 2026-08-31 | [4.3](#43-elevation)                                                        | Four shadows, none of them tinted                                                                                                                                                                   | A **fifth**, the ⚡Play disc's, in `coral` — and the calibration table that turns the prototype's `-6px` spread into a radius, an offset and an opacity RN can actually express                                                                                                                                                                                                                                                                   | The one thing in the bottom chrome that floats, and it floats in its own colour. Stated with the Android caveat, because `elevation` cannot be tinted and half the platform gets a dim instead                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 2026-08-31 | [6.6](#66-press-states)                                                     | The tab bar had no registered press at all                                                                                                                                                          | Two: `opacity: .7` on a tab **column**, and [6.1](#61-button) `primary`'s `coral` on the ⚡Play disc — which does **not** also dim                                                                                                                                                                                                                                                                                                                | One channel per state. The disc has a second fill and the flanks do not, so each takes the answer its own surface allows                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| 2026-08-31 | [10.1](#101-screen-structure)                                               | The structure, stated and never confirmed against a specification that proposed the opposite                                                                                                        | The same structure, recorded as **confirmed for Play**: the header pins above the scroller, the CTA and the bar are flex siblings below it, and the **bar owns the bottom inset**                                                                                                                                                                                                                                                                 | The counter-argument is a viewport budget computed against a phone with no safe areas, so it gets worse on a real device. An inset applied twice is 34pt of nothing                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| 2026-08-31 | [10.2](#102-the-tab-bar)                                                    | Geometry for a bar nobody had built: paddings, a 16pt box, `currentColor` squares, and no label role at all                                                                                         | The whole bar. Five columns, a 30pt disc at radius 11 in [6.1](#61-button) `primary` with `shadow.fab`, a 2pt `coral` ring **absolutely positioned**, `tag` labels under a **derived** `maxFontSizeMultiplier`, Feather and its five names, no badge — and [Part 14](#part-14--corrections-applied-to-the-prototype) row 6 retired                                                                                                                | The bar ships, so every question it was holding open is now due. Volt lost the ring by measurement (1.25:1) and the disc lost white-on-`coral` to Rule C; the cap is derived because a guessed one fails on one word, on one phone, at one OS setting                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 2026-08-31 | [4.3](#43-elevation) · [10.2](#102-the-tab-bar)                             | —                                                                                                                                                                                                   | **Four new values in `theme.ts`.** `size.fab` **28 → 30**, `radius.fab: 11`, a `size.tabBar` block holding the bolt, the ring's gap and stroke and the derived label cap, and `shadow.fab`                                                                                                                                                                                                                                                        | `size.fab` was unreferenced and off the 3pt grid at both values; 30 is what the bar draws. The ring is kept as its two stated numbers rather than a pre-added 38, and the bar does the arithmetic                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |

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
