# Spec delta — Now's geometry on the native kit

**Governs over** `1-now_screen_production_spec.md` §329's *"362px content width as a maximum
— on a wider phone the column stays 362px and centres"*, and over the two documents'
treatment of the strip's peek. Everything else in them stands unchanged and remains final.

**Authority for this file:**
[ADR-0012](../../../adr/0012-player-app-design-system.md) Part 0.1 — *the harness is not
the app* — read together with
[ADR-0036](../../../adr/0036-a-ui-document-is-final-on-the-screen-not-on-the-arithmetic.md).
**The evidence:** the prototype on branch
[`prototype/now-native-kit`](https://github.com/Raketa02/Raketa/tree/prototype/now-native-kit),
built on the real kit and measured at 320, 375, 393 and 430 pt.
**The reasoning:** [`Raketa02/Raketa#11`](https://github.com/Raketa02/Raketa/issues/11).

The source documents are **not edited**. 486 `[SRC: line N]` citations and 27 bare-filename
cross-references resolve against their bytes.

---

## 1. Content width — §329 is superseded

| §329 as written | What governs |
|---|---|
| The 15px gutter **and** the 362px content width carry over; 362 is a **maximum**, and the column centres rather than stretching on a wider phone | Only the **15pt gutter** carries over. **Content width = screen width − 30**, at every width, with no cap and no centring |

**Why the direction is this way.** 362 is not a measured design value; it is `392 − 30`, and
the 392 is the width of `#phone` — the picture of a phone the prototype draws itself inside.
ADR-0012 Part 0.1 already ruled that `#phone` is harness and does not ship. §329 carries the
gutter and the content width forward as a pair, but only one of them is a design decision:
the gutter is chosen, the 362 is arithmetic performed on the frame. Treating the derived
number as a constraint would put paper margins on a 430pt phone in order to preserve a
measurement of a stage prop.

This is not a UI document being overruled on the screen. It is ADR-0012's existing
harness/app boundary applied one line further than §329 applied it, and ADR-0012 already
states the replacement rule in Part 0.2 — as does `theme.space.lg`, verbatim:
*"THE HORIZONTAL PAGE GUTTER. Content width = screen width − 30."* **No code changes.**

**What this costs, recorded honestly.** §329's stated reason — *"every internal proportion
on the state card and the glyph is tuned to it"* — is real. The 58pt court glyph is fixed,
so between 320 and 430 the whole 110pt of extra column is absorbed by the identity column,
the two facet columns and the fact-list measure. Built and looked at, it holds; if a later
screen shows it does not, the fix is to scale the glyph, **not** to reinstate the cap.

## 2. The strip's peek — the ticket's premise, corrected

`5-now_screen_architecture_review.md` and ADR-0012's Context both describe the peek as
created by *"the match rail's 268px child"*, and conclude that on a 320pt phone 268 leaves
no peek, so the affordance is *"a ratio that was written down as a constant"*.

**That is true of `.mrail`, and `.mrail` is not on this screen.** `UI` §D5 states it:
*"`.mrail` — a `.sqrow` whose children are 268px cards — **not used by Now**"*. Now's strip
is `.hstrip`, whose child is `flex: 0 0 100%` of the content box with the strip bled to the
frame edge.

| | Card width | Peek at 320 | Peek at 430 |
|---|---|---|---|
| `.hstrip` — what Now uses | content width | **5pt** | **5pt** |
| `.mrail` at `railCardRatio` 0,74 | 0,74 × content | 65pt | 94pt |

**The peek is `gutter − gap` = 15 − 10 = 5pt, at every width.** It is not a ratio, it is not
a constant, and it does not depend on the card width at all — which is why it survives 320pt
untouched while `.mrail` does not.

Consequences:

- **`size.railCardRatio` (0,74) is correct for the component it was written for and must not
  be applied to Now's strip.** Applying it produces a card 94pt narrower than the column at
  430, showing a quarter of the *next card's contents* — its alert box, its fact lines — which
  reads as two cards, not as a peek.
- **`frontend_player/docs/design-system.md` §7.7 documents one rail and Now needs a second.**
  §7.7 stays as it is; the `.hstrip` geometry is added beside it, and its entry must say that
  the peek is a consequence of the gutter and the gap rather than a number of its own.
- **5pt is kept**, and the dependency is recorded: the peek only has to *confirm* what the
  page dots beneath the strip and the `swipe →` hint in the section heading already say.
  **If either is ever dropped, this is no longer sufficient and must be revisited.**

## 3. Card height — what the 788pt frame hid

`.hstrip` children are laid out in a row, so the strip takes the height of its **tallest**
child. Measured at 320pt, `heldSoft` — five fact lines and a Court value that wraps to three
— is roughly 640pt tall, against a 568–667pt screen. Two consequences the frame could not
show, because it was 788pt tall:

1. **The fullest card's action row falls below the fold** on a 320pt phone.
2. **Short contexts float in a slab of empty night.** `ready` carries two fact lines and is
   stretched to the tallest card's height.

**Decision.** The action row takes `marginTop: auto`, so footers align across cards of
differing height. This is not a new rule: `design-system.md` §7.7 already states it for the
rail — *"`marginTop: auto` on the last hairline pushes the footer to the bottom so footers
align across cards of differing height"* — and it removes the slab.

**The overflow is accepted, not fixed.** Now is *a status surface before a search box*: on
this screen reading is the primary act, and clamping the fact list would delete copy the
specification chose deliberately — `heldSoft`'s fifth line is *"Leaving now returns
everything, in minutes"*, the line that tells a player they can get out. A clamp would hide
the exit. Recorded as a thing to watch rather than a thing to pre-empt.

## 4. Colour on the surface it actually lands on

Two values in `UI` §A1.2/§E5 are specified once and used on both a light and a dark surface,
and are legible on only one of them. Both become **surface-aware**, which is the same
principle in both cases: a colour is chosen for its meaning, but it must be legible on the
surface it lands on, and one hex cannot promise that across two surfaces.

| Value | As written | What governs |
|---|---|---|
| Empty-seat ring, `glyph()` | `#E8482B` (coral), dashed — **1,17:1** on the on-night court fill (ADR-0012) | **White on the dark glyph, `muted` on the light one.** The **dash** carries *"a place that could be filled"* — it is the only dashed element in the app, so the shape is already unique without the hue — and coral is freed to mean only *"yours"*, which is the filled `me` dot inches away in the same glyph |
| `ST_TONE.idle` | `rgba(255,255,255,.45)` — fine on the dark card, **≈1,0:1 on the light match card**, so every `forming` / `played*` / `waitlisted` feed row draws a blank dot | `rgba(255,255,255,.45)` on dark, **`muted`** on light |

Two further §B6.3/§E5 defects need **no** decision here, because they are already settled:

- **`inventoryLost` declaring `tone: 'bad'` where `ST_TONE` has no `bad` key**, so the dot
  renders with `background: undefined`. [ADR-0031](../../../adr/0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md)
  already moves `inventoryLost`'s tone to `ended`. The defect dies with the retone.
- **White on `coral` at 3,89** — v37's primary CTA and its `.hi` fit badge. ADR-0012's
  Rule C already forbids it and `design-system.md` Part 14 already records the correction:
  `coralInk`, not `coral`.

## 5. What the theme cannot express yet

Every value below is written as a literal in the prototype with a `MISSING TOKEN` comment
beside it. A literal in a production component is a bug ([ADR-0012](../../../adr/0012-player-app-design-system.md)),
so each is a value `theme.ts` has to grow before the state card can be built for real.

| Needed | Nearest thing the theme has |
|---|---|
| 30pt Archivo 700, tracking −1,05, lineHeight 30 — the state card's start time | Nothing. `theme.num.*` is **entirely IBM Plex Mono**, so the one figure in the feature large enough for its tracking to be visible has no role |
| 8,5pt eyebrow — the state card's Court/Group labels | `type.eyebrow` at 9,5. §E5 also measures 8,5 on-dark at 4,3:1, failing at that size |
| 12pt Archivo 600 — the `when · club` line | `type.inlineTitle` at 12,5 |
| 11pt at lineHeight 14,85 — the facet values | `type.tiny` at 11/16 |
| padding 13 (state card) and 11 (match card) | `space` has 12 and 15. Neither 13 nor 11 is on the 3pt grid ADR-0012 adopted |
| Alert box `#D64D3A` at 16 % fill / 40 % border | **Not** `color.red` (`#B4392C`). A distinct hex the palette does not hold |
| On-dark tag fill at **0,17** | `color.onDarkTag` is **0,14** |
| On-dark line text `rgba(255,255,255,.92)` and unchecked ring `rgba(255,255,255,.75)` | Nothing between `onDarkTiny` (0,68) and white |
| Court-glyph fills: `#EEF2F1`, `#D8DFDD`, and on-night `rgba(255,255,255,.1 / .3)` | Nothing |
| **IBM Plex Mono 700** — the 14pt payable amount | The family loads **400/500/600 only**. Weight is a family name on Android, so 700 is **unreachable**, not merely unwritten. Either load it or ratify 600 |

One divergence in the opposite direction: `UI` §B7 draws the tag's leading dot **round**
(`border-radius: 3px` on a 6px box), and the shipped `Tag` draws it **square**, reserving the
round form for the sport dot. The shipped component carries more information than v37 did and
**governs**; it belongs in `design-system.md` Part 14 as a correction applied to the
prototype, so a later reader does not "fix" it back.

## 6. What ported with no loss

Recorded so nobody re-opens them:

- **`box-shadow` spread is a non-issue on this screen.** §A3.3: *"Inside the phone, the Now
  section uses no shadows at all"* — elevation is a refusal in this design, and `.card-n` has
  none. The only spread shadow anywhere near Now is the long-press ring
  `box-shadow: 0 0 0 3px var(--coral-soft)`, which is zero-blur — an outline, reproduced
  exactly by a wrapper `View` with a border.
- **`scroll-snap-type: x mandatory` + `scroll-snap-stop: always`** → `snapToInterval` +
  `disableIntervalMomentum` + `decelerationRate="fast"`. One flick moves one card. Verified
  on device.
- **`glyph()`** ports to `react-native-svg` — already a dependency — with every ratio in
  §A5.1 intact.
- **44 × 44pt reachable area is satisfiable at 320pt without changing a single visual size.**
  The chips already have `hit.chipSm`; the CTA has `hit.btn`. The one gap is the two 40 × 34
  icon buttons, which have no preset — `hit.btn` is vertical-only and leaves them 40 wide.
  Add `hit.iconBtn = { top: 5, bottom: 5, left: 2, right: 2 }`.
