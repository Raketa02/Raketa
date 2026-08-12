> **Archived measurement — not the rules.**
> This is the verbatim audit of the v7 HTML prototype
> (`rakieta-club-console-v7-intent-pool-2.0.html`), preserved because the reason a value
> was chosen is itself information. It is **descriptive**: it records the prototype
> including its inconsistencies (Part 12 below).
>
> **The system to build against is [`design-system.md`](design-system.md).** Where the
> two differ, that file wins — every difference is listed in its Part 13.

---

# Rakieta Club Console v7 — Design System

**Source of truth:** `rakieta-club-console-v7-intent-pool-2.0.html`
**Total CSS across all layers:** 36 570 bytes · 255 selectors in the base sheet + 4 injected layers
**Design tokens declared:** 34
**Nature of this document:** descriptive first, prescriptive second. Every value below was read out of the built stylesheet. Where the implemented system is inconsistent, this document says so rather than describing the system as it was meant to be — those are collected in Part 12.

---

# Part 1 — Design philosophy

## 1.1 The three commitments

**1. The interface is a document, not an application.**
There is no chrome for its own sake, no gradient for its own sake, no shadow that does not indicate elevation. The paper background (`#F4F2ED`) and the serif-adjacent grotesque establish a reading surface. A manager scanning at 08:00 is reading, not operating.

**2. Colour carries meaning, never decoration.**
Every colour in the palette maps to a state or a category. There is no "brand blue" applied to a button because buttons are blue. Coral means *this is live and it is moving*. Mint means *settled*. Amber means *provisional, and time is working against it*. If a new element needs a colour, the question is which of those it is — not which looks best.

**3. Density is a feature.**
Base font size is **12.5px**, rows are **44px**, card padding is **14px**. This is deliberately tighter than a consumer product. A club manager needs a day on one screen; scrolling to compare two hours is a failure. The density is bought back with generous line-height (1.45) on secondary text and disciplined whitespace between groups.

## 1.2 What the system refuses

| Refused | Why |
|---|---|
| Drop shadows on cards | Elevation is reserved for genuinely floating surfaces: sheet, drawer, toast |
| Colour-only state | Every tag carries a word. Colour is redundant reinforcement, never the sole signal |
| More than one accent | Coral is the only accent. Volt is a highlight *within* dark surfaces only |
| Icons without labels | Nav icons sit beside text; no icon-only controls except the sheet close |
| Animation as delight | Two keyframes exist, both functional (entry, sheet slide) |

---

# Part 2 — Colour

## 2.1 Numbered palette

### Primary — the ink family

The reading colours. These carry text and the structural darks.

| # | Token | Hex | Role |
|---|---|---|---|
| P1 | `--ink` | `#101B20` | Body text, headings, the default foreground |
| P2 | `--night` | `#0A3441` | Primary dark surface: active nav, dark buttons, toast, progress fills |
| P3 | `--night2` | `#12495B` | Secondary dark: hover on dark buttons, secondary fills |
| P4 | `--muted` | `#6E7F85` | Secondary text, labels, eyebrows, captions |

`--ink` on `--paper` is **15.65:1** — AAA with enormous headroom, which is what buys the 12.5px base size.

### Secondary — the paper family

The surfaces. Everything sits on one of these.

| # | Token | Hex | Role |
|---|---|---|---|
| S1 | `--paper` | `#F4F2ED` | Application background; also the sheet background |
| S2 | `--paper2` | `#EDEAE3` | Deeper paper, used in the block hatch |
| S3 | `--surface` | `#FFFFFF` | Cards, nav, table headers, calendar — everything raised off the paper |
| S4 | `--line` | `#E5E1D8` | Structural borders: card edges, nav divider, table header rule |
| S5 | `--line2` | `#F0EDE6` | Hairlines and inert fills: row separators, track backgrounds, segmented-control troughs |

**The `--line` / `--line2` distinction is the most-used decision in the system.** `--line` bounds a thing; `--line2` separates rows *within* a thing. Getting this wrong is the single most common visual error — a card whose internal rows use `--line` reads as five cards.

### Tertiary — the semantic accents

Each maps to exactly one meaning. Each has a **soft** companion for backgrounds and, where needed, an **ink** companion for text on the soft.

| # | Token | Hex | Soft | Ink | Means |
|---|---|---|---|---|---|
| T1 | `--coral` | `#E8482B` | `--coral-soft` `#FDEBE6` | `--coral-ink` `#B8351C` | Live, urgent, the accent. The only accent. |
| T2 | `--mint` | `#0C8F6B` | `--mint-soft` `#E2F3EC` | — | Settled, confirmed, done, safe |
| T3 | `--amber` | `#9A6A0B` | `--amber-soft` `#FBF0DA` | — | Provisional, soft-held, time working against it |
| T4 | `--red` | `#B4392C` | `--red-soft` `#FBEAE7` | — | Failure, cancellation, at risk |
| T5 | `--info` | `#12495B` | `--info-soft` `#EAF1F4` | `--info-line` `#C7DBE3` | Neutral emphasis, explanation |

**Amber versus red is a real distinction, not a severity gradient.** Amber means *this may still resolve, and the clock is the thing deciding*. Red means *this has failed or is failing*. A soft-held court is amber forever; it becomes red only if it dies.

### Quaternary — highlight

| # | Token | Hex | Role |
|---|---|---|---|
| Q1 | `--volt` | `#D9F24B` | Highlight **on dark surfaces only** — active pill in the top bar, scenario group labels in the drawer, emphasis inside toasts, nav badge on an active item |

Volt never appears on paper. `night on volt` is **10.60:1**; volt on paper would be roughly 1.3:1 and illegible. This is a hard rule, not a preference.

