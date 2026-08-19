# The Now Screen — Production Specification

*Everything needed to build the Now screen end to end: purpose, business value, player value, interaction model, every component, every token, every state, every string.*

**Scope changes from the prototype, applied throughout this document:**

1. **The MultiSport card block is removed.** It does not appear in any layout, token list or interaction below.
2. **"Even matches for you" becomes "Best fit for you."** The prototype's label implied the list was ranked on skill parity alone. It is not — it is ranked by Match Fit, which weighs seven factors. The section is renamed and the copy rewritten to say what it actually does.

---
---

# PART 0 — WHAT THIS SCREEN IS

## 0.1 The one-sentence purpose

**Now answers two questions in one scroll: *what have I already committed to*, and *what should I do next*.**

Everything above the fold is the first question. Everything below it is the second. The screen never mixes them, and it never asks the player to choose which mode they are in.

## 0.2 Why the screen exists at all

A booking app's default home screen is a search box. That is the correct design when the product is a search engine and the wrong one here, because a Rakieta player's most common state is **already having something booked that is not yet certain.**

An open match is a live object. Between paying and playing, it can:

- gain and lose players
- gain a court, lose it, and gain it back
- cross a commitment deadline that changes what leaving costs
- lose a player after commitment and enter a search
- be cancelled by the club, by the checkpoint, or by running out of court inventory

**Every one of those is something the player needs to know without asking.** A screen that made them tap into each match to find out would produce exactly the anxiety the product exists to remove.

So Now is a **status surface first and a discovery surface second.** The order is not negotiable, and it is why the state cards sit above the recommendations.

## 0.3 Business value

| Value | Mechanism |
|---|---|
| **Reduces support load to near zero** | Every question a player would email about — *is the court booked? what happens if I leave? why was it cancelled?* — is answered on the card, before they ask |
| **Converts idle sessions into bookings** | A player opening the app to check a match sees three matches they would want. The check-in visit becomes a booking visit |
| **Fills matches that would otherwise die** | Best fit is a supply-side lever: it points demand at the open matches most likely to complete, rather than letting players scatter across matches that will all fail |
| **Makes the waitlist a real product** | *Full, but worth waiting for* converts a dead end into standing demand the Rescue cascade can draw on. A waitlist entry costs nothing and creates a real option |
| **Protects the trust the whole model rests on** | The product's central promise — *nothing about your booking changes* — is only credible if the app says so at the moment the thing it is promising about is under threat |
| **Creates a daily habit without notifications** | A screen that is genuinely different each morning is opened each morning |

## 0.4 Player value

| Value | What it replaces |
|---|---|
| **One glance tells you where you stand** | Opening three chat threads to work out whether Saturday is happening |
| **You are never surprised by money** | Discovering a cancellation charge after the fact |
| **The next good thing is already chosen for you** | Scrolling a list of forty matches and picking badly |
| **A full match is not a dead end** | Closing the app because everything good was taken |
| **Bad news arrives with its explanation attached** | *"Match cancelled"* with no reason and no recourse |

## 0.5 How a player is expected to use it

**The dominant session is eight seconds long.** Open the app, look at the top card, close it. That session must be complete without a tap. Everything the top card shows is therefore chosen to be the thing a player checking in actually wants: the time, the state, the court, the group, and what happens next.

**The second session is a horizontal swipe.** Two or three booked matches, swiped through, each with the same anatomy so the eye knows where to look on the second card without re-reading the first.

**The third session is a scroll to the bottom third.** No booked matches, or all of them are settled, so the player is here to find a game. Three best-fit matches, then one full match worth waiting for.

**The fourth session is the one that matters most and happens least.** Something went wrong — a player left, a court went back, the club cancelled. The player opens the app because they were notified. The card must carry the full explanation, in plain language, with the money position stated, because this is the session that decides whether they trust the product.

---
---

# PART 1 — ANATOMY

## 1.1 The full layout, top to bottom

```
┌─ 392 × 788 phone frame ────────────────────────────┐
│  status bar                              28px      │
├────────────────────────────────────────────────────┤
│  .pbar                                             │  ← header, does not scroll
│    HI, TOMEK                          .h1 19px     │
│    Kraków · Saturday · 14:30          .eyebrow     │
├────────────────────────────────────────────────────┤
│  sport bar  [All][●Padel][●Tennis][●Squash][●Bad]  │  ← chips, horizontal scroll
├────────────────────────────────────────────────────┤
│  ┌─ #scroll ──────────────────────────────────┐    │
│  │                                            │    │
│  │  YOUR MATCHES · 2 · SOONEST FIRST  swipe → │    │  ← .sect + hint
│  │                                            │    │
│  │  ┌─ .card-n ──────────────────────────┐    │    │
│  │  │ [● Court protected]   PADEL · DOUB │    │    │
│  │  │ 18:30                        ╭───╮ │    │    │  ← the state card
│  │  │ Sat · Zabłocie Sport         │▦▦▦│ │    │    │
│  │  │ Mondo · 90 min               ╰───╯ │    │    │
│  │  │                                3/4 │    │    │
│  │  │ ── COURT ──────── │ ── GROUP ───── │    │    │
│  │  │ Protected · Mondo │ 3 of 4 paid    │    │    │
│  │  │ ────────────────────────────────── │    │    │
│  │  │ ✓ You paid 38,00 zł                │    │    │
│  │  │ ✓ Three paid seats, so a court…    │    │    │
│  │  │ ○ The exact court is assigned…     │    │    │
│  │  │ ○ Leaving now returns everything   │    │    │
│  │  │ [ Open match ] [ ✉ ] [ ⌘ ]         │    │    │
│  │  └────────────────────────────────────┘    │    │
│  │            ● ─ ○                           │    │  ← .dots pager
│  │                                            │    │
│  │  BEST FIT FOR YOU                          │    │  ← .sect
│  │  Ranked on seven things, not just level    │    │  ← .tiny
│  │  ┌─ .card ────────────────────────────┐    │    │
│  │  │ Sat · 18:30    [Promotion]   ╭───╮ │    │    │
│  │  │ Zabłocie Sport · 14 min      │▦▦▦│ │    │    │  ← matchCard ×3
│  │  │ [●Padel][Doubles][Counts]    ╰───╯ │    │    │
│  │  │                                3/4 │    │    │
│  │  │ ─────────────────────────────────  │    │    │
│  │  │ [✦93] [●Forming]     38,00 zł·0fee │    │    │
│  │  └────────────────────────────────────┘    │    │
│  │  … ×3                                      │    │
│  │                                            │    │
│  │  FULL, BUT WORTH WAITING FOR               │    │  ← .sect
│  │  These fit you as well as anything above…  │    │  ← .tiny
│  │  ┌─ .card ────────────────────────────┐    │    │
│  │  │ … same matchCard, [●Full] tag      │    │    │
│  │  └────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────┘    │
├────────────────────────────────────────────────────┤
│  [Now] [Find] (＋) [Inbox] [You]        #tabbar    │  ← 5 columns, does not scroll
└────────────────────────────────────────────────────┘
```

## 1.2 The six blocks

| # | Block | Component | Condition |
|---|---|---|---|
| 1 | Header | `.pbar` | always |
| 2 | Sport bar | `.chip.sm` row | always |
| 3 | Your matches | `.hstrip` of `stateCard` + `.dots` | when the player is in ≥1 live match |
| 3b | Empty state | `.card` + `.empty` | when they are in none |
| 4 | Best fit for you | `.sect` + `.tiny` + `matchCard` ×3 | always — with its own empty state |
| 5 | Full, but worth waiting for | `.sect` + `.tiny` + `matchCard` ×1–2 | only when a qualifying full match exists |
| 6 | Tab bar | `#tabbar` | always |

**There is no block 7.** No promo tiles, no streaks, no "you played 4 times this month". Now is a working screen, and everything on it is either a thing the player is in or a thing they could join.

---
---

# PART 2 — DESIGN SYSTEM FOR THIS SCREEN

*Only the tokens, types and components the Now screen actually uses. Nothing else from the design system is reproduced.*

## 2.1 Colour tokens

