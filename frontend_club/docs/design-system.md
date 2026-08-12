# Rakieta Club Console — Design System

**Status: locked.** This is the club web app's visual and interaction contract. Every
screen, component and stylesheet in `frontend_club/` conforms to it. Building a surface
that is not described here means extending the system deliberately (Part 13), not
inventing beside it.

- **Origin:** measured out of the v7 HTML prototype
  (`rakieta-club-console-v7-intent-pool-2.0.html`, 36 570 bytes of CSS, 255 selectors,
  34 tokens). The verbatim measurement is preserved at
  [`design-system-v7-prototype-audit.md`](design-system-v7-prototype-audit.md).
- **Relationship to that audit:** the audit is *descriptive* — it recorded the prototype
  including its inconsistencies. This document is *prescriptive*. Where the two differ,
  **this document wins**, and every difference is listed with its reason in
  [Part 12](#part-12--corrections-applied-to-the-prototype).
- **Implementation:** the tokens are real code at
  [`../src/shared/ui/tokens.css`](../src/shared/ui/tokens.css). That file is the single
  source of colour, type and spacing values. Components reference `var(--…)`, never a
  literal.
- **Scope:** the **club web app only**. The player app (`frontend_player/`) has its own
  design system; do not import from, or reason across, the two.

---

# Part 1 — Design philosophy

## 1.1 The three commitments

**1. The interface is a document, not an application.**
No chrome for its own sake, no gradient for its own sake, no shadow that does not
indicate elevation. The paper background (`--paper`) and the grotesque type establish a
reading surface. A manager scanning at 08:00 is reading, not operating.

**2. Colour carries meaning, never decoration.**
Every colour maps to a state or a category. There is no "brand blue" applied to a button
because buttons are blue. Coral means *this is live and it is moving*. Mint means
*settled*. Amber means *provisional, and time is working against it*. When a new element
needs a colour, the question is **which of those it is** — never which looks best.

**3. Density is a feature.**
Base font size is **12.5px**, rows are **44px**, card padding is **14px**. Deliberately
tighter than a consumer product: a club manager needs a day on one screen, and scrolling
to compare two hours is a failure. The density is bought back with generous line-height
(1.45) on secondary text and disciplined whitespace between groups.

## 1.2 What the system refuses

| Refused | Why |
|---|---|
| Drop shadows on cards | Elevation is reserved for genuinely floating surfaces: sheet, drawer, toast |
| Colour-only state | Every tag carries a word. Colour is redundant reinforcement, never the sole signal |
| More than one accent | Coral is the only accent. Volt is a highlight *within* dark surfaces only |
| Icons without labels | Nav icons sit beside text; no icon-only controls except the sheet close |
| Animation as delight | Two keyframes exist, both functional (entry, sheet slide) |
| A literal colour, size or gap in a component | Everything comes from a token or a documented scale step |

---

# Part 2 — Colour

## 2.1 Numbered palette

### Primary — the ink family

The reading colours: text and the structural darks.

| # | Token | Hex | Role |
|---|---|---|---|
| P1 | `--ink` | `#101B20` | Body text, headings, the default foreground |
| P2 | `--night` | `#0A3441` | Primary dark surface: active nav, dark buttons, toast, progress fills |
| P3 | `--night2` | `#12495B` | Secondary dark: hover on dark buttons, secondary fills |
| P4 | `--night-deep` | `#071C24` | The deepest surface: top bar and drawer only |
| P5 | `--muted` | `#5C6D73` | Secondary text, labels, eyebrows, captions |

`--ink` on `--paper` is **15.65:1** — AAA with enormous headroom, which is what buys the
12.5px base size.

### Secondary — the paper family

The surfaces. Everything sits on one of these.

| # | Token | Hex | Role |
|---|---|---|---|
| S1 | `--paper` | `#F4F2ED` | Application background; also the sheet background |
| S2 | `--paper2` | `#EDEAE3` | Deeper paper, used in the block hatch |
| S3 | `--surface` | `#FFFFFF` | Cards, nav, table headers, calendar — everything raised off the paper |
| S4 | `--line` | `#E5E1D8` | Structural borders: card edges, nav divider, table header rule |
| S5 | `--line2` | `#F0EDE6` | Hairlines and inert fills: row separators, track backgrounds, segmented troughs |

> **The `--line` / `--line2` distinction is the most-used decision in the system.**
> `--line` **bounds a thing**; `--line2` **separates rows within a thing.** Getting this
> wrong is the single most common visual error — a card whose internal rows use `--line`
> reads as five cards.

### Tertiary — the semantic accents

Each maps to exactly one meaning. Each has a **soft** companion for backgrounds and an
**ink** companion for text or white-bearing fills.

| # | Token | Base | Soft | Ink | Means |
|---|---|---|---|---|---|
| T1 | `--coral` | `#E8482B` | `--coral-soft` `#FDEBE6` | `--coral-ink` `#B8351C` | Live, urgent, the accent. The only accent. |
| T2 | `--mint` | `#0C8F6B` | `--mint-soft` `#E2F3EC` | `--mint-ink` `#0A7355` | Settled, confirmed, done, safe |
| T3 | `--amber` | `#8A5E09` | `--amber-soft` `#FBF0DA` | — | Provisional, soft-held, time working against it |
| T4 | `--red` | `#B4392C` | `--red-soft` `#FBEAE7` | — | Failure, cancellation, at risk |
| T5 | `--info` | `#12495B` | `--info-soft` `#EAF1F4` | `--info-line` `#C7DBE3` | Neutral emphasis, explanation |

Supporting values, each carrying one job:

| Token | Hex | Role |
|---|---|---|
| `--coral-line` | `#F3CFC5` | Border of a coral-tinted surface (`.stat.hot`) |
| `--mint-pale` | `#8BC5A8` | Timeline band 1 (opened → commitment) — a low-consequence green |
| `--mint-deep` | `#2C7A5A` | The booked court chip: white text on a committed green |

> **Amber versus red is a real distinction, not a severity gradient.** Amber means
> *this may still resolve, and the clock is the thing deciding*. Red means *this has
> failed or is failing*. A soft-held court is amber forever; it becomes red only if it
> dies.

#### Rule C — text on a saturated fill

`--coral` and `--mint` are **marks, not text beds**. White on either is 3.89:1 and
4.07:1 — below AA, and no text in this product reaches WCAG's large-text threshold
(18.66px bold / 24px regular). So:

| You want | Use |
|---|---|
| A coral or mint **mark** with no text on it (rails, dots, now-line, bars, hover rings, pips) | `--coral` / `--mint` |
| **White text** on a coral fill | `--coral-ink` — white on it is **5.89** |
| **White text** on a mint fill | `--mint-ink` (5.84) or `--mint-deep` (5.20) |
| **Dark text** on a coral fill | `--ink` on `--coral` is **4.50** — the only dark-on-coral pairing that passes |
| Coral or mint **text on its own soft** | `--coral-ink` on `--coral-soft` (5.11); `--mint-ink` on `--mint-soft` (5.08) |

Never white on `--coral`. Never white on `--mint`. Never `--mint` as a text colour on
`--mint-soft`.

### Quaternary — highlight

| # | Token | Hex | Role |
|---|---|---|---|
| Q1 | `--volt` | `#D9F24B` | Highlight **on dark surfaces only** — active pill in the top bar, scenario group labels in the drawer, emphasis inside toasts, nav badge on an active item |

**Volt never appears on paper.** `--night` on `--volt` is **10.60**; volt on paper would
be roughly 1.3:1 and illegible. A hard rule, not a preference.

### Quinary — sport identity

| # | Token | Resolves to | Sport |
|---|---|---|---|
| X1 | `--sport-padel` | `var(--coral)` | Padel |
| X2 | `--sport-tennis` | `var(--mint)` | Tennis |
| X3 | `--sport-squash` | `var(--night2)` | Squash |
| X4 | `--sport-badminton` | `var(--amber)` | Badminton |

**These deliberately alias the semantic colours**, and now do so through `var()` rather
than by repeating the hex, so a change to the semantic token cannot silently miss them.
A club runs one or two sports; the collision between "padel" and "urgent" is acceptable
because **sport dots never appear in a severity context**. If a club ran all four, this
needs revisiting.

> Renamed from the prototype's `--pad / --ten / --squ / --bad`: `--bad` as *badminton*
> collided with `.tag.bad` as *at risk*, which is exactly the kind of ambiguity a design
> system exists to remove.

### Senary — the calendar surface

The grid speaks in **fills**, not tags, so it gets its own set. A cell must be readable
at 44 × ~38px with no room for a label.

| # | Token | Value | Means |
|---|---|---|---|
| G1 | `--g-free` | `var(--surface)` | Sellable |
| G2 | `--g-free-line` | `#E9E5DC` | Border of a free cell |
| G3 | `--g-priv` | `var(--night)` | Private hire — solid dark, the most committed thing on the grid |
| G4 | `--g-hard` | `var(--mint-ink)` | Hard-held match (carries white text — Rule C) |
| G5 | `--g-soft` | `var(--amber)` | Soft-held match |
| G6 | `--g-block` | 45° hatch, `--paper2` / `#E3DFD6` at 4px | Blocked, programme, competition — *texture*, not colour |
| G7 | `--g-past` | `#F7F5F1` | Elapsed, inert |

> **The hatch is the cleverest token in the system.** Blocked time is neither revenue
> nor opportunity; giving it a colour would place it on the same axis as sold and free.
> Texture removes it from that axis entirely.

## 2.2 Contrast — every pair, computed

Verified by computation against WCAG 2.1, not estimated. **Every pair below is AA or
better at the size it is used.**

| Pair | Ratio | WCAG |
|---|---|---|
| ink on paper | 15.65 | AAA |
| ink on surface | 17.50 | AAA |
| white on night-deep | 17.49 | AAA |
| white on night | 13.29 | AAA |
| ink on volt | 13.96 | AAA |
| night on volt | 10.60 | AAA |
| white on night2 / info | 9.86 | AAA |
| ink on mint-pale | 8.88 | AAA |
| info on info-soft | 8.63 | AAA |
| white on red | 5.90 | AA |
| coral-ink on surface | 5.89 | AA |
| white on coral-ink | 5.89 | AA |
| white on mint-ink | 5.84 | AA |
| white on amber | 5.70 | AA |
| amber on surface | 5.70 | AA |
| muted on surface | 5.40 | AA |
| coral-ink on paper | 5.27 | AA |
| white on mint-deep | 5.20 | AA |
| coral-ink on coral-soft | 5.11 | AA |
| mint-ink on mint-soft | 5.08 | AA |
| red on red-soft | 5.06 | AA |
| amber on amber-soft | 5.04 | AA |
| muted on g-past | 4.96 | AA |
| muted on paper | 4.83 | AA |
| muted on line2 | 4.62 | AA |
| muted on paper2 | 4.49 | AA |
| **ink on coral** | **4.50** | AA — the only dark-on-coral pairing |
| coral on paper (non-text: focus ring, rails) | 3.48 | ≥3:1, meets **1.4.11** for UI components |

Deliberately absent: *white on coral* (3.89) and *white on mint* (4.07). See Rule C.

## 2.3 Using a colour

1. Name the **meaning**, then look up the token. Never pick a hex.
2. If white text will sit on it, check Rule C before choosing the base.
3. If it is a state, it also needs a **word** — see [Part 5.3](#53-tag).

---

# Part 3 — Typography

## 3.1 Families

```
Archivo        400 500 600 700 800   — everything
IBM Plex Mono  400 500 600 700       — numbers, times, codes, identifiers
```

Loaded through `next/font/google` (self-hosted at build time, no render-blocking request
to Google, no layout shift) and exposed as `--font-sans` / `--font-mono`.

**The rule for the mono face:** it appears wherever a value must be *compared vertically*
or is a machine artefact — money, times, percentages, slot labels, court codes, badges,
keyboard hints. **Prose is never mono.** This is what makes a column of prices scannable.

`.num` adds `font-variant-numeric: tabular-nums` and `letter-spacing: -.02em`. **Any
figure appearing in a list or table must carry it**, or digits will not align.

## 3.2 The type scale — eleven steps

The prototype used 21 distinct sizes between 7px and 46px. That is a set, not a scale.
The locked scale is eleven steps; every prototype use maps onto one within ~1px.

| Token | px | Used for |
|---|---|---|
| `--t-micro` | **8** | micro overlays: grid glyphs, timeline stop names, calendar block subtitles, court-count overlays, the NOW pill |
| `--t-label` | **9.5** | eyebrows, tags, table headers, field labels, stat keys, calendar hour heads, nav group labels |
| `--t-caption` | **10.5** | stat descriptions, legends, KPI descriptions, calendar block titles, keyboard hints |
| `--t-tiny` | **11** | `.tiny` — the workhorse secondary text; buttons, toast, table numerics |
| `--t-body` | **12.5** | base body, nav items, card titles, table cells, inputs, row lists |
| `--t-lead` | **13** | empty-state titles, ladder counts |
| `--t-title` | **15** | sheet title, brand wordmark |
| `--t-kpi` | **19** | KPI values; also the page title and stat value at ≤900px |
| `--t-head` | **22** | page title |
| `--t-stat` | **27** | stat value |
| `--t-hero` | **38** | the one hero number |

Removed and remapped: 7→8, 8.5→8, 9→9.5, 10→10.5, 11.5→11, 12→12.5, 14→15, 16→15,
20→19, 46→38.

**A size outside this scale is a bug.** If a surface genuinely needs one, that is a
change to the scale, made in `tokens.css` and recorded here — not a local override.

## 3.3 The semantic type roles

These are the ones to reach for. Everything else is a one-off and needs justifying.

| Role | Spec | Purpose |
|---|---|---|
| **Page title** | 22 / 700 / `-.03em` | one per screen; 19 at ≤900px |
| **Page subtitle** | 11 / `--muted` / 1.45 / max-width 640px | the sentence explaining the screen |
| **Card title** | 12.5 / 700 | the card's heading row |
| **Body** | 12.5 / 400 | default |
| **Secondary** (`.tiny`) | 11 / 1.45 / `--muted` | every explanatory line; `<b>` inside reverts to `--ink` 600 |
| **Eyebrow** | 9.5 / 700 / `.15em` / uppercase / `--muted` | group label above a set |
| **Stat key** | 9.5 / 700 / `.15em` / uppercase | tile label |
| **Stat value** | 27 / 700 / `-.035em` / mono / tabular | the number itself |
| **KPI value** | 19 / 700 / `-.03em` | inside grouped KPI blocks |
| **Table header** | 9.5 / 700 / `.12em` / uppercase | `th` |
| **Tag** | 9.5 / 700 / `.04em` / uppercase | state chips |

> **The letter-spacing pattern is systematic and worth internalising:** as size goes
> **down**, tracking goes **up** (22px → `-.03em`; 9.5px → `+.15em`). Small uppercase
> text needs air; large display text needs tightening.

## 3.4 Line height

| Context | Value |
|---|---|
| Default | 1.2 |
| `.tiny` and all explanatory copy | **1.45** |
| `.note` bodies | **1.5** |
| If/then prose | **1.6** |
| Numbers (stat values) | **1** |

Explanatory text is where the reasoning lives, so it gets the most generous leading in
the system. Numbers get `line-height: 1` so a 27px figure does not push its tile taller
than its neighbours.

---

# Part 4 — Spacing and geometry

## 4.1 The spacing scale

Ten steps. The prototype used nearly every integer from 1 to 16; these are the load-
bearing values, with `11` and `14` retained because the whole rhythm rests on them.

```
--s-1:  2px     hairline gaps, grid cell gutters, segmented trough padding
--s-2:  4px     micro gaps
--s-3:  6px     tag padding, tight internal gaps
--s-4:  8px     button gaps, note vertical padding, table cell vertical
--s-5: 11px     THE GAP BETWEEN THINGS — cards, grid columns, stack items, sheet body
--s-6: 14px     THE PADDING INSIDE THINGS — card padding, header gaps, action rows
--s-7: 16px     sheet horizontal padding, page-head bottom margin
--s-8: 24px     main content horizontal padding
--s-9: 34px     empty-state vertical padding
--s-10: 48px    bottom of the scroll
```

### The three numbers to remember

```
11px   the gap BETWEEN cards, and between grid columns
14px   the padding INSIDE a card
13px   the RADIUS of a card
```

Everything else follows from those. Note that `.hair` — the divider inside a card — uses
`11px` margins, matching the card gap: **the rhythm is the same inside and out.**

## 4.2 Radius scale

Radius is its own scale, not the spacing scale.

| Radius | Applied to |
|---|---|
| **999px** | pills, chips, avatars, toggles, badges |
| **13px** | cards, stats, the calendar container |
| **11px** | KPI blocks, toast |
| **9px** | buttons, notes (right side only), nav items, inputs, segmented trough |
| **8px** | small buttons, top-bar buttons, funnel rows |
| **7px** | segmented button, lifecycle step |
| **6px** | tags, calendar blocks, expander squares |
| **5px** | heat-map cells, ticks, the NOW pill |
| **4px** | keyboard hints, legend swatches, timeline band ends |
| **3px** | progress bars, mini bars, sport swatches |
| **2px** | severity rails, timeline bands |

**The pattern:** radius shrinks with the element — roughly **radius ≈ height / 3.5**,
snapped to a step above.

## 4.3 Layout

```
top bar     height 52px, sticky, z-index 20
nav         width 212px, sticky at top:52px, own scroll, min/max-height calc(100vh - 52px)
main        flex:1, padding 16px 24px 48px
```

The asymmetric main padding (16 top / 24 sides / 48 bottom) gives breathing room at the
end of a scroll without wasting vertical space at the start.

### Grids

| Class | Columns | Gap |
|---|---|---|
| `grid2` | 2 equal | 11px |
| `grid3` | 3 equal | 11px |
| `grid4` | 4 equal | 11px |
| `grid6` | `auto-fit, minmax(178px, 1fr)` | 11px |
| `stack` | 1 | 11px |
| `split` | `1.6fr 1fr` | 11px |

`grid6` is the only responsive-by-default grid; the others collapse at breakpoints
([Part 10](#part-10--responsive-and-print)).

## 4.4 Elevation

Only genuinely floating things cast shadows.

| Element | Shadow |
|---|---|
| Sheet | `-20px 0 50px -20px rgba(10,32,40,.45)` |
| Drawer | `0 0 70px rgba(0,0,0,.5)` |
| Toast | `0 12px 28px -12px rgba(0,0,0,.5)` |
| Mobile nav | `12px 0 40px -20px rgba(0,0,0,.4)` |
| Segmented active thumb | `0 1px 2px rgba(0,0,0,.06)` — the one micro-shadow |
| Toggle knob | `0 1px 2px rgba(0,0,0,.2)` |

**Cards never cast shadows.** They are defined by a 1px `--line` border on white against
paper. If a card looks flat, that is the system working.

## 4.5 Focus

```css
:focus-visible {
  outline: 2px solid var(--coral);
  outline-offset: 2px;
  border-radius: inherit;
}
```

Global, single rule, using the existing accent. Coral clears 3:1 against both paper
(3.48) and night, satisfying **WCAG 1.4.11** for non-text UI. Every interactive
element — buttons, chips, nav items, calendar cells, toggles, tabs — inherits it. **Do
not remove an outline without replacing it with an equally visible indicator.**

---

# Part 5 — The five containers

The system's coherence comes from re-use. There are **five containers**, and nearly every
screen is built from them: **card · stat · note · row list · action row**. Before
building anything new, check this list.

## 5.1 Card

```css
background: var(--surface);
border: 1px solid var(--line);
border-radius: 13px;
padding: 14px;
```

Two variants: the plain card for direct content, and a **clipping** variant
(`overflow:hidden`, padding moved to an inner element) for content that must clip to the
radius — tables, grids, the calendar.

**Anatomy:**
```
┌─ 1px --line, radius 13 ──────────────────────┐
│ 14px padding                                  │
│  Title 12.5/700          [right slot: btn/tag]│
│  ↕ 11px                                       │
│  body                                         │
│    rows separated by a hairline or border-top  │
└───────────────────────────────────────────────┘
```

The title row is 12.5/700 on the left with the right-hand slot pushed by
`margin-left:auto`, and 11px below it.

### The hairline

`height:1px; background:var(--line2); margin:11px 0` — a divider **inside** a card.
`--line2`, never `--line`.

## 5.2 Stat tile

```css
/* container: as card */
key         9.5 / 700 / .15em / uppercase / --muted
value       27 / 700 / -.035em / mono / tabular-nums; margin: 4px 0; line-height: 1
description 10.5 / --muted / 1.4
hot variant border-color: var(--coral-line); background: var(--coral-soft);
            value colour: var(--coral-ink)
```

An optional bar sits between value and description with `margin: 6px 0`.

**Structure is always key → value → description.** The description is **not optional**:
a number without a sentence is a vanity metric. When the tile is actionable it becomes a
`<button>` and gains the pointer affordance — it does not change shape.

## 5.3 Tag

```css
display: inline-flex; height: 19px; padding: 0 6px; border-radius: 6px;
font: 700 9.5px/1 var(--font-sans); letter-spacing: .04em; text-transform: uppercase;
background: var(--line2); color: var(--muted);
```

| Variant | Background | Foreground | Used for |
|---|---|---|---|
| *(default)* | `--line2` | `--muted` | neutral state |
| `ok` | `--mint-soft` | `--mint-ink` | confirmed, booked, settled |
| `hot` | `--coral-soft` | `--coral-ink` | live, peak, urgent |
| `warn` | `--amber-soft` | `--amber` | held, provisional, waiting |
| `bad` | `--red-soft` | `--red` | at risk, cancelled |
| `info` | `--info-soft` | `--info` | funded, neutral emphasis |

**Every tag carries a word.** The 19px height and uppercase 9.5px type make it read as a
label, not a button — important, because **tags are never clickable**.

## 5.4 Note

```css
border-left: 3px solid <accent>;
background: <accent>-soft;
padding: 8px 11px;
border-radius: 0 9px 9px 0;
font-size: 11px; line-height: 1.5;
```

**The asymmetric radius is the signature** — square on the left where the rail is,
rounded on the right. Variants: mint, coral, amber, info.

**Notes carry reasoning.** They are the one place in the system where a paragraph is
acceptable.

## 5.5 Row list

```css
display: flex; justify-content: space-between; gap: 11px;
padding: 6px 0; font-size: 12.5px;
border-top: 1px solid var(--line2);   /* :first-child resets to 0 */
key:   var(--muted)
value: font-weight 600; text-align right
```

The label/value workhorse. `border-top` with a `:first-child` reset is used throughout
instead of `border-bottom` — **it means a list can end anywhere without a trailing
rule.**

## 5.6 Action row

```css
display: flex; gap: 11px; align-items: flex-start;
padding: 14px 0; border-top: 1px solid var(--line2);
severity rail:  width 4px; align-self: stretch; border-radius: 2px
                (coral | amber | info | mint)
body title:     12.5px; display: block; margin-bottom: 4px
done variant:   background: linear-gradient(90deg, var(--mint-soft), transparent 62%);
                border-radius: 9px; padding: 11px;
```

**The severity rail is 4px wide and stretches the full row height.** It is the only
vertical colour bar in the system, which is why it reads as severity rather than
decoration. A completed action is **tinted, not boxed** — the mint fades to transparent
at 62%.

---

# Part 6 — Controls

## 6.1 Buttons

```css
base      height 32px; padding 0 14px; radius 9px; 1px solid var(--line);
          background var(--surface); font: 600 11px
small     height 27px; padding 0 11px; radius 8px
primary   background var(--night);      color #fff;  hover var(--night2)
accent    background var(--coral-ink);  color #fff;  hover var(--coral)
secondary background var(--surface)
full      width 100%
disabled  opacity .45; cursor not-allowed
```

**Hierarchy in practice: at most one filled button per card.** The **night** fill is the
default filled button; the **coral-ink** fill is reserved for *the action that spends
money or changes the market*. Everything else is an outline button.

> Per Rule C, the accent button is filled with `--coral-ink` and brightens to `--coral`
> on hover — the inverse of the prototype, which put white 11.5px text on `--coral`
> (3.89:1). Coral still reads as the accent; the label is now legible.

## 6.2 Chips

`height 27px; radius 999px; 1px solid var(--line)` — filters and multi-select. The active
state inverts to a `--night` fill with white text.

## 6.3 Pills (top bar only)

`height 26px; radius 999px; background rgba(255,255,255,.1)`. The active pill uses
`--volt` with `--night` text — one of the few legitimate homes for volt.

## 6.4 Segmented control

```css
trough  display: inline-flex; background: var(--line2); radius 9px; padding 2px; gap 2px
button  height 25px; radius 7px; transparent; color var(--muted)
active  background var(--surface); color var(--ink); box-shadow 0 1px 2px rgba(0,0,0,.06)
```

**The 2px trough padding plus 7px inner radius against 9px outer is the detail that makes
the thumb look inset rather than stuck on.** Three scales of the same idea exist:

| Scale | Height | Radius | Used for |
|---|---|---|---|
| small | 25px | 7 in 9 | binary/ternary mode switches |
| medium | 26px | 7 in 9 | two tabs inside a section |
| large | 28px | 8 in 10 | top-level section switching |

All three share the `--line2` trough, 2–3px padding, a white raised thumb with a 1–2px
micro-shadow, and `--muted` inactive text.

## 6.5 Toggle

`38 × 21px`, knob `17px` travelling `left: 2px → 19px`, active fill `--mint` (a mark, no
text on it — Rule C is satisfied). Transition `.14s`.

## 6.6 Avatar

`26 × 26px`, `border-radius: 50%`, `--line2` fill, initials at 9.5/700 in `--night`.

- **dashed variant** — dashed border, transparent: an *empty seat*.
- **self variant** — `--coral` fill with **`--ink`** initials (4.50:1). Not `--night`
  (3.41:1).

## 6.7 Progress and bars

| Element | Height | Track | Fill |
|---|---|---|---|
| Bar | 5px | `--line2` | `--night` |
| Mini bar | 5px, width 56px | `--line2` | `--night` |
| Progress | 6px | `--line2` | `--mint` / warn `--amber` / bad `--coral` |
| Column chart | 46px column | — | `--night`, peak `--coral` |

## 6.8 Empty state

```css
padding: 34px 16px; text-align: center;
title: display block; font-size 13px; margin-bottom 4px
```

**Every empty state states value, never absence.** Not *"No data"* but *"No matches
currently need rescue. Rakieta will show matches here when a cancellation puts a booking
at risk."* The 34px vertical padding gives the message presence rather than letting it
look like an error.

---

# Part 7 — The schedule calendar

The most specialised surface in the product and the one with the most bespoke rules.

## 7.1 Structure

```css
container   background var(--surface); 1px solid var(--line); radius 13; overflow hidden
scroller    overflow-x: auto
grid        display: grid; min-width: 1180px
row         display: contents      /* rows flatten into the parent grid */
```

`display: contents` on the row is what allows a single CSS grid to own both axes while
the DOM keeps a row-per-court structure. The column template is generated per render: a
fixed name column plus N slot columns.

## 7.2 Sticky architecture — three z-index layers

| Element | Position | z-index |
|---|---|---|
| Corner | sticky left **and** top | 3 |
| Hour header | sticky top | 2 |
| Court name | sticky left | 1 |
| Cell hover | — | 4 |
| Now line | — | 5 |

**The corner must outrank both axes** or it is overrun when scrolled diagonally.

## 7.3 Cell

```css
height: var(--row) /* 44px */;
border-right: 1px solid var(--line2); border-bottom: 1px solid var(--line2);
position: relative; cursor: pointer; transition: .1s; background: none; padding: 0;

hover     box-shadow: inset 0 0 0 2px var(--coral); z-index: 4
past      background: var(--g-past); cursor: default
nosell    background: var(--g-past); opacity: .65
now::before  position:absolute; left:-1px; top:0; bottom:0; width:2px;
             background: var(--coral); z-index: 5
```

**The hover is an inset shadow, not a border**, so the cell does not shift by 2px on
hover — the grid stays absolutely still.

**Past versus nosell is a real distinction.** *Past* is time that has elapsed. *Nosell*
is time outside that court's own opening hours — Court 3 before 09:00. Both are inert,
but nosell also dims to 65% because **it is not a missed opportunity, it is not inventory
at all**.

**The now line** is 2px coral offset `left:-1px`, so it straddles the cell boundary
rather than sitting inside one cell.

## 7.4 Booking block

```css
position: absolute; inset: 2px; radius 6px;
display: flex; flex-direction: column; justify-content: center;
padding: 0 6px; overflow: hidden; pointer-events: none;
title    10.5px / 700, ellipsis
subtitle 8px, opacity .78, ellipsis
glyph    absolute top 4 right 4; 8px; opacity .8
```

`inset: 2px` creates a 2px gutter so adjacent bookings never touch. `pointer-events:none`
so **the click always lands on the cell beneath**, which owns the handler.

| Variant | Fill | Text | Means |
|---|---|---|---|
| Private | `--g-priv` (night) | white 13.29 | private hire — the darkest, most committed |
| Hard hold | `--g-hard` (mint-ink) | white 5.84 | hard-held match |
| Soft hold | `--amber-soft` + **1px dashed `--amber`** | amber 5.04 | soft hold |
| Club | `--night2` | white 9.86 | club-committed court |
| Block / programme | 45° hatch | `--muted` | blocked / programme |

> **The dashed border on the soft hold is the most important single detail on this
> screen.** A soft hold is provisional; the dashed edge says so pre-attentively, before
> any label is read. **Solid fill = certain, dashed outline = provisional.** A manager
> learns this in one session.

## 7.5 Peak indication

Peak hour headers get an `--amber-soft` background with `--amber` text. **Peak is marked
once, in the header**, rather than tinting 4 × 10 cells — which would fight with the
booking fills.

## 7.6 Legend

```css
display: flex; gap: 14px; flex-wrap: wrap; padding: 11px 14px;
border-top: 1px solid var(--line);
swatch: 14 × 14px; radius 4px; grid place-items center; font-size 8px; color #fff
```

Sits **inside** the calendar container, below the grid, above the border-radius clip.
Hidden in print.

---

# Part 8 — Demand surfaces (heat map, demand map, matches, timeline)

These render the demand-matching engine's output. They are the app's most information-
dense surfaces and follow one principle: **encode independent signals in independent
channels — position, size, and corner — so they can be read simultaneously.**

> **Naming caveat.** The domain concepts behind these surfaces (demand pooling, holds,
> rescue, commitment checkpoints) are **not yet in the shared glossary**
> ([`../../CONTEXT.md`](../../CONTEXT.md)) — the Bookings, Courts and Matches contexts are
> unmodelled. The names below are *interface* names. When those contexts are modelled,
> resolve the domain terms into the root glossary first, then rename here to match.
> Do not let this document become the place domain naming is settled.

## 8.1 Heat map

```css
row   display: grid; grid-template-columns: 30px repeat(15, 1fr); gap: 2px
cell  height 19px; radius 3px; background var(--night2); color #fff; 8px/700 mono
hot   background var(--coral-ink)     /* Rule C: white text */
hover outline: 2px solid var(--coral); outline-offset: 1px
```

## 8.2 Demand map

```css
row     display: grid; grid-template-columns: 38px repeat(15, 1fr); gap: 3px
cell    height 30px; radius 5px; mono 10.5px/700
  count       absolute inset 0; grid place-items center     /* how many people */
  free courts absolute left 2 bottom 2; 8px                 /* "2c" */
  marker      absolute right 2 top 2; 8px                   /* ● ○ ◐ ⚠ */
blocked ::after inset 0; 1.5px dashed var(--amber); radius 5px
```

**Three independent signals on a 30px cell**, each in its own corner and its own size:

- **centre, 10.5px** — how many people
- **bottom-left, 8px** — how many courts are free
- **top-right, 8px** — what the engine can do here

### The magnitude ramp

Opacity encodes magnitude, **quantised into five conformant buckets** rather than a
continuous alpha. A continuous ramp cannot state a text colour that is legible at every
step — the prototype's "flip to white above 0.45" produced 2.3:1 text.

| Ramp | Buckets (alpha over `--paper`) | Text |
|---|---|---|
| General demand — `--night2` | 0.18 · 0.32 · 0.46 · 0.60 | `--ink` (4.90 at the darkest) |
| | 1.00 | white (9.86) |
| Eligible — `--coral-ink` | 0.20 · 0.36 · 0.53 · 0.70 | `--ink` (4.91 at the darkest) |
| | 1.00 | white (5.89) |

Bucket = `ceil(value / peak × 4)` clamped to `[1, 5]`. The jump from the fourth bucket to
solid is the most legible break in the ramp, and it is where the text flips.

## 8.3 Match card

```css
row      display flex; gap 11px; padding 14px 0; border-top 1px solid var(--line2)
hover    background var(--line2); radius 11px
past     opacity .62
when     width 52px; centred; mono            /* day over time */
body     flex 1; min-width 0
right    text-align right                     /* state + counts */
```

### Seat pips

```css
pip       11 × 11px; radius 50%; 1.5px solid var(--line); box-sizing border-box
filled    background var(--night)     /* paid, already there */
by-engine background var(--coral)     /* paid, brought by the engine */
```

Hollow = open seat. Four pips answer *"how full, and how much of it was us"* without a
word.

### Court chip

```css
display inline-block; padding: 2px 6px; radius 5px; 10.5px/700 uppercase
booked   background var(--mint-deep); color #fff   /* committed — money is the club's */
off-sale background var(--night);     color #fff   /* held, refundable */
on-sale  background var(--line2);     color var(--muted)  /* available */
```

## 8.4 The five-band timeline

```css
track  display flex; gap 2px; height 7px; position relative; margin-top 14px
band   flex 1; radius 2px; background var(--line2)
       first-child radius 4px 2px 2px 4px; last-child radius 2px 4px 4px 2px

band 1  opened → commitment    var(--mint-pale)
band 2  commitment → rescue    var(--night2)
band 3  rescue → checkpoint    var(--amber)
band 4  checkpoint → play      var(--coral)

current  the same colour at 0.45–0.55 opacity
elapsed  full colour
```

**Bands are equal width, never to scale** — a deliberate information-design decision. The
escalation **mint-pale → night2 → amber → coral** encodes rising consequence.

```css
cursor       absolute; width 2px; height 15px; background var(--ink); z-index 2
cursor label absolute bottom 19px; translateX(-50%); --ink pill;
             white 8px/700 mono; padding 2px 6px; radius 5px
at the end   translateX(-92%)   /* keeps the pill on-canvas */
```

Stop labels below: name at 8px uppercase `--muted`, time at 9.5px mono. Elapsed stops
darken to `--ink` at 75%; the current stop colours its name coral; a met checkpoint turns
mint; a missed one greys and strikes through.

## 8.5 Live indication

Two bespoke animations, and only these: a **1.8s pulse** on the live engine stage and a
**1.6s blink** on the live badge dot. They are the only decorative-looking motion in the
product, justified because *"the engine is running while you are not touching it"* is
otherwise invisible.

---

# Part 9 — Overlays

## 9.1 Sheet — the primary detail surface

```css
scrim  fixed inset 0; background rgba(10,52,65,.42); z-index 60; transition opacity .22s
sheet  fixed right; width min(430px, 94vw); background var(--paper); z-index 61;
       box-shadow -20px 0 50px -20px rgba(10,32,40,.45);
       enter: translateX(100%) → 0 over .24s cubic-bezier(.2,.8,.2,1)
```

Three regions:

```
head  padding 14px 16px; background var(--surface); border-bottom 1px var(--line)
      title 15/700 + secondary line + close
body  padding 14px 16px 24px; scrolls; display grid; gap 11px; align-content start
foot  padding 11px 16px; background var(--surface); border-top 1px var(--line);
      display flex; gap 8px
```

> **The sheet background is `--paper`, not white.** Cards inside it are white, so they
> read as raised on the sheet exactly as they do on the page — **the visual language does
> not change when you go one level deeper.**

The body being a grid with `gap: 11px` means sheet content never needs manual spacers.

## 9.2 Drawer

`min(330px, 92vw)`, `--night-deep` background (darker than `--night`), white text,
`translateX(100%)` with `.26s cubic-bezier(.4,0,.2,1)`. Group labels use `--volt`; the
active item uses `--coral`.

**The drawer is deliberately a different surface from the sheet:** dark, narrower,
faster. It is a developer/operator tool and it looks like one.

## 9.3 Toast

```css
fixed; left 50%; bottom 24px; transform translateX(-50%) translateY(14px);
background var(--night); color #fff; padding 11px 16px; radius 11px; 11px/600;
max-width min(520px, 92vw); opacity 0; transition .2s
on: opacity 1; transform translateX(-50%)
emphasis: font-style normal; color var(--volt)
```

The 14px vertical travel on entry is small — **a nudge, not a leap**. Emphasis renders
volt: **a toast carries one emphasised phrase and it is always the object that changed.**

## 9.4 Z-index scale

| Layer | z |
|---|---|
| Top bar | 20 |
| Mobile nav scrim | 49 |
| Mobile nav | 50 |
| Sheet scrim | 60 |
| Sheet | 61 |
| Drawer scrim | 70 |
| Drawer | 71 |
| Toast | 90 |
| *(calendar internals)* | 1–5, locally scoped |

**Deliberate gaps of 10 between families** leave room to insert without renumbering. A
new overlay picks a family, not an arbitrary number.

---

# Part 10 — Motion

Two keyframes exist in the entire system.

```css
@keyframes rise  { from { opacity:0; transform:translateY(7px) } to { opacity:1; transform:none } }
@keyframes slide { from { transform:translateX(100%) }          to { transform:none } }
```

| Duration | Easing | Used for |
|---|---|---|
| `.1s` | linear | calendar cell hover |
| `.12s` | linear | buttons, chips, nav items |
| `.14s` | linear | toggle knob |
| `.2s` | linear | toast |
| `.22s` | linear | scrim opacity |
| `.24s` | `cubic-bezier(.2,.8,.2,1)` | sheet slide-in — decelerating |
| `.26s` | `cubic-bezier(.4,0,.2,1)` | drawer and mobile nav — standard |

Plus the two live-engine animations in [8.5](#85-live-indication). **Nothing else moves.**

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important }
}
```

---

# Part 11 — Responsive and print

## 11.1 Breakpoints

Two, both **content-driven** rather than device-driven.

### `max-width: 1180px` — the grid stops fitting

```
grid4 → 2 columns
grid3 → 2 columns
grid6 → 3 columns
split → 1 column
```

### `max-width: 900px` — the sidebar stops fitting

```
body layout  → block (nav leaves the flow)
nav          → fixed drawer, translateX(-100%), 236px, revealed by a nav-open state
burger       → appears
nav scrim    → inset 52px 0 0
main         → padding 16px 14px 34px
all grids    → 1 column
page title   → 19px
stat value   → 19px
sheet        → 100vw
tables       → horizontally scrollable, min-width 460px
heat map     → min-width 400px
calendar     → 104px name column + N slots, min-width 1000px (still scrolls — correctly)
week label   → hidden
sport filter → drops off the top bar
```

> **The calendar deliberately does not reflow.** A court grid with fewer columns is not a
> court grid. It scrolls horizontally with sticky court names, which is the correct
> behaviour for a spreadsheet-like surface.

## 11.2 Print

```css
@media print {
  top bar, nav, scrims, sheet, drawer, toast, page-head actions, legend { display: none !important }
  body, main { overflow: visible; height: auto }
  app        { display: block }
  calendar   { min-width: 0 }
  card, calendar { break-inside: avoid }
}
```

**Print is a real feature** — the day sheet is printed at the front desk. All chrome, all
actions and the legend are removed; the calendar's min-width is released so it fits the
page. A new screen is not finished until it prints sensibly.

---

# Part 12 — Writing in the interface

The copy is part of the design system and is governed by rules.

## 12.1 Vocabulary

| Use | Not | Because |
|---|---|---|
| **Off sale** | soft-held / hard-held | The hold *rule* is internal; the club needs to know the hour left the pool |
| **Booked** | confirmed | Booked means the money is the club's; confirmed is a lifecycle state |
| **For sale** | available | An hour is for sale; a *person* is actionable |
| **Actionable** | available (of people) | Everyone on the demand map wants that hour; what differs is whether we may act |
| **Unearned** | lost revenue | It is not lost until the hour has passed |
| **Empty court-hours** | underutilised inventory | Club language, not analyst language |
| **Players still looking for a game** | unsatisfied demand entities | — |

These are **interface copy** decisions. See the naming caveat in [Part 8](#part-8--demand-surfaces-heat-map-demand-map-matches-timeline):
when the underlying contexts are modelled, the domain terms are settled in the root
[`CONTEXT.md`](../../CONTEXT.md) first.

## 12.2 Sentence patterns

**Every number gets a sentence.** The stat description is not optional. A tile that
cannot justify itself in one line is a vanity metric and should be removed.

**Automation is reported as: *Rakieta did X because Y, producing Z.***

> *"Invited 3 players to Thu 13 21:00 — first wave · Kamil, Szymon, Filip · 25,25 zł a
> seat, nobody charged."*

**Empty states state value:** what will appear here, and when.

**Notes carry the reasoning**, always in second person about the club's own position:

> *"Unless another seat sells, the court goes back on sale 13 h from now."*

## 12.3 Numbers

- **Polish formatting throughout:** `2 474,25 zł` — space as thousands separator, comma
  as decimal.
- Money in prose is written in full; money in tiles drops the `zł` where the label
  carries it.
- Durations: `1 h`, `45 min`, `3 d` — **space before the unit**, always abbreviated.
- Percentages: **no space** — `65%`.
- Times: 24-hour, zero-padded — `09:00`.

Format at the edge, in a shared formatter — never with an inline `toLocaleString` in a
component.

---

# Part 13 — Corrections applied to the prototype

The [prototype audit](design-system-v7-prototype-audit.md) recorded twelve
inconsistencies. All are resolved here. **This table is the diff** — read it if
something in this document contradicts the prototype.

| # | Prototype | Locked here | Why |
|---|---|---|---|
| 1 | Six hexes bypass `:root` (`#071C24`, `#12495B`, `#8BC5A8`, `#2C7A5A`, `#F3CFC5`, `#8a6100`) | Tokens: `--night-deep`, `var(--night2)`, `--mint-pale`, `--mint-deep`, `--coral-line`, `var(--amber)` | `#12495B` was `--night2` written by hand; changing the token would have silently missed two places |
| 2 | `--g-free` and `--pad` declared, never referenced | `--g-free` used for the free cell; sport tokens resolve through `var()` | A token nothing references is a lie about the system |
| 3 | 21 type sizes, 7–46px | **11 steps** (Part 3.2) | Every prototype use maps within ~1px; a set is not a scale |
| 4 | Nearly every integer 1–16 as spacing | **10 steps** (Part 4.1), keeping 11 and 14 | Those two are load-bearing; the rest snap to the nearest step |
| 5 | `--muted` `#6E7F85` — 3.73 on paper | **`#5C6D73`** — 4.83 on paper, 5.40 on surface, 4.62 on line2 | The most-referenced token in the system: one line, widest possible reach |
| 6 | `--amber` `#9A6A0B` — 4.18 on its soft | **`#8A5E09`** — 5.04 | Amber text on amber-soft is used at 9.5px |
| 7 | mint on mint-soft — 3.54 | **`--mint-ink` `#0A7355`** — 5.08 | The `ok` tag is 9.5px |
| 8 | White on `--coral` (3.89) and `--mint` (4.07) on buttons, blocks, heat cells | **Rule C** (Part 2.1): white text requires `--coral-ink` / `--mint-ink` / `--mint-deep`; `--ink` is the only dark that may sit on coral | No text in this product reaches WCAG's large-text threshold (18.66px bold), so "AA-large only" means "fails" here |
| 9 | Demand-map text flips to white above alpha 0.45 (≈2.3:1) | **Five quantised buckets** with a stated text colour each (Part 8.2) | A continuous ramp cannot guarantee legible text at every step |
| 10 | Active chip declared twice — `--ink`, then `--night` | Declared once: `--night` | The later declaration won anyway; a reader of the first believed the wrong thing |
| 11 | No `:focus-visible` styles anywhere but inputs | **One global rule** (Part 4.5) | The most serious accessibility gap in the prototype |
| 12 | Sport tokens `--pad / --ten / --squ / --bad` | `--sport-padel / -tennis / -squash / -badminton` | `--bad` (badminton) collided with the `bad` tag (at risk) |
| 13 | CSS injected at runtime in namespaced layers | **No runtime injection.** CSS Modules, colocated with the component | The prototype's layering hazard — *later declarations win* — does not survive into a real codebase ([ADR-0011](../../docs/adr/0011-club-console-design-system.md)) |

Every ratio quoted was computed against WCAG 2.1, not estimated.

---

# Part 14 — Extension guide

## 14.1 Adding a component

1. **Is it one of the five containers?** card · stat · note · row list · action row. If
   yes, **use it**. The system's coherence comes from re-use, not from new parts.
2. **Colour:** pick the *meaning*, then the token. Never pick a hex. Check Rule C if
   white text will sit on it.
3. **Radius:** height ÷ 3.5, snapped to a step on the radius scale (Part 4.2).
4. **Type:** from the eleven-step scale. Secondary text is always 11 / 1.45 / `--muted`.
5. **Spacing:** **11 between things, 14 inside things.** Everything else from the ten-step
   scale.
6. **State:** if it has one, it needs a **tag with a word in it**. Colour alone is never
   the signal.
7. **Focus:** do not remove the global outline.
8. **Print:** decide whether it survives printing.

## 14.2 Adding a colour

Only if it carries a meaning **none of the five semantic accents carries**. It needs:

- a base, a `-soft` at roughly 92% lightness, and an `-ink` if text sits on the soft or
  if white sits on the base;
- a **computed** contrast check against paper, surface and its own soft — all pairs at
  AA or better for the sizes it will be used at;
- an entry in the numbered palette (Part 2.1) and in `tokens.css`;
- a sentence saying what state it means.

## 14.3 Adding a type size or spacing step

Don't, first. If a surface genuinely needs one, change `tokens.css` and Part 3.2 / 4.1 in
the same commit. **A local `font-size: 12px` is a bug**, not an extension.

---

# Appendix A — The token contract

The authoritative values live in
[`../src/shared/ui/tokens.css`](../src/shared/ui/tokens.css). That file and this document
change together.

# Appendix B — Quick reference card

```
COLOUR      coral = live · mint = settled · amber = provisional · red = failed
            volt on DARK only · white text needs *-ink fills (Rule C)
SURFACE     paper background · white cards · --line borders THINGS
                                             --line2 separates ROWS
TYPE        Archivo everywhere · IBM Plex Mono for anything compared vertically
            base 12.5 · secondary 11 · eyebrow 9.5 uppercase .15em
            small text gets MORE tracking, large text gets LESS
            eleven sizes exist; a twelfth is a bug
SPACE       11 between · 14 inside · 13 radius on cards
CONTROL     btn 32 · btn.sm 27 · chip 27 · tag 19 · toggle 38×21
GRID        cell 44px · blocks inset 2px · soft holds are DASHED
MOTION      .12s controls · .24s sheet · nothing else moves
FOCUS       2px coral outline, 2px offset, never removed
STATE       every state has a word, not just a colour
COPY        every number has a sentence
```