### Quinary — sport identity

| # | Token | Hex | Sport |
|---|---|---|---|
| X1 | `--pad` | `#E8482B` | Padel (= coral) |
| X2 | `--ten` | `#0C8F6B` | Tennis (= mint) |
| X3 | `--squ` | `#12495B` | Squash (= night2) |
| X4 | `--bad` | `#9A6A0B` | Badminton (= amber) |

**These deliberately alias the semantic colours.** A club runs one or two sports; the collision between "padel" and "urgent" is acceptable because sport dots never appear in a severity context. If a club ran all four, this would need revisiting.

### Senary — the calendar surface

The grid speaks in **fills**, not tags, so it gets its own set. A cell must be readable at 44 × ~38px with no room for a label.

| # | Token | Value | Means |
|---|---|---|---|
| G1 | `--g-free` | `#FFFFFF` | Sellable |
| G2 | `--g-free-line` | `#E9E5DC` | Border of a free cell |
| G3 | `--g-priv` | `#0A3441` | Private hire — solid dark, the most committed thing on the grid |
| G4 | `--g-hard` | `#0C8F6B` | Hard-held match |
| G5 | `--g-soft` | `#9A6A0B` | Soft-held match |
| G6 | `--g-block` | 45° hatch, `#EDEAE3` / `#E3DFD6` at 4px | Blocked, programme, competition — *texture*, not colour, because it is not sold and not sellable |
| G7 | `--g-past` | `#F7F5F1` | Elapsed, inert |

**The hatch is the cleverest token in the system.** Blocked time is neither revenue nor opportunity; giving it a colour would place it on the same axis as sold and free. Texture removes it from that axis entirely.

## 2.2 Token usage audit

Measured across all layers:

| Token | References | |
|---|---|---|
| `--muted` | 54 | the most-used token in the system |
| `--line2` | 46 | |
| `--coral` | 31 | |
| `--line` | 25 | |
| `--night` | 21 | |
| `--ink` | 17 | |
| `--mint` | 14 | |
| `--amber` | 14 | |
| `--volt` | 5 | |
| `--red` | 1 | correctly rare — genuine failure is rare |
| `--g-free`, `--pad` | **0** | declared and never referenced |

## 2.3 Contrast

Computed, not assumed.

| Pair | Ratio | WCAG |
|---|---|---|
| ink on paper | 15.65 | AAA |
| ink on surface | 17.50 | AAA |
| white on top bar `#071C24` | 17.49 | AAA |
| white on night | 13.29 | AAA |
| night on volt | 10.60 | AAA |
| white on night2 | 9.86 | AAA |
| info on info-soft | 8.63 | AAA |
| coral-ink on coral-soft | 5.11 | AA |
| red on red-soft | 5.06 | AA |
| white on amber | 4.73 | AA |
| **muted on surface** | **4.17** | AA-large only |
| **amber on amber-soft** | **4.18** | AA-large only |
| **white on mint** | **4.07** | AA-large only |
| **white on coral** | **3.89** | AA-large only |
| **muted on paper** | **3.73** | AA-large only |
| **muted on line2** | **3.57** | AA-large only |
| **mint on mint-soft** | **3.54** | AA-large only |

**Six pairs fail AA for normal-size text.** They are used at 9.5–11px, which is *below* the large-text threshold, so those uses are non-conformant. See Part 12.

---

# Part 3 — Typography

## 3.1 Families

```
Archivo        400 500 600 700 800   — everything
IBM Plex Mono  400 500 600 700       — numbers, times, codes, identifiers
```

Loaded from Google Fonts with `preconnect` on both origins and `display=swap`.

**The rule for the mono face:** it appears wherever a value must be *compared vertically* or is a machine artefact — money, times, percentages, slot labels, court codes, badges, keyboard hints. Prose is never mono. This is what makes a column of prices scannable.

`.num` adds `font-variant-numeric: tabular-nums` and `letter-spacing: -.02em`. Any figure that appears in a list or table must carry it, or digits will not align.

## 3.2 The implemented type scale

21 distinct sizes are in use. Ordered by frequency:

| px | Uses | Where |
|---|---|---|
| **9.5** | 19 | eyebrows, tags, table headers, field labels, stat keys, calendar hour heads |
| **11** | 15 | `.tiny` — the workhorse secondary text |
| **10.5** | 11 | stat descriptions, legends, kpi descriptions, note bodies |
| **12.5** | 10 | base body, nav items, card titles, buttons |
| **12** | 8 | table cells, row-list text, inputs |
| **11.5** | 8 | buttons, small headings, if/then prose |
| **10** | 7 | calendar block titles, keyboard hints |
| **9** | 6 | nav group labels, drawer group labels, heat map labels |
| **13** | 6 | empty-state titles, ladder counts |
| **8.5** | 5 | calendar block subtitles, heat map cells, NOW pill |
| **8** | 5 | timeline stop labels, grid glyphs |
| 19 | 3 | kpi values, mobile stat values |
| 20 | 2 | mobile stat value, big-number suffix |
| 7 | 2 | court-count overlay on heat cells |
| 14, 15, 16, 22, 27, 38, 46 | 1 each | brand, sheet title, big numbers |

**This is not a scale — it is a set.** Documented honestly; a proposed consolidation is in Part 12.

## 3.3 The semantic type roles

These are the ones to use. Everything else is a one-off.