```css
:root{
  /* surfaces */
  --paper:#F4F2ED;      /* the phone body behind the scroll column      */
  --paper2:#EDEAE3;     /* shaded header inside a card                   */
  --surface:#FFFFFF;    /* .card background                              */

  /* ink */
  --ink:#101B20;        /* primary text                                  */
  --night:#0A3441;      /* .card-n background, .avat, .fit, toast        */
  --night2:#12495B;     /* the second half of the balance bar            */
  --muted:#6E7F85;      /* .tiny, .eyebrow, .sect                        */
  --line:#E5E1D8;       /* card borders, tab bar rule                    */
  --line2:#F0EDE6;      /* .hair rules, .tag default background          */

  /* the four semantic colours — see 2.2 */
  --coral:#E8482B;  --coral-soft:#FDEBE6;  --coral-ink:#B8351C;
  --mint:#0C8F6B;   --mint-soft:#E2F3EC;
  --amber:#9A6A0B;  --amber-soft:#FBF0DA;
  --red:#B4392C;    --red-soft:#FBEAE7;
  --volt:#D9F24B;   /* ticks on the dark card ONLY                       */

  /* sport identity */
  --pad:#E8482B;    /* Padel     — shares coral                          */
  --ten:#0C8F6B;    /* Tennis    — shares mint                           */
  --squ:#12495B;    /* Squash    — shares night2                         */
  --bad:#9A6A0B;    /* Badminton — shares amber                          */
}
```

## 2.2 What each colour means, and it means only that

**This is the rule the whole screen rests on.** A colour used for two things is a colour that means nothing.

| Colour | Meaning | On Now it appears on |
|---|---|---|
| **Coral** `--coral` | *You. Your action. Your position.* | The primary button, the active tab, the active dot, your seat in the glyph, your level mark, the `.fit.hi` badge at 90+ |
| **Mint** `--mint` | *Settled. Nothing to do.* | The `good` state dot, `.tag.ok` for a card discount, `Court protected` / `Confirmed` / `Ready` tags |
| **Amber** `--amber` | *Time-bound. A window is open and will close.* | The `time` state dot — `Rescue active` only |
| **Red** `--red` | *Ended, or ending.* | The `ended` state dot — the four Cancelled contexts. The alert strip border on the dark card |
| **Night** `--night` | *Structure.* Not a semantic colour | `.card-n`, `.fit`, `.avat`, the toast |
| **Volt** `--volt` | *Confirmed fact, on dark only.* | The `✓` tick in state-card lines. **Nowhere else in the app** |

**Coral is never decorative.** If coral appears on this screen and the player is not being pointed at a thing they own or an action they can take, that is a bug.

## 2.3 The five state tones

```js
ST_TONE = {
  good:  'var(--mint)',            // settled — nothing for you to do
  watch: 'var(--coral)',           // something is moving that concerns you
  time:  'var(--amber)',           // a window is open and will close
  ended: 'var(--red)',             // over
  idle:  'rgba(255,255,255,.45)',  // in progress, nothing wrong — DARK CARD ONLY
}
```

**`idle` is white-at-45%, not a hue**, because it only ever renders on `.card-n`. A forming match is not good news, not bad news, and not urgent — it is simply in progress, and giving it a colour would imply otherwise. On the light `matchCard` the same state renders through `.tag` with the default `--line2` background.

## 2.4 Typography

```css
body   { font-family:'Archivo', system-ui, sans-serif; -webkit-font-smoothing:antialiased }
.mono  { font-family:'IBM Plex Mono', ui-monospace, monospace; font-variant-numeric:tabular-nums }
.num   { font-weight:700; letter-spacing:-.035em; font-variant-numeric:tabular-nums }
```

**Two families. Archivo for language, IBM Plex Mono for anything a player compares.** Times, prices, seat counts and levels are all mono with tabular figures, so a column of them lines up and a changing number does not shift its neighbours.

**`.num` is a treatment, not a family** — it sets weight and tracking only, and is almost always combined: `class="mono num"`.

| Role | Class | Size | Weight | Tracking | Line |
|---|---|---|---|---|---|
| Screen title | `.h1` | 19px | 700 | −.03em | — |
| The big clock on the state card | inline `.num` | **30px** | 700 | −.035em | 1 |
| Price on a match card | inline `.mono .num` | 14px | 700 | −.035em | — |
| Time on a match card | inline `.mono` | 12px | 700 | — | — |
| Match card sub-line | inline | 12px | 600 | — | — |
| State card sub-line | inline | 12px | 600 | — | — |
| Secondary text | `.tiny` | 11px | 400 | — | 1.45 |
| Section label | `.sect` | 9.5px | 700 | .15em | — |
| Card region label | `.eyebrow` | 9.5px | 700 | .15em | — |
| Facet label on dark card | `.eyebrow` override | **8.5px** | 700 | .15em | — |
| Pill text | `.tag` | 9.5px | 700 | — | — |
| Fit badge | `.fit` | 11px | 700 | — | — |
| Tab label | `.tab` | 8.5px | 600 | — | — |

**Negative tracking on every heading, tightening as size grows.** Archivo at 19px with default tracking reads loose; at −.03em it reads set. Body text is never tracked.

## 2.5 Spacing

**There is no 4- or 8-point grid.** Values are chosen per component: **5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15**. Two dominate:

- **9px** — the gap between stacked cards, and the standard `.hair` top margin
- **15px** — the horizontal page gutter

**Content width is 392 − 30 = 362px**, and every horizontal measurement on this screen derives from it.

| Measurement | Value |
|---|---|
| Page gutter | 15px |
| Content width | 362px |
| Card gap | 9px |
| `.hstrip` gap | 10px |
| `.hstrip` bleed | `margin:0 -15px 10px; padding:1px 15px 5px` |
| `.row` gap (tags) | 5px |
| `.pbar` padding | `12px 15px 9px` |
| Sport bar padding | `0 15px 9px` |
| `.sect` margin | `14px 0 7px` · first child `2px 0 7px` |
| `#scroll` padding | `0 15px 14px` |
| Tab bar padding | `7px 0 12px` |

## 2.6 Radius

| Radius | Applied to |
|---|---|
| 34px | Phone frame |
| 15px | `.card-n` |
| 13px | `.card` |
| 10px | `.btn`, the alert strip, the state-card facet panel |
| 9px | `.avat` |
| 999px | `.chip` |
| 7px | `.fit` |
| 6px | `.tag` |
| 5px | `.tab i` |
| 4px | `.hstrip` glyph court rect |
| 3px | `.dots i`, `.tag i` dot |

## 2.7 Elevation

**Almost none, and that is deliberate.** The screen has exactly two shadows:

```css
#phone { box-shadow: 0 40px 90px -40px rgba(0,0,0,.8) }   /* the device, not the UI */
.tst   { box-shadow: 0 12px 28px -12px rgba(0,0,0,.6) }   /* toast only */
```

Cards are separated by **border and background**, never by shadow. `.card` is white on `--paper` with a 1px `--line` border; `.card-n` is `--night` on `--paper`, which needs no border at all. Depth comes from contrast, which survives a bright phone screen outdoors in a way a soft shadow does not.

## 2.8 Motion

```css
#scroll > * { animation: rise .3s cubic-bezier(.2,.8,.2,1) both }
@keyframes rise { from { opacity:0; transform:translateY(7px) } to { opacity:1; transform:none } }

.card.tap, .card-n.tap { transition:.12s }
.card.tap:hover        { border-color:var(--coral); transform:translateY(-1px) }
.card-n.tap:hover      { transform:translateY(-1px) }
.btn                   { transition:.12s }
.btn:hover             { filter:brightness(1.06) }

@media (prefers-reduced-motion:reduce) { * { animation:none !important; transition:none !important } }
```

**One entrance animation, 300ms, applied to direct children of the scroll column.** 7px of travel and a fade. Nothing on this screen slides in from the side, scales up, or bounces.

**The reduced-motion query is not optional.** It kills both animation and transition globally.

---
---

# PART 3 — THE COMPONENTS

*Every class the Now screen uses, with its full definition and the reason it is shaped that way.*

## 3.1 Shell

