# Rakieta Player App — "Now" section · Definitive UI Specification

**Feature in scope:** the complete Now section — the `Now` tab screen (`V.home`), every component it renders, the shell regions it lives in, the two sheets reachable directly from it, and the formatters that produce its strings.

**Source of truth:** `rakietaPlayerPrototype.html` (7 261 lines; `<style>` = lines 18–332; `<script>` = lines 369–7 259). Two supporting documents were read for cross-checking only and are cited as `DOC` where they disagree with the prototype: `rakieta-player-app-documentation-v37.md`, `5-now_screen_architecture_review.md`. **Where the prototype and the documents disagree, the prototype wins and the disagreement is recorded.**

**Target stack:** `[GAP: the brief's [TARGET_STACK] placeholder was never substituted. Recommended default — React Native (Expo) + TypeScript, per `5-now_screen_architecture_review.md` §E1, which states the player app is "Expo with a typed theme object, a locked design system under ADR-0012". All prop signatures below are written for that. Decision to ratify.]`

**Late-override audit (protocol step 3).** Every reassignment in the file was located. Seven exist, five of which change Now:

| Reassigned | Line | Affects Now? | Composed behaviour |
|---|---|---|---|
| `deadlines` | 6211 | **Yes** | Reads `pol(club)` instead of `CLUBS[club]`; `commit = min(start − policy.window·h, start − 12h)`; `joinCut` from policy |
| `courtHold` | 6227 | **Yes** | Wraps the ladder: adds `why:'stale'` (club max hold age) and `why:'extended'` (club demand hold). May only ever *extend* |
| `matchState` | 6264 | **Yes** | Wraps the 33-key resolver: re-routes to `heldStale` / `heldExtended` when `courtHold().why` says so |
| `payable` | 6316 | **Yes** | Now `shareAfterDisc(m) − cardOff`, i.e. slot discounts are applied. **`cardOff` was not similarly wrapped** — see §G |
| `freshState` | 6345, 7018 | **Yes** (indirect) | Adds ecosystem state (`eco`, `member`, `queues`…) then intent state (`optIn`, `intent`) |
| `render` | 6953 | **Yes** | Calls the original, then injects an unread-count badge into the Inbox tab button |
| `V.*` (7 views) | 6704–7224 | No | `wallet`, `score`, `match`, `courts`, `onboard`, `you`, `intent` — none is `home` |

**`V.home` is defined once, at line 1578, and is never reassigned.** The Now screen is therefore its first and only definition, composed with the five overridden helpers above.

---

# A. FOUNDATIONS

## A1. Colour

### A1.1 Declared custom properties

All from `:root`, lines 21–30. Every one is listed; the "Used in Now" column is the audit.

| Token | Hex | Role | Used in Now |
|---|---|---|---|
| `--paper` | `#F4F2ED` | app background behind the scroll body | Yes — `#phone` background |
| `--paper2` | `#EDEAE3` | second paper, popover close button | No |
| `--surface` | `#FFFFFF` | card surface | Declared but **never referenced**; cards hardcode `#fff` |
| `--ink` | `#101B20` | primary text | Yes — body default, `NOW` pill, chip-on |
| `--night` | `#0A3441` | dark surface / inverted card | Yes — `.card-n` (state card), `.btn.n`, `.avat`, toast, balance bar |
| `--night2` | `#12495B` | second dark, deep teal | Not in Now (balance bar only) |
| `--muted` | `#6E7F85` | secondary text, eyebrow, section heading | Yes — heavily |
| `--line` | `#E5E1D8` | card border, hairline | Yes |
| `--line2` | `#F0EDE6` | soft fill, inner hairline, tag default bg | Yes |
| `--coral` | `#E8482B` | **brand / "yours"** — active tab, focus ring, fit-high, seat-that-is-you | Yes |
| `--coral-soft` | `#FDEBE6` | coral soft background | Yes — `.tag.hot` |
| `--coral-ink` | `#B8351C` | coral text on coral-soft | Yes — `.tag.hot` text |
| `--mint` | `#0C8F6B` | success / safe state | Yes — `.tag.ok`, tone `good` |
| `--mint-soft` | `#E2F3EC` | mint soft background | Yes — `.tag.ok`, MultiSport card |
| `--amber` | `#9A6A0B` | time-pressure state | Yes — tone `time` |
| `--amber-soft` | `#FBF0DA` | amber soft background | Yes — `.tag.warn` |
| `--red` | `#B4392C` | terminal / bad state | Yes — tone `ended`, `.tag.bad` |
| `--red-soft` | `#FBEAE7` | red soft background | Yes — `.tag.bad` |
| `--volt` | `#D9F24B` | affirmation mark on dark only | Yes — the `✓` in state-card lines |
| `--info` | `#12495B` | information (deliberately the deep teal, **not** a new blue — comment at line 27) | Not in Now |
| `--info-soft` | `#EAF1F4` | info background | Not in Now |
| `--info-line` | `#C7DBE3` | info border | Not in Now |
| `--pad` | `#E8482B` | sport: Padel (= coral) | Yes — sport chip dot, match card sport tag |
| `--ten` | `#0C8F6B` | sport: Tennis (= mint) | Yes |
| `--squ` | `#12495B` | sport: Squash (= info/night2) | Yes |
| `--bad` | `#9A6A0B` | sport: Badminton (= amber) | Yes |

**Sport colours are aliases of state colours** `[SRC: :root lines 29–30]`. A Tennis dot and a "good" tone dot are the same pixel value. `[DERIVED]` This violates the rule the review quotes from the Now spec — *"a colour used for two things is a colour that means nothing"* `[SRC: 5-now_screen_architecture_review.md §E1]`. Recommendation in §G.

### A1.2 Non-token colour literals used inside Now

Every one of these is an inline value in a template literal or a utility class and must be promoted.

| Literal | Where | Meaning | Promote to |
|---|---|---|---|
| `#08222B` | `html,body` background `[SRC: line 32]` | stage backdrop outside the phone | `--stage` |
| `#24505E` | `#phone` border `[SRC: line 79]` | device bezel | prototype-only, delete |
| `#071C24` | `#rail`, `#mtop` `[SRC: lines 61, 265]` | scenario rail | prototype-only, delete |
| `#EEF2F1` | `glyph()` court fill, light `[SRC: line 1291]` | court surface | `--court-fill` |
| `#D8DFDD` | `glyph()` court line, light `[SRC: line 1291]` | court outline / net | `--court-line` |
| `#0A3441` | `glyph()` occupied seat, light `[SRC: line 1292]` | duplicate of `--night` | `--night` |
| `#E8482B` | `glyph()` "me" seat and empty-seat stroke `[SRC: lines 1302, 1305]` | duplicate of `--coral` | `--coral` |
| `rgba(255,255,255,.1 / .3)` | `glyph()` fill/line, dark `[SRC: line 1291]` | on-night court | `--on-night-fill-08`, `--on-night-line-30` |
| `#CFE7DD` | MultiSport card border `[SRC: line 1608]` | mint-soft border | `--mint-line` |
| `rgba(214,77,58,.16)` / `rgba(214,77,58,.4)` | state-card alert box `[SRC: line 4000]` | **`#D64D3A` is not `--red` (`#B4392C`)** | `--red` at 16 % / 40 % |
| `rgba(255,255,255,.15)` | `.card-n .hair`, state-card column divider `[SRC: lines 134, 3996]` | on-night hairline | `--on-night-line-15` |
| `rgba(255,255,255,.17)` | `.tag.w`, `.btn.w` `[SRC: lines 148, 194]` | on-night chip fill | `--on-night-fill-17` |
| `rgba(255,255,255,.75)` | unchecked bullet ring in state-card lines `[SRC: line 4006]` | on-night outline | `--on-night-line-75` |
| `rgba(255,255,255,.92)` | state-card line text `[SRC: line 4007]` | on-night body | `--on-night-ink` |
| `rgba(255,255,255,.68)` | `.card-n .tiny` `[SRC: line 133]` | on-night secondary | `--on-night-ink-2` |
| `rgba(255,255,255,.52)` | `.card-n .eyebrow` `[SRC: line 134]` | on-night tertiary | `--on-night-ink-3` |
| `rgba(255,255,255,.45)` | `ST_TONE.idle` `[SRC: line 3530]` | idle tone dot | see §G — **broken on light surfaces** |
| `rgba(10,52,65,.45)` | `#scrim` `[SRC: line 232]` | sheet scrim | `--scrim` |

### A1.3 Semantic state families

`ST_TONE` `[SRC: line 3529]` maps a state's `tone` to one dot colour. This is the only place tone becomes pixels.

| Tone | Dot colour | Soft bg (paired class) | Border | Text |
|---|---|---|---|---|
| `good` | `--mint` `#0C8F6B` | `--mint-soft` `#E2F3EC` (`.tag.ok`) | `#CFE7DD` (inline, MultiSport only) | `--mint` |
| `watch` | `--coral` `#E8482B` | `--coral-soft` `#FDEBE6` (`.tag.hot`) | none | `--coral-ink` `#B8351C` |
| `time` | `--amber` `#9A6A0B` | `--amber-soft` `#FBF0DA` (`.tag.warn`) | none | `--amber` |
| `ended` | `--red` `#B4392C` | `--red-soft` `#FBEAE7` (`.tag.bad`) | none | `--red` |
| `idle` | `rgba(255,255,255,.45)` | `--line2` (`.tag` default) | none | `--muted` |

`[DERIVED]` The soft/border/text triple is complete only for `watch`; the other families borrow. `idle` has **no light-surface dot colour at all**, which is a defect, not a design (§G).

### A1.4 Dark-surface repaints

`.card-n` (`background: --night; color: #fff`) repaints its descendants `[SRC: lines 132–135]`:

- `.card-n .tiny` → `rgba(255,255,255,.68)`
- `.card-n .eyebrow` → `rgba(255,255,255,.52)`
- `.card-n .hair` border → `rgba(255,255,255,.15)`
- `.card-n .ipop .tiny / .eyebrow / .mono` → repainted **back** to light values, because a popover inside a dark card is a white box `[SRC: lines 326–328]`

Inside the state card, four further inline overrides fight the repaint: the Court and Group values force `color:#fff; font-weight:600`, and the line text forces `rgba(255,255,255,.92)` `[SRC: lines 3995–4007]`. `[DERIVED]` The production component must expose an `onDark` context rather than re-specifying colour per slot.

## A2. Typography

### A2.1 Families

| Family | Weights loaded | For |
|---|---|---|
| **Archivo** | 400, 500, 600, 700 | all UI text, headings, body, labels `[SRC: line 19 @import; line 32 body]` |
| **IBM Plex Mono** | 400, 500, 600 | **numerals, clock times, money, seat counts, IDs, door codes** — applied via `.mono`, which also sets `font-variant-numeric: tabular-nums` `[SRC: line 34]` |

Fallbacks: `system-ui, sans-serif` and `ui-monospace, monospace`.

`.num` `[SRC: line 35]` is an orthogonal *numeric treatment*, not a family: `font-weight:700; letter-spacing:-.035em; font-variant-numeric:tabular-nums`. It is combined with `.mono` for money (`.mono.num`, matchCard price) and used **alone** for the 30 px start time on the state card — which therefore renders in **Archivo**, not Plex Mono `[SRC: line 3992]`. That is a deliberate-looking asymmetry and is listed in §G.

### A2.2 Every size/weight/tracking pairing used by Now