| Role | Spec | Purpose |
|---|---|---|
| **Page title** | 22px / 700 / `-.03em` | `.phead h1`, one per screen |
| **Page subtitle** | 11px / `--muted` / 1.45 / max-width 640px | the sentence explaining the screen |
| **Card title** | 12.5px / 700 | `cardT` heading |
| **Body** | 12.5px / 400 | default |
| **Secondary** (`.tiny`) | 11px / 1.45 / `--muted` | every explanatory line; `b` inside reverts to `--ink` 600 |
| **Eyebrow** | 9.5px / 700 / `.15em` / uppercase / `--muted` | group labels above a set |
| **Stat key** | 9.5px / 700 / `.15em` / uppercase | tile label |
| **Stat value** | 27px / 700 / `-.035em` / mono | the number itself |
| **KPI value** | 19px / 700 / `-.03em` | inside grouped kpi blocks |
| **Table header** | 9.5px / 700 / `.12em` / uppercase | `.tbl th` |
| **Tag** | 9.5px / 700 / `.04em` / uppercase | state chips |

**The letter-spacing pattern is systematic and worth internalising:** as size goes *down*, tracking goes *up* (22px → `-.03em`; 9.5px → `+.15em`). Small uppercase text needs air; large display text needs tightening.

## 3.4 Line height

| Context | Value |
|---|---|
| Default | browser default (~1.2) |
| `.tiny` and all explanatory copy | **1.45** |
| `.note` bodies | **1.5** |
| `.ifthen` prose | **1.6** |
| Numbers (`.stat .v`) | **1** |

Explanatory text is where the reasoning lives, so it gets the most generous leading in the system. Numbers get `line-height: 1` so a 27px figure does not push its tile taller than its neighbours.

---

# Part 4 — Spacing and geometry

## 4.1 The implemented spacing set

Values 1–16 appear at nearly every integer. The frequency distribution shows the real system underneath:

| px | Frequency | Meaning in practice |
|---|---|---|
| **9** | 26 | the most common gap: button internals, note padding, small radii |
| **5** | 22 | tight internal gap, small radius |
| **8** | 21 | nav item padding, radii |
| **2, 3** | 19, 19 | hairline gaps, grid cell gaps |
| **10, 11** | 19, 19 | **11 is the canonical card gap** — every grid, stack and card spacer |
| **6, 7** | 18, 15 | button gaps, tag padding |
| **4** | 15 | micro gaps |
| **12** | 15 | flex gaps in headers and rows |
| **14** | 14 | **the canonical card padding**, and the header gap |
| **13** | 8 | **the canonical card radius** |
| **16** | 6 | sheet horizontal padding, page-head bottom margin |
| **24** | 3 | main content horizontal padding |

### The three numbers to remember

```
11px   the gap between cards, and between grid columns
14px   the padding inside a card
13px   the radius of a card
```

Everything else follows from those.

## 4.2 Radius scale

| Radius | Applied to |
|---|---|
| **999px** | pills, chips, avatars, toggles, badges |
| **13px** | cards, stats, the calendar container |
| **11px** | kpi blocks, toast |
| **9px** | buttons, notes (right side only), nav items, inputs, segmented trough |
| **8px** | small buttons, top-bar buttons, sitem, funnel rows |
| **7px** | segmented button, lifecycle step |
| **6px** | tags, calendar blocks, expander squares |
| **5px** | heat map cells, ticks, NOW pill |
| **4px** | keyboard hints, legend swatches, timeline band ends |
| **3px** | progress bars, mini bars, sport swatches |
| **2px** | severity rails, timeline bands |

**The pattern:** radius shrinks with the element. A 32px button gets 9px; a 19px tag gets 6px; a 5px progress bar gets 3px. Roughly *radius ≈ height / 3.5*, clamped.

## 4.3 Layout

```
#top    height 52px, sticky, z-index 20
#nav    width 212px, sticky at top:52px, own scroll, min/max-height calc(100vh - 52px)
#main   flex:1, padding 20px 24px 48px
```

The asymmetric main padding (20 top / 24 sides / 48 bottom) gives breathing room at the end of a scroll without wasting vertical space at the start.

### Grids

| Class | Columns | Gap |
|---|---|---|
| `.grid2` | 2 equal | 11px |
| `.grid3` | 3 equal | 11px |
| `.grid4` | 4 equal | 11px |
| `.grid6` | `auto-fit, minmax(178px, 1fr)` | 11px |
| `.stack` | 1 | 11px |
| `.split` | `1.6fr 1fr` | 11px |

`.grid6` is the only responsive-by-default grid; the others collapse at breakpoints.

## 4.4 Elevation

Only four things cast shadows, and each is genuinely floating:

| Element | Shadow |
|---|---|
| Sheet | `-20px 0 50px -20px rgba(10,32,40,.45)` |
| Drawer | `0 0 70px rgba(0,0,0,.5)` |
| Toast | `0 12px 28px -12px rgba(0,0,0,.5)` |
| Mobile nav | `12px 0 40px -20px rgba(0,0,0,.4)` |
| Segmented active | `0 1px 2px rgba(0,0,0,.06)` — the one micro-shadow, indicating the raised thumb |
| Toggle knob | `0 1px 2px rgba(0,0,0,.2)` |

Cards never cast shadows. They are defined by a 1px `--line` border on white against paper.

---

# Part 5 — Component reference

## 5.1 Card

```css
.card   { background:#fff; border:1px solid var(--line); border-radius:13px; padding:14px }
.card-n { same, overflow:hidden; }  .card-n .pad { padding:14px }
```

Two variants: `.card` for direct content, `.card-n` for content that must clip to the radius (tables, grids). `cardT(title, right, body)` renders `.card-n` with a title row: title `12.5px/700` on the left, right-hand slot pushed by `margin-left:auto`, `10px` bottom margin.

**Card anatomy:**
```
┌─ 1px --line, radius 13 ──────────────────────┐
│ 14px padding                                  │
│  Title 12.5/700          [right slot: btn/tag]│
│  ↕ 10px                                       │
│  body                                         │
│    rows separated by .hair or .rl border-top  │
└───────────────────────────────────────────────┘
```

