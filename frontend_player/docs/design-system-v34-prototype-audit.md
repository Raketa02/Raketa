> **Archived measurement — not the rules.**
> This is the verbatim audit of the v34 HTML prototype
> (`rakieta-player-app-prototype-v34.html`, cross-checked against
> `rakieta-player-deck-v34.html`), preserved because the reason a value was chosen is
> itself information. It is **descriptive**: it records the prototype including its
> inconsistencies (Part 20) and its accessibility gaps (Part 21).
>
> It also describes a **web page**. Parts of it — the phone frame, the stage, the
> scenario rail, the time bar, the 900px breakpoint — are prototype harness and do not
> ship in the native app.
>
> **The system to build against is [`design-system.md`](design-system.md).** Where the
> two differ, that file wins — every difference is listed in its Part 14.

---

# Rakieta — Design System, Theming and Visual Specification

_Derived from `rakieta-player-app-prototype-v34.html`, cross-checked against
`rakieta-player-deck-v34.html`. Every token, class and measurement in this document is read
from the implementation. Where the prototype and the deck differ, the prototype wins and the
difference is noted._

---

# Part I — Foundations

## 1. Design principles

These are not aspirations. Each one is visible in the CSS and can be checked against it.

### 1.1 Paper, not glass

The app background is `#F4F2ED` — a warm off-white — not pure white. Cards are `#FFFFFF` on
top of it. The contrast between surface and background is what creates depth, so the app needs
almost no shadow: exactly three box-shadows exist in the entire stylesheet, and two of them are
for elements that genuinely float (the sheet and the popover).

This is a deliberate rejection of the "floating card on grey" pattern. Warm paper reads as a
physical object; a card on it reads as a piece of paper on a desk.

### 1.2 One accent, used sparingly

`--coral: #E8482B` is the only attention colour. It appears on: the active tab, the primary
button, the level mark on the band bar, the active rail item, the FAB, the timeline fill, and
`.tag.hot`. Nothing else. When everything is accented, nothing is.

### 1.3 Semantic colour is never decorative

`--mint`, `--amber`, `--red` and `--info` each mean one thing and are never used to make
something look nice:

| Token     | Means                                  |
| --------- | -------------------------------------- |
| `--mint`  | Settled, safe, covered, confirmed      |
| `--amber` | Watch this — reversible, not yet wrong |
| `--red`   | Ended badly                            |
| `--info`  | Explanation, not status                |

`--info` is `#12495B`, the deep teal already in the palette, rather than a new blue. The palette
does not grow to accommodate a new meaning; a meaning is assigned to a colour already present.

### 1.4 Numbers are monospaced, always

Money, levels, times, percentages and counts all use `IBM Plex Mono` with
`font-variant-numeric: tabular-nums`. A column of prices lines up. A level that changes from
2,71 to 2,80 does not reflow the row it sits in.

### 1.5 Nothing animates that does not have to

One entrance animation (`rise`, 300ms), one sheet animation (`up`, 260ms), one popover
animation (`ipop`, 130ms), one fade. Hover transitions are 120ms. `prefers-reduced-motion`
disables all of it in a single rule.

### 1.6 The frame is not the app

Above 900px the app renders inside a 392×788 phone frame on a dark stage, with a scenario rail
and a time bar. Below 900px **the frame is dropped entirely** — the app becomes the app rather
than a picture of a phone, the rail becomes a drawer, and the time bar docks to the bottom.

---

## 2. Colour tokens

All defined on `:root`. Twenty-six tokens, no more.

### 2.1 Surfaces and structure

| Token       | Value     | Role                                                                           |
| ----------- | --------- | ------------------------------------------------------------------------------ |
| `--paper`   | `#F4F2ED` | App background. Warm off-white                                                 |
| `--paper2`  | `#EDEAE3` | Recessed surface — the situation block in a question, the popover close button |
| `--surface` | `#FFFFFF` | Declared, but cards use literal `#fff`                                         |
| `--ink`     | `#101B20` | Body text, selected chip, `.tsq.on`                                            |
| `--night`   | `#0A3441` | Dark cards, avatars, fit badge, meter fill, toast                              |
| `--night2`  | `#12495B` | Secondary dark, panel body text in the deck                                    |
| `--muted`   | `#6E7F85` | Secondary text, `.tiny`, eyebrows, disabled                                    |
| `--line`    | `#E5E1D8` | Card borders, chip borders, dividers                                           |
| `--line2`   | `#F0EDE6` | Hairlines inside cards, tag backgrounds, inactive tracks                       |

`--surface` is defined and never used — a small inconsistency; cards are written as `#fff`.

### 2.2 Accent and semantics

Each semantic colour ships as a **triplet**: the colour, a soft background, and where needed an
ink variant for text on that background.