| px | Weight | Tracking | Line-height | Family | Named class / inline origin | Used for |
|---|---|---|---|---|---|---|
| 30 | 700 | −.035em | 1 | Archivo | `.num` + inline `font-size:30px;line-height:1` `[SRC: 3992]` | state-card start time |
| 19 | 700 | −.03em | default | Archivo | `.h1` `[SRC: 122]` | screen title "Hi, Tomek" |
| 15 | 700 | −.025em | default | Archivo | `.h2` `[SRC: 123]` | MultiSport plan name |
| 14 | 700 | −.035em | default | Plex Mono | `.mono.num` + inline `font-size:14px` `[SRC: 1420]` | match-card payable amount |
| 13 | 700 | — | default | Archivo | `.empty b` `[SRC: 230]` | empty-state headline |
| 12.5 | 700 | −.02em | 1.3 | Archivo | `.ipop-t` `[SRC: 322]` | popover title (not on Now) |
| 12 | 700 | — | default | Plex Mono | inline `font-size:12px;font-weight:700` `[SRC: 1401]` | match-card `when()` line |
| 12 | 600 | — | default | Archivo | inline `font-size:12px;font-weight:600` `[SRC: 3993]` | state-card when · club line |
| 12 | 700 | — | — | Archivo | `.btn` `[SRC: 188]` | all buttons |
| 11.5 | 700/600 | — | 1.4 | Archivo | `.rl`, timeline copy `[SRC: 199]` | not on Now |
| 11 | 400 | — | 1.45 | Archivo | `.tiny` `[SRC: 124]` | every secondary line |
| 11 | 400 | — | 1.45 | Plex Mono | `.tiny.mono` `[SRC: 1409, 3994]` | seat count `3/4` |
| 11 | 400 | — | 1.35 | Archivo | inline `line-height:1.35` `[SRC: 3995]` | state-card Court / Group values |
| 11 | 400 | — | 1.45 | Archivo | inline `line-height:1.45` `[SRC: 4001]` | state-card alert text |
| 11 | 700 | — | — | Archivo | `.fit` `[SRC: 184]` | fit badge |
| 10.5 | 600 | — | — | Archivo | `.chip` `[SRC: 153]` | full-size chip |
| 10 | 600 | — | — | Archivo | `.chip.sm` `[SRC: 158]` | sport chips (the ones Now uses) |
| 10 | 400 | — | 1.5 | Archivo | inline `font-size:10px` `[SRC: 4005]` | the `✓` mark |
| 9.5 | 700 | .15em, uppercase | — | Archivo | `.eyebrow` `[SRC: 120]` | header eyebrow |
| 9.5 | 700 | .15em, uppercase | — | Archivo | `.sect` `[SRC: 228]` | section headings |
| 9.5 | 700 | — | — | Archivo | `.tag` `[SRC: 144]` | every tag |
| 8.5 | 700 | .15em, uppercase | — | Archivo | `.eyebrow` + inline `font-size:8.5px` `[SRC: 3995–3998]` | state-card Court / Group labels |
| 8.5 | 600 | — | — | Archivo | `.tab` `[SRC: 88]` | tab-bar labels |

**Do not normalise silently.** Body text in this feature exists at **11 px, 11.5 px, 12 px and 12.5 px**; eyebrows at **8.5 px, 9.5 px and 10.5 px** (`.flab`). Consolidation proposal is in §G, not here.

### A2.3 Numeric treatments

- Tabular numerals everywhere `.mono` or `.num` is applied — so a re-render at a clock tick never reflows a card `[SRC: lines 34–35]`.
- Negative tracking is applied at exactly two thresholds: −.035em on `.num` (any size) and −.03em / −.025em on `.h1` / `.h2`.
- The 30 px start time is the only figure in the feature large enough for the tracking to be visible; it is also the only one **not** in the mono family.

## A3. Spacing, radius, elevation, borders

### A3.1 Spacing values in use (Now only)

`2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18, 30`

| Purpose | Value | Origin |
|---|---|---|
| Screen gutter (scroll body) | `15px` | `#scroll{padding:0 15px 14px}` `[SRC: 84]` |
| Header bar padding | `12px 15px 9px` | `.pbar` `[SRC: 117]` — **additive to the gutter, so the title sits 30 px from the frame edge while cards sit at 15 px** `[DERIVED]` |
| Sport bar padding | `0 15px 9px` | inline in `sportbar()` `[SRC: 1564]` — same 30 px problem |
| Card → card gap | `9px` | `.card{margin-bottom:9px}` `[SRC: 129]` |
| Card padding, default | `12px` | `.card` `[SRC: 129]` |
| Card padding, match card | `11px` | inline `style="padding:11px"` `[SRC: 1396]` |
| Card padding, state card | `13px` | inline `style="padding:13px"` `[SRC: 3989]` |
| Card padding, dark default | `14px` | `.card-n` `[SRC: 132]` |
| Hairline block | `margin-top:9px; padding-top:8px` | `.hair` `[SRC: 136]` |
| Section heading | `margin:14px 0 7px` (first child `2px` top) | `.sect` `[SRC: 228–229]` |
| Strip gap | `10px` | `.hstrip{gap:10px}` `[SRC: 174]` |
| Dots block | `gap:5px; margin:-2px 0 11px` | `.dots` `[SRC: 180]` |
| Tag padding | `3px 7px`, gap `4px` | `.tag` `[SRC: 144]` |
| Chip padding | `0 11px` (sm `0 8px`), gap `5px` (sm `4px`) | `.chip` `[SRC: 153, 158]` |
| Button padding | `0 14px` | `.btn` `[SRC: 188]` |
| Empty state | `30px 18px` (feed variant overridden inline to `18px`) | `.empty` `[SRC: 229]`, inline `[SRC: 1615]` |

`[DERIVED]` Implied scale: **odd-numbered 2 · 5 · 7 · 9 · 11 · 13 · 15** for internal rhythm, even numbers only for icon geometry. This is unusual but consistent; do not "round it to a 4 pt grid" without ratifying §G.

### A3.2 Radius, by component size

Radius is a function of the element's size, not a single token.

| Component | Radius | Origin |
|---|---|---|
| Phone frame | `34px` | `#phone` `[SRC: 79]` |
| Sheet | `22px 22px 0 0` | `#sheet` `[SRC: 233]` |
| Dark card (`.card-n`) | `15px` | `[SRC: 132]` |
| Light card (`.card`) | `13px` | `[SRC: 129]` |
| Toast | `12px` | `.tst` `[SRC: 249]` |
| Button, segmented control | `10px` | `.btn`, `.seg` `[SRC: 188, 205]` |
| Avatar, alert box, hold row | `9px` | `.avat`, inline `[SRC: 216, 4000]` |
| Fit badge | `7px` | `.fit` `[SRC: 184]` |
| Tag | `6px` | `.tag` `[SRC: 144]` |
| Tab icon square | `5px` (fab `10px`) | `.tab i` `[SRC: 89–90]` |
| Court glyph outline | `4px` (`rx="4"`) | `glyph()` `[SRC: 1307]` |
| Dots, seat dots, tone dots | `50 %` (`border-radius: 3px` on a 6 px box, `4px` on 8 px, `5px` on 9 px) | various inline |
| Chip | `999px` | `.chip` `[SRC: 153]` |

`[DERIVED]` The mapping is: **radius ≈ 0.09 × the element's shorter side, clamped to the ladder 4 · 5 · 6 · 7 · 9 · 10 · 12 · 13 · 15 · 22 · 34.**

### A3.3 Elevation

Inside the phone, the Now section uses **no shadows at all**. Separation is done entirely with 1 px borders and the dark-card inversion. The only shadows in the shell are:

| Element | Shadow |
|---|---|
| `#phone` | `0 40px 90px -40px rgba(0,0,0,.8)` `[SRC: 80]` — prototype chrome only |
| `#sheet` | `0 -20px 40px -22px rgba(10,32,40,.6)` `[SRC: 234]` |
| `.tst` (toast) | `0 12px 28px -12px rgba(0,0,0,.6)` `[SRC: 250]` |
| `.ipop` | `0 12px 30px rgba(11,31,42,.24)` `[SRC: 315]` — not on Now |

`[DERIVED]` **Elevation is a refusal in this design**: only things that float above the app (sheet, toast, popover) cast anything. Carry that rule forward.

### A3.4 Borders

| Use | Value |
|---|---|
| Card outline | `1px solid var(--line)` |
| Inner hairline | `1px solid var(--line2)` (`.hair`, `.rl + .rl`) |
| Dark inner hairline | `1px solid rgba(255,255,255,.15)` |
| Alert box | `1px solid rgba(214,77,58,.4)` |
| MultiSport card | `1px solid #CFE7DD` (inline) |
| Chip | `1px solid var(--line)`, `--ink` when on |
| Tab bar / CTA bar | `border-top: 1px solid var(--line)` |
| Vertical divider (state card) | a `1px`-wide `<div>` with `background: rgba(255,255,255,.15)`, **not** a border `[SRC: 3997]` |

## A4. Motion

| Name | Keyframe | Duration · easing | Trigger |
|---|---|---|---|
| `rise` | `opacity 0 → 1`, `translateY(7px) → 0` | `.3s cubic-bezier(.2,.8,.2,1) both` | applied to **every direct child of `#scroll`** `[SRC: 256–257]`. On Now that is exactly three nodes — the header bar, the sport bar, and `#scroll-inner` — so the entire feed rises as **one block**, not per card `[DERIVED]` |
| `up` | `translateY(100%) → 0` | `.26s cubic-bezier(.2,.8,.2,1)` | sheet presentation `[SRC: 241]` |
| `up` (reused) | same | `.24s` | toast entry `[SRC: 249]` |
| `fade` | `opacity 0 → 1` | `.2s` | sheet scrim `[SRC: 242]` |
| `ipop` | `opacity 0 → 1`, `translateY(-4px) → 0` | `.13s cubic-bezier(.22,.8,.3,1)` | info popover (not on Now) |
| Card hover | `transform: translateY(-1px)`, border → coral | `transition: .12s` | `.card.tap:hover`, `.card-n.tap:hover` `[SRC: 130–131]` — pointer only |
| Button hover | `filter: brightness(1.06)` | `.12s` | `.btn:hover` `[SRC: 189]` |
| Avatar press | `transform: scale(.93)` | `.12s` | `.hold:active .avat` `[SRC: 221]` |
| Long-press ring | `box-shadow: 0 0 0 3px var(--coral-soft)` | none (instant) | `.holding` class added on pointerdown `[SRC: 223]` |
| Toast exit | `opacity → 0` | `.3s`, starts at **2 600 ms**, node removed at **+320 ms** `[SRC: 1552–1556]` |
| Scroll | `scroll-behavior: smooth` on `#scroll` `[SRC: 84]` |
| Rail drawer (≤900 px) | `transform` | `.26s cubic-bezier(.4,0,.2,1)` — prototype chrome |

**Reduced motion:** `@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}` `[SRC: line 258]` — a single global kill. `[DERIVED]` Nothing is given a reduced-motion *substitute* (no cross-fade, no instant-but-still-present state change); production must decide whether the sheet still slides.

## A5. Iconography and glyphs

### A5.1 `glyph()` — the programmatic court diagram

The only real illustration in the feature. `[SRC: lines 1289–1308]`

**Signature:** `glyph(sport, seats[], w, dark)`

| Parameter | Derivation |
|---|---|
| height | `w × 0.62` for Squash, `w × 0.56` otherwise |
| padding | `w × 0.05` |
| seat positions, Squash | `[.38w, .62h]`, `[.62w, .42h]` (staggered, same side of the line) |
| seat positions, 2 players | `[.22w, .5h]`, `[.78w, .5h]` |
| seat positions, 4 players | `[.21w,.3h] [.21w,.72h] [.79w,.3h] [.79w,.72h]` |
| net, Squash | one horizontal line at `.55h`, stroke `1.2` |
| net, others | centre vertical at `w/2` stroke `1.4`, plus service lines at `.3w` and `.7w` stroke `0.8` |
| seat = `'me'` | filled circle `r = .082w`, `#E8482B` |
| seat = `'g'` (guest) | hollow circle `r = .075w`, stroke `1.6`, colour `on` |
| seat = other player | filled circle `r = .075w`, colour `on` |
| seat = `null` (open) | hollow circle `r = .075w`, stroke `1.4`, `#E8482B`, `stroke-dasharray "2.5 2.5"` |
| frame | `rect rx=4`, fill `fill`, stroke `ln` |

Sizes used in Now: **`w = 58`, `dark = true`** (state card) and **`w = 46`, `dark = false`** (match card).

Seat symbols come from `seatSyms(m)` `[SRC: 1389]`: `'me' | 'g' | 'x' | null` per seat, in seat order.

