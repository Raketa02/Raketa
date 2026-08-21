# ADR-0082 — The tab bar is one stock outline family, and coral alone says which tab you are on

- **Status:** Accepted
- **Date:** 2026-08-22
- **Closes:** [ADR-0012](0012-player-app-design-system.md)'s one deliberately-open item — *"the glyph set for tab icons is deliberately still open … `@expo/vector-icons` … is the likely answer, but choosing it is a separate decision"*
- **Ratifies and amends:** `rakieta-now-section-ui-spec.md` §A5.2's `[GAP]` and its **Decision to ratify**; overrides §B13's badge colour
- **Answers:** [#49](https://github.com/Raketa02/Raketa/issues/49) — *"Five glyphs the tab bar has never had"*
- **Evidence:** branch [`prototype/tabbar-glyphs`](https://github.com/Raketa02/Raketa/tree/prototype/tabbar-glyphs) — five tab bars built on the real kit and looked at

## Context

The five tab-bar icons have never existed. `.tab i` is a **16 px rounded square of
`currentColor`** and the create tab a **28 px coral one** — placeholders that have shipped
in the prototype for months. `UI` §A5.2 marks them `[GAP]` and recommends *"commission five
outline icons at 24 px on a 24 px canvas, 1.75 px stroke, and keep the coral filled circle
for create"*. ADR-0012 declined to choose, and left the question with a name attached to it
and no decision.

Now renders the tab bar, so Now is the first screen that needs the answer.

Five bars were built on the real kit — real `theme.ts`, real Archivo, an iOS simulator —
and rendered underneath enough of Now to expose the two collisions that a bar in a vacuum
hides: **Padel *is* `coral`**, the same coral the selected tab uses, 300pt away on the same
screen; and the create control is **28pt against everything else at 16pt**. Width was
clampable to 320pt and the specified Inbox badge was switchable.

Three findings came out of building it, before anyone looked at anything.

**`@expo/vector-icons` costs nothing.** It ships *inside* the `expo` package. The prototype
imports Feather, Ionicons and MaterialIcons, and `pnpm typecheck` passes with no line added
to `package.json`, no install, and no Metro configuration. ADR-0012's "likely answer" turned
out to be already present — which removes the only real argument for the commissioned SVG
set §A5.2 recommends. **We are not paying for what we already have.**

**Labels-only could only win by overriding a UI authority.** A bar with no glyphs at all was
built, because a placeholder square that shipped this long is weak evidence anyone missed
them. It does not survive its own geometry: §B13 fixes the tab label at **8.5/600**, and
five words at 8.5pt cannot carry a bar by themselves. The variant was only legible after the
label grew to 11pt — a value two UI authorities state. So "no icons" is not the cheap option;
it is a request to amend the type scale, and it has to win on that ground rather than on
this one. It did not.

**One family does cover all five acts.** Feather supplies `home`, `search`, `plus`, `inbox`
and `user`. None of the five is a metaphor anybody has to be taught, none is borrowed from a
second family, and none needs a sport to be drawn.

## Decision

**We will draw the tab bar with Feather from `@expo/vector-icons`, at the 16pt box the
design system already specifies.**

### The five glyphs

| Tab | Glyph | Label |
|---|---|---|
| `now` | `home` | Now |
| `find` | `search` | Find |
| `create` | `plus` | *(none)* |
| `msg` | `inbox` | Inbox |
| `you` | `user` | You |

**The family is fixed; the inventory is these five.** This ADR does not authorise icons
elsewhere in the app. A sixth glyph on a sixth surface is a fresh question, and it inherits
only the family — never a licence to sprinkle.

### The create control is a flat coral circle

**28pt, filled `coral`, radius 14, with Feather's own `plus` knocked out in white, sitting
level with the other four.** This ratifies §A5.2's *"keep the coral filled circle"* over
§B13's `radius: 10`, which describes the placeholder rather than a design; and it declines
to raise the control out of the bar. It is the odd one out at nearly twice the size and in
the only filled shape on the bar — that is enough to say *this is not a fifth destination*
without also breaking the bar's top line.

**The white plus is allowed where a white numeral is not, and the reason is not aesthetic.**
`theme.ts` Rule C forbids white **text** on `coral` — white on coral is **3.89:1**, under the
4.5:1 that WCAG 1.4.3 requires of text. A glyph is **non-text content**, governed by 1.4.11,
whose threshold is **3:1**. 3.89 clears it. So the plus is white and the badge below is not,
and the two are one rule rather than two opinions.

### The Inbox badge is `ink` on `coral`

§B13 specifies the badge as **white on `coral`** — 3.89:1. A badge is a **numeral**: it is
text, it is read, and 1.4.11 does not cover it. So the pill stays `coral` and the numeral
becomes **`ink`, 4.50:1** — the one dark Rule C permits on coral.

This overrides a UI authority on a value it states, on the ground
[ADR-0063](0063-where-a-player-plays-is-declared-and-precision-follows-the-anchor.md)
established: a UI authority is final on design, and a measured accessibility failure is not
a design disagreement.

### The selected tab is coral, and nothing else

Feather is a **font, not SVG**. There is no filled counterpart to `home`, no `strokeWidth`
prop, no per-glyph weight. So selection is carried by colour alone: **`coral` selected,
`muted` resting**, exactly as §B13 says.

**We are accepting a known failure, not overlooking one.** `coral` (#E8482B) against `muted`
(#5C6D73) is **1.39:1** — the two are within a hair of the same lightness, so in greyscale,
or to a player with a red-green deficiency, *the selected tab is not distinguishable from the
other four*. That is WCAG **1.4.1 Use of Colour**, unmet, on the app's primary navigation.

Two things bound the cost, and they are why this is acceptable rather than merely convenient:

1. **Assistive technology is unaffected.** `UI` §a11y already requires `role="tab"` /
   `accessibilityState={{ selected }}`, so VoiceOver and TalkBack announce the selected tab
   correctly. The exposure is sighted-only.
2. **The fix is pre-costed and needs no family change.** A **3pt `coral` dot, 3pt under the
   selected label** restores a non-colour cue with one element and no new dependency. It was
   built and looked at.

Recording the fix here is the point: a later accessibility pass must find **a decision with
a named remedy**, not a gap it has to re-derive.

## Consequences

**Easier**

- A build agent can render the tab bar today. The family, the five glyph names, the box, the
  create treatment, the badge colour and the selected cue are all fixed, and every one of
  them resolves against a package already in `node_modules`.
- No commissioned icon set, no SVG pipeline, no designer in the loop, no asset licence — the
  three costs §A5.2's recommendation carried are all avoided.
- The 16pt box, `size.tabIcon`, needed no change: Feather scales to it cleanly, so nothing in
  `theme.ts` moves.

**Harder**

- **The primary navigation does not meet WCAG 1.4.1.** Stated plainly because it is the real
  price of this ADR. It is bounded, remediable and knowingly taken — but until the dot ships,
  a colour-blind player cannot see which tab they are on.
- **Feather being a font forecloses tuning.** No stroke weight, no fill, no optical size. §A5.2
  recommended 1.75 units on a 24 canvas; Feather draws **2**, and that is not adjustable. If a
  future surface genuinely needs a filled or heavier glyph, it needs a second family or a
  hand-drawn SVG, and **this ADR authorises neither** — it would be a new decision, and it
  would have to argue with the one-family finding above.
- Selection now depends on `muted` staying visually distant from `coral`. It is not distant.
  Anyone re-tuning either token is re-tuning the tab bar, and nothing mechanical says so.

**Neutral**

- Ionicons was the only variant that carried selection without colour — outline resting,
  filled selected — and it lost on the glyph set rather than on that mechanism. If the dot
  proves unsatisfying in use, **switching family is the other way to fix 1.4.1**, and the
  prototype branch holds a working version of it.
- The tab label's **8.5/600** is the smallest type in the app and has no `theme.type` token.
  It stays that way. This ADR notes it only because the labels-only variant is what surfaced
  it, and the next person to want a token will find the size already load-bearing.