### `.hair`
`height:1px; background:var(--line2); margin:11px 0` — a divider *inside* a card. Note the 11px, matching the card gap: the rhythm is the same inside and out.

## 5.2 Stat tile

```css
.stat     { background:#fff; border:1px solid var(--line); border-radius:13px; padding:14px }
.stat .k  { 9.5px / 700 / .15em / uppercase / --muted }
.stat .v  { 27px / 700 / -.035em / mono / tabular-nums; margin:5px 0 3px; line-height:1 }
.stat .d  { 10.5px / --muted / 1.4 }
.stat.hot { border-color:#F3CFC5; background:var(--coral-soft) }
.stat.hot .v { color:var(--coral-ink) }
```

Optional `.bar` sits between value and description with `margin:7px 0 6px`.

**Structure is always key → value → description.** The description is not optional: a number without a sentence is a vanity metric. When `{act}` is passed the tile becomes a `<button>` and gains `.clik`.

## 5.3 Tag

```css
.tag { inline-flex; height:19px; padding:0 7px; radius:6px;
       9.5px / 700 / .04em / uppercase; background:--line2; color:--muted }
```

| Variant | Background | Foreground | Used for |
|---|---|---|---|
| *(default)* | `--line2` | `--muted` | neutral state |
| `.ok` | `--mint-soft` | `--mint` | confirmed, booked, settled |
| `.hot` | `--coral-soft` | `--coral-ink` | live, peak, urgent |
| `.warn` | `--amber-soft` | `--amber` | held, provisional, waiting |
| `.bad` | `--red-soft` | `--red` | at risk, cancelled |
| `.info` | `--info-soft` | `--info` | funded, neutral emphasis |

**Every tag carries a word.** The 19px height and uppercase 9.5px type make it read as a label, not a button — important, because tags are never clickable.

## 5.4 Buttons

```css
.btn      { height:32px; padding:0 13px; radius:9px; 1px --line; #fff; 11.5px/600 }
.btn.sm   { height:27px; padding:0 10px; radius:8px; font-size:11px }
.btn.p    { --coral fill, white text; hover --coral-ink }      primary, destructive-adjacent
.btn.n    { --night fill, white text; hover --night2 }         primary, safe
.btn.s    { white fill }                                        secondary
.btn.full { width:100% }
.btn[disabled] { opacity:.45; cursor:not-allowed }
```

**Hierarchy in practice:** at most one filled button per card. `.n` is the default filled button; `.p` (coral) is reserved for the action that spends money or changes the market. Everything else is `.btn` or `.btn.sm` outline.

### Chips
`height:27px; radius:999px; 1px --line` — filters and multi-select. `.on` inverts to `--night` fill (the base sheet declares `--ink` first and `--night` later; **the later declaration wins**).

### Pills (top bar only)
`height:26px; radius:999px; rgba(255,255,255,.1)` — `.on` uses `--volt` with `--night` text.

### Segmented control
```css
.seg        { inline-flex; background:--line2; radius:9px; padding:2px; gap:2px }
.seg button { height:25px; radius:7px; transparent; --muted }
.seg .on    { #fff; --ink; box-shadow:0 1px 2px rgba(0,0,0,.06) }
```
The 2px trough padding plus 7px inner radius against 9px outer is the detail that makes the thumb look inset rather than stuck on.

### Toggle
`38 × 21px`, knob `17px` travelling `left:2px → 19px`, `.on` fills `--mint`. Transition `.14s`.

## 5.5 Note

```css
.note { border-left:3px solid; background:--line2; padding:9px 11px;
        border-radius:0 9px 9px 0; 11px / 1.5 }
```

**The asymmetric radius is the signature.** Square on the left where the rail is, rounded on the right. Variants: `.mint`, `.coral`, `.amber`, `.info` — each sets `border-color` and the matching soft background.

Notes carry reasoning. They are the one place in the system where a paragraph is acceptable.

## 5.6 Row list

```css
.rl { flex; justify-content:space-between; gap:12px; padding:7px 0; font-size:12px;
      border-top:1px solid --line2 }
.rl:first-child { border-top:0 }
.rl .k { --muted }   .rl .v { font-weight:600; text-align:right }
```

The label/value workhorse. `border-top` with `:first-child` reset is used throughout instead of `border-bottom` — it means a list can end anywhere without a trailing rule.

## 5.7 Action row

```css
.act        { flex; gap:12px; align-items:flex-start; padding:13px 0; border-top:1px --line2 }
.act .sev   { width:4px; align-self:stretch; radius:2px }   /* coral | amber | info | ok */
.act .bd b  { 12.5px; display:block; margin-bottom:3px }
.act.done   { background:linear-gradient(90deg, var(--mint-soft), transparent 62%);
              radius:9px; padding:11px 10px }
```

**The severity rail is 4px wide and stretches the full row height.** It is the only vertical colour bar in the system, which is why it reads as severity rather than decoration. `.act.done` fades mint to transparent at 62% — a completed action is tinted, not boxed.

## 5.8 Table

```css
.tbl th { 9.5px/700/.12em uppercase --muted; text-align:left;
          padding:0 10px 8px; border-bottom:1px solid --line }
.tbl td { padding:9px 10px; border-bottom:1px solid --line2; vertical-align:middle }
.tbl tr:last-child td { border-bottom:0 }
.tbl .r { text-align:right }        .tbl .num { font-size:11.5px }
.tbl tr.win td { background:--mint-soft }
```

Header rule uses `--line`; body rules use `--line2`. `.win` highlights a recommended row (used by the price ladder).

## 5.9 Avatar