### A5.2 Character glyphs (no icon font, no SVG)

| Glyph | Codepoint | Where | Meaning |
|---|---|---|---|
| `✓` | U+2713 | state-card line, `--volt`, 10 px | this fact is already true |
| (ring) | — | state-card line, 7 px hollow circle, `1.5px` `rgba(255,255,255,.75)` | this fact is not yet true |
| `✦` | U+2726 | fit badge prefix | match fit score |
| `✉` | U+2709 | state-card secondary button | go to Inbox |
| `⌘` | U+2318 | state-card tertiary button | open the Getting-in sheet |
| `→` | U+2192 | "swipe →" hint | the strip is horizontally scrollable |
| `·` | U+00B7 | **the universal metadata separator**, always spaced ` · ` | see §F |
| `−` | U+2212 | `lvl()` negative sign, `card −15,00 zł` | true minus, never a hyphen |
| `—` / `–` | U+2014 / U+2013 | state copy | consequence clause / numeric range |
| `‹` `›` | U+2039 / U+203A | back affordance, chevron | navigation |
| `▮` | U+25AE | status bar signal bars | prototype chrome |

`[GAP]` The five tab-bar icons do not exist. `.tab i` renders a **16 px rounded square of `currentColor`** as a placeholder `[SRC: line 89]`; the create tab is a 28 px coral square `[SRC: line 90]`. Recommended default: commission five outline icons at 24 px on a 24 px canvas, 1.75 px stroke, and keep the coral filled circle for create. **Decision to ratify.**

---

# B. COMPONENT INVENTORY

Ordered as the screen composes them.

---

## B1. `ScreenHeader` (`head()`)

**Purpose.** The screen title block. On Now it is the greeting and the current place/day/time.
**Source.** `[SRC: head(), line 1558]`, `.pbar` `[SRC: line 117]`

**Anatomy (DOM order).**
1. `.back` button — *omitted on Now* (`showBack` falsy)
2. `.t` — flex:1, min-width:0
   a. `.eyebrow` (optional)
   b. `.h1`
3. `right` slot — *unused on Now*

**Now's content:** eyebrow `Kraków · Saturday · 14:00` = `'Kraków · ' + dowl(S.now) + ' · ' + hm(S.now)`; title `Hi, Tomek` (hardcoded) `[SRC: line 1580]`.

**Variants.** `withBack` · `withRightSlot` · `plain` (Now uses plain).
**States.** Rest only. Back button has `:focus-visible` (2 px coral, 2 px offset) because it is a real `<button>`.
**Content rules.** No truncation is specified. `.t{min-width:0}` allows shrink but no `text-overflow` is set, so a long title wraps to two lines and pushes the layout `[DERIVED]`.
**Tokens.** padding `12px 15px 9px`; eyebrow 9.5/700/.15em/uppercase/`--muted`; title 19/700/−.03em/`--ink`; title `margin-top:2px`.

```ts
type ScreenHeaderProps = {
  title: string;
  eyebrow?: string;
  onBack?: () => void;          // renders the ‹ affordance when present
  right?: React.ReactNode;      // trailing slot, vertically centred
};
```

---

## B2. `SportFilterBar` (`sportbar()`)

**Purpose.** One-tap filter across `all` + the four sports. Shared with Find; identical markup.
**Source.** `[SRC: sportbar(), line 1563]`

**Anatomy.** `.row` (flex, `flex-wrap:nowrap`, `overflow:auto`, inline padding `0 15px 9px`) → 5 × `.chip.sm` buttons in the order **All · Padel · Tennis · Squash · Badminton** `[SRC: SPORTS, line 374]`. Each non-`all` chip carries a leading `6px × 6px`, `border-radius:2px` swatch in that sport's colour; `sm` shrinks the swatch to `5px`.

**Variants / states.**

| State | Treatment |
|---|---|
| Rest | `background:#fff; border:1px solid var(--line); color:--ink` |
| Selected (`.on`) | `background:--ink; color:#fff; border-color:--ink` |
| Hover | not styled (inherits) |
| Focus-visible | 2 px `--coral` outline, 2 px offset (real `<button>`) |
| Disabled | not implemented |

**Interaction.** `data-act="sport"`, `data-v="{all|Padel|Tennis|Squash|Badminton}"` → `ACT.sport` sets `S.sport` **and clears `S.durs`**, then re-renders `[SRC: line 4504]`.
**Content rules.** `white-space:nowrap`; the row scrolls horizontally. Its scroll offset is **not** preserved across re-render (only `.sqrow` offsets are) `[SRC: render(), line 4277]` — see §G.
**Tokens.** height 25 px (`sm`), padding `0 8px`, gap 4 px, font 10/600, radius 999.

```ts
type SportFilterBarProps = {
  value: 'all' | Sport;
  sports: Sport[];                      // colour comes from the sport token map
  onChange: (v: 'all' | Sport) => void;
};
```

---

## B3. `SectionHeading` (`.sect`)

**Purpose.** Names each band of the feed.
**Source.** `[SRC: .sect, line 228]`, three usages in `V.home` `[SRC: 1594, 1611, 1619]`

**Two forms:**

| Form | Markup | Used for |
|---|---|---|
| Plain | `<div class="sect">Even matches for you</div>` | "Even matches for you", "Full, but worth waiting for" |
| Split | `.sect` + inline `display:flex; justify-content:space-between; align-items:baseline`, containing a `<span>` label and a `<span class="tiny">` hint with `letter-spacing:0; text-transform:none` | "Your matches · 3 · soonest first" + "swipe →" |

**Tokens.** 9.5/700/.15em/uppercase/`--muted`; `margin:14px 0 7px`; `:first-child` → `margin-top:2px`; the first heading in Now is additionally forced to `margin-top:0` inline `[SRC: 1594]`.

```ts
type SectionHeadingProps = { label: string; hint?: string };   // hint renders un-tracked, sentence case
```

---

## B4. `MatchStrip` (`.hstrip`) + `PageDots` (`.dots`) + `GalleryCaption`

**Purpose.** The enrolled-match carousel — one full-width state card per page.
**Source.** `[SRC: .hstrip lines 174–179, .dots 180–182, V.home 1596–1600, wireStrip() 4302]`

**Anatomy.**
1. `.hstrip` — `display:flex; gap:10px; overflow-x:auto; scroll-snap-type:x mandatory; margin:0 -15px 10px; padding:1px 15px 5px; scrollbar-width:none`
2. children — `scroll-snap-align:center; scroll-snap-stop:always; flex:0 0 100%; margin-bottom:0 !important`
3. `.dots` — rendered only when `shown.length > 1`; `gap:5px; justify-content:center; margin:-2px 0 11px`
4. `.dots i` — `5×5px`, radius 3, `--line`; active `i.on` → `--coral` **and width 14px** (a pill, not a dot)
5. `#galcap` — gallery mode only, `.tiny`, centred, `margin:-5px 0 11px`, text = `tag — ctx`

**Geometry `[DERIVED]`.** Phone content width 390 px (392 − 2×1 px border) → `#scroll` content box 360 px → `.hstrip` (−15 px margins) is 390 px wide with 15 px padding → each child is `flex-basis:100%` of the 360 px content box = **360 px**, step = 360 + 10 = **370 px**. `wireStrip()` computes the active dot as `round(scrollLeft / (firstChild.offsetWidth + 10))`, which matches exactly.

**Peek affordance.** With snap-align `center` and a 360 px card in a 390 px viewport, **15 px of the next card shows on each side**. That, plus the "swipe →" hint, is the entire affordance.

**Interaction.** A passive `scroll` listener is attached on every render; it updates the dots and, in gallery mode, rewrites the caption from `matchState(list[i])` `[SRC: 4302–4315]`.
**Position preservation.** **None.** `render()` restores `.sqrow` horizontal offsets only, so any re-render (a clock tick, a sport change, any action) snaps the strip back to card 1 and repaints the dots with index 0 active `[SRC: 4277, 4281]`. §G.

```ts
type MatchStripProps<T> = {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  showDots?: boolean;              // default: items.length > 1
  caption?: (index: number) => string | undefined;
  initialIndex?: number;           // production must own this; the prototype cannot
  onIndexChange?: (i: number) => void;
};
```

---

## B5. `StateCard` — the primary component of the feature

**Purpose.** One enrolled match, rendered as the whole truth about it: tag, time, place, court state, group state, any alert, the fact list, and the actions.
**Source.** `[SRC: stateCard(), lines 3987–4018]`. Data from `matchState(m)` `[SRC: 3929 + override 6264]`.

**Anatomy (DOM order).**

| # | Slot | Content | Tokens |
|---|---|---|---|
| 1 | Header row | left `.tag.w` with tone dot + `st.tag`; right `.eyebrow` `{sport} · {fmt}`, `white-space:nowrap` | `justify-content:space-between; gap:8px; margin-bottom:8px` |
| 2 | Identity row | left column: `.num` 30 px start time → 12/600 `when(start) · club.n` → `.tiny` `club.court · {dur} min`; right column: `glyph(sport, seats, 58, dark)` + `.tiny.mono` `filled/n` (`margin-top:3px`) | `align-items:flex-start`; left `min-width:0`; right `flex-shrink:0; text-align:right` |
| 3 | Facet row (`.hair`) | two equal columns split by a 1 px `rgba(255,255,255,.15)` divider. Left: `.eyebrow` **Court** + value. Right: `.eyebrow` **Group** + value | `display:flex; gap:10px`; eyebrows forced to 8.5 px; values `#fff/600/line-height 1.35` |
| 4 | Alert (conditional, `st.alert`) | 7 px red dot + text; may contain `<b>` | `padding:8px 10px; radius 9px; bg rgba(214,77,58,.16); border 1px rgba(214,77,58,.4); margin-top:9px`; text 11/1.45/`#fff` |
| 5 | Line list (`.hair`) | one row per `st.lines` entry: `[done, text]`. `done=1` → volt `✓` (10 px, line-height 1.5); `done=0` → 7 px hollow ring, `margin-top:4px` | row `gap:7px; padding:2px 0`; text `.tiny` at `rgba(255,255,255,.92)` |
| 6 | Action row | `.btn.p` flex:1 (label `st.cta.label ?? 'Open match'`, `+ ' · ' + st.left` if present) · `.btn.w` 40 px `✉` → Inbox · `.btn.w` 40 px `⌘` → access sheet, **omitted when `st.post` is set** | `.row; margin-top:11px; flex-wrap:nowrap`; buttons `height:34px` |

**Variants.** One structural variant, driven by `st.post` (the six after-the-match contexts) which drops the `⌘` button. Everything else varies by *content*, not by structure.

**Tone → dot colour** is the only per-state visual difference: `ST_TONE[st.tone]` on the `.tag.w` dot. **The card's background never changes with state.**

**Interaction states.**

| State | Treatment |
|---|---|
| Rest | `.card-n` night surface, radius 15, padding 13 |
| Hover | `.card-n.tap:hover{transform:translateY(-1px)}` (no border change — the dark card has no border) |
| Active / pressed | not specified `[GAP]` — recommend `scale(.99)`, 120 ms |
| Focus-visible | **impossible**: the card is a `<div>`, the CTAs are `<span>`s. §E |
| Disabled / loading / error | never rendered `[GAP]` |
| Selected | n/a |

**Content rules.** No `max-lines`, no `text-overflow`, no clamp anywhere in the card. The Court value routinely runs to two lines (`"Held · Mondo — held until 12h before play"`), and `cancelledClub`'s Group value is the single word `everybody refunded`. Lines lists are 3–5 entries; the longest observed is 5 (`heldSoft`, `heldStale`, `heldExtended`, `clubHeld`) `[SRC: ST table]`.

**Every state's exact payload** is tabulated in §B6.