```css
#phone   { width:392px; height:788px; background:var(--paper); border-radius:34px;
           display:flex; flex-direction:column; overflow:hidden }
#view    { flex:1; display:flex; flex-direction:column; min-height:0; overflow:hidden }
#scroll  { flex:1; overflow-y:auto; overflow-x:hidden; padding:0 15px 14px; scroll-behavior:smooth }
#scroll::-webkit-scrollbar { width:0 }
#tabbar  { display:grid; grid-template-columns:repeat(5,1fr); border-top:1px solid var(--line);
           background:#fff; padding:7px 0 12px; flex-shrink:0 }
```

**In production this becomes a viewport, not a fixed 392×788 frame.** The measurements that carry over are the **15px gutter** and the **362px content width** as a maximum — on a wider phone the column stays 362px and centres rather than stretching, because every internal proportion on the state card and the glyph is tuned to it.

**The header and tab bar do not scroll.** Only `#scroll` moves.

## 3.2 `.pbar` — the header

```css
.pbar    { display:flex; align-items:center; gap:10px; padding:12px 15px 9px; flex-shrink:0 }
.pbar .t { flex:1; min-width:0 }
.h1      { font-size:19px; font-weight:700; letter-spacing:-.03em; margin-top:2px }
.eyebrow { font-size:9.5px; letter-spacing:.15em; text-transform:uppercase;
           color:var(--muted); font-weight:700 }
```

```html
<div class="pbar">
  <div class="t">
    <div class="eyebrow">Kraków · Saturday · 14:30</div>
    <div class="h1">Hi, Tomek</div>
  </div>
</div>
```

**The eyebrow sits above the title**, which is the reverse of the usual convention and correct here: the context (*where and when*) is what changes, and the greeting is what does not.

**No back chevron on Now.** It is the root of the stack.

## 3.3 The sport bar

```css
.chip     { display:inline-flex; align-items:center; gap:5px; height:27px; padding:0 11px;
            border-radius:999px; border:1px solid var(--line); font-size:10.5px;
            background:#fff; font-weight:600; white-space:nowrap }
.chip.on  { background:var(--ink); color:#fff; border-color:var(--ink) }
.chip.sm  { height:25px; padding:0 8px; font-size:10px; gap:4px }
.chip.sm i{ width:5px; height:5px; border-radius:2px }
```

```html
<div class="row" style="padding:0 15px 9px;flex-wrap:nowrap;overflow:auto">
  <button class="chip sm on" data-sport="all">All</button>
  <button class="chip sm"><i style="background:var(--pad)"></i>Padel</button>
  <button class="chip sm"><i style="background:var(--ten)"></i>Tennis</button>
  <button class="chip sm"><i style="background:var(--squ)"></i>Squash</button>
  <button class="chip sm"><i style="background:var(--bad)"></i>Badminton</button>
</div>
```

**A 5px rounded square, not a circle**, so it does not read as a status dot — status dots on this screen are 6px circles inside `.tag`.

**The `All` chip has no square**, because there is no colour for "every sport" that would not claim to be one.

**Selection is `--ink`, not `--coral`.** A filter is not an action. Coral here would compete with the primary button below it.

**The bar is persistent across Now, Find and Create**, and the selection carries. A player who filters to Padel on Now and taps Find sees Padel.

## 3.4 `.sect` — the section label

```css
.sect             { font-size:9.5px; letter-spacing:.15em; text-transform:uppercase;
                    color:var(--muted); font-weight:700; margin:14px 0 7px }
.sect:first-child { margin-top:2px }
```

Three on this screen: `Your matches · 2 · soonest first`, `Best fit for you`, `Full, but worth waiting for`.

**The first section carries a count and an ordering claim**, because a horizontally scrolling strip must say how many things are in it — the player cannot see.

## 3.5 `.card-n` — the dark state card

```css
.card-n          { background:var(--night); color:#fff; border-radius:15px;
                   padding:14px; margin-bottom:9px }
.card-n .tiny    { color:rgba(255,255,255,.68) }
.card-n .eyebrow { color:rgba(255,255,255,.52) }
.card-n .hair    { border-color:rgba(255,255,255,.15) }
.card-n.tap      { cursor:pointer; transition:.12s }
.card-n.tap:hover{ transform:translateY(-1px) }
```

**The colour inversion is the information architecture.** Dark means *you are in this*. Light means *you could be*. A player scrolling Now knows which is which before reading a word, and the same rule holds on Find, Match detail and Inbox.

**Padding is 14px, not the 12px of `.card`.** The dark card carries more content and needs the extra breathing room; at 12px the tick lines crowd the edge.

## 3.6 `.card` — the light match card

```css
.card          { background:#fff; border:1px solid var(--line); border-radius:13px;
                 padding:12px; margin-bottom:9px }
.card.tap      { cursor:pointer; transition:.12s }
.card.tap:hover{ border-color:var(--coral); transform:translateY(-1px) }
```

**`matchCard` overrides padding to 11px**, because it is denser than a general-purpose card and 12px leaves the tag row looking loose.

## 3.7 `.hair` — the internal rule

```css
.hair            { border-top:1px solid var(--line2); margin-top:9px; padding-top:8px }
.card-n .hair    { border-color:rgba(255,255,255,.15) }
```

**The only divider in the system.** Both cards use it; the dark card lightens it. It appears three times on a state card (facets, lines, buttons) and once or twice on a match card.

## 3.8 `.tag` — the status pill

```css
.tag      { display:inline-flex; align-items:center; gap:4px; padding:3px 7px; border-radius:6px;
            font-size:9.5px; font-weight:700; background:var(--line2); color:var(--muted);
            white-space:nowrap; overflow:hidden; text-overflow:ellipsis }
.tag.ok   { background:var(--mint-soft);  color:var(--mint) }
.tag.hot  { background:var(--coral-soft); color:var(--coral-ink) }
.tag.warn { background:var(--amber-soft); color:var(--amber) }
.tag.bad  { background:var(--red-soft);   color:var(--red) }
.tag.w    { background:rgba(255,255,255,.17); color:#fff }
.tag i    { width:6px; height:6px; border-radius:3px; display:block; flex-shrink:0 }
```

**Five variants, and `.tag.w` is the dark-card one.** On `.card-n` the state tag is white-on-translucent with a coloured 6px dot; on `.card` it is the default grey pill with the same dot. **The dot carries the tone in both cases** — the pill background does not change per state, which keeps a card with four tags from becoming a rainbow.