| Token          | Value     | Used for                                                                |
| -------------- | --------- | ----------------------------------------------------------------------- |
| `--coral`      | `#E8482B` | The single accent                                                       |
| `--coral-soft` | `#FDEBE6` | Backgrounds behind coral messaging                                      |
| `--coral-ink`  | `#B8351C` | Text on `--coral-soft` (`.tag.hot`)                                     |
| `--mint`       | `#0C8F6B` | Good, settled, covered                                                  |
| `--mint-soft`  | `#E2F3EC` | Free time slots, ok tags                                                |
| `--amber`      | `#9A6A0B` | Caution, reversible                                                     |
| `--amber-soft` | `#FBF0DA` | Caution backgrounds                                                     |
| `--red`        | `#B4392C` | Failure                                                                 |
| `--red-soft`   | `#FBEAE7` | Failure backgrounds                                                     |
| `--volt`       | `#D9F24B` | Rail group headers, confidence ring, active info mark. **Only on dark** |
| `--info`       | `#12495B` | Explanatory notes                                                       |
| `--info-soft`  | `#EAF1F4` | Explanatory backgrounds                                                 |
| `--info-line`  | `#C7DBE3` | Explanatory borders                                                     |

`--volt` is the one colour that only ever appears on a dark surface. It is illegible on paper
and is never used there.

### 2.3 Sport identity

| Sport     | Token   | Value     | Shares with           |
| --------- | ------- | --------- | --------------------- |
| Padel     | `--pad` | `#E8482B` | `--coral`             |
| Tennis    | `--ten` | `#0C8F6B` | `--mint`              |
| Squash    | `--squ` | `#12495B` | `--info` / `--night2` |
| Badminton | `--bad` | `#9A6A0B` | `--amber`             |

Sport colours **reuse the semantic palette rather than extending it**. This is a deliberate
constraint: four more hues would have made every screen with a sport dot on it noisier, and the
sport dot is always accompanied by the sport name in text, so the colour carries recognition
rather than meaning.

The consequence to be aware of: a padel dot and a "hot" tag are the same hue. They are never
adjacent in a way that could confuse, but a fifth sport would force a real decision.

### 2.4 Band colours (the level bar)

Not CSS variables — a JS constant, because the bar needs both a tint and a deep value per band.

| Band        | Range     | Tint      | Deep      |
| ----------- | --------- | --------- | --------- |
| New         | 1,0–1,55  | `#9AA8AD` | `#7E8C92` |
| Developing  | 1,55–2,65 | `#7FB3CC` | `#4E8FAE` |
| Established | 2,65–3,85 | `#6FC5A8` | `#3FA184` |
| Advanced    | 3,85–5,0  | `#F0A08A` | `#D9714F` |

These are drawing boundaries and are **contiguous**; the model's documented band edges have gaps
(1,0–1,5 / 1,6–2,6 / 2,7–3,8 / 3,9–5,0). The rating carries `bandLo`/`bandHi` so the card prints
the model's values, never the drawing values.

### 2.5 Fixed colours outside the token set