```ts
type Tone = 'good' | 'watch' | 'time' | 'ended' | 'idle';

type StateCardProps = {
  tag: string;                       // e.g. 'Court protected'  — the truth about the group
  tone: Tone;                        // maps to the dot colour only
  sport: Sport;
  format: string;                    // 'Doubles' | 'Singles'
  startTime: string;                 // pre-formatted 'HH:mm'
  whenLabel: string;                 // 'Today · 18:30' | 'Sat · 18:30'
  clubName: string;
  courtLabel: string;                // club.court, e.g. 'Court 2 · Mondo'
  durationMin: number;
  seats: Array<'me' | 'guest' | 'other' | null>;
  filled: number;
  capacity: number;
  court: string;                     // facet 1 value
  group: string;                     // facet 2 value
  alert?: RichText;                  // supports one <b> emphasis span
  lines: Array<{ done: boolean; text: RichText }>;
  cta?: { label: string; target: Route };      // default { label: 'Open match', target: match }
  ctaSuffix?: string;                          // rendered as ' · {suffix}'
  showAccess?: boolean;                        // false for post-match contexts
  onPress: () => void;
  onInbox: () => void;
  onAccess: () => void;
};
```

---

## B6. `matchState()` — the state resolver and its 35 payloads

**Purpose.** Turns a match record plus the clock into the card's entire content. **This is a formatting decision as much as a logic one and must be specified exactly.**
**Source.** `[SRC: matchState() 3929; ST table 3557–3844; override 6264; ST.heldStale/heldExtended 6245–6262]`

### B6.1 Resolution order (order *is* the specification)

`syncMatch(m)` runs first (mutates the record), then, in this exact order `[SRC: 3936–3966]`:

1. `m.forced` → gallery short-circuit (prototype only)
2. `inventoryLost`
3. `clubCancelled || weather` → `cancelledClub`
4. `formCancelled` → `cancelledIncomplete`
5. `checkpointCancelled` → `cancelledCheckpoint`
6. `now ≥ end` → `playedNoShow` / `playedShort` / `completed` / `playedNoScore` / `confirmResult` / `needsResult`
7. not my seat **and** on waitlist → `waitlisted`
8. `kind === 'private'` → `privateOpen` / `privatePartial` / `privateReserved`
9. `vacated && committedAt != null` → `replacementTransfer` / `rescueLate` / `rescue` / `replacement`
10. `vacated` → `protectedBack` / `formingBack`
11. `isFull` → `ready` (≥ T−15 m) / `confirmedOnFill` / `confirmed` / `full`
12. `isProtected` → `clubHeld` / `heldSoft` / `protectedLate` / `protectedCourt`
13. `releasedAt != null && filled ≥ 2 && now < check` → `heldReleased`
14. any seat present-but-unpaid → `formingHeld`
15. `now ≥ commit` → `formingLate`
16. else → `forming`

Then the **override** `[SRC: 6264]` re-routes:
- `courtHold().why === 'stale'` and key ∈ {`heldReleased`, `forming`, `formingLate`} → `heldStale`
- `courtHold().why === 'extended'` and key ∈ {`heldReleased`, `forming`, `formingLate`, `heldSoft`} → `heldExtended`

**Non-member rewrite** `[SRC: 3968–3973]`: if the viewer has no seat (and the state is not `waitlisted`), every line beginning `You paid` is replaced with `Your share would be {payable} · booking fee 0,00 zł`. This is why the same state reads differently to a browser and a member.

### B6.2 The 17 tags

`Forming · Court held · Court released · Court committed · Court protected · Full · Confirmed · Replacement pending · Rescue active · Ready to play · Needs result · Confirm the result · Completed · Played · On standby · Reserved · Cancelled`

### B6.3 Every context, its tag, tone, and both facets

| Key | Tag | Tone | Backend (`be`) | Court facet | Group facet | Alert | `post` |
|---|---|---|---|---|---|---|---|
| `forming` | Forming | idle | FORMING | `Not held — the club is still selling this slot` | `{f} of {n} seats paid` | — | — |
| `formingHeld` | Forming | idle | FORMING | `Not protected — no court is held yet` | `{f} of {n} paid · 1 seat held` | — | — |
| `formingLate` | Forming | idle | FORMING | `Protected · {cat}` or `Not protected — no court is held yet` | `{f} of {n} seats paid` | — | — |
| `formingBack` | Forming | **watch** | FORMING | `Released — the court is no longer held` | `{f} of {n} seats paid` | — | — |
| `heldSoft` | Court held | watch | COURT_HELD | `Held · {cat} — {hold.note}` | `{f} of {n} seats paid` | — | — |
| `heldReleased` | Court released | watch | COURT_RELEASED | `Released — back on sale at {club}` | `{f} of {n} seats paid` | — | — |
| `heldStale` | Court released | watch | RELEASED | `Released — back on sale at {club}` | `{f} of {n} seats paid` | — | — |
| `heldExtended` | Court held | **good** | HELD | `Held · {cat} — beyond what the ladder guarantees` | `{f} of {n} seats paid` | — | — |
| `clubHeld` | Court committed | good | COURT_PROTECTED | `Committed by {club} · {cat}` | `{f} of {n} seats paid` | — | — |
| `protectedCourt` | Court protected | good | COURT_PROTECTED | `Protected · {cat} — a private booking can no longer take it` | `{f} of {n} seats paid` | — | — |
| `protectedBack` | Court protected | good | COURT_PROTECTED | `Still held · {cat} — three seats are still paid` | `{f} of {n} seats paid` | — | — |
| `protectedLate` | Court protected | good | COURT_PROTECTED | `Protected · {cat}` | `{f} of {n} seats paid` | — | — |
| `full` | Full | good | FULL_UNCOMMITTED | `Reserved · settles to the club at {commit HH:mm}` | `{n} of {n} seats paid` | — | — |
| `confirmed` | Confirmed | good | CONFIRMED | `{price} settled to the club` | `{n} of {n} · committed` | — | — |
| `confirmedOnFill` | Confirmed | good | CONFIRMED | `{price} settled to the club` | `{n} of {n} · committed on the spot` | — | — |
| `replacement` | Replacement pending | watch | REPLACEMENT_PENDING | `{price} settled to the club` | `{n−1} of {n} · the seat stays funded` | **yes** | — |
| `replacementTransfer` | Replacement pending | watch | REPLACEMENT_PENDING | `{price} settled to the club` | `{n−1} of {n} · the seat stays funded` | — | — |
| `rescue` | Rescue active | time | RESCUE_ACTIVE | `{price} settled to the club` | `{n−1} of {n} · the seat stays funded` | **yes** | — |
| `rescueLate` | Rescue active | time | RESCUE_ACTIVE | `{price} settled to the club` | `{n−1} of {n} · the seat stays funded` | — | — |
| `ready` | Ready to play | good | CONFIRMED | `Court {courtName ?? club.court}` | `{n} of {n} · everybody expected` | — | — |
| `cancelledIncomplete` | Cancelled | ended | CANCELLED | `Released back to the club` | `{f} of {n} — it never filled` | — | — |
| `cancelledCheckpoint` | Cancelled | ended | CANCELLED | `Released back to the club` | `{n−1} of {n} — the seat was never refilled` | — | — |
| `cancelledClub` | Cancelled | ended | CANCELLED | `Cancelled by {club}` | `everybody refunded` | — | — |
| `inventoryLost` | Cancelled | **bad** ⚠ | CANCELLED | `Gone — the last {cat} court was sold` | `{f} of {n} seats paid` | — | — |
| `needsResult` | Needs result | watch | COMPLETED | `Settled` | `{n} of {n} played` | — | **1** |
| `confirmResult` | Confirm the result | watch | COMPLETED | `Settled` | `{n} of {n} played` | — | **1** |
| `completed` | Completed | good | COMPLETED | `Settled` | `{n} of {n} played` | — | **1** |
| `playedShort` | Played | idle | COMPLETED | `Settled` | `{n−1} of {n} played` | — | **1** |
| `playedNoShow` | Played | idle | COMPLETED | `Settled` | `{n−1} of {n} played` | — | **1** |
| `playedNoScore` | Played | idle | COMPLETED | `Settled` | `{n} of {n} played` | — | **1** |
| `waitlisted` | On standby | idle | `—` | `Fully paid by four other players` | `{n} of {n} · you are 2nd on the standby list` | — | — |
| `privateReserved` | Reserved | good | RESERVED | `Yours · {club.court}` | `you invite whoever you like` | — | — |
| `privatePartial` | Reserved | good | PARTIALLY_PAID | `Yours · {club.court}` | `{f} of {n} shares paid` | — | — |
| `privateFull` | Reserved | good | FULLY_PAID | `Yours · {club.court}` | `{n} of {n} shares paid` | — | — |
| `privateOpen` | Reserved | good | PUBLIC_SEATS_OPEN | `Yours · {club.court}` | `{f} of {n} · 1 seat open to the marketplace` | — | — |

⚠ `inventoryLost` declares `tone:'bad'` `[SRC: line 3600]`, but **`ST_TONE` has no `bad` key** `[SRC: 3529]`, so `ST_TONE['bad']` is `undefined` and the dot renders with `background:undefined` → no colour. Defect; see §G.

`[GAP]` **`cta` and `left` are read by `stateCard` but no state in the table ever sets them.** Every card therefore shows the fallback `Open match` targeting the match screen, with no countdown suffix. The mechanism exists and is unused. Recommendation in §G.

### B6.4 The alert copy (verbatim, the only two)

- `replacement` → `{Name} left after the commitment deadline. We are looking for a replacement. <b>Your payment will not change.</b>`
- `rescue` → `Still looking for a replacement. <b>Your payment will not change.</b>`

```ts
type MatchStateResult = {
  key: ContextKey;                     // one of the 35
  tag: Tag;                            // one of the 17
  tone: Tone;
  be: LifecycleState;                  // one of the 9 canonical states
  ctx: string;                         // the disambiguating context line (gallery + a11y)
  court: string;
  group: string;
  lines: Array<{ done: boolean; text: RichText }>;
  alert?: RichText;
  cta?: { label: string; target: Route };
  left?: string;
  post?: boolean;
};
```

---

## B7. `StatusTag` (`.tag`)

**Source.** `[SRC: lines 144–152]`

**Anatomy.** inline-flex · optional 6×6 px dot (`.tag i`, radius 3) · label.
**Base tokens.** `padding:3px 7px; gap:4px; radius:6px; font 9.5/700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis`.

| Variant | Background | Text | Used on Now for |
|---|---|---|---|
| default | `--line2` | `--muted` | sport, format, "Friendly", the state tone tag on match cards |
| `.ok` | `--mint-soft` | `--mint` | `card −…`, MultiSport "N left" |
| `.hot` | `--coral-soft` | `--coral-ink` | `m.badge`, "Counts" |
| `.warn` | `--amber-soft` | `--amber` | not on Now |
| `.bad` | `--red-soft` | `--red` | not on Now |
| `.w` | `rgba(255,255,255,.17)` | `#fff` | **state-card header tag** (on night) |

**Content rules.** `text-overflow:ellipsis` is declared but there is no `max-width`, so it only fires when a flex parent shrinks it — which happens on the match-card hair row, where the tag carries `min-width:0` inline `[SRC: 1417]`.

```ts
type StatusTagProps = {
  label: string;
  variant?: 'default' | 'ok' | 'hot' | 'warn' | 'bad' | 'onDark';
  dotColor?: string;      // renders the 6px leading dot
};
```

---

## B8. `MatchCard` (`matchCard()`)

**Purpose.** A joinable match in a vertical list — the recommendation feed and the "full, but worth waiting for" slot.
**Source.** `[SRC: matchCard(), lines 1392–1424]`

**Anatomy (DOM order).**
1. `.card.tap` with inline `padding:11px`, `data-go="match" data-id`
2. Top row (`space-between`, gap 10)
   - left (`min-width:0`)
     - title row: `.mono` 12/700 `when(start)` + optional `.tag.hot` `{m.badge}` (`flex-wrap:wrap`, gap 5)
     - `.tiny` `{club.n} · {club.dist} min` (`margin-top:2px`)
     - `.row` (`margin-top:6px`): sport tag with colour dot · format tag · `Counts`(`.hot`)/`Friendly`(default) · conditional `card −all` or `card −{zl(off)}` (`.ok`) when `cardOff > 0`
   - right (`flex-shrink:0; text-align:right`): `glyph(sport, seatSyms, 46)` + `.tiny.mono` `{filled}/{n}`