`26 × 26px`, `border-radius:50%`, `--line2` fill, initials at 9.5px/700 in `--night`.
`.av.d` — dashed border, transparent: an *empty seat*.
`.av.me` — coral fill: the current user.

## 5.10 Progress and bars

| Element | Height | Track | Fill |
|---|---|---|---|
| `.bar` | 5px | `--line2` | `--night` |
| `.minibar` | 5px, width 56px | `--line2` | `--night` |
| `.prg` | 6px | `--line2` | `--mint` / `.warn` amber / `.bad` coral |
| `.hbar` | 46px column chart | — | `--night`, `.pk` coral |

## 5.11 Empty state

```css
.empty   { padding:34px 16px; text-align:center }
.empty b { display:block; font-size:13px; margin-bottom:5px }
```

**Every empty state states value, never absence.** Not "No data" but *"No matches currently need rescue. Rakieta will show matches here when a cancellation puts a booking at risk."* The 34px vertical padding gives the message presence rather than letting it look like an error.

---

# Part 6 — The schedule calendar

The most specialised surface in the product and the one with the most bespoke rules.

## 6.1 Structure

```css
#cal        { #fff; 1px --line; radius 13; overflow:hidden }
.calscroll  { overflow-x:auto }
.calgrid    { display:grid; min-width:1180px }
.crow       { display:contents }     /* rows are flattened into the parent grid */
```

`display:contents` on the row is what allows a single CSS grid to own both axes while the DOM keeps a row-per-court structure. Column template is generated per render: a fixed name column plus 30 slot columns.

## 6.2 Sticky architecture — three z-index layers

| Element | Position | z-index |
|---|---|---|
| `.corner` | sticky left **and** top | 3 |
| `.ch` (hour header) | sticky top | 2 |
| `.cname` (court name) | sticky left | 1 |
| `.cell:hover` | — | 4 |
| `.cell.now::before` | — | 5 |

The corner must outrank both axes or it will be overrun when scrolled diagonally.

## 6.3 Cell

```css
.cell        { height:var(--row) /* 44px */; border-right:1px --line2;
               border-bottom:1px --line2; position:relative; cursor:pointer;
               transition:.1s; background:none; padding:0 }
.cell:hover  { box-shadow:inset 0 0 0 2px var(--coral); z-index:4 }
.cell.past   { background:var(--g-past); cursor:default }
.cell.nosell { background:var(--g-past); opacity:.65 }
.cell.now::before { content:''; position:absolute; left:-1px; top:0; bottom:0;
                    width:2px; background:var(--coral); z-index:5 }
```

**The hover is an inset shadow, not a border**, so the cell does not shift by 2px on hover — the grid stays absolutely still.

**`.past` versus `.nosell` is a real distinction.** `.past` is time that has elapsed. `.nosell` is time outside that court's own opening hours — Court 3 before 09:00. Both are inert, but `.nosell` also dims to 65% because it is not a missed opportunity, it is not inventory at all.

**The now line** is 2px coral, offset `left:-1px` so it straddles the cell boundary rather than sitting inside one cell.

## 6.4 Booking block

```css
.blk    { position:absolute; inset:2px; radius:6px; flex column centred;
          padding:0 7px; overflow:hidden; pointer-events:none }
.blk b  { 10px/700; ellipsis }
.blk span { 8.5px; opacity:.78; ellipsis }
.blk .gy  { absolute top:3 right:4; 8px; opacity:.8 }
```

`inset:2px` creates a 2px gutter so adjacent bookings never touch. `pointer-events:none` so the click always lands on the cell beneath, which owns the handler.

| Class | Fill | Text | Means |
|---|---|---|---|
| `.b-priv` | `--g-priv` `#0A3441` | white | private hire — the darkest, most committed |
| `.b-hard` | `--g-hard` `#0C8F6B` | white | hard-held match |
| `.b-soft` | `--amber-soft` + **1px dashed `--amber`** | amber | soft hold |
| `.b-club` | `--night2` | white | club-committed court |
| `.b-block` / `.b-prog` | 45° hatch | `--muted` | blocked / programme |

**The dashed border on `.b-soft` is the most important single detail on this screen.** A soft hold is provisional; the dashed edge says so pre-attentively, before any label is read. Solid fill = certain, dashed outline = provisional. A manager learns this in one session.

## 6.5 Peak indication

`.ch.pk` gives peak hour headers `--amber-soft` background with `--amber` text. Peak is marked once, in the header, rather than tinting 4 × 10 cells — which would fight with the booking fills.

## 6.6 Legend

```css
.leg   { flex; gap:14px; wrap; padding:10px 14px; border-top:1px --line }
.leg i { 14 × 14px; radius:4px; grid place-items:center; font-size:7px; color:#fff }
```

Sits inside the calendar container, below the grid, above the border radius clip. Hidden in print.

---

# Part 7 — Lists, maps and the Intent Pool surfaces

## 7.1 Heat map (base)

```css
.hm .hmrow { grid: 30px repeat(15, 1fr); gap:2px }
.hm .hmc   { height:19px; radius:3px; --night2 fill; white 8.5px/700 mono }
.hm .hmc.hot   { --coral }
.hm .hmc:hover { outline:2px solid --coral; outline-offset:1px }
```

## 7.2 Intent Pool map

```css
.ipmrow { grid: 38px repeat(15, 1fr); gap:3px }
.ipc    { height:30px; radius:5px; mono 10px/700 }
.ipc .ipn      { absolute inset:0; grid place-items:center }   /* the number */
.ipc .ipcourt  { absolute left:2 bottom:1; 7px }               /* "2c" free-court count */
.ipc .ipmk     { absolute right:2 top:1; 8px }                 /* ● ○ ◐ ⚠ marker */
.ipc.blocked::after { inset:0; 1.5px dashed --amber; radius:5px }
```