**`.tag.hot` uses `--coral-ink` (#B8351C), not `--coral`.** Coral on coral-soft at 9.5px/700 fails contrast; the darker ink passes.

## 3.9 `.fit` — the Match Fit badge

```css
.fit    { display:inline-flex; align-items:center; gap:4px; height:23px; padding:0 9px;
          border-radius:7px; background:var(--night); color:#fff; font-size:11px; font-weight:700 }
.fit.hi { background:var(--coral) }
```

```html
<span class="fit hi">✦ 93</span>     <!-- score ≥ 90 -->
<span class="fit">✦ 84</span>        <!-- score < 90  -->
```

**The `✦` is part of the badge, not decoration.** It marks the number as a computed recommendation rather than a rating the player gave.

**Coral at 90+** is the only place on this screen where a threshold changes a colour, and it is justified: a 90 is rare and means *drop what you are doing*.

## 3.10 `.btn` — buttons

```css
.btn      { display:inline-flex; align-items:center; justify-content:center; height:34px;
            padding:0 14px; border-radius:10px; font-size:12px; font-weight:700;
            cursor:pointer; transition:.12s; text-align:center }
.btn:hover{ filter:brightness(1.06) }
.btn.p    { background:var(--coral); color:#fff }
.btn.w    { background:rgba(255,255,255,.17); color:#fff }
```

Only two variants appear on Now, both inside the state card's button row: one `.btn.p` primary and one or two `.btn.w` icon buttons.

## 3.11 `.hstrip` — the snapping carousel

```css
.hstrip     { display:flex; gap:10px; overflow-x:auto; scroll-snap-type:x mandatory;
              margin:0 -15px 10px; padding:1px 15px 5px; scrollbar-width:none }
.hstrip::-webkit-scrollbar { height:0 }
.hstrip > * { scroll-snap-align:center; scroll-snap-stop:always;
              flex:0 0 100%; margin-bottom:0 !important }
```

**Three details that matter.**

`margin:0 -15px` with `padding:… 15px` **bleeds the strip to the screen edge** while keeping the first card aligned to the gutter. Without it the second card is clipped at 362px and looks broken rather than peeking.

`scroll-snap-stop:always` means **one swipe moves one card.** A fast flick through five booked matches would otherwise skip past the one the player wanted.

`flex:0 0 100%` makes each card exactly the content width, so **the next card peeks by exactly the 10px gap** — enough to signal more, not enough to distract.

## 3.12 `.dots` — the pager

```css
.dots      { display:flex; gap:5px; justify-content:center; margin:-2px 0 11px }
.dots i    { width:5px; height:5px; border-radius:3px; background:var(--line); display:block }
.dots i.on { background:var(--coral); width:14px }
```

**Rendered only when there are 2+ cards.** The active dot widens to 14px rather than only changing colour, so it is legible at a glance and to a player who cannot distinguish the hues.

## 3.13 `.empty` — the empty state

```css
.empty   { text-align:center; padding:30px 18px; color:var(--muted) }
.empty b { display:block; font-size:13px; color:var(--ink); margin-bottom:5px }
```

Always inside a `.card`. Bold line in `--ink`, explanation in `--muted`.

## 3.14 `#tabbar` — the five tabs

```css
#tabbar    { display:grid; grid-template-columns:repeat(5,1fr); border-top:1px solid var(--line);
             background:#fff; padding:7px 0 12px; flex-shrink:0 }
.tab       { display:flex; flex-direction:column; align-items:center; gap:4px;
             font-size:8.5px; color:var(--muted); font-weight:600 }
.tab.on    { color:var(--coral) }
.tab i     { width:16px; height:16px; border-radius:5px; background:currentColor;
             opacity:.85; display:block }
.tab.fab i { width:28px; height:28px; border-radius:10px; background:var(--coral);
             opacity:1; margin-bottom:-4px }
```

```
[ Now ]  [ Find ]  ( ＋ )  [ Inbox ]  [ You ]
   ▲                                          ← .tab.on, coral
```

**Five columns, the centre one a FAB.** Create is 28px and coral, lifted 4px above the row, with no label — the shape is the label.

**Icons are `currentColor` squares in the prototype.** Production ships a real icon set at 16px, and the tab colour must still come from `currentColor` so `.tab.on` recolours the icon without a second rule.

## 3.15 The court glyph

Rendered inline as SVG at two sizes on this screen: **58px** on the state card, **46px** on a match card.

```js
glyph(sport, seats, w, dark)
```

| Element | Rule |
|---|---|
| Height | `w × 0.56`, or `w × 0.62` for Squash |
| Court rect | `rx:4`, inset by `w × 0.05`, fill `#EEF2F1` (light) / `rgba(255,255,255,.1)` (dark) |
| Lines | `#D8DFDD` light / `rgba(255,255,255,.3)` dark |
| Net | Vertical centre line 1.4px + two service lines 0.8px at 30% and 70%. Squash: one horizontal line at 55% |
| Seat positions | Doubles `[21%,30%] [21%,72%] [79%,30%] [79%,72%]` · Singles `[22%,50%] [78%,50%]` · Squash `[38%,62%] [62%,42%]` |
| **Your seat** | Filled circle, `r = w × 0.082`, **`#E8482B` coral** — the only coral in the glyph |
| A taken seat | Filled circle, `r = w × 0.075`, `#0A3441` light / `#fff` dark |
| A guest seat | Outlined circle, 1.6px stroke, same size as taken |
| **An empty seat** | Outlined circle, **1.4px coral, `stroke-dasharray:2.5 2.5`** |

**The dashed coral ring is doing real work.** An empty seat is not merely absent — it is the thing that has to be filled for the match to happen, and it is what a player scanning a list is actually looking for. Solid grey would have made it disappear.

**Your seat is drawn slightly larger** (0.082 vs 0.075 of width) as well as coral. Two signals, because on a 46px glyph the colour alone is four pixels wide.

## 3.16 Accessibility requirements

The prototype has known gaps. **Production must close all seven.**

| # | Requirement |
|---|---|
| 1 | `--muted` (#6E7F85) on white is **4.02:1** — below AA for body text. Production uses **#5C6D73** for `.tiny` and `.sect` |
| 2 | `--mint` (#0C8F6B) on `--mint-soft` is **3.6:1**. Production uses **#0A7355** for `.tag.ok` text |
| 3 | `--amber` (#9A6A0B) on `--amber-soft` is **3.9:1**. Production uses **#8A5E09** for `.tag.warn` |
| 4 | `:focus-visible { outline:2px solid var(--coral); outline-offset:2px }` on every interactive element |
| 5 | The `.hstrip` is a `role="region"` with `aria-label="Your matches"`; each card is a `<article>` with `aria-roledescription="match card"` and `aria-posinset` / `aria-setsize` |
| 6 | `.dots` are `aria-hidden` — the strip's `aria-posinset` already carries the position |
| 7 | The glyph carries `role="img"` and an `aria-label` stating the occupancy: *"Padel doubles, 3 of 4 seats taken, your seat is on the left"* |

**Tone is never carried by colour alone anywhere on this screen.** Every state dot sits beside its own text label; the fit badge prints its number; the seat glyph is backed by a `filled/n` count in mono.

**Minimum tap target is 44 × 44.** The state card's `.btn.w` icon buttons are 40 × 34 visually and must carry invisible padding to reach 44.

---
---

# PART 4 — THE STATE CARD

*The most important component on the screen, and the one that carries the product's promise.*

## 4.1 What it is for

A state card is the canonical representation of **a match you are in.** One card, one match. Its job is to make the eight-second session complete without a tap.

**Its anatomy is identical across all thirty-two contexts.** Only the content changes. That constancy is the point: a player who has read one state card can read every other one without relearning where anything is.

## 4.2 Anatomy

```
┌─ .card-n · 15px radius · 14px padding ─────────────────┐
│                                                        │
│  [● Court protected]              PADEL · DOUBLES      │  A  tag row
│                                                        │
│  18:30                              ╭──────────╮       │  B  clock + glyph
│  Sat · Zabłocie Sport               │ ▦  ·  ▦  │       │
│  Mondo · 90 min                     │ ▦  ·  ○  │       │
│                                     ╰──────────╯       │
│                                            3/4         │
│  ──────────────────────────────────────────────────    │  .hair
│  COURT              │  GROUP                           │  C  facets
│  Protected · Mondo  │  3 of 4 seats paid               │
│  ──────────────────────────────────────────────────    │  .hair
│  ┌──────────────────────────────────────────────────┐  │  D  alert (conditional)
│  │ ● Ola left after the deadline. We are looking    │  │
│  │   for a replacement. Your payment will not change │  │
│  └──────────────────────────────────────────────────┘  │
│  ──────────────────────────────────────────────────    │  .hair
│  ✓ You paid 38,00 zł                                   │  E  lines ×3–5
│  ✓ Three paid seats, so a court is held until 4h…      │
│  ○ The exact court is assigned by us, never chosen     │
│  ○ Leaving now returns everything, in minutes          │
│                                                        │
│  [   Open match   ]  [ ✉ ]  [ ⌘ ]                      │  F  button row
└────────────────────────────────────────────────────────┘
```

## 4.3 Region A — the tag row

```html
<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px">
  <span class="tag w"><i style="background:var(--mint)"></i>Court protected</span>
  <span class="eyebrow" style="white-space:nowrap">Padel · Doubles</span>
</div>
```

**Left: the state tag**, `.tag.w` with a 6px tone dot. **Right: sport and format**, `.eyebrow` at 52% white.

**The tag is the answer to "what is happening", and it comes first** because that is what the player opened the app to find out.

## 4.4 Region B — the clock and the glyph

```html
<div style="display:flex;justify-content:space-between;align-items:flex-start">
  <div style="min-width:0">
    <div class="num" style="font-size:30px;line-height:1">18:30</div>
    <div style="font-size:12px;font-weight:600;margin-top:4px">Sat · Zabłocie Sport</div>
    <div class="tiny">Mondo · 90 min</div>
  </div>
  <div style="text-align:right;flex-shrink:0">
    <!-- glyph(sport, seats, 58, dark) -->
    <div class="tiny mono" style="margin-top:3px">3/4</div>
  </div>
</div>
```

**30px is the largest type on the screen**, and it is the time. Everything else on the card is context for it.

**`line-height:1`** so the 30px number does not push the two lines below it out of alignment with the glyph.

**The `3/4` under the glyph is redundant with the glyph, deliberately.** The glyph is fast and the count is precise, and a player at a glance in bright sun gets one of the two.

## 4.5 Region C — the two facets

```html
<div class="hair" style="display:flex;gap:10px">
  <div style="flex:1;min-width:0">
    <div class="eyebrow" style="font-size:8.5px">Court</div>
    <div class="tiny" style="color:#fff;font-weight:600;line-height:1.35">Protected · Mondo</div>
  </div>
  <div style="width:1px;background:rgba(255,255,255,.15)"></div>
  <div style="flex:1;min-width:0">
    <div class="eyebrow" style="font-size:8.5px">Group</div>
    <div class="tiny" style="color:#fff;font-weight:600;line-height:1.35">3 of 4 seats paid</div>
  </div>
</div>
```

**Court and group are the two independent axes of an open match**, and they can be in any combination. A match can be full with no court; a match can have a court with two players. Splitting them into two facets is what lets a player read both without a sentence that has to hedge.

**Facet values are white at 600 weight, not the 68% of `.tiny`.** These are facts, not commentary.

## 4.6 Region D — the alert strip

Rendered only when `st.alert` exists. Two states do so: `replacement` and `rescue` — the two moments when something happened that the player did not cause and needs to know about immediately.

```html
<div style="display:flex;gap:8px;align-items:flex-start;margin-top:9px;padding:8px 10px;
     border-radius:9px;background:rgba(214,77,58,.16);border:1px solid rgba(214,77,58,.4)">
  <span style="width:7px;height:7px;border-radius:4px;background:var(--red);
        flex-shrink:0;margin-top:4px;display:block"></span>
  <span class="tiny" style="color:#fff;flex:1;line-height:1.45">
    Ola left after the commitment deadline. We are looking for a replacement.
    <b>Your payment will not change.</b>
  </span>
</div>
```

**The bold clause is always the money clause.** The alert exists to deliver bad news, and the second half of the sentence is the reason the news is not as bad as it sounds. Emphasising it is not decoration — it is the sentence the player needs to read if they read nothing else.

## 4.7 Region E — the lines

Three to five per state. Each is `[marker, text]` where marker `1` is a settled fact and `0` is a condition or a consequence.

```html
<div class="hair">
  <div style="display:flex;gap:7px;align-items:flex-start;padding:2px 0">
    <span style="color:var(--volt);font-size:10px;line-height:1.5;flex-shrink:0">✓</span>
    <span class="tiny" style="color:rgba(255,255,255,.92);flex:1">You paid 38,00 zł</span>
  </div>
  <div style="display:flex;gap:7px;align-items:flex-start;padding:2px 0">
    <span style="width:7px;height:7px;border-radius:4px;border:1.5px solid rgba(255,255,255,.75);
          margin-top:4px;flex-shrink:0;display:block"></span>
    <span class="tiny" style="color:rgba(255,255,255,.92);flex:1">
      A court is held from the second paid seat…</span>
  </div>
</div>
```

**Volt tick for a settled fact. Hollow ring for a condition.** The distinction is the whole grammar of the card: *this has happened* versus *this is what happens next, or what would happen if.*

**Line text is white at 92%, not the 68% of `.tiny`.** Four lines at 68% on a dark card is a grey block nobody reads.

**The first line of almost every state is the money line** — *"You paid 38,00 zł"* — because that is the fact the player most wants confirmed and it anchors everything below it.

**On a match the player is NOT in** (the waitlist case), the money line is rewritten to *"Your share would be 38,00 zł · booking fee 0,00 zł"*, because *"You paid"* would be a lie.

## 4.8 Region F — the button row

```html
<div class="row" style="margin-top:11px;flex-wrap:nowrap">
  <span class="btn p" style="flex:1;height:34px">Open match</span>
  <span class="btn w" style="width:40px;height:34px">✉</span>
  <span class="btn w" style="width:40px;height:34px">⌘</span>
</div>
```

| Button | Width | Action |
|---|---|---|
| Primary | `flex:1` | The state's own CTA, or *Open match*. Label may carry a countdown suffix |
| ✉ | 40px | Opens Inbox filtered to this match |
| ⌘ | 40px | Opens the access sheet — door code and card QR. **Hidden on post-play states** |

**The primary label is state-driven**, not fixed. `Confirm the result`, `Enter the result`, `Getting in`, `See what happened`, `Open match`.

## 4.9 The nine tags and their tones

Fourteen tags exist across the full lifecycle; **these nine appear on Now.**

| Tag | Tone | Dot | Meaning |
|---|---|---|---|
| `Forming` | `idle` | white 45% | Seats still selling. No court held yet |
| `Court held` | `watch` | coral | A court is held, but this is not a firm booking |
| `Court released` | `watch` | coral | The hold lapsed. Money unaffected, match still looking |
| `Court committed` | `good` | mint | The club committed a court by hand |
| `Court protected` | `good` | mint | Enough paid seats. A private booking cannot take it |
| `Full` | `good` | mint | Every seat paid, not yet past the deadline |
| `Confirmed` | `good` | mint | Committed. Money settled |
| `Replacement pending` | `watch` | coral | Somebody left after commitment. Full-price search running |
| `Rescue active` | `time` | amber | Targeted 50/50 invitations are out |
| `Ready to play` | `good` | mint | Door code live |
| `On standby` | `idle` | white 45% | You are on a waitlist, not committed |
| `Cancelled` | `ended` | red | Four contexts, all terminal |

**Plus the post-play set**, which stays on Now for 24 hours: `Needs result` (watch), `Confirm the result` (watch), `Completed` (good), `Played` (idle).

## 4.10 The thirty-two contexts

**One tag, several situations.** The tag is the truth about the group and the court; the context line under it says which of that tag's situations you are in. This table is the complete content contract.

### Forming — court not protected

| Key | Context | Court facet | Group facet |
|---|---|---|---|
| `forming` | no court held yet | Not held — the club is still selling this slot | `n` of 4 seats paid |
| `formingHeld` | a seat is held for an invited player | Not protected — no court is held yet | 2 of 4 paid · 1 seat held |
| `formingLate` | the deadline has passed and the match is still incomplete | Not protected — no court is held yet | `n` of 4 seats paid |
| `formingBack` | a player left before commitment | Released — the court is no longer held | `n` of 4 seats paid |

**`formingLate` has a second variant.** A match created *inside* its own commitment window has a deadline already in the past. Saying *"the deadline has passed"* would read as a warning about something the player just did on purpose, so the context becomes **"it commits as soon as it is complete."**

### Court held — the ladder

| Key | Context | Court facet |
|---|---|---|
| `heldSoft` | two paid seats **or** one player short | Held · Mondo — `note` |
| `heldReleased` | still short, close to play | Released — back on sale at Zabłocie Sport |
| `clubHeld` | the club put a court behind it | Committed by Zabłocie Sport · Mondo |

**`heldReleased` is its own state and must not be collapsed into `forming`.** The player paid for a match that briefly had a court and now does not, and *"silence there would be the single most alarming gap on the screen."*

### Court protected

| Key | Context |
|---|---|
| `protectedCourt` | one player needed |
| `protectedBack` | a player left before commitment |
| `protectedLate` | past the deadline, still free to leave |

### Full, confirmed, replacement, rescue, ready

| Key | Tag | Context |
|---|---|---|
| `full` | Full | free cancellation until the deadline |
| `confirmed` | Confirmed | committed at the deadline |
| `confirmedOnFill` | Confirmed | the last seat filled after the deadline |
| `replacement` | Replacement pending | full-price search |
| `replacementTransfer` | Replacement pending | a transfer is being arranged |
| `rescue` | Rescue active | targeted 50/50 invitations |
| `rescueLate` | Rescue active | past the checkpoint, still searching |
| `ready` | Ready to play | door code live |

### Cancelled

| Key | Context | Group facet |
|---|---|---|
| `cancelledIncomplete` | never completed · T−2h | `n` of 4 — it never filled |
| `cancelledCheckpoint` | certainty checkpoint · rebooking club | 3 of 4 — the seat was never refilled |
| `cancelledClub` | club, court or weather | everybody refunded |
| `inventoryLost` | no court left to play on | Gone — the last compatible court was sold |

### After the match — 24 hours, then it becomes history

| Key | Tag | Context |
|---|---|---|
| `needsResult` | Needs result | thirty minutes, any of the four |
| `confirmResult` | Confirm the result | one tap from the other side |
| `completed` | Completed | levels already moved |
| `playedShort` | Played | played a player short |
| `playedNoShow` | Played | somebody did not turn up |
| `playedNoScore` | Played | nobody entered a score |

### Standby and private

| Key | Tag | Context |
|---|---|---|
| `waitlisted` | On standby | you are queued, not committed |
| `privateReserved` | Reserved | you own this court |
| `privatePartial` | Reserved | shares partly paid · you guarantee the rest |
| `privateFull` | Reserved | every share paid |
| `privateOpen` | Reserved | empty seats opened publicly |

## 4.11 Three worked cards

### `protectedCourt` — the common good case

```
[● Court protected]                        PADEL · DOUBLES
18:30
Sat · Zabłocie Sport
Mondo · 90 min                                   ▦ · ▦
                                                 ▦ · ○     3/4
── COURT ──────────────────── │ ── GROUP ────────────────
Protected · Mondo — a private  │ 3 of 4 seats paid
booking can no longer take it  │
──────────────────────────────────────────────────────────
✓ You paid 38,00 zł
✓ Three paid seats, so a compatible court is held until 4h before play
○ The exact court is assigned by us, never chosen — the price cannot change
○ Leaving now returns everything, in minutes
[      Open match      ]  [ ✉ ]  [ ⌘ ]
```

### `replacement` — the case the product exists for

```
[● Replacement pending]                    PADEL · DOUBLES
18:30
Sat · Zabłocie Sport
Mondo · 90 min                                   ▦ · ▦
                                                 ▦ · ●     3/4
── COURT ──────────────────── │ ── GROUP ────────────────
152,00 zł settled to the club  │ 3 of 4 · the seat stays funded
──────────────────────────────────────────────────────────
┌────────────────────────────────────────────────────────┐
│ ● Ola left after the commitment deadline. We are       │
│   looking for a replacement. Your payment will not     │
│   change.                                              │
└────────────────────────────────────────────────────────┘
✓ You paid 38,00 zł — nothing about your booking changes
○ Their payment stays on the seat, so the court is safe
○ The seat is offered at the normal 38,00 zł to compatible players
○ They are refunded in full if somebody pays it
[      Open match      ]  [ ✉ ]  [ ⌘ ]
```

**Note the glyph.** The vacated seat renders as a **filled** dot, not a dashed ring, because the seat is still funded. That is the visual form of *"the court is safe"* — and it is why seat symbols are derived from `paid`, not from occupancy.

### `heldReleased` — the case that would otherwise be silence

```
[● Court released]                         PADEL · DOUBLES
18:30
Sat · Zabłocie Sport
Mondo · 90 min                                   ▦ · ▦
                                                 ▦ · ○     3/4
── COURT ──────────────────── │ ── GROUP ────────────────
Released — back on sale at     │ 3 of 4 seats paid
Zabłocie Sport                 │
──────────────────────────────────────────────────────────
✓ You paid 38,00 zł — unchanged, and refundable in full
○ Inside 4 hours, a court is only held for a complete match
○ The match is still open and still looking. The last seat books a court on the spot
○ If the club sells its last compatible court first, everybody is refunded in full
[      Open match      ]  [ ✉ ]  [ ⌘ ]
```

---
---

# PART 5 — BEST FIT FOR YOU

*The recommendation engine's surface, and the section whose name changed.*

## 5.1 Why the section is renamed

The prototype called this list **"Even matches for you"**, which implied one thing and delivered another. The list has always been ranked by **Match Fit**, a weighted score over seven factors — of which skill parity is only the largest.

Calling it *even* taught the player the wrong mental model. A player who believes the list is skill-matched cannot explain why a 2,71 match ranks below a 2,78 one, and will conclude the ranking is broken rather than that it is weighing travel, price and the group.

**"Best fit for you" is what the list actually is**, and naming it correctly lets the app explain itself.

```
BEST FIT FOR YOU
Ranked on seven things, not just level
```

That subtitle is not filler. It is the sentence that makes the ✦ badge legible.

## 5.2 The seven factors

| Factor | Weight | What it measures |
|---|---|---|
| **Skill overlap** | **30%** | How close you are to the level this match is aimed at |
| **Predicted balance** | **20%** | How even the match is forecast to be with you in it |
| **Group reliability** | **15%** | The Player Scores of the people already in |
| **Time and travel** | **15%** | Minutes to the club |
| **Match type** | **8%** | Counted or friendly, against your preference |
| **Price vs your ceiling** | **7%** | Your share after your card, against what you will pay |
| **Preferences and side** | **5%** | Side and format preferences |

**Weights sum to exactly 100.** A match scoring 1.0 on everything scores 100 before modifiers.

### How each is computed

```
skill        max(0, 1 − |myLevel − target| / 0.55)
             target = the open seat's ideal level, or the band midpoint, or your own level
balance      forecast.pct / 100          · default 0.70 when no forecast is possible
reliability  (0.5 × min(scores) + 0.5 × mean(scores)) / 100   · default 0.80 when nobody else is in
travel       max(0, 1 − max(0, distanceMin − 20) / 18)
type         1.0 counted · 0.72 friendly
price        clamp(0, 1, 1 − (payable − 30) / 30)
preferences  0.9
```

**Three of these deserve a note.**

**Skill falls off over 0,55 of a level** — roughly half a band. More than half a level from where the match is aimed and you are not the right player for it, and at weight 30 that costs the full thirty points.

**Reliability weights the minimum equally with the mean**, because *a group is as reliable as its least reliable member.* Three players at 95 and one at 55 scores 0.70, not the 0.85 a plain mean would give. One no-show ruins the evening for everybody, so one weak score visibly drags the term.

**Balance defaults to 0.70 when it cannot be computed** — deliberately neither rewarding nor punishing a match that has nobody in it yet.

### The three modifiers

Applied after the weighted sum, before the clamp. **Mutually exclusive by construction.**

| Modifier | Condition | Reason shown |
|---|---|---|
| **+8** | The match carries a Promotion badge | qualifies for your ladder |
| **+5** | You have played none of the people in it | opponents you have not played |
| **−8** | Three or more others, **all** of them regulars | the same four again |

**The −8 is strict on purpose.** Playing with one regular is normal. Playing with your entire usual group every week is the pattern that makes a marketplace stop being a marketplace.

**Final score is clamped to 20–99.** No match ever scores 100, because certainty is never warranted. None scores below 20, because a score of 3 is not more useful than a score of 20 — both mean *no*.

## 5.3 The ranking and the cut

```
candidates = every open match, in the selected sport, starting in the future,
             with at least one unpaid seat, that I am not already in
sort       = Match Fit, descending
show       = the top 3
```

**Three, not ten.** The section's value is that somebody already did the choosing. A list of ten is Find, and Find is one tab away.

**No minimum score on Now.** The Find screen splits at 80 into *Best fit* and *Above your band*; Now shows the best three whatever they score, because a player with nothing booked needs a suggestion more than they need a purity threshold. If the best available is a 62, that is the honest answer and the badge says so.

## 5.4 The card

`matchCard` — the canonical representation of a match you could join. Used identically on Now, Find, the waitlist and the creation overlap rail.

```
┌─ .card.tap · 13px radius · 11px padding ───────────────┐
│ 18:30  [Promotion]                         ╭────────╮  │
│ Zabłocie Sport · 14 min                    │ ▦ · ▦  │  │
│ [●Padel] [Doubles] [Counts] [card −all]    │ ▦ · ○  │  │
│                                            ╰────────╯  │
│                                                  3/4   │
│ ────────────────────────────────────────────────────── │
│ [✦ 93] [● Forming]          38,00 zł · 0 fee           │
└────────────────────────────────────────────────────────┘
```

### Left column

| Element | Class | Content |
|---|---|---|
| Time | `.mono` 12px/700 | `Today · 18:30` · `Tomorrow · 09:00` · `Sat · 18:30` |
| Badge | `.tag.hot` | Only when the match carries one — e.g. `Promotion` |
| Club line | `.tiny` | `Zabłocie Sport · 14 min` |
| Tag row | `.row` gap 5 | Sport (with colour square) · Format · Counts/Friendly · card discount |

**The sport tag carries a 6px square in the sport's colour.** The format tag is plain. `Counts` is `.tag.hot`; `Friendly` is the default grey — a counted match moves your rating and that is the more consequential fact.

**The card tag is `.tag.ok`** and reads `card −all` when the club card covers the whole share, or `card −15,00 zł` when it takes a fixed amount off.

### Right column

The 46px glyph, then `filled/n` in `.tiny.mono`.

### The `.hair` footer

```html
<div class="hair" style="display:flex;justify-content:space-between;align-items:center;gap:6px">
  <span style="display:flex;gap:5px;align-items:center;min-width:0">
    <span class="fit hi">✦ 93</span>
    <span class="tag"><i style="background:var(--mint)"></i>Court protected</span>
  </span>
  <span style="text-align:right">
    <span class="tiny" style="text-decoration:line-through">38,00 zł</span>
    <span class="mono num" style="font-size:14px">20,00 zł</span>
    <span class="tiny"> · 0 fee</span>
  </span>
</div>
```

**Left: fit and state. Right: price.** The struck-through original appears only when a club card reduces it.

**`· 0 fee` is on every card, every time.** It is the product's most repeated claim and the one competitors cannot match. Repetition is the mechanism.

## 5.5 The empty state

```html
<div class="card">
  <div class="empty" style="padding:18px">
    <b>Nothing open in Padel right now</b>
    We do not invent players to make a city look busy. Try another day, or create a match.
  </div>
</div>
```

**The sport name is interpolated** — *"in Padel"* when a sport is selected, *"in your sports"* when All is.

**The copy is the point.** An empty list is a true answer, and saying so is what makes a full list believable. This sentence is the single clearest statement of the product's relationship with its own data, and it must not be softened into *"No matches found. Try adjusting your filters."*

---
---

# PART 6 — FULL, BUT WORTH WAITING FOR

## 6.1 What it is for

A section that turns a dead end into standing demand.

**The player's problem:** the best match on the board is full. Without this section, they close the app.

**The product's problem:** the Rescue cascade needs a standby pool. When somebody leaves a committed match, the first rung offers the seat at full price to standby players — and that rung only works if a pool exists.

**One section solves both.** A waitlist entry costs nothing, commits to nothing, and creates a real option on both sides.

## 6.2 What qualifies

```
candidates = every full match, in the selected sport, starting in the future,
             that I am not already in
filter     = Match Fit ≥ 80
sort       = Match Fit, descending
show       = the top 1 on Now  (Find shows up to 3)
```

**The 80 floor is stricter than the open list, and that is deliberate.** Asking a player to wait for something is a bigger ask than asking them to join something. It has to be genuinely good, or the section teaches them to ignore it.

**One card on Now.** The section is a prompt, not a list. A player who wants more taps through to Find.

## 6.3 The section

```
FULL, BUT WORTH WAITING FOR
These fit you as well as anything above, and seats do come free.
Joining a waitlist costs nothing and commits to nothing.
```

**Three claims, all true, in the order the player needs them.** It is as good as the ones above (or it would not be here) · seats genuinely do free up (because the cascade exists) · it costs nothing (because a waitlist entry never charges).

## 6.4 The card

**Identical `matchCard`**, with two differences that fall out of the data rather than being styled in:

- The glyph shows every seat filled, no dashed rings
- The state tag reads `Full`, `Confirmed`, or `Ready to play` with a mint dot

**The price still shows.** It is what the seat would cost if one came free, and a player deciding whether to wait needs it.

## 6.5 What happens on tap

Tapping opens the match detail, where the CTA is **`Join the standby list · 0,00 zł`** rather than a payment button. Joining is one tap and produces a toast.

**The player then sees the match on Now** with the `On standby` tag — `idle` tone, because they are queued and not committed:

```
[○ On standby]                             PADEL · DOUBLES
── COURT ──────────────────── │ ── GROUP ────────────────
Fully paid by four other       │ 4 of 4 · you are 2nd on
players                        │ the standby list
──────────────────────────────────────────────────────────
✓ You joined the standby list · 0,00 zł
○ If a seat frees the top candidates are told at the same moment
○ Ten minutes to accept, five to pay, then it moves on
○ Ignoring it costs nothing and you keep your place
```

**"You are 2nd on the standby list" is a live position, not a queue number.** Order is computed against the vacancy that actually occurs — level fit against the seat that opened, proximity, reliability — so it can move without anybody doing anything wrong. The copy says *2nd*, never *your place in the queue*, for exactly that reason.

---
---

# PART 7 — INTERACTION

## 7.1 The full interaction map

| # | Target | Gesture | Result |
|---|---|---|---|
| 1 | Sport chip | tap | Filters the whole screen. Persists to Find and Create |
| 2 | State card body | tap | → Match detail |
| 3 | State card primary button | tap | → the state's own CTA destination |
| 4 | State card ✉ | tap | → Inbox, filtered to this match |
| 5 | State card ⌘ | tap | Opens the access sheet — door code + card QR |
| 6 | `.hstrip` | swipe horizontally | Snaps one card. Updates `.dots` |
| 7 | `.dots` | — | **Not interactive.** Indicator only |
| 8 | Match card | tap | → Match detail |
| 9 | `#scroll` | pull down | Refresh |
| 10 | Tab | tap | Switches root view |
| 11 | Create FAB | tap | → Create flow |

**Eleven targets. No long-press, no swipe-to-action, no contextual menu.** Everything on this screen is a tap or a horizontal swipe.

## 7.2 Scroll position must survive a re-render

The screen re-renders on every clock tick, every state change and every push notification. **The vertical scroll position and the `.hstrip` horizontal position must both be preserved**, or a player reading the third line of a card gets thrown to the top when a match two cards away changes state.

```js
const y = scroll.scrollTop;
const x = hstrip?.scrollLeft;
render();
scroll.scrollTop = y;
if (hstrip) hstrip.scrollLeft = x;
```

**This is not a nicety.** Without it the screen is unusable during the ten minutes around a commitment deadline, which is exactly when a player is most likely to be looking at it.

## 7.3 Live updates

| Trigger | Effect |
|---|---|
| Clock tick | Re-derive every state. Countdown suffixes update |
| Push: a player joined | Card re-renders, `.dots` unchanged |
| Push: court held / released | Tag, facet and lines change together |
| Push: a player left | `replacement` state, alert strip appears |
| Push: cancelled | Terminal state. Card stays for 24h |
| Pull to refresh | Full re-fetch |

**A state change never re-orders the strip.** Cards are sorted by start time, which does not change. A player watching a card change state watches it in place.

## 7.4 What a tick actually recomputes

Every derived value on this screen is a **pure function of the match record and the current instant.** Nothing is cached, and nothing needs to be — which is what lets the screen re-render on a tick with no invalidation step, and what lets a QA build scrub the clock backwards as freely as forwards.

Recomputed per tick: the tag, the context, both facets, every line, the alert, the CTA label, the countdown, the glyph, the fit score, the price.

**Persisted, never recomputed:** the commitment timestamp. It records that a threshold was crossed, and crossing it is irreversible. Everything else is derived.

## 7.5 Loading, error and offline

| State | Treatment |
|---|---|
| **First load** | Skeletons matching the real layout: one `.card-n` block at 226px, three `.card` at 118px. `--line2` fills, no shimmer |
| **Partial** | Booked matches render as they arrive; the recommendation sections show skeletons. **Never block the top of the screen on the bottom of it** |
| **Error, booked matches** | `.card` with `.empty`: *"Could not load your matches"* + a Retry button. **Never show a blank where a booking was** |
| **Error, recommendations** | The section is omitted entirely. A failed recommendation is not worth an error message |
| **Offline** | Last-known state renders with a `.tag.warn` in the header reading `Offline · last updated 14:12`. Times and deadlines still compute locally from the cached record and the device clock |

**Offline correctness is possible here precisely because everything is derived.** A cached match record plus a clock produces a correct tag, a correct deadline and a correct money position with no network at all. The only thing that goes stale is whether somebody else joined.

## 7.6 Notification deep links

| Notification | Lands on |
|---|---|
| Court held | Now, strip scrolled to that match |
| Court released | Now, strip scrolled to that match |
| A player joined | Now |
| A player left | **Match detail** — the alert needs the full context |
| Rescue seat available | Match detail |
| Cancelled | Now, strip scrolled to that match |
| Result needed | Match detail, result sheet open |

**Bad news deep-links deeper.** A cancellation lands on Now because the card carries the whole story; a player leaving lands on the match because the player will want the timeline.

---
---

# PART 8 — DATA CONTRACT

## 8.1 What the screen needs

```ts
GET /now?sport=all|Padel|Tennis|Squash|Badminton

{
  player: { firstName: string; city: string },
  serverTime: Instant,

  myMatches: MatchView[],        // sorted by start ascending
  bestFit:   MatchCardView[],    // top 3 by fit, descending
  fullWorth: MatchCardView[],    // top 1 by fit, ≥80, descending
}
```

```ts
type MatchView = {
  id: MatchId; sport: Sport; format: string;
  start: Instant; durationMin: number;
  club: { name: string; distanceMin: number; courtLabel: string };
  seats: { occupied: boolean; paid: boolean; isMe: boolean; isGuest: boolean }[];
  filled: number; capacity: 2 | 4;

  state: {
    key: string;                 // one of the 32
    tag: string;
    tone: 'good'|'watch'|'time'|'ended'|'idle';
    context: string;
    court: string;               // facet value
    group: string;               // facet value
    alert: string | null;        // may contain <b>
    lines: { settled: boolean; text: string }[];
    cta: { label: string; target: string };
    showAccess: boolean;
  },

  money: { share: Grosze; cardOff: Grosze; payable: Grosze },
}

type MatchCardView = {
  id: MatchId; sport: Sport; format: string;
  start: Instant; badge: string | null;
  club: { name: string; distanceMin: number };
  counts: boolean;
  seats: { occupied: boolean; paid: boolean; isGuest: boolean }[];
  filled: number; capacity: 2 | 4;
  fit: { score: number; reasons: string[]; warn: string | null };
  state: { tag: string; tone: string };
  money: { share: Grosze; cardOff: Grosze; payable: Grosze };
}
```

## 8.2 Server computes, client renders

**Every string on this screen comes from the server.** The client does not build a sentence, does not decide a tag, and does not know the thirty-two contexts.

**Why:** two applications and two platforms consume the same lifecycle. Duplicating the ST table client-side guarantees the club console and the player app eventually disagree about what a match is doing — and that disagreement is invisible until a player and a manager are on the phone about the same booking.

**The client owns exactly three things:** layout, the countdown tick, and the seat glyph geometry.

## 8.3 The one client-side derivation

Countdown suffixes on the CTA label tick locally between fetches — `Getting in · 42 min` — computed from `serverTime` plus elapsed device time, never from the device clock directly. **The device clock may be wrong; the offset must not compound.**

## 8.4 Which matches appear

```
myMatches:  I hold a seat  AND  I have not left  AND  end + 24h > now
            sorted by start ascending

bestFit:    I hold no seat  AND  starts in the future  AND  filled < capacity
            AND fit is computable
            sorted by fit descending, top 3

fullWorth:  I hold no seat  AND  starts in the future  AND  filled = capacity
            AND fit ≥ 80
            sorted by fit descending, top 1
```

**A settled match stays on Now for 24 hours, then becomes history.** That window covers entering a result, confirming the other side's result, and seeing the level move — three things a player does the morning after, not the minute after.

## 8.5 Caching

| Data | TTL | Invalidated by |
|---|---|---|
| `myMatches` | none — always fresh | — |
| `bestFit` | 60s | Joining or creating a match |
| `fullWorth` | 60s | Joining a waitlist |
| Static strings | build | — |

**`myMatches` is never cached.** It is the reason the screen exists.

---
---

# PART 9 — COPY

*Every string, verbatim. These are not placeholders.*

## 9.1 Header

```
Hi, {firstName}
{city} · {dayName} · {HH:MM}
```

## 9.2 Sections

```
Your matches · {n} · soonest first        swipe →
Best fit for you
Ranked on seven things, not just level
Full, but worth waiting for
These fit you as well as anything above, and seats do come free.
Joining a waitlist costs nothing and commits to nothing.
```

## 9.3 Empty states

**No booked matches**

```
No matches booked
Find a game or create one. You only ever pay your own share,
and the fee is always zero.
```

**Nothing open**

```
Nothing open in {sport} right now
We do not invent players to make a city look busy.
Try another day, or create a match.
```

## 9.4 The copy rules

| Rule | Right | Wrong |
|---|---|---|
| **Name the money, always** | *"You paid 38,00 zł"* | *"Payment confirmed"* |
| **Say what happens next, not what happened** | *"Leaving now returns everything, in minutes"* | *"Cancellation policy applies"* |
| **Never euphemise bad news** | *"The court went back"* | *"Court availability updated"* |
| **Attach the reassurance to the bad news** | *"…We are looking for a replacement. **Your payment will not change.**"* | Two separate messages |
| **Zero is stated, never omitted** | *"· 0 fee"* · *"0,00 zł"* | Silence |
| **Polish number format** | `38,00 zł` — comma, non-breaking space | `38.00 zł` |
| **Second person, active** | *"You paid"* · *"Leaving now returns"* | *"The user has paid"* |
| **No exclamation marks** | *"Ready to play"* | *"You're all set!"* |

**The last one matters more than it looks.** This screen delivers cancellations, court losses and no-shows. A voice that gets excited about good news has no register left for bad news.

---
---

# PART 10 — BUILD ORDER

| # | Deliverable | Blocked by | Done when |
|---|---|---|---|
| **1** | Tokens, type scale, `.card`, `.card-n`, `.tag`, `.chip`, `.btn`, `.hair` | — | Every class matches §2–3 exactly, including the three accessibility overrides |
| **2** | Shell: header, sport bar, scroll column, tab bar | 1 | Header and tabs do not scroll; gutter is 15px; content is 362px |
| **3** | `glyph()` at 46 and 58, light and dark | 1 | All three seat symbols render; your seat is coral and larger; empty is dashed coral |
| **4** | `matchCard` | 1, 3 | Matches the §5.4 anatomy; struck-through price appears only with a card discount |
| **5** | `stateCard` shell — regions A, B, C, F | 1, 3 | Renders from a single state object; facets split correctly |
| **6** | `stateCard` regions D and E — alert and lines | 5 | Volt tick vs hollow ring; alert only when `alert` is non-null |
| **7** | All 32 contexts, driven by data | 5, 6 | A gallery route renders every one; no client-side branching on `key` |
| **8** | `.hstrip` + `.dots` | 5 | One swipe = one card; scroll position survives re-render |
| **9** | Best fit section | 4 | Three cards, fit-descending; empty state copy exact |
| **10** | Full-worth section | 4 | One card, ≥80 only; section absent when none qualifies |
| **11** | Empty, loading, error, offline | 2 | Skeletons match real heights; offline strip renders |
| **12** | Interaction: taps, swipe, refresh, deep links | 8, 9, 10 | All eleven targets; scroll preservation verified |
| **13** | Live updates | 7, 12 | State changes in place, strip does not re-order |
| **14** | Accessibility pass | all | Seven requirements met; all contrast ratios pass AA |

## 10.1 The acceptance gate

- [ ] Every colour, size, radius and spacing value matches Part 2
- [ ] All 32 contexts render correctly from server data alone
- [ ] The client contains no copy of the state table and builds no sentence
- [ ] Scroll position and `.hstrip` position survive a re-render
- [ ] One swipe moves exactly one card
- [ ] The strip never re-orders on a state change
- [ ] `.fit.hi` fires at exactly 90
- [ ] Full-worth requires fit ≥ 80; best fit has no floor
- [ ] Every price reads `38,00 zł` and every card says `· 0 fee`
- [ ] The three accessibility colour overrides are applied
- [ ] `prefers-reduced-motion` kills all animation and transition
- [ ] The screen is usable offline from cached records
- [ ] **The MultiSport card block does not exist anywhere in the codebase**
- [ ] **The string "Even matches" does not exist anywhere in the codebase**

---

*Now screen · 6 blocks · 32 contexts · 14 components · 7 fit factors · 3 empty states · every string specified.*