3. `.hair` footer row (`space-between`, gap 6, `align-items:center`)
   - left group (gap 5, `min-width:0`): `.fit` badge when `f.score != null` · state tone tag (`.tag` + dot)
   - right group: struck-through `{zl(share)}` when a card discount applies · `.mono.num` 14 px `{zl(payable)}` · `.tiny` ` · 0 fee`
4. optional `.tiny.hair` footer (`opts.foot`) — **not used by Now**

**States.** rest · `.card.tap:hover` → `border-color:--coral; translateY(-1px)` · no active/focus/disabled/loading.
**Content rules.** No clamping. The tag row wraps to two lines when a badge and a card discount coexist `[DERIVED]`.

```ts
type MatchCardProps = {
  whenLabel: string;
  badge?: string;                       // e.g. 'Promotion' | 'Box league'
  clubName: string;
  travelMinutes: number;
  sport: Sport; format: string;
  counts: boolean;                      // 'Counts' vs 'Friendly'
  cardDiscount?: { full: boolean; amount: string };   // 'card −all' | 'card −15,00 zł'
  seats: SeatSymbol[]; filled: number; capacity: number;
  fitScore?: number;                    // null → badge omitted
  stateTag: string; stateTone: Tone;
  strikePrice?: string;                 // shown only when a discount applies
  payable: string;                      // 'zł'-formatted
  foot?: string;
  onPress: () => void;
};
```

---

## B9. `FitBadge` (`.fit`)

**Source.** `[SRC: lines 184–185]` · logic `matchFit()` `[SRC: 1144–1192]`

| Property | Value |
|---|---|
| Shape | inline-flex, height 23 px, padding `0 9px`, gap 4, radius 7 |
| Type | 11/700 |
| Rest | `background:--night; color:#fff` |
| `.hi` (score ≥ 90) | `background:--coral` |
| Content | `✦ {score}` — integer, clamped `20…99` `[SRC: 1183]` |
| Omitted when | `matchFit().score === null`, i.e. the player has no rating in that sport `[SRC: 1146]` |

Score = weighted sum of seven terms (Skill overlap 30 · Predicted balance 20 · Group reliability 15 · Time and travel 15 · Match type 8 · Price vs ceiling 7 · Preferences 5), plus modifiers `+8` promotion, `+5` unfamiliar opponents, `−8` "the same four again", then `clamp(20, 99)` `[SRC: 1155–1183]`.

⚠ `[SRC: 5-now_screen_architecture_review.md §E2]` The `.hi` coral treatment contradicts the stated rule that coral marks only *what the player owns or can act on*. §G.

```ts
type FitBadgeProps = { score: number; emphatic?: boolean };   // emphatic ⇔ score >= 90
```

---

## B10. `Button` (`.btn`)

**Source.** `[SRC: lines 188–196]`

| Property | Value |
|---|---|
| Base | inline-flex centred, height **34 px**, padding `0 14px`, radius 10, font 12/700, `transition:.12s` |
| `.p` primary | `--coral` on `#fff` |
| `.n` night | `--night` on `#fff` |
| `.s` secondary | `#fff`, `1px solid --line`, ink text |
| `.w` on-dark | `rgba(255,255,255,.17)`, `#fff` |
| `.full` | `width:100%` |
| Hover | `filter: brightness(1.06)` |
| Disabled | `opacity:.4; cursor:default` |
| Focus-visible | 2 px coral / 2 px offset — **only when rendered as a real `<button>`**, which on Now it never is |

Now uses: `.btn.p` (flex:1, 34 px) and two `.btn.w` at `width:40px; height:34px`. The pinned-CTA bar would use `.btn.{kind}.full` at `height:38px` `[SRC: render(), 4286]` but **Now never sets `CTA`**, so that bar stays hidden.

```ts
type ButtonProps = {
  label: string; variant?: 'primary' | 'night' | 'secondary' | 'onDark';
  full?: boolean; disabled?: boolean; iconOnly?: boolean;
  accessibilityLabel?: string;     // REQUIRED when iconOnly
  onPress: () => void;
};
```

---

## B11. `MembershipCard` (the MultiSport block)

**Purpose.** Today's club-card entitlement, always present, between the strip and the feed.
**Source.** inline in `V.home` `[SRC: 1607–1610]`; data from `CARD` `[SRC: line 677]`

**Anatomy.** `.card.tap` with inline `background:var(--mint-soft); border-color:#CFE7DD`, `data-go="card"` → flex `space-between`, `align-items:center` → left column `.h2 {CARD.plan}` + `.tiny` `{used} of {allowed} entries used today · show the QR at reception` (`margin-top:2px`) → right `.tag.ok` `{allowed − used} left`.

**Seeded values:** `plan:'MultiSport Plus'`, `allowed:2`, `used:1` `[SRC: 677]`.
**Conditional?** No — it renders unconditionally, even at zero entries left and even when the player has no matches `[SRC: 1607]`. `[GAP]` No "0 left" or "no card linked" treatment exists. Recommend a `.tag` default (grey) at 0 and hiding the block entirely when no card is linked. **Decision to ratify.**

```ts
type MembershipCardProps = {
  planName: string; used: number; allowed: number;
  helpText?: string;            // default: 'show the QR at reception'
  onPress: () => void;
};
```

---

## B12. `EmptyState` (`.empty`)

**Source.** `[SRC: line 229–230]` · two instances in Now

| Instance | Condition | Padding | Copy |
|---|---|---|---|
| No enrolled matches | `shown.length === 0` | `30px 18px` (class default), inside a `.card` | **No matches booked** / `Find a game or create one. You only ever pay your own share, and the fee is always zero.` |
| Nothing to recommend | `feed.length === 0` | `18px` (inline override) | **Nothing open in {sport} right now** / `We do not invent players to make a city look busy. Try another day, or create a match.` — where `{sport}` is `your sports` when the filter is `all`, else the sport name |

**Tokens.** centred; container `--muted`; `b` → `display:block; 13px; --ink; margin-bottom:5px`.
`[GAP]` Neither empty state offers an action, although both name one in prose. Recommend adding a `.btn.s` — *decision to ratify*.

```ts
type EmptyStateProps = { title: string; body: string; action?: { label: string; onPress: () => void } };
```

---

## B13. `TabBar`

**Source.** `[SRC: .tabbar lines 85–90; render() 4292; badge override 6953]`

**Anatomy.** `display:grid; grid-template-columns:repeat(5,1fr); border-top:1px solid --line; background:#fff; padding:7px 0 12px`. Each tab: column flex, `gap:4px`, label 8.5/600, icon `<i>` 16×16 radius 5 filled with `currentColor` at `opacity:.85`.

| Index | Key | Label | Route |
|---|---|---|---|
| 1 | `now` | Now | `home` ← **this feature** |
| 2 | `find` | Find | `find` |
| 3 | `create` | *(no label)* | `create` — `.fab`, icon 28×28, radius 10, solid `--coral`, `opacity:1`, `margin-bottom:-4px` |
| 4 | `msg` | Inbox | `inbox` |
| 5 | `you` | You | `you` |

**Selected:** `.tab.on{color:--coral}` — icon inherits via `currentColor`.
**Badge:** after the base render, if `reqOpen().length > 0`, a pill is injected into the Inbox tab: `position:absolute; margin:-26px 0 0 13px; min-width:15px; height:15px; padding:0 4px; radius:8px; background:--coral; color:#fff; font 9/700 Plex Mono; line-height:15px` `[SRC: 6957–6963]`.

```ts
type TabBarProps = {
  active: TabKey;
  badges?: Partial<Record<TabKey, number>>;
  onSelect: (t: TabKey) => void;
};
```

---

## B14. `Toast`

**Source.** `[SRC: #toast line 248; .tst 249–252; toast() 1552]`

Container is absolutely positioned `left:15px; right:15px; bottom:78px; z-index:40; pointer-events:none`. Each toast: `--night` surface, `#fff`, radius 12, padding `11px 14px`, 12/600, shadow `0 12px 28px -12px rgba(0,0,0,.6)`, entry `up .24s`, `margin-top:7px` so several stack downward. Variants `.ok` → `--mint`, `.bad` → `--red`. Auto-dismiss at 2 600 ms + 300 ms fade.

`[DERIVED]` `bottom:78px` is hand-fitted to clear the 5-tab bar; it must become `tabBarHeight + 16`.

```ts
type ToastProps = { message: string; variant?: 'neutral' | 'ok' | 'bad'; durationMs?: number };
```

---

## B15. `Sheet` shell

**Source.** `[SRC: lines 231–247]`

`#sheetwrap` covers the phone at `z-index:20`; `#scrim` `rgba(10,52,65,.45)` fading in over 200 ms and dismissing on tap; `#sheet` bottom-anchored, `max-height:88%`, radius `22px 22px 0 0`, shadow `0 -20px 40px -22px rgba(10,32,40,.6)`, entry `up .26s cubic-bezier(.2,.8,.2,1)`. Head: 36×4 px grab handle (`--line`, radius 2, centred, `margin-bottom:10px`) and a 28 px circular close button at `top:12px; right:14px` (`--line2` → `--line` on hover, `aria-label="Close"`). Body scrolls with hidden scrollbar, padding `0 15px 16px`. `Escape` closes the sheet, else navigates back `[SRC: 5037]`.

---

## B16. `AccessSheet` (`SH.access`) — reachable directly from Now via `⌘`

**Source.** `[SRC: 4102–4117]`

Anatomy: `.h2` **Getting in** → `.tiny` `{club} · unlocks at {start − 15 min}` → centred `.card-n`: `.eyebrow` **Door code**, then `.num.mono` 33 px with `letter-spacing:.1em` showing `4417#` when `now ≥ start − 15 min` else `••••`, then a 96×96 white rounded (13 px) tile with 8 px padding containing an 80×80 21-unit QR (`qr()`), then `.tiny` explaining keypad vs staffed clubs → `.card` with two `.rl` rows (gear list; `+48 12 000 00 00`) and a `.tiny` line → closing centred `.tiny` `Cached on your phone — it works with no signal.`

**Locked state** is the only genuine state variant: the code is masked with four `•` characters. There is no countdown.

---

## B17. `PlayerSheet` (`SH.player`) — reachable from Now only by long-press on an element carrying `data-hold`

**Source.** `[SRC: 4181–4227]`. `[DERIVED]` **No element rendered by `V.home` carries `data-hold`**, so on the Now screen this sheet is currently unreachable; it becomes reachable one level deeper. Documented because the long-press handler is global and fires anywhere.

---

## B18. Formatting helpers — **their output format is a design decision**

| Helper | Source | Output | Rule |
|---|---|---|---|
| `zl(v)` | `[SRC: 831]` | `38,00 zł` · `0,00 zł` | **always two decimals**; decimal separator **comma**; **no thousands separator**; currency **suffixed after a single space**, lower-case `zł` |
| `lvl(v)` | `[SRC: 832]` | `2,71` · `—` when null · `−0,35` | two decimals, comma separator, minus rendered as **U+2212**, em-dash for absent |
| `hm(t)` | `[SRC: 814]` | `18:30` | zero-padded 24-hour, colon |
| `dow(t)` | `[SRC: 815]` | `Sat` | 3-letter English, Sunday-first array |
| `dowl(t)` | `[SRC: 816]` | `Saturday` | full English |
| `when(t, now)` | `[SRC: 817–824]` | `Today · 18:30` · `Tomorrow · 18:30` · `Yesterday · 18:30` · `Sat · 18:30` | **calendar-day** difference, not elapsed hours; relative words only for −1/0/+1 |
| `dur(ms)` | `[SRC: 825]` | `2d 6h` · `4 h 30` · `45 min` | ⚠ inconsistent: `h` has a space before it, `d`/`h` do not, and minutes in the `h` form are zero-padded and unlabelled. Not used by Now, but shared |
| `hhmm(min)` | `[SRC: 675]` | `18:30` from minutes-of-day | |
| `matchState().group` | — | `3 of 4 seats paid` | count-of-count in words, never `3/4` |
| glyph counter | `[SRC: 1409, 3994]` | `3/4` | the **only** slash form, always in Plex Mono |