**Three independent signals on a 30px cell**, each in its own corner and its own size:
- centre, 10px — how many people
- bottom-left, 7px — how many courts are free
- top-right, 8px — what the engine can do here

Opacity encodes magnitude: `rgba(18,73,91, a)` for general demand, `rgba(232,72,43, a)` for eligible, where `a = max(0.18, min(1, v/peak))`. Text flips to white above `a > 0.45`.

## 7.3 Match card (Matches formed)

```css
.ipm    { flex; gap:12px; padding:13px 0; border-top:1px --line2 }
.ipm:hover { background:--line2; radius:10px }
.ipm.past  { opacity:.62 }
.ipmw   { width:52px; centred; mono }        /* day over time */
.ipmb   { flex:1; min-width:0 }              /* the body */
.ipmr   { text-align:right }                 /* state + counts */
```

### Seat pips
```css
.ipseats i      { 11 × 11px; radius:50%; 1.5px solid --line; box-sizing:border-box }
.ipseats i.on   { --night fill }     /* paid, already there */
.ipseats i.pool { --coral fill }     /* paid, brought by the engine */
```
Hollow = open seat. Four pips answer "how full, and how much of it was us" without a word.

### Court chip
```css
.ipcourt { inline-block; padding:1.5px 7px; radius:5px; 10px/700 uppercase }
.ipc-booked  { #2C7A5A fill, white }   /* committed — money is the club's */
.ipc-offsale { --night fill, white }   /* held, refundable */
.ipc-onsale  { --line2 fill, --muted } /* available */
```

## 7.4 The five-band timeline

```css
.iptl   { flex; gap:2px; height:7px; position:relative; margin-top:14px }
.iptl i { flex:1; radius:2px; background:--line2 }
.iptl i:first-child { radius:4px 2px 2px 4px }
.iptl i:last-child  { radius:2px 4px 4px 2px }

.b1 opened→commitment   #8BC5A8   (soft green)
.b2 commitment→rescue   #12495B   (night2)
.b3 rescue→checkpoint   --amber
.b4 checkpoint→play     --coral

.on  { same colour at 0.45–0.55 opacity }   /* the band the clock is in */
.done{ full colour }                        /* elapsed */
```

**Bands are equal width, never to scale** — a deliberate information-design decision documented in the product docs. The escalation green → night → amber → coral encodes rising consequence.

```css
.ipcur    { absolute; 2px wide; 15px tall; --ink; z-index:2 }
.ipcur em { absolute bottom:19px; translateX(-50%); --ink pill;
            white 8.5px/700 mono; padding:2px 6px; radius:5px }
.ipcur.end em { transform: translateX(-92%) }   /* keeps the pill on-canvas at the end */
```

Stop labels below: name at 8px uppercase `--muted`, time at 9.5px mono. `.past` darkens to `--ink` at 75%; `.at` colours the name coral; `.g-met` turns COMMITMENT green, `.g-missed` greys and strikes it through.

## 7.5 Sub-navigation patterns

Three variants of the same idea, at three scales:

| Class | Height | Radius | Used for |
|---|---|---|---|
| `.seg` | 25px | 7px in 9px trough | binary/ternary mode switches |
| `.ipsub` | 26px | 7px in 9px trough | two tabs inside a section |
| `.ipsec` | 28px | 8px in 10px trough | the four Intent Pool sections |

All three share: `--line2` trough, 2–3px padding, white raised thumb with a 1–2px micro-shadow, `--muted` inactive text.

---

# Part 8 — Overlays

## 8.1 Sheet (the primary detail surface)

```css
#ssc    { fixed inset:0; rgba(10,52,65,.42); z-index:60; transition opacity .22s }
#sheet  { fixed right; width:min(430px, 94vw); background:--paper; z-index:61;
          shadow -20px 0 50px -20px rgba(10,32,40,.45);
          transform:translateX(100%) }
body.sheetopen #sheet { animation:slide .24s cubic-bezier(.2,.8,.2,1) forwards }
```

Three regions:
```
#shead  14px 16px, white, border-bottom --line   title 15px/700 + .tiny sub + close
#sbody  14px 16px 24px, scrolls, display:grid, gap:11px, align-content:start
#sfoot  12px 16px, white, border-top --line, flex gap 7px
```

**The sheet background is `--paper`, not white.** Cards inside it are white, so they read as raised on the sheet exactly as they do on the page — the visual language does not change when you go one level deeper.

`#sbody` being a grid with `gap:11px` means sheet content never needs manual spacers.

## 8.2 Drawer (scenarios)

`#drawer` — `min(330px, 92vw)`, `#071C24` (darker than `--night`), white text, `translateX(100%)` with a `.26s cubic-bezier(.4,0,.2,1)` transform. Group labels use `--volt`; the active item uses `--coral`.

The drawer is deliberately a *different* surface from the sheet: dark, narrower, faster. It is a developer/demo tool, and it looks like one.

## 8.3 Toast

```css
#toast { fixed; left:50%; bottom:22px; translateX(-50%) translateY(14px);
         --night; white; padding:10px 15px; radius:11px; 11.5px/600;
         max-width:min(520px,92vw); opacity:0; transition:.2s }
#toast.on { opacity:1; transform:translateX(-50%) }
#toast em { font-style:normal; color:var(--volt) }
```

The 14px vertical travel on entry is small — a nudge, not a leap. `em` renders volt: toasts carry one emphasised phrase and it is always the object that changed.

## 8.4 Z-index scale

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

Deliberate gaps of 10 between families leave room to insert without renumbering.

---

# Part 9 — Motion

Two keyframes exist in the entire system.