| Value                             | Where                                                          |
| --------------------------------- | -------------------------------------------------------------- |
| `#08222B`                         | `html, body` — the stage behind everything                     |
| `#071C24`                         | Scenario rail and mobile top bar                               |
| `#0B2B36`                         | Mobile time bar                                                |
| `#24505E`                         | Phone frame border                                             |
| `#BFE0D2`                         | Free-slot border (a mint-soft companion, not tokenised)        |
| `#C7D3D1`                         | _(removed in v34 — the band bar's grey span became `#5C6B70`)_ |
| `#5C6B70`                         | The likely-range bracket on light backgrounds                  |
| `#CFE7DD` / `#F3CFC5` / `#EFDCB8` | Note border companions for mint / coral / amber                |

---

## 3. Typography

### 3.1 Families

```css
@import url('…Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600…');
```

**Archivo** for everything, **IBM Plex Mono** for numbers. Two families, seven weights between
them.

```css
body {
  font-family: 'Archivo', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}
.mono {
  font-family: 'IBM Plex Mono', ui-monospace, monospace;
  font-variant-numeric: tabular-nums;
}
.num {
  font-weight: 700;
  letter-spacing: -0.035em;
  font-variant-numeric: tabular-nums;
}
```

`.num` is the **display number** treatment — it does not change the family, only the weight and
tracking. It is almost always combined with `.mono`: `class="mono num"`.

### 3.2 The scale

There is no modular ratio. Sizes are chosen per role and there are only nine of them.

| Class      | Size   | Weight  | Tracking | Line | Role                                             |
| ---------- | ------ | ------- | -------- | ---- | ------------------------------------------------ |
| `.h1`      | 19px   | 700     | −.03em   | —    | Screen title in `.pbar`                          |
| `.h2`      | 15px   | 700     | −.025em  | —    | Card and section title                           |
| —          | 13px   | 600–700 | —        | —    | Card title inline (`<b style="font-size:13px">`) |
| —          | 12.5px | 600–700 | —        | —    | The most common inline title size                |
| `.rl`      | 11.5px | 400/600 | —        | —    | Row label and value                              |
| `.tiny`    | 11px   | 400     | —        | 1.45 | Secondary text everywhere                        |
| `.eyebrow` | 9.5px  | 700     | .15em    | —    | Uppercase section label                          |
| `.flab`    | 10.5px | 700     | .09em    | —    | **Form label** — uppercase, `--night`, not muted |
| `.tag`     | 9.5px  | 700     | —        | —    | Pill text                                        |

Display sizes are inline rather than classed:

| Size                 | Where                                             |
| -------------------- | ------------------------------------------------- |
| 40px                 | The estimated level on the onboarding result card |
| 26px                 | Level on comparison cards                         |
| 22px / 20px / 19px   | Numbers in panels and summaries                   |
| 17px / 14px / 13.5px | `.num` in rows and prices                         |

### 3.3 Why `.flab` exists separately from `.eyebrow`

They look almost identical and mean different things:

```css
.eyebrow {
  font-size: 9.5px;
  letter-spacing: 0.15em;
  color: var(--muted);
}
.flab {
  font-size: 10.5px;
  letter-spacing: 0.09em;
  color: var(--night);
  margin-bottom: 7px;
}
```

`.eyebrow` labels a region you are reading. `.flab` labels a control you are about to operate.
The comment in the source is explicit: _"a form label has to be findable at a glance, which the
muted eyebrow was not."_ It is a full point larger, tighter-tracked, and near-black.

### 3.4 Negative tracking on headings

Every heading carries negative letter-spacing (−.02 to −.035em), tightening as the size grows.
Archivo at 19px with default tracking reads loose; at −.03em it reads set. Body text is never
tracked.

---

## 4. Space, radius and elevation

### 4.1 Spacing

There is no 4- or 8-point grid. The values in use are **5, 6, 7, 9, 10, 11, 12, 13, 14, 15**,
chosen per component. The two that appear most:

- **9px** — the gap between stacked cards (`.card{margin-bottom:9px}`) and the standard
  `.hair` top margin.
- **15px** — the horizontal page gutter (`#scroll{padding:0 15px 14px}`).

Content width inside the phone is therefore **392 − 30 = 362px**, and every horizontal
measurement in the app derives from it.

### 4.2 Radius

| Radius        | Applied to                      |
| ------------- | ------------------------------- |
| 34px          | The phone frame                 |
| 22px 22px 0 0 | Bottom sheet                    |
| 15px          | `.card-n` (dark cards)          |
| 13px          | `.card`, `.ipop`                |
| 12px          | Toast                           |
| 10px          | `.btn`, `.note`, `.dsq`, `.seg` |
| 9px           | `.hr`, `.hsq`, `.avat`, `.ibtn` |
| 8px           | `.tsq`, `.balbar`, rail items   |
| 7px           | `.fit`                          |
| 6px           | `.tag`, sport dots              |
| 999px         | `.chip` — the only true pill    |

The pattern: **the bigger the surface, the rounder**. A dark card is 15px where a light one is
13px, because the darker fill makes the corner read tighter at the same radius.

### 4.3 Elevation

Three shadows in the entire stylesheet.

```css
#phone {
  box-shadow: 0 40px 90px -40px rgba(0, 0, 0, 0.8);
}
#sheet {
  box-shadow: 0 -20px 40px -22px rgba(10, 32, 40, 0.6);
}
.ipop {
  box-shadow: 0 12px 30px rgba(11, 31, 42, 0.24);
}
.tst {
  box-shadow: 0 12px 28px -12px rgba(0, 0, 0, 0.6);
}
```

Cards never have a shadow. Depth on the paper background comes from the surface change and the
1px `--line` border.

---

# Part II — Components

## 5. Structural primitives

### 5.1 `.card` — the workhorse

```css
.card {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 13px;
  padding: 12px;
  margin-bottom: 9px;
}
.card.tap {
  cursor: pointer;
  transition: 0.12s;
}
.card.tap:hover {
  border-color: var(--coral);
  transform: translateY(-1px);
}
```

The hover state changes the **border** to coral and lifts by 1px. No shadow, no scale.

### 5.2 `.card-n` — the dark card

```css
.card-n {
  background: var(--night);
  color: #fff;
  border-radius: 15px;
  padding: 14px;
  margin-bottom: 9px;
}
.card-n .tiny {
  color: rgba(255, 255, 255, 0.68);
}
.card-n .eyebrow {
  color: rgba(255, 255, 255, 0.52);
}
.card-n .hair {
  border-color: rgba(255, 255, 255, 0.15);
}
```

The dark card **repaints its children** rather than requiring every child to know it is on
dark. This is elegant until something light-on-light sits inside it — which is exactly what
happened with the info popover, and is why three counter-overrides exist:

```css
.card-n .ipop .tiny {
  color: var(--muted);
}
.card-n .ipop .eyebrow {
  color: var(--muted);
}
.card-n .ipop .mono {
  color: var(--ink);
}
```

Used for: the onboarding result, the state card on a match, the level card on the passport.

### 5.3 `.hair` — the internal divider

```css
.hair {
  border-top: 1px solid var(--line2);
  margin-top: 9px;
  padding-top: 8px;
}
```

One rule, used everywhere a card needs a second section. `--line2` rather than `--line` so it
reads as a fold inside one object rather than a boundary between two.

### 5.4 `.note` — the message block

```css
.note {
  padding: 11px 13px;
  border: 1px solid var(--line);
  border-left: 3px solid var(--night);
  border-radius: 10px;
  background: #fff;
  margin-bottom: 9px;
}
.note b {
  display: block;
  font-size: 11.5px;
  margin-bottom: 3px;
}
```

A card with a **3px left bar** carrying the semantic. Four variants:

| Variant  | Left bar  | Background     | Border        |
| -------- | --------- | -------------- | ------------- |
| _(base)_ | `--night` | `#fff`         | `--line`      |
| `.mint`  | `--mint`  | `--mint-soft`  | `#CFE7DD`     |
| `.coral` | `--coral` | `--coral-soft` | `#F3CFC5`     |
| `.amber` | `--amber` | `--amber-soft` | `#EFDCB8`     |
| `.info`  | `--info`  | `--info-soft`  | `--info-line` |

`.note.info` is the only one with a glyph — a CSS-generated serif _i_ in a filled circle:

```css
.note.info b::before {
  content: 'i';
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--info);
  color: #fff;
  font-family: Georgia, serif;
  font-style: italic;
}
```

A serif italic _i_ inside a sans-serif app, because the information mark is a **symbol**, not
text, and the serif form is the one people recognise.

### 5.5 `.rl` — the row

```css
.rl {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 6px 0;
  font-size: 11.5px;
}
.rl + .rl {
  border-top: 1px solid var(--line2);
}
```

Label left, value right, hairline between consecutive rows via the adjacent-sibling selector —
so the first row has no rule above it and the last none below, automatically. Used for every
key-value list in the app: price breakdowns, passport stats, wallet lines.

---

## 6. Controls

### 6.1 `.btn`

```css
.btn {
  height: 34px;
  padding: 0 14px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
}
.btn:hover {
  filter: brightness(1.06);
}
.btn.p {
  background: var(--coral);
  color: #fff;
} /* primary */
.btn.n {
  background: var(--night);
  color: #fff;
} /* dark    */
.btn.s {
  background: #fff;
  border: 1px solid var(--line);
} /* secondary */
.btn.w {
  background: rgba(255, 255, 255, 0.17);
  color: #fff;
} /* on dark   */
.btn.full {
  width: 100%;
}
.btn:disabled {
  opacity: 0.4;
}
```

Hover is `filter: brightness()` rather than a second colour token — one rule covers all four
variants.

Heights in practice: 32px (tertiary in a card), 34px (default), 40px (screen action), 42px
(the primary action on a result screen).

### 6.2 `.chip` — the filter pill

```css
.chip {
  height: 27px;
  padding: 0 11px;
  border-radius: 999px;
  border: 1px solid var(--line);
  font-size: 10.5px;
  background: #fff;
  font-weight: 600;
}
.chip.on {
  background: var(--ink);
  color: #fff;
  border-color: var(--ink);
}
.chip.sm {
  height: 25px;
  padding: 0 8px;
  font-size: 10px;
}
```

The **only** true pill in the app. Selected state is ink-filled, not coral — coral is reserved
for actions, and a selected filter is a state.

### 6.3 `.seg` — the segmented control

```css
.seg {
  display: flex;
  background: var(--line2);
  border-radius: 10px;
  padding: 3px;
  gap: 3px;
}
.seg span {
  flex: 1;
  text-align: center;
  padding: 7px 4px;
  font-size: 10.5px;
  font-weight: 700;
  color: var(--muted);
  border-radius: 8px;
}
.seg span.on {
  background: #fff;
  color: var(--ink);
}
```

Inset track, raised selection — the inverse of the chip. Used for Games/Courts and for
time-of-day.

### 6.4 `.tag` — the status pill

```css
.tag { padding:3px 7px; border-radius:6px; font-size:9.5px; font-weight:700;
       background:var(--line2); color:var(--muted) }
.tag.ok{…mint} .tag.hot{…coral-ink} .tag.warn{…amber} .tag.bad{…red} .tag.w{…on dark}
.tag i { width:6px; height:6px; border-radius:3px }
```

Optional 6px square dot for a sport colour or a state tone. `overflow:hidden;
text-overflow:ellipsis` so a long state tag truncates rather than breaking a row.

### 6.5 Slot squares

Three siblings for the three kinds of time selector:

```css
.dsq { border-radius:10px; padding:6px 9px; text-align:center; border:1px solid }  /* day */
.tsq { border-radius:8px;  height:32px; …mono 11.5px 700 }                          /* time */
.hsq { border-radius:9px;  padding:7px 10px; …mono 11.5px 700 }                     /* hour */
.hr  { border-radius:9px;  padding:5px 10px; text-align:center; border:1px solid }  /* range */
```

`.tsq` and `.hr` share a four-state vocabulary:

| State             | Background    | Border      | Text      |
| ----------------- | ------------- | ----------- | --------- |
| `.free`           | `--mint-soft` | `#BFE0D2`   | `--ink`   |
| `.off` / `.taken` | `--line2`     | transparent | `--muted` |
| `.on` / `.sel`    | `--ink`       | `--ink`     | `#fff`    |
| `.end`            | `#fff`        | `--ink`     | `--ink`   |

`.end` is the hollow square marking where a booking finishes — the same border as selected, the
opposite fill.

---

## 7. Data display

### 7.1 `.fit` — the Match Fit badge

```css
.fit {
  height: 23px;
  padding: 0 9px;
  border-radius: 7px;
  background: var(--night);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
}
.fit.hi {
  background: var(--coral);
}
```

Dark by default, **coral at 90 or above**. The threshold is in the JS
(`f.score>=90?'hi':''`), so a very good match is the only thing on a Find card that competes
with the accent.

### 7.2 `.balbar` — the balance split

```css
.balbar {
  display: flex;
  height: 24px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--line2);
}
.balbar i {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9.5px;
  font-weight: 700;
  color: #fff;
  font-style: italic;
}
```

Two flex children whose widths are the predicted shares. Percentages sit **inside** the bar,
white, italic.

### 7.3 `.meter` and `.bar`

```css
.meter { height:5px; border-radius:3px; background:var(--line2) }   .meter i { background:var(--night) }
.bar   { height:4px; border-radius:2px; background:var(--line2) }   .bar i   { …caller sets fill }
```

`.meter` fills dark and is used for progress within a card. `.bar` leaves the fill to the
caller and is used for the onboarding progress strip, where it is coral.

### 7.4 `.avat` — the seat avatar

```css
.avat {
  width: 27px;
  height: 27px;
  border-radius: 9px;
  background: var(--night);
  color: #fff;
  font-size: 9.5px;
  font-weight: 700;
  transition: transform 0.12s;
}
.avat.d {
  background: none;
  border: 1.5px dashed var(--line);
  color: var(--muted);
} /* empty seat */
.avat.me {
  background: var(--coral);
}
.hold:active .avat {
  transform: scale(0.93);
}
.holding .avat {
  box-shadow: 0 0 0 3px var(--coral-soft);
}
```

A **dashed** border for an empty seat is the only dashed element in the app, and it means one
thing: a place that could be filled. `.holding` is the press-and-hold state for peeking at a
player.

### 7.5 The level bar

Not a CSS component — built in JS by `bandBar(l, dark, opts)` — but it is a design object and
its geometry is fixed:

```
row 1 (y=0,  h=6px)   four band segments, radius 3, the current band at full
                      opacity and the others at .38 (light) / .42 (dark),
                      1px separators in the surface colour
mark  (y=−3, h=12px)  3px coral bar, 2px surface-coloured ring
row 2 (y=13, h=8px)   the likely-range bracket: 2px centre line with 2px end caps
row 3 (y=24)          four band names, the current one at 800 weight and full colour
legend (optional)     a coral tick and a bracket glyph, with labels
```

The **separation of the two rows is the whole design**. An earlier version drew the range on
top of the bands and it hid exactly what the bands were there to show.

Scale is always the full 1,00–5,00 so the same value always lands in the same place.

### 7.6 `.ipop` — the anchored popover

```css
.ipop {
  position: absolute;
  top: 25px;
  width: 250px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 13px;
  padding: 11px 12px 12px;
  box-shadow: 0 12px 30px rgba(11, 31, 42, 0.24);
}
.ipop-arrow {
  top: -6px;
  width: 11px;
  height: 11px;
  background: #fff;
  border-left: 1px solid var(--line);
  border-top: 1px solid var(--line);
  transform: rotate(45deg);
  border-radius: 2px 0 0 0;
}
```

The arrow is a rotated square carrying **two** of the four borders, so it reads as a continuation
of the outline rather than a floating diamond. Position is set in JS after render
(`placeInfoPopover`), which measures the mark and clamps the box inside the scroll column —
necessary because the column clips horizontally and a mark two-thirds across would lose the
right edge.

### 7.7 `.mrail` — the horizontal card rail

```css
.mrail {
  margin: 0 0 9px;
}
.mrail > * {
  width: 268px;
}
.mrail .card {
  margin-bottom: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.mrail .card > .hair:last-child {
  margin-top: auto;
}
```

Applied together with `.sqrow`. **268px against 362px of content** leaves the next card peeking
by ~88px, which is the entire affordance. `margin-top:auto` on the last hairline pushes the
footer to the bottom so footers align across cards of differing height.

---

## 8. Scrolling patterns

```css
.sqrow {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding: 1px 0 3px;
  scrollbar-width: none;
}
.sqrow > * {
  flex: 0 0 auto;
}
.hstrip {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  margin: 0 -15px 10px;
  padding: 1px 15px 5px;
}
.hstrip > * {
  scroll-snap-align: center;
  scroll-snap-stop: always;
  flex: 0 0 100%;
}
```

Two horizontal patterns with different jobs:

- **`.sqrow`** — free scroll, content-sized children. Day squares, chips, the match rail.
- **`.hstrip`** — snapping carousel, full-width children, **negative margins that bleed to the
  screen edge**. Used where one item at a time is the point.

`render()` preserves `scrollLeft` on every `.sqrow` across a re-render. Without it, a rail would
snap to the start on every tap, because the screen re-renders on every interaction.

`.dots` is the pager for `.hstrip`: 5px dots, the active one widened to 14px and coloured coral.

---

## 9. Overlays

### 9.1 Bottom sheet

```css
#sheetwrap { position:absolute; inset:0; z-index:20 }
#scrim { background:rgba(10,52,65,.45); animation:fade .2s }
#sheet { bottom:0; max-height:88%; border-radius:22px 22px 0 0;
         animation:up .26s cubic-bezier(.2,.8,.2,1) }
.grab  { width:36px; height:4px; background:var(--line); border-radius:2px; margin:0 auto 10px }
#xsheet{ 28px circle, --line2 background, top-right }
```

The scrim is the **night** colour at 45%, not black — the dim matches the palette.

### 9.2 Toast

```css
#toast {
  position: absolute;
  left: 15px;
  right: 15px;
  bottom: 78px;
  z-index: 40;
  pointer-events: none;
}
.tst {
  background: var(--night);
  color: #fff;
  border-radius: 12px;
  padding: 11px 14px;
  font-size: 12px;
  font-weight: 600;
}
.tst.ok {
  background: var(--mint);
}
.tst.bad {
  background: var(--red);
}
```

Bottom 78px clears the tab bar. `pointer-events:none` on the container so a toast never blocks
a tap.

### 9.3 Z-index scale

| z   | Element                            |
| --- | ---------------------------------- |
| 20  | Sheet wrapper                      |
| 30  | Mobile top bar                     |
| 40  | Toast, mobile time bar             |
| 50  | Rail scrim (mobile)                |
| 60  | Rail drawer (mobile), info popover |

---

# Part III — Screens and features

## 10. The app shell

### 10.1 Desktop (≥900px)

```
┌──────────────┬──────────────────────────────────────┐
│              │  #stagehead   scenario name + desc   │
│  #rail 290px │  ┌────────────────────────────────┐  │
│  #071C24     │  │  #phone 392×788, radius 34     │  │
│              │  │  ┌──────────────────────────┐  │  │
│  #railhead   │  │  │ #statusbar 28px          │  │  │
│  #railbody   │  │  │ #view                    │  │  │
│   .rgrp      │  │  │   .pbar                  │  │  │
│    h5 volt   │  │  │   #scroll  flex:1        │  │  │
│    .ritem    │  │  │   #cta     (conditional) │  │  │
│              │  │  │   #tabbar  5 columns     │  │  │
│              │  │  └──────────────────────────┘  │  │
│              │  └────────────────────────────────┘  │
│              │  #timebar  max-width 980             │
└──────────────┴──────────────────────────────────────┘
```

The rail is a 290px column at `#071C24` — darker than `--night`, so the stage reads as
background and the rail as chrome. Group headers are `--volt` uppercase at 9.5px/.16em. Items
carry a 20px monospace glyph square and an optional `<em>` description line.

### 10.2 Phone (<900px)

The phone frame is removed. `#mtop` appears — a 46px bar with a hamburger, the scenario name and
the brand. The rail becomes a fixed drawer at `min(320px, 86vw)` with a 260ms slide and a scrim.
`#timebar` docks to the bottom at `#0B2B36`. The phone height becomes
`calc(100dvh - 46px - 56px)`.

### 10.3 The tab bar

```css
#tabbar {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  padding: 7px 0 12px;
}
.tab i {
  width: 16px;
  height: 16px;
  border-radius: 5px;
  background: currentColor;
  opacity: 0.85;
}
.tab.fab i {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  background: var(--coral);
  margin-bottom: -4px;
}
```

Five columns. Icons are `currentColor` squares — the prototype does not ship an icon set, and
this is the honest placeholder: shape and position are specified, glyph is not. The centre tab
is a FAB, 28px and coral, lifted 4px above the row.

---

## 11. Cross-screen patterns

Before the per-screen sections, these appear in three or more places and are specified once.

### 11.1 The screen header

```js
head(title, sub, back, right)  →  .pbar  [.back] [.t > .eyebrow + .h1] [right]
```

Eyebrow above, `.h1` below, optional back chevron at 20px `--muted`, optional right slot for a
segmented control.

### 11.2 The sport bar

A `.sqrow` of chips, one per sport plus "All", each with a 6px sport-coloured square. Persistent
across Find, Courts and Create.

### 11.3 The match card

`matchCard(m, opts)` — the canonical representation of a joinable match, used on Home, Find,
the waitlist and the creation overlap rail.

```
┌────────────────────────────────────────────┐
│ Sat · 18:30  [Promotion]          ╭─────╮  │
│ Zabłocie Sport · 14 min           │glyph│  │
│ [●Padel] [Doubles] [Counts] [card]╰─────╯  │
│                                      3/4   │
├────────────────────────────────────────────┤
│ [✦ 93] [●Forming]        38,00 zł · 0 fee  │
├────────────────────────────────────────────┤
│ optional footer line (opts.foot)           │
└────────────────────────────────────────────┘
```

Left column: monospace time, optional badge, club + distance in `.tiny`, then a `.row` of tags.
Right column: the sport glyph with seat occupancy, and `filled/n` in mono. Then a `.hair` with
the fit badge, the state tag, and the price — struck through when a club card applies.

`opts.foot` renders a second `.hair` with `.tiny` content. It exists for the creation flow,
which needs to say the category and the target level — the two things a Find card cannot know
to say.

### 11.4 The state card

`stateCard(m)` — the canonical representation of a match you are **in**. A `.card-n` carrying
the tag, a context line, the group facet, the court facet, and up to four `lines` each with a
tick (1) or a circle (0) marker. Driven entirely by the `ST` table, so the visual is identical
across all 32 contexts and only the content changes.

---

## 12. Onboarding — `V.onboard`

### 12.1 Steps and chrome

`obShell(title, sub, pct, body, back)` — a `.pbar` plus a `.bar` progress strip filled coral.
Steps: welcome → sports → q (adaptive) → result → done → data.

### 12.2 The question screen

```
Match execution                       ← .h1 is the CATEGORY, not the question
Padel · Rating 1 of 1                 ← .eyebrow

Question 3        [discriminating] [3,17 so far]     ← meter row
┌─ card ────────────────────────────────────────┐
│ ── PICTURE THIS ──────────── .paper2 header ── │
│ A deep lob pushes you off the net             │  13.5px/600
│ ─────────────────────────────────────────────  │
│ How often do you play a controlled overhead   │  15px/650/−.01em
│ and recover position, instead of going for a  │
│ winner?                                       │
│ A normal match against players at your level  │  .tiny
└───────────────────────────────────────────────┘
[ Almost never ]      ← five .card.tap
[ Occasionally ]
…
```

The **situation is a shaded header inside the same card** as the question, on `--paper2` with a
1px bottom border. The reading order is fixed and deliberate: category → progress → situation →
question → answers. The question is never the page title, because a title is read last on a
screen the eye scans top-down.

Difficulty appears as a tag: `basic` / `standard` / `discriminating`, the last one `.tag.hot`.

### 12.3 The result screen

```
┌─ .card-n ─────────────────────────────────────┐
│ ESTIMATED LEVEL ⓘ              ╭───────╮      │
│ 3,14                    40px   │  30%  │ ring │
│ likely range 2,30 – 3,98 ⓘ     ╰───────╯      │
│                            CONFIDENCE ⓘ       │
│ ─── level bar, labels, legend ───────────────  │
│ ─── Band | Status | Questions ───────────────  │
└───────────────────────────────────────────────┘
┌─ .card, 3px left border in the band colour ──┐
│ Established                                   │
│ Reliable recreational or club player…         │
│ This is the name for where you are today…     │
└───────────────────────────────────────────────┘
```

Three information marks, three anchored popovers. The band card's left border is the band's own
colour — the only place a band colour appears outside the bar.

---

## 13. Find — `V.find`

Two tabs via `.seg`: Games and Courts.

**Games** — sport bar, day chips, a filter chip with a count badge, then `matchCard` per match
ordered by Match Fit. Empty state is `.empty`: bold line, `.tiny` explanation, and a clear-filters
button. The copy is explicit that an empty list is a true answer.

**Courts** — club cards, each with the club name, distance, a "from" price, and a `.sqrow` of
`.hsq` hour squares. Sorted by soonest / cheapest / nearest.

---

## 14. Match detail — `V.match`

The longest screen in the app. Order:

1. `stateCard(m)` — the dark state card
2. The five numbers (balance, fit, at stake, target, price) — `.card` with `.rl` rows
3. `.balbar` with the predicted split
4. The seat row — `.avat` per seat, dashed for empty, coral for me
5. Court certainty — which court, held or not, and why
6. The deadline strip — three markers on a `.bar`
7. Money — share, card, payable
8. `#cta` — the join or leave action, pinned

---

## 15. Creating — `V.create`

Step 1 is the mode choice (Open Match / Private Court) as two tall `.card.tap`s with a
four-row comparison each.

Step 2 is one scrolling screen: sport → club → category chips → **calendar** → _overlap block_ →
price → five rules → create.

### 15.1 The calendar

`.sqrow` of `.dsq` day squares — weekday, date, count of free starts, and a **coral count badge**
at the top-right when open matches already exist that day. Then three `.eyebrow`-labelled grids
of `.tsq` time squares (Morning / Afternoon / Evening), four columns.

### 15.2 The overlap block

```
[note, tone by severity]
  Sunday morning at Zabłocie Sport is busy        [7 open]
  7 open matches within two hours…

[.sqrow .mrail]  ← horizontal, 268px cards, next peeking
  ┌ matchCard ┐ ┌ matchCard ┐ ┌ matchCard ┐ →
  │  + foot   │ │  + foot   │ │  + foot   │
  └───────────┘ └───────────┘ └───────────┘

[.btn.s.full]  See all 7 in Find
[.note.amber]  no Wall court free, 3 matches wanting…
[.card]        Quieter at the same time → Monday, Tuesday
```

The frame is a **note plus cards**, not a card containing cards. Note tone escalates: `info` →
`coral` (tight) → `amber` (busy) → `coral` (saturated).

---

## 16. Skill Passport — `V.passport`

A `.card-n` with the level, the band bar with labels, and the counted-match count. Then a per-
sport `.rl` list, a per-format block when a sport has two, and the calibration explanation.

## 17. Wallet — `V.wallet`

Three totals (held / committed / settled) then a ledger of `.rl` rows, each with a label, a
reference in `.tiny`, and a signed monospace amount. Held lines carry a `.tag.warn`, pending
refunds a `.tag.ok`.

## 18. Player Score — `V.score`

A large `.num`, a `.meter`, the gate threshold marked, and the record rows.

---

# Part IV — Reference

## 19. Complete class index

| Class                                          | Purpose                   |
| ---------------------------------------------- | ------------------------- |
| `.mono` `.num`                                 | Monospace, display number |
| `.h1` `.h2` `.eyebrow` `.flab` `.tiny` `.sect` | Type roles                |
| `.card` `.card-n` `.card.tap` `.hair`          | Containers                |
| `.note` + `.mint` `.coral` `.amber` `.info`    | Message blocks            |
| `.btn` + `.p` `.n` `.s` `.w` `.full`           | Buttons                   |
| `.chip` + `.on` `.sm`                          | Filter pills              |
| `.seg`                                         | Segmented control         |
| `.tag` + `.ok` `.hot` `.warn` `.bad` `.w`      | Status pills              |
| `.rl`                                          | Key-value row             |
| `.row` `.sqrow` `.hstrip` `.dots` `.mrail`     | Layout and scroll         |
| `.dsq` `.tsq` `.hsq` `.hr` + states            | Slot selectors            |
| `.fit` `.balbar` `.meter` `.bar` `.avat`       | Data display              |
| `.iwrap` `.ibtn` `.ipop` `.ipop-*`             | Information popover       |
| `.empty` `.grab` `.tst` `.hold` `.holding`     | Misc                      |

## 20. Known inconsistencies

Documented rather than hidden.

1. **`--surface` is defined and never used.** Cards hard-code `#fff`.
2. **`--paper2` was used before it was defined** — fixed in v34; it now resolves to `#EDEAE3`.
3. **Sport colours alias semantic colours.** Padel is coral, tennis is mint, squash is info,
   badminton is amber. A fifth sport forces a real decision.
4. **Band drawing boundaries are contiguous; model boundaries are not.** The bar uses
   1,55/2,65/3,85 while the model uses 1,5–1,6 / 2,6–2,7 / 3,8–3,9. The card prints the model's
   values from `bandLo`/`bandHi`.
5. **No spacing scale.** Values are chosen per component from 5–15px.
6. **No icon set.** Tab icons are `currentColor` squares.
7. **Two "open seat" casings** in the line-up helpers: _"the open seat"_ mid-sentence and
   _"Open seat"_ in lists.
8. **The deck maintains a parallel implementation** of `matchCard` (`mCard`), `bandBar`
   (`obBar`) and the popover. They are kept in sync by hand and have drifted before.

## 21. Accessibility

**Present:**

- `:focus-visible { outline:2px solid var(--coral); outline-offset:2px }` globally.
- `prefers-reduced-motion` disables every animation and transition in one rule.
- `aria-label` on the info marks, the popover close and the mobile rail toggle.
- `role="dialog"` on the popover.
- Tabular numerals everywhere numbers are compared.

**Missing, and worth recording:**

- No `aria-live` region for the toast.
- No focus trap in the sheet or the popover.
- `.tiny` at 11px in `--muted` on `--paper` is **3.9:1** — below WCAG AA for body text. It
  passes at large sizes only.
- Tab icons carry no accessible name beyond the visible label.
- Horizontal rails have no keyboard scroll affordance.