**The metadata separator is ` · ` (space, U+00B7, space) everywhere**, without exception, in: the header eyebrow, `when()`, `{club} · {dist} min`, `{sport} · {fmt}`, `{court} · {dur} min`, `Your matches · 3 · soonest first`, `{used} of {allowed} entries used today · show the QR`, `{payable} · 0 fee`, and every state's `court`/`group` value. `[SRC: passim]`

**Travel is expressed in minutes, not kilometres**, on both cards (`{dist} min`) even though `CLUBS[*].km` exists `[SRC: 447–465]`.

```ts
export const fmt = {
  money: (v: number) => string,     // '38,00 zł'   — 2dp, comma, space, 'zł'
  level: (v: number | null) => string,  // '2,71' | '—' | '−0,35'
  time:  (d: Date) => string,       // '18:30'
  dayShort: (d: Date) => string,    // 'Sat'
  dayLong:  (d: Date) => string,    // 'Saturday'
  when: (d: Date, now: Date) => string, // 'Today · 18:30'
  SEP: ' · ',
};
```

---

# C. SCREEN COMPOSITION

## C1. Screen: **Now** (`V.home`, route key `home`, tab `now`)

**Shell regions occupied**

| Region | State on Now |
|---|---|
| Status bar (`#statusbar`, 28 px) | clock `hm(S.now)` left; `dow(S.now)` + signal glyphs right. Prototype chrome; hidden below 900 px |
| Scroll body (`#scroll`) | **everything**, including the screen header — the header scrolls away |
| Pinned CTA (`#cta`) | **hidden.** `render()` sets `CTA=null` before calling the view and Now never assigns it `[SRC: 4281]` |
| Tab bar (`#tabbar`) | visible, `Now` active |
| Sheet | closed unless `⌘` was tapped (`access`) |
| Toast | empty unless an action fired one |

### C2. Component stack in render order

```
1  ScreenHeader          eyebrow 'Kraków · {dowl(now)} · {hm(now)}' · title 'Hi, Tomek'
2  SportFilterBar        all · Padel · Tennis · Squash · Badminton
3  <div id="scroll-inner">                       ← opened at 1583, closed at 1622, never styled
4  IF shown.length:
4a   SectionHeading(split)  'Your matches · {n} · soonest first'   |  'swipe →'
                            gallery mode: '{tagCount} tags · {n} contexts'
4b   MatchStrip            one StateCard per enrolled match
4c   IF shown.length > 1:  PageDots
4d   IF gallery:           GalleryCaption '{tag} — {ctx}'
   ELSE:
4e   Card > EmptyState     'No matches booked'
5  MembershipCard          always
6  SectionHeading          'Even matches for you'
7  IF feed.length:  MatchCard × min(3, feed.length)
   ELSE:           Card > EmptyState 'Nothing open in {sport} right now'
8  IF full.length:  SectionHeading 'Full, but worth waiting for' + MatchCard × 1
9  </div>
```

### C3. The three queries that drive it `[SRC: 1579–1592]`

| List | Predicate | Sort | Limit |
|---|---|---|---|
| `ms` → `shown` | `mySeat(m) && !m.left && matchEnd(m) + 24h > now`, then `sport === 'all' \|\| m.sport === sport` | `start` **ascending** (soonest first) | none |
| `feed` | `!mySeat && !m.forced && start > now && filled < n && sport filter`, then `matchFit(m).score != null` | fit score **descending** | **3** |
| `full` | `!mySeat && !m.forced && start > now && isFull(m) && sport filter` | **unsorted** — document order | **1** |

**Retention rule:** `KEEP_H = 24` `[SRC: 3533]` — a finished match stays on Now for 24 h after its end, then leaves for history.
**Gallery override:** when `S.gallery` is true the strip shows *every* `m.forced` match and ignores the sport filter `[SRC: 1584–1585]` — prototype only.

### C4. Conditional blocks and their exact conditions

| Block | Shows when |
|---|---|
| Strip section | `shown.length > 0` |
| Page dots | `shown.length > 1` |
| Gallery caption | `shown.length > 1 && S.gallery` |
| "No matches booked" | `shown.length === 0` |
| MultiSport card | always |
| "Even matches for you" heading | always — **even when the list under it is the empty state** |
| Feed cards | `feed.length > 0` (max 3) |
| "Nothing open in …" | `feed.length === 0` |
| "Full, but worth waiting for" | `full.length > 0` (exactly 1 card) |
| Inbox tab badge | `reqOpen().length > 0` |

### C5. Scroll and position preservation on re-render

`render()` `[SRC: 4269–4300]`:
1. `syncAll()` mutates every match against the clock **before** anything is drawn.
2. `key = [view, step, id, tab, findTab].join('|')`; `same = key === VIEWKEY`.
3. If `same`: capture `sc.scrollTop` and every `.sqrow` `scrollLeft`; else start from 0.
4. `sc.innerHTML = fn()` — **full teardown, every time**.
5. Restore `.sqrow` offsets, then `scrollTop`.

**Consequences for Now** `[DERIVED]`: changing the sport filter keeps the vertical scroll position (same key). The **`.hstrip` carousel is not a `.sqrow`, so its horizontal position is always lost**, and so is the sport bar's own horizontal scroll. Every re-render also restarts the `rise` animation on all three top-level children.

## C6. Sheet: **Getting in** (`access`) — in scope, opened from the Now card

Region: bottom sheet over the Now screen, scrim visible, tab bar occluded. Stack: title → subtitle → dark code card (masked/live) → info card → closing line. Empty state: none. Position preservation: the sheet body is re-rendered on every `render()` while open, and its scroll position is **not** preserved `[SRC: 4296]`.

---

# D. LAYOUT & RESPONSIVE

## D1. App shell (desktop / prototype presentation)

| Region | Dimensions |
|---|---|
| `#app` | grid `290px 1fr`, full height |
| `#rail` | 290 px, `#071C24`, scenario list — **prototype only, delete in production** |
| `#stage` | centred flex column, `padding:18px 20px 0`, background `#08222B` |
| `#phone` | **392 × 788**, radius 34, `1px solid #24505E`, `overflow:hidden`, `margin-top:8px` |
| `#statusbar` | height **28 px**, `padding:0 20px`, 10.5/600 |
| `#view` | flex column, `min-height:0`, `position:relative` — the containing block for sheets and toasts |
| `#scroll` | `flex:1; overflow-y:auto; overflow-x:hidden; padding:0 15px 14px; scroll-behavior:smooth`; scrollbar width 0 |
| `#cta` | `flex-shrink:0; background:#fff; border-top:1px solid --line; padding:10px 15px; display:none` → `.on{display:block}` |
| `#tabbar` | grid of 5, `padding:7px 0 12px`, `border-top:1px solid --line` |
| `#timebar` | simulated-clock scrubber, **prototype only** |

**Derived content width:** 392 − 2 (border) = 390 → minus `#scroll` gutters (2 × 15) = **360 px** for cards.

## D2. Breakpoints

| Breakpoint | Exactly what changes |
|---|---|
| `max-height: 900px` | `#phone` height 788 → **700** |
| `max-height: 800px` | `#phone` height → **620**; `#timebar` padding `12px 16px 14px` → `9px 14px 11px` |
| `max-width: 900px` | `#app` becomes single column · `#mtop` (46 px dark bar with hamburger) appears · `#rail` becomes a fixed drawer, `width:min(320px,86vw)`, `translateX(-100%)`, `.26s cubic-bezier(.4,0,.2,1)`, opened by `body.railopen`, with `#railscrim` at `rgba(4,18,24,.55)` · `#stage` padding 0, top-aligned, `overflow:visible` · `#stagehead` and `#statusbar` **hidden** · `#phone` becomes `width:100%`, `height: calc(100dvh − 46px − 56px)`, no border, no radius, no shadow · `#timebar` becomes a fixed bottom bar, `#0B2B36`, `z-index:40`, padding `8px 14px 10px` |
| `max-width:900px and max-height:800px` | phone height restated (identical value) |

`[DERIVED]` Only one breakpoint is real for the app itself: **900 px**, at which "the app should be the app, not a picture of a phone" `[SRC: comment, lines 260–264]`. In production the phone frame, rail, stage and time bar all disappear and the layout is simply the scroll body + tab bar.

## D3. Z-index order (ascending)

| z | Element |
|---|---|
| 1 | `#track input` (scrubber) |
| 3 | `#track .stop`, `#xsheet` |
| 20 | `#sheetwrap` (scrim + sheet) |
| 30 | `#mtop` (≤900 px) |
| 40 | `#toast`, `#timebar` (≤900 px) |
| 50 | `#railscrim` (≤900 px) |
| 60 | `#rail` (≤900 px), `.ipop` |

## D4. Safe areas

`[GAP]` **No `env(safe-area-inset-*)` anywhere in the file.** The tab bar's `padding:7px 0 12px` and the toast's `bottom:78px` are hand-fitted. Recommended: `paddingBottom = 12 + safeAreaBottom` on the tab bar, `bottom = tabBarHeight + safeAreaBottom + 16` on toasts, `paddingTop = safeAreaTop` on the header. **Decision to ratify.**

## D5. Overflow and scroll-snap