```css
@keyframes rise  { from { opacity:0; transform:translateY(7px) } to { opacity:1; transform:none } }
@keyframes slide { from { transform:translateX(100%) } to { transform:none } }
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

Two bespoke animations exist in the Intent Pool: `ippulse` (1.8s, the live engine stage) and `ipblink` (1.6s, the LIVE badge dot). Both indicate *something is genuinely happening now* and are the only decorative-looking motion in the product — justified because "the engine is running while you are not touching it" is otherwise invisible.

```css
@media (prefers-reduced-motion:reduce) { * { animation:none!important; transition:none!important } }
```

---

# Part 10 — Responsive

## 10.1 Breakpoints

Two, both content-driven rather than device-driven.

### `max-width: 1180px` — the grid stops fitting
```
.grid4 → 2 columns
.grid3 → 2 columns
.grid6 → 3 columns
.split → 1 column
```

### `max-width: 900px` — the sidebar stops fitting
```
#body      → block (nav leaves the flow)
#nav       → fixed drawer, translateX(-100%), 236px, revealed by body.navopen
#burger    → appears
#navsc     → scrim at inset 52px 0 0
#main      → padding 16px 14px 40px
all grids  → 1 column
.phead h1  → 19px
.stat .v   → 20px
#sheet     → 100vw
.tbl       → horizontally scrollable, thead/tbody min-width 460px
.hm .hmrow → min-width 400px
.calgrid   → 104px + 30 columns, min-width 1000px  (still scrolls — correctly)
.wkc span  → hidden
.spf       → hidden (sport filter drops off the top bar)
```

**The calendar deliberately does not reflow.** A court grid with fewer columns is not a court grid. It scrolls horizontally with sticky court names, which is the correct behaviour for a spreadsheet-like surface.

## 10.2 Print

```css
@media print {
  #top, #nav, #ssc, #sheet, #dsc, #drawer, #toast, .phead .rt, .leg { display:none!important }
  body, #main { overflow:visible; height:auto }
  #app { display:block }
  .calgrid { min-width:0 }
  .card, .card-n, #cal { break-inside:avoid }
}
```

Print is a real feature — the day sheet is printed at the front desk. All chrome, all actions and the legend are removed; the calendar's min-width is released so it fits the page.

---

# Part 11 — Writing in the interface

The copy is part of the design system and is governed by rules.

## 11.1 Vocabulary decisions

| Use | Not | Because |
|---|---|---|
| **Off sale** | soft-held / hard-held | The hold *rule* is internal; the club needs to know the hour left the pool |
| **Booked** | confirmed | Booked means the money is the club's; confirmed is a lifecycle state |
| **For sale** | available | An hour is for sale; a *person* is actionable |
| **Actionable** | available (of people) | Everyone on the demand map wants that hour; what differs is whether we may act |
| **Unearned** | lost revenue | It is not lost until the hour has passed |
| **Empty court-hours** | underutilised inventory | Club language, not analyst language |
| **Players still looking for a game** | unsatisfied demand entities | — |

## 11.2 Sentence patterns

**Every number gets a sentence.** `.stat .d` is not optional. A tile that cannot justify itself in one line is a vanity metric and should be removed.

**Automation is reported in the form:** *Rakieta did X because Y, producing Z.*
> *"Invited 3 players to Thu 13 21:00 — first wave · Kamil, Szymon, Filip · 25,25 zł a seat, nobody charged."*

**Empty states state value:** what will appear here, and when.

**Notes carry the reasoning**, always in second person about the club's own position: *"Unless another seat sells, the court goes back on sale 13 h from now."*

## 11.3 Numbers

- Polish formatting throughout: `2 474,25 zł` — space as thousands separator, comma as decimal.
- Money in prose is written in full; money in tiles drops the `zł` where the label carries it.
- Durations: `1 h`, `45 min`, `3 d` — space before the unit, always abbreviated.
- Percentages: no space, `65%`.
- Times: 24-hour, zero-padded, `09:00`.

---

# Part 12 — Audit: where the implemented system is inconsistent

Recorded honestly. Each has a recommended resolution.

## 12.1 Hard-coded colours outside `:root`

| Hex | Uses | Should be |
|---|---|---|
| `#071C24` | 2 | new token `--night-deep` (top bar, drawer) |
| `#12495B` | 2 | `var(--night2)` — an exact duplicate |
| `#8BC5A8` | 2 | new token `--mint-pale` (timeline band 1) |
| `#2C7A5A` | 2 | new token `--mint-deep` (booked chip) |
| `#F3CFC5` | 1 | new token `--coral-line` (hot stat border) |
| `#8a6100` | 1 | `var(--amber)` — near-duplicate, also lowercase |

**Six colour values bypass the token system.** `#12495B` is the worst: it is `--night2` written out by hand, so a change to the token would silently miss two places.

## 12.2 Two tokens declared and never used

`--g-free` and `--pad` are referenced zero times. `--g-free` is superseded by literal `#fff`; `--pad` is aliased by the sport-colour lookup which resolves through a different path.

## 12.3 The type set is not a scale

21 distinct sizes between 7px and 46px. Recommended consolidation to **11 steps**, which covers every current use with at most a 0.5px shift:

```
 8    micro overlays (grid glyphs, timeline stops)
 9.5  eyebrows, tags, table headers, field labels
10.5  descriptions, legends, captions
11    secondary text (.tiny)
12.5  body, nav, card titles, buttons
13    empty-state titles
15    sheet title
19    kpi value
22    page title
27    stat value
38    hero number
```

This removes 7, 8.5, 9, 10, 11.5, 12, 14, 16, 20, 46 — each of which is within 0.5–1px of a retained step.

## 12.4 Spacing is dense but unsystematic

Nearly every integer 1–16 appears. Recommended scale, retaining the three canonical values:

```
2  4  6  8  11  14  16  24  34  48
```

`11` (card gap) and `14` (card padding) stay because they are load-bearing and appear 19 and 14 times respectively. `5, 7, 9, 10, 12, 13` map to the nearest step.

## 12.5 Contrast failures

Six pairs fall below AA for normal text and are used at 9.5–11px:

| Pair | Ratio | Fix |
|---|---|---|
| `--muted` on `--paper` | 3.73 | darken `--muted` to `#5C6D73` → **4.83** |
| `--muted` on `--line2` | 3.57 | same fix → **4.62** |
| `mint` on `mint-soft` | 3.54 | add `--mint-ink` `#0A7355` → **5.08** |
| `amber` on `amber-soft` | 4.18 | darken `--amber` to `#8A5E09` → **5.04** |
| white on `--coral` | 3.89 | acceptable for ≥14px bold only; audit small coral buttons |
| white on `--mint` | 4.07 | same |

Darkening `--muted` alone fixes the two highest-volume failures and lifts a third (`--muted` on `--surface`, 4.17 → 5.40). It is the most-referenced token in the system at 54 uses, so this is a one-line change with the widest possible reach. All four replacement values above were verified against WCAG 2.1 by computation, not estimated.

## 12.6 The chip active state is declared twice

`.chip.on` is set to `--ink` in the base sheet and `--night` in a later block. The later wins. Harmless, but a reader of the base sheet will believe the wrong thing — an instance of the layering hazard that governs the whole file.

## 12.7 No focus-visible styles

Only `.inp:focus` is styled. Buttons, chips, nav items and calendar cells have no visible keyboard focus state, relying on the browser default which is largely invisible against these backgrounds. **This is the most serious accessibility gap in the system.**

Recommended: a single global rule using the existing accent —
```css
:focus-visible { outline:2px solid var(--coral); outline-offset:2px; border-radius:inherit }
```

---

# Part 13 — Extension guide

## 13.1 Adding a component

1. **Is it one of the existing five containers?** card · stat · note · row list · action row. If yes, use it. The system's coherence comes from re-use, not from new parts.
2. **Colour:** pick the *meaning*, then the token. Never pick a hex.
3. **Radius:** height ÷ 3.5, snapped to the radius scale.
4. **Type:** from the eleven-step scale; secondary text is always `.tiny`.
5. **Spacing:** 11 between things, 14 inside things.
6. **State:** if it has one, it needs a `.tag` with a word in it.

## 13.2 Adding a colour

Only if it carries a meaning none of the five semantic accents carries. It needs:
- a base, a `-soft` at roughly 92% lightness, and an `-ink` if text sits on the soft
- a contrast check against paper, surface and its own soft
- an entry in the numbered palette in Part 2

## 13.3 Injecting CSS from a layer

The v7 layers inject styles at runtime:

```js
const css = `...`;
const t = document.createElement('style');
t.textContent = css;
document.head.appendChild(t);
```

**Rules for injected CSS:**
- prefix every class with the layer's namespace (`ip` for Intent Pool, `wl` for waitlist)
- reference tokens, never hexes
- never redefine a base class — extend it with a modifier
- keep it adjacent to the component that uses it, not in a shared block

## 13.4 The layering hazard

The stylesheet, like the script, is built in layers, and **later declarations win**. Before changing a base rule, search for later overrides of the same selector. `.chip.on` (§12.6) is the existing instance of this trap.

---

# Appendix A — Complete token reference

```css
:root{
  /* surfaces */
  --paper:#F4F2ED;  --paper2:#EDEAE3;  --surface:#FFFFFF;
  /* ink */
  --ink:#101B20;    --night:#0A3441;   --night2:#12495B;  --muted:#6E7F85;
  /* structure */
  --line:#E5E1D8;   --line2:#F0EDE6;
  /* semantic */
  --coral:#E8482B;  --coral-soft:#FDEBE6;  --coral-ink:#B8351C;
  --mint:#0C8F6B;   --mint-soft:#E2F3EC;
  --amber:#9A6A0B;  --amber-soft:#FBF0DA;
  --red:#B4392C;    --red-soft:#FBEAE7;
  --info:#12495B;   --info-soft:#EAF1F4;  --info-line:#C7DBE3;
  /* highlight */
  --volt:#D9F24B;
  /* sport */
  --pad:#E8482B;    --ten:#0C8F6B;  --squ:#12495B;  --bad:#9A6A0B;
  /* calendar */
  --g-free:#FFFFFF;       --g-free-line:#E9E5DC;
  --g-block:repeating-linear-gradient(45deg,#EDEAE3,#EDEAE3 4px,#E3DFD6 4px,#E3DFD6 8px);
  --g-priv:#0A3441;       --g-hard:#0C8F6B;   --g-soft:#9A6A0B;   --g-past:#F7F5F1;
  /* metrics */
  --row:44px;
}
```

# Appendix B — Quick reference card

```
COLOUR      coral = live · mint = settled · amber = provisional · red = failed
            volt on dark only
SURFACE     paper background · white cards · --line borders THINGS
                                             --line2 separates ROWS
TYPE        Archivo everywhere · IBM Plex Mono for anything compared vertically
            base 12.5 · secondary 11 · eyebrow 9.5 uppercase .15em
            small text gets MORE tracking, large text gets LESS
SPACE       11 between · 14 inside · 13 radius on cards
CONTROL     btn 32 · btn.sm 27 · chip 27 · tag 19 · toggle 38×21
GRID        cell 44px · blocks inset 2px · soft holds are DASHED
MOTION      .12s controls · .24s sheet · nothing else moves
STATE       every state has a word, not just a colour
COPY        every number has a sentence
```