| Pattern | Behaviour |
|---|---|
| `#scroll` | vertical only, `overflow-x:hidden`, smooth, scrollbar hidden |
| `.hstrip` (Now's carousel) | `overflow-x:auto`, `scroll-snap-type:x mandatory`, children `scroll-snap-align:center` + `scroll-snap-stop:always` (so a fast flick advances exactly one card), scrollbar hidden, **bleeds to the frame edge via `margin:0 -15px`** |
| `.sqrow` | `overflow-x:auto`, no snap, children `flex:0 0 auto`, **offset preserved across re-render** |
| `.mrail` | a `.sqrow` whose children are 268 px cards — *not used by Now* |
| sport bar | `overflow:auto`, `flex-wrap:nowrap`, no snap, offset **not** preserved |

**Peek affordance:** 360 px card in a 390 px viewport, centre-snapped → **15 px of the neighbouring card visible on each side**, reinforced by the "swipe →" hint and the dots.

---

# E. INTERACTION & ACCESSIBILITY

## E1. Event delegation

Three global listeners on `document` `[SRC: 4991–5039]`, resolved with `closest()`:

| Attribute | Resolution | Precedence |
|---|---|---|
| `data-act="{key}"` | `ACT[key](el)` | **first** — wins over `data-go` on an ancestor |
| `data-go="{view}"` (+ `data-id`, `data-step`, `data-kind`) | `go(view, …)` — **pushes** onto the stack; the literal `inbox` is special-cased to `S.tab='msg'; reset('inbox')` | second |
| `#scrim` | `closeSheet()` | third |

### Now's complete action map

| Element | Attribute | Effect |
|---|---|---|
| Sport chip | `data-act="sport" data-v` | set `S.sport`, clear `S.durs`, re-render |
| State card body | `data-go="match" data-id` | push match screen |
| State card primary CTA | `data-go="{st.cta.go ?? 'match'}" data-id` | push (currently always the match screen) |
| State card `✉` | `data-go="inbox"` | switch tab to Inbox, reset stack |
| State card `⌘` | `data-act="access" data-id` | open the Getting-in sheet |
| MultiSport card | `data-go="card"` | push the club-card screen |
| Match card | `data-go="match" data-id` | push match screen |
| Tab bar item | `data-act="tab" data-v` | switch tab, reset that tab's stack |
| Sheet close | `data-act="closesheet"` | close |
| `Escape` key | — | close sheet, else `back()` |

## E2. Gestures

| Gesture | Threshold | Result |
|---|---|---|
| Long press on `[data-hold]` | **420 ms**, cancelled by **> 8 px** pointer movement in either axis | opens the player sheet; sets `SUPPRESS` so the following `click` is swallowed `[SRC: 4974–4986]` |
| Long-press feedback | immediate on pointerdown | `.holding` → `box-shadow:0 0 0 3px var(--coral-soft)`; `:active` → `scale(.93)` |
| Right-click / context menu on `[data-hold]` | — | same as long press, default prevented |
| Horizontal swipe on `.hstrip` | mandatory snap, `scroll-snap-stop:always` | exactly one card per flick |
| Vertical scroll | — | `scroll-behavior:smooth` |

`[GAP]` No swipe-to-dismiss on the sheet (only the grab handle *looks* draggable), no pull-to-refresh, no swipe actions on cards.

## E3. Focus order and visible focus

Real focusable elements on Now, in DOM order: **the five sport chips**, then **the five tab-bar buttons**. That is all. `:focus-visible{outline:2px solid var(--coral); outline-offset:2px}` `[SRC: line 37]` applies to them.

**Everything else is a `<div>` or `<span>`** — the state card, its three action buttons, the match cards, the MultiSport card. They are unreachable by keyboard, unannounced by screen readers, and have no press state. This is the single largest production gap in the feature.

## E4. Touch targets

| Target | Size | Verdict |
|---|---|---|
| Sport chip (`.chip.sm`) | height **25 px** | ⚠ **under 44** |
| State-card primary CTA | height **34 px**, width ~206 | ⚠ **under 44** |
| State-card `✉` and `⌘` | **40 × 34** | ⚠ **under 44 in both axes** |
| State card (whole) | ~360 × 260 | ok |
| Match card (whole) | ~360 × 120 | ok |
| MultiSport card | ~360 × 62 | ok |
| Tab item | ~78 × 47 | ⚠ marginal (47 tall including padding, but the icon+label cluster is ~28) |
| Sheet close button | **28 × 28** | ⚠ **under 44** |
| Page dots | 5 × 5 | not interactive — correct, but they *look* tappable |

Recommendation: keep the visual sizes, add invisible **44 × 44** hit slop to the chips, the two icon buttons, and the sheet close.

## E5. Colour-contrast risks

| Pair | Approx. ratio | Verdict |
|---|---|---|
| `--muted #6E7F85` on `#fff` at **11 px** (`.tiny`) | ≈ 4.0 : 1 | ⚠ below 4.5 for text under 18.66 px |
| `--muted` on `--line2 #F0EDE6` at **9.5 px/700** (default `.tag`) | ≈ 3.7 : 1 | ⚠ fails |
| `--muted` at **9.5 px** uppercase `.15em` (`.eyebrow`, `.sect`) | ≈ 4.0 : 1 | ⚠ fails, and the tracking makes it worse |
| `--mint #0C8F6B` on `--mint-soft` (`.tag.ok`) | ≈ 3.9 : 1 | ⚠ borderline |
| `--amber #9A6A0B` on `--amber-soft` | ≈ 4.6 : 1 | ok |
| `--coral-ink #B8351C` on `--coral-soft` (`.tag.hot`) | ≈ 5.3 : 1 | ok |
| `rgba(255,255,255,.52)` on `--night` (`.card-n .eyebrow` at 8.5 px) | ≈ 4.3 : 1 | ⚠ fails at that size |
| `rgba(255,255,255,.68)` / `.92` on `--night` | ≈ 7 : 1 / 12 : 1 | ok |
| `--volt #D9F24B` on `--night` | ≈ 11 : 1 | ok |
| **Tone dot `idle` = `rgba(255,255,255,.45)` on a white `.tag`** | ≈ 1.0 : 1 | ✖ **invisible.** Every `forming` / `played*` / `waitlisted` match card renders a blank tone dot |

Ratios are `[DERIVED]` estimates and must be re-measured against the final theme.

## E6. Required ARIA / accessibility properties

| Control | Requirement |
|---|---|
| State card | `role="button"`, `accessibilityLabel` = `"{tag}. {when} at {club}. {filled} of {capacity} seats paid."`, `accessibilityHint` = "Opens the match" |
| Court glyph | `accessibilityRole="image"`, label `"{filled} of {capacity} seats paid, including yours"`; the SVG is otherwise pure decoration and must be `aria-hidden` if the count is announced separately |
| Fact lines | present as a list; each item prefixed "Done: " / "Not yet: " so the `✓`-vs-ring distinction survives |
| Alert block | `role="status"` (polite) — it is news, not an error |
| `✉` button | `accessibilityLabel="Open inbox"` |
| `⌘` button | `accessibilityLabel="Getting in — door code and QR"` |
| Sport chips | `role="radiogroup"` on the row, `role="radio"` + `accessibilityState={{selected}}` per chip |
| Carousel | `accessibilityRole="adjustable"` or a paged scroll view announcing "Match 2 of 3" |
| Page dots | `aria-hidden` — the carousel announces position |
| Tab bar | `role="tablist"` / `role="tab"` / `accessibilityState={{selected}}`; the badge must be in the tab's label ("Inbox, 2 new") |
| Tone dot | decorative only; the tag text already carries the meaning `[DERIVED — and this is correct: no state is signalled by colour alone]` |

## E7. Screen-reader text for icon-only buttons

Only three exist on Now — `✉`, `⌘`, and the sheet's `✕` (which already has `aria-label="Close"`). The first two have **nothing** `[SRC: 4013–4015]`. Labels above.

---

# F. CONTENT & TONE

## F1. The rules, each evidenced

| # | Rule | Verbatim evidence |
|---|---|---|
| 1 | **Sentence case everywhere except tags and eyebrows**, which are ALL CAPS via CSS `text-transform`, never in the string itself. | `Even matches for you` · `Full, but worth waiting for` · `Nothing open in your sports right now` `[SRC: 1611, 1619, 1614]` |
| 2 | **Second person, present tense, active voice.** The app addresses the player and names the actor for everything else. | `You paid 38,00 zł — your seat only, never the court` `[SRC: 3562]` |
| 3 | **A limitation is stated as a fact with its reason, never apologised for.** | `Not held — the club is still selling this slot` `[SRC: 3561]` |
| 4 | **A rule is attributed to whoever owns it**, by name, so the player knows who to be annoyed with. | `This is a club setting, not a marketplace rule, and it is on the club's rules screen` `[SRC: 6249]` · `Zabłocie Sport has committed a court to this match by hand` `[SRC: 3597]` |
| 5 | **Amounts are always exact and always formatted**; the zero fee is stated rather than omitted. | `38,00 zł · 0 fee` `[SRC: 1421]` · `Our cancellation fee, in every zone / 0,00 zł. There has never been one` `[SRC: 1524]` |
| 6 | **Times are given as clock times, not durations**, and deadlines are named with their hour. | `Rescue runs until 18:00, and you can bring a guest, or play three` `[SRC: 3735]` |
| 7 | **Reassurance is specific and bounded**, never "don't worry". | `Leaving now returns everything, in minutes` `[SRC: 3565]` |
| 8 | **The product refuses to flatter the marketplace.** Emptiness is reported, not disguised. | `We do not invent players to make a city look busy. Try another day, or create a match.` `[SRC: 1614]` |
| 9 | **The unpleasant consequence is stated in the same breath as the benign one.** | `Until then the club could sell its last Mondo court — if that happens the match is cancelled and everybody is refunded in full` `[SRC: 3563]` |
| 10 | **Emphasis is rationed to one `<b>` per alert**, and only on the sentence that answers "what does this cost me?". | `We are looking for a replacement. <b>Your payment will not change.</b>` `[SRC: 3689]` |
| 11 | **Em-dash introduces the consequence; the middot separates metadata.** Never interchanged. | `Released — back on sale at Zabłocie Sport` vs `Held · Mondo — held until 12h before play` `[SRC: 3581, 3574]` |
| 12 | **The player is never told what to feel or what to do next by an exclamation.** There is not one exclamation mark in the feature. | `[DERIVED — grep of all Now strings]` |

## F2. Ten verbatim strings that define the voice

1. `You only ever pay your own share, and the fee is always zero.` — the promise, restated in the emptiest possible moment.
2. `We do not invent players to make a city look busy.` — refusal as a feature.
3. `You paid 38,00 zł — your seat only, never the court` — Invariant 1, in the card, every time.
4. `A court is held from the second paid seat, and held more firmly as more of you pay` — the ladder explained without the word "ladder".
5. `Leaving now returns everything, in minutes` — reassurance with a unit.
6. `The deadline has passed, but an incomplete match commits nobody` — the rule stated against the intuition it defeats.
7. `Their model puts this match at 97% to fill, and a club may extend a hold on that basis` — someone else's decision, attributed and quantified.
8. `It can never work the other way: no model may release a court earlier than the ladder promised` — the guarantee stated as a prohibition.
9. `Nobody's reliability is touched. Alternatives are suggested below` — consequences named even when there are none.
10. `Your matches · 3 · soonest first` — the sort order is part of the label, so the ordering is never a mystery.

## F3. Fixed strings in Now

| String | Origin |
|---|---|
| `Hi, Tomek` | hardcoded greeting `[SRC: 1580]` — must become `Hi, {firstName}` |
| `Kraków · {day} · {time}` | hardcoded city `[SRC: 1580]` |
| `swipe →` | strip hint `[SRC: 1596]` |
| `Your matches · {n} · soonest first` | strip heading |
| `Even matches for you` | recommendation heading — note **"even", not "best"**; it promises balance, not quality |
| `Full, but worth waiting for` | standby heading |
| `show the QR at reception` | MultiSport helper |
| `{n} left` | MultiSport entitlement tag |
| `· 0 fee` | appended to every price on a match card |
| `Open match` | the universal fallback CTA |

---

# G. PRODUCTION DELTA

## G1. Inline styles to promote to tokens or props

| Inline value | Component | Promote to |
|---|---|---|
| `padding:11px` / `13px` | match card / state card | `Card.density = 'compact' \| 'comfortable' \| 'feature'` (11 / 12 / 13) |
| `font-size:8.5px` on `.eyebrow` | state-card facet labels | `Eyebrow.size = 'sm' \| 'md'` |
| `font-size:30px;line-height:1` | state-card time | `Display.time` type token |
| `font-size:14px` on `.mono.num` | match-card price | `Money.lg` token |
| `background:var(--mint-soft);border-color:#CFE7DD` | MultiSport card | `Card.tone = 'mint'` + `--mint-line` |
| `rgba(214,77,58,.16/.4)` | alert box | `--red` @16 % / 40 % |
| `background:${ST_TONE[tone]}` | tone dots | `<ToneDot tone>` component |
| `width:40px;height:34px` | icon buttons | `Button.iconOnly` with 44 × 44 hit slop |
| `margin-top:0` on the first `.sect` | strip heading | `SectionHeading.first` |
| `letter-spacing:0;text-transform:none` | the "swipe →" hint | `SectionHeading.hint` slot |
| `padding:18px` on the feed empty state | empty state | `EmptyState.size = 'sm' \| 'md'` |
| `margin:-5px 0 11px` | gallery caption | strip-caption slot |
| `width:96px;height:96px;padding:8px;border-radius:13px` | access sheet QR tile | `QRTile` component |
| `letter-spacing:.1em` on the 33 px door code | access sheet | `Display.code` token |
| `bottom:78px` | toast container | `tabBarHeight + safeAreaBottom + 16` |

## G2. Values used inconsistently — one canonical decision each

| Thing | Candidates found | Recommendation |
|---|---|---|
| Body text size | 11 · 11.5 · 12 · 12.5 px | **11 / 12 / 14** — 11 secondary, 12 primary body, 14 emphasis |
| Eyebrow size | 8.5 · 9.5 · 10.5 px | **9.5** everywhere; delete the 8.5 override (it fails contrast) |
| Card radius | 13 (light) · 15 (dark) | **14** for both; the split reads as an accident at these sizes |
| Card padding | 11 · 12 · 13 · 14 px | **12** default, **14** for the feature card |
| Card gap | 9 px (`.card`), 10 px (`.hstrip`) | **10** |
| Red | `--red #B4392C` vs alert `#D64D3A` | **`--red`**, at 16 %/40 % alpha for the alert |
| Coral | `--coral` vs literal `#E8482B` in `glyph()` | **`--coral`** |
| Sport colours | aliases of state colours | **Give sports their own four hues.** A green Tennis dot next to a green "good" dot is the exact failure §2.2 of the Now spec forbids |
| Idle tone | `rgba(255,255,255,.45)` used on both dark and light | **Two tokens**: `--tone-idle-on-dark` (white 45 %) and `--tone-idle-on-light` (`--muted`) |
| `inventoryLost` tone | declares `bad`, which `ST_TONE` does not define | Map to **`ended`** |
| Big time numeral family | `.num` alone (Archivo) vs `.mono.num` elsewhere | **`.mono.num`** — a clock time is a numeral, and tabular alignment matters when the strip pages |
| Header inset | 30 px (gutter + `.pbar`) vs 15 px for cards | **15 px** for both; remove the double inset |
| Travel unit | `dist` minutes vs `km` string | **Minutes** on cards (already consistent); keep km for the club screen |
| Fit-badge emphasis | coral at ≥ 90 | **Change the trigger, not the colour** — reserve coral for things the player owns; use it only for high fit *and* high coverage `[SRC: 5-now_screen_architecture_review.md §E2]` |
| Retention | `KEEP_H = 24` in the app vs "24 h after play" in the state doc | Agree; make it a server-supplied policy value |

## G3. String templates that need real component boundaries

Everything in the Now feature is a template literal returning HTML. These must become components, in priority order:

1. `stateCard` → **StateCard** (+ `ToneDot`, `FacetPair`, `AlertBlock`, `FactLine`, `CardActions`)
2. `matchState` → a **pure data function** returning `MatchStateResult`; no HTML. It currently calls `syncMatch()`, which **mutates the match record** — that side effect must move to the server or a reducer.
3. `matchCard` → **MatchCard** (+ `TagRow`, `PriceBlock`)
4. `glyph` → **CourtGlyph** (React Native SVG; the ratios in §A5.1 are the spec)
5. `head` / `sportbar` / `.sect` / `.empty` → **ScreenHeader**, **SportFilterBar**, **SectionHeading**, **EmptyState**
6. `.hstrip` + `.dots` → **MatchStrip** with owned index state
7. `toast()` → an imperative **ToastHost** with a queue (the current one appends unboundedly)
8. `zl` / `lvl` / `when` / `hm` → an **i18n-aware format module**; `zl` hardcodes Polish grouping and the `zł` suffix, `dow`/`dowl` hardcode English day names — **the app currently mixes a Polish number format with English weekday names**

## G4. Prototype-only machinery that must be replaced by real state

| Prototype mechanism | Replace with |
|---|---|
| `S.now` + the `#timebar` scrubber + `T.created/commit/rescue/play` | server time + monotonic elapsed; **never the device clock** `[SRC: 5-now_screen_architecture_review.md §E3]` |
| `syncAll()` mutating every match on every render | server-authoritative state; the client re-evaluates *which supplied transition is current*, nothing more |
| `seedMatches()`, `PLAYERS`, `REC`, `CLUBS`, `COURTS`, `CARD` | API resources |
| `S.gallery` / `buildGallery()` / `m.forced` / `demoFar` / `demoNear` / `demoEnd` / `demoCut` | delete; keep the 35-context table as **test fixtures** |
| `SCEN` scenario rail, `#rail`, `#railscrim`, `#mtop` | delete |
| `#phone`, `#stage`, `#statusbar`, `#stagehead` | delete — the app is the app |
| `hm(S.now)` in the header eyebrow | a live-ticking value; decide the tick interval (recommend 60 s, aligned to the minute) |
| `CARD.used/allowed` constants | entitlement API |
| Hardcoded `Hi, Tomek` and `Kraków` | profile + geolocation/home club |
| `S.waitlists` array | server standby records |
| `'You are 2nd on the standby list'` | ⚠ a precise rank for an unobserved event `[SRC: 5-now_screen_architecture_review.md §E4]`. Replace with the pool size: `you and five others are on standby` |

## G5. States the prototype never renders but production must

| Missing state | Required treatment (recommendation) |
|---|---|
| **Initial load** | Skeleton: one 260 px state-card block + three 120 px match-card blocks, `--line2` fill, no spinner |
| **Refreshing** (data present) | Keep content, no skeleton; a 2 px coral progress line under the header |
| **Network error** | Inline card above the strip: *"We can't reach Rakieta. Your matches are as of {time}."* + Retry. **Never blank the screen** — a stale enrolled match is more useful than nothing |
| **Stale data / offline** | Timestamp the strip (`as of 14:02`) and freeze all countdowns rather than letting them drift; the access sheet already promises `Cached on your phone — it works with no signal` and that promise must be kept |
| **Permission denied** (location, notifications) | Never block Now; degrade the travel-minutes line to the club name only |
| **Empty + first run** (no rating in any sport) | `matchFit()` returns `score:null` for every match, so the feed is silently empty. Needs its own copy: *"Finish your rating and we can tell you which matches are even."* + CTA to onboarding |
| **Auth expired** | Full-screen takeover, not an inline card — the money statements on the card would be unverifiable |
| **A match changing state while on screen** | The prototype swaps content instantly. Specify a cross-fade of the facet/alert region only (150 ms), and never move the card's position in the strip mid-swipe |
| **> 6 enrolled matches** | The strip has no limit and no "see all". Decide a cap (recommend 5 + a trailing "See all" card) |
| **Zero entitlement entries left** | MultiSport tag currently renders `0 left` in mint. Needs a neutral variant |

## G6. Defects to fix in transit (not style opinions — behaviour)

1. `ST_TONE['bad']` is undefined → `inventoryLost` renders a colourless dot `[SRC: 3600 vs 3529]`.
2. `ST_TONE.idle` is a white alpha used on a white surface in `matchCard` → invisible dot for every forming/played/waitlisted match `[SRC: 1417]`.
3. `cardOff()` was **not** wrapped by the ecosystem override while `payable()` was, so with a slot discount the struck-through price and the `card −all` test both use the **undiscounted** share `[SRC: 1233 vs 6316]`.
4. `st.cta` / `st.left` are read but never supplied — the per-state CTA and countdown mechanism is dead code `[SRC: 4011 vs the whole ST table]`.
5. `.hstrip` scroll position is lost on every re-render, and the dots reset to index 0 `[SRC: 4277]`.
6. `#scroll-inner` is emitted and never used `[SRC: 1583]`.
7. `formingHeld` hardcodes `You invited Ewa at 19:41` and `Her seat is held until 21:41`; `formingBack` hardcodes `Ola`; `confirmResult` hardcodes `Kuba` and a score; `cancelledClub` hardcodes `08:12` and `standing water on the court` `[SRC: 3603–3608, 3616, 3771, 3755]`. All must become parameters.
8. The screen title and sport bar are inset 30 px while every card is inset 15 px `[SRC: 84 + 117 + 1564]`.
9. `#cta` exists, is styled, and Now never uses it — confirm that Now genuinely has no pinned action before deleting the branch.
10. Every interactive surface on the screen except the sport chips and the tab bar is a non-focusable `<div>`/`<span>` `[SRC: 3989–4016, 1396]`.

---

## Open decisions

| # | Question | Options found in source | Recommendation | Blast radius |
|---|---|---|---|---|
| 1 | What is `[TARGET_STACK]`? | Never substituted in the brief; the review names Expo + `theme.ts` + ADR-0012 | **React Native (Expo) + TypeScript**, tokens in `theme.ts` | Every prop signature in §B; all of §A3–A4 |
| 2 | Body-text scale | 11 · 11.5 · 12 · 12.5 px | **11 / 12 / 14** | Every component; one pass over §A2.2 |
| 3 | Eyebrow scale | 8.5 · 9.5 · 10.5 px | **9.5 only** | State card facets, header, section headings |
| 4 | Card radius | 13 vs 15 | **14 for both** | All cards, sheets unaffected |
| 5 | Are sport colours their own family? | Currently aliases of `--pad/--ten/--squ/--bad` = coral/mint/night2/amber | **Yes — four new hues**; keep state colours untouched | Sport chips, match-card sport tag, glyph dots, and any legend |
| 6 | Idle tone on a light surface | `rgba(255,255,255,.45)` only | **Split into on-dark / on-light tokens**, on-light = `--muted` | `ST_TONE`, match card, state card |
| 7 | `inventoryLost` tone | declares `bad`; no such key | **Map to `ended`** | One row of the state table |
| 8 | Does the state card get a per-state CTA? | `st.cta`/`st.left` read, never written | **Yes — populate it.** `ready` → "Getting in", `needsResult` → "Enter the score", `confirmResult` → "Confirm 6-4, 3-6, 6-2", `cancelled*` → "See alternatives"; everything else keeps "Open match" | Every state row; the action row's layout when a label is long |
| 9 | Fit badge's emphatic state | coral at ≥ 90 | **Trigger on fit × coverage, not score alone**; if coverage is unavailable at launch, drop `.hi` entirely rather than break the coral rule | Match card only |
| 10 | Big start time: Archivo or Plex Mono? | `.num` alone (Archivo) on the state card; `.mono.num` for money | **Plex Mono** | State card only; expect a ~4 % width change at 30 px |
| 11 | Strip index ownership | Not preserved at all | **Component-owned index, preserved across data refresh, reset only on tab change** | Strip, dots, gallery caption, and any deep-link into a specific match |
| 12 | Enrolled-match cap in the strip | Unbounded | **5 + a trailing "See all" card** | Strip, plus a new "Your matches" list screen |
| 13 | Header behaviour | Scrolls away with the content | **Keep it scrolling** (it is a greeting, not a control) but pin the sport bar | Shell layout, scroll restoration |
| 14 | Empty states with no action | Both name an action in prose only | **Add a secondary button to each** | Two empty states |
| 15 | Language of formatters | Polish money format + English weekday names | **Pick one locale and drive both from it** | `zl`, `lvl`, `dow`, `dowl`, `when`, and every string in §F |
| 16 | Does Now show club requests? | `V.home` does not; only the Inbox tab badge does | **Keep them off Now.** The Inbox badge is enough, and the strip is for matches | Now composition, notification design |
| 17 | Countdown ticking | No countdown exists; `st.left` is dead | **60 s tick, minute-aligned**, driven by server time + monotonic elapsed | Header eyebrow, any CTA suffix, deadline copy |
| 18 | Safe areas | None anywhere | **Apply insets to the tab bar, toast and header** | Shell only |

---

## Self-check

1. **Did I read every source completely, including the entire stylesheet?** Yes — all 332 lines of `<style>` verbatim, the full `V.home`, every helper it calls (`head`, `sportbar`, `stateCard`, `matchCard`, `glyph`, `seatSyms`, `matchState`, the whole 33-entry `ST` table plus the two ecosystem additions, `courtHold`, `deadlines`, `payable`, `cardOff`, `matchFit`, the formatters), `render`/`wireStrip`/`ACT`/the three global listeners, the sheet registry entries reachable from Now, plus the two supporting markdown documents.
2. **Did I search for late reassignments of every view and component I documented?** Yes — a file-wide scan found exactly seven (`deadlines`, `courtHold`, `matchState`, `payable`, `freshState` ×2, `render`) plus seven `V.*` view overrides; `V.home` and every component in §B were confirmed to have **no** later reassignment, and the five overrides that change Now are described as composed behaviour in the header table.
3. **Is every value tagged SRC, DERIVED or GAP?** Every non-obvious value carries a tag; token tables inherit the `[SRC]` of the selector or function named in the row or the table's introduction, and every computed figure (content widths, snap step, contrast ratios, the radius ladder) is marked `[DERIVED]`.
4. **Could an agent with only this document build the feature without opening the source?** Yes for structure, tokens, composition, copy, all 35 state payloads, the glyph geometry, and the interaction map. It would build from the recommendations in §G rather than reproducing the prototype's defects, which is the intent.
5. **What did I have to guess?** The target stack (unsubstituted placeholder); the five tab-bar icons (placeholder squares in the source); all pressed/loading/error/offline/skeleton treatments (never rendered); contrast ratios (estimated, not measured); safe-area handling (absent); the `st.cta` labels proposed in Open Decision 8; the reduced-motion substitutes; and the enrolled-match cap. Each is marked `[GAP]` or appears in the Open decisions table.
