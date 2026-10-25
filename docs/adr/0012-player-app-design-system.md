# ADR-0012 — A locked design system for the player app, translated from web prototype to native

- **Status:** Accepted — **its *Consequences*' *AA-conformant … and screen-reader navigable from
  its first screen* amended 2026-10-25 by
  [ADR-0198](0198-the-player-app-is-not-built-for-screen-readers-for-now.md).** For now the app is
  not built for screen readers or the phone's accessibility settings, and nothing already built is
  removed. AA contrast, 44 × 44 pt targets and a name on every pressable stand. A dated note marks
  the passage below.
- **Date:** 2026-08-12

> **Note — the 2026-08-25 reset.** It cites **ADR-0011** (the club console's design system), removed in the 2026-08-25 reset. Every comparison to the club console below is a comparison to a system that no longer ships; this ADR's own rules for the player app are unchanged. See the [ADR index](README.md#the-2026-08-25-reset--why-the-sequence-has-gaps). This ADR's body is left as written: an accepted ADR is immutable, and the reason a past decision looked right is itself information.

## Context

Like the club console (**ADR-0011** *(removed)*), the player app was
designed before it was built: a v34 HTML prototype
(`raketa-player-app-prototype-v34.html`) established the whole visual language and was
audited value by value, including an honest list of its own inconsistencies and
accessibility gaps.

The same force applies here as there — the app will be built by agents one feature at a
time, each seeing a fraction of the UI, and a design system that lives only in prose does
not survive that. But this app adds a problem the club app does not have.

**The prototype is a web page and the product is not.** That gap is not cosmetic:

- **Half the prototype is scaffolding.** Above 900px it renders the app inside a 392×788
  phone frame on a dark stage, with a 290px scenario rail for stepping through 32 states
  and a time bar. Four hard-coded colours exist only to paint that harness. An agent
  reading the audit as a spec would build a phone frame inside a phone.
- **Several CSS constructs have no React Native equivalent**, and the naive translations
  are all wrong in the same direction — they compile and then quietly misbehave.
  `fontWeight` is ignored on Android when a custom family is set. `letterSpacing` and
  `lineHeight` are points, not em and multiples, so copying `-.035em` yields a
  35× error. `:hover` does not exist. `box-shadow` spread does not exist.
- **Fixed pixel geometry does not survive real devices.** The prototype's content width is
  a constant 362px, and the match rail's 268px child is what creates the "next card
  peeking" affordance. On a 320pt phone, 268 leaves no peek at all — the affordance is a
  *ratio* that was written down as a constant.
- **Two requirements could not exist in a web prototype at all:** 44pt touch targets and
  screen-reader semantics. The prototype's controls are 23–32px tall.

The prototype's own audit also under-reports its accessibility problems. It records
`.tiny` at 3.9:1 and stops there. Computation finds five more: the band names are drawn in
values that are 2.83–3.20:1 on paper; the empty-seat avatar's dashed border — *the only
dashed element in the app, and the one that means "a place that could be filled"* — is
1.17:1; the free-slot border is 1.27:1; and white sits on `coral` and `mint` in four
places at 3.89 and 4.07.

## Decision

We will adopt the v34 design system as the player app's **locked** visual contract,
translated for React Native, in three artefacts that change together:

1. **`frontend_player/src/shared/ui/theme.ts`** — the single source of every value, as a
   frozen typed object. Components read from it via `StyleSheet.create`; **a literal hex,
   font size or gap in a component is a bug.** Chosen over NativeWind (whose
   arbitrary-value escape hatch is the door this system exists to shut) and over a themed
   styling library (another dependency, and Restyle pushes toward its own primitives).
   Zero new styling dependencies, and a wrong token is a typecheck error rather than a
   silent string.
2. **`frontend_player/docs/design-system.md`** — the prescriptive rules, opening with a
   **Part 0 that separates the harness from the product** and tabulates every web→native
   translation before any styling is described.
3. **`frontend_player/docs/design-system-v34-prototype-audit.md`** — the original
   measurement, verbatim and marked archival.

**The harness does not ship.** The phone frame, the stage, the scenario rail, the time bar,
the mobile top bar, the 900px breakpoint and their four colours are recorded as prototype
scaffolding and dropped from the palette.

**Fixed geometry becomes derived geometry.** Content width is `screen width − 30`; the
rail card is `0.74 × content width`; the toast clears the tab bar plus the bottom safe-area
inset. No layout constant survives that encoded a 392pt phone.

We will **correct the prototype rather than reproduce it** — the same policy as ADR-0011 —
and every correction is listed in Part 14 of the design-system doc. The substantive ones:

- **Rule C**, identical to the club app: white text never sits on `coral` (3.89) or `mint`
  (4.07); it needs `coralInk` (5.89) or `mintInk` (5.84), and `ink` is the only dark that
  may sit on coral (4.50). This changes the primary button, the high fit badge, the success
  toast and the *me* avatar.
- **Accessibility.** `muted` darkens `#6E7F85 → #5C6D73` (fixing the audit's own headline
  failure); `amber` darkens `#9A6A0B → #8A5E09`; `mintInk` is added; each band gains an
  **`ink`** value at 4.51–4.59 on paper for text and rails, leaving `tint`/`deep` for the
  bar; the empty-seat avatar's dashed border moves to `muted` and the free-slot border to
  `mint`, so both are actually visible. Toasts announce themselves, the sheet and popover
  are real modals, and everything tappable carries a name, a role and a state.
- **44 × 44pt minimum reachable area** on every control, with `hitSlop` presets in the
  theme. The visual sizes are unchanged.
- **A 3pt spacing grid** — 3, 6, 9, 12, 15, 18, 24, 30. The audit records "no spacing
  scale"; in fact every value it lists (5, 6, 7, 9, 10, 11, 12, 13, 14, 15) is within 1pt
  of a multiple of 3. The grid was already there and unnamed.
- **One implementation of the shared components.** The prototype maintained a parallel copy
  of the match card, band bar and popover in its deck, kept in sync by hand, and records
  that they had drifted. The match card, state card, level bar and popover are shared
  components from the first commit.
- **The popover renders through a root overlay host**, so the dark card's child-repaint
  never reaches it — fixing the containment rather than keeping the prototype's three
  counter-overrides.

**Two dependencies are added** because the design system cannot be implemented without
them: `expo-font`, `@expo-google-fonts/archivo` and `@expo-google-fonts/ibm-plex-mono`.

**There is no dark mode.** The dark card is a component, not a theme. Adding one is a new
ADR, not a styling change.

**Scope: the player app only.** The two clients' palettes converge because it is one brand,
but the values are duplicated deliberately — no shared package, no cross-import
([ADR-0005](0005-three-app-monorepo-ownership-boundaries.md)).

## Consequences

**Easier**

- An agent with a small context can build a correct screen: pick the meaning, take the
  token, 9 between cards and 15 at the gutter. The judgement calls are already made.
- The four React Native traps that silently degrade typography and touch on one platform
  are closed by the shape of the theme, not by remembering.
- The app is AA-conformant, thumb-reachable and screen-reader navigable from its first
  screen, rather than after an audit that finds four white-on-coral labels and an invisible
  empty-seat marker.
  > **Amended 2026-10-25 by [ADR-0198](0198-the-player-app-is-not-built-for-screen-readers-for-now.md).**
  > *AA contrast* and *thumb-reachable* stand. *Screen-reader navigable* no longer does, and nor
  > does full AA conformance: the fixed ten seconds of *Undo* miss WCAG 2.2.1.
- A rule learned in the club app mostly transfers: same palette meanings, same Rule C, same
  card/note/row vocabulary. The instruction surface across two stacks is smaller than two.

**Harder**

- The built app is **not a pixel copy of the prototype**. The primary button is `coralInk`,
  band names are darker, several spacings shift by 1pt, and the frame is gone entirely.
  Anyone comparing against the HTML must consult Part 14 rather than "fix" the differences.
- `StyleSheet.create` is verbose for variant-heavy components — the note has five tones and
  the button four. That verbosity is the cost of not adding a styling framework.
- Nothing mechanically enforces "no literals" in TS. Until a lint rule exists (an
  ESLint `no-restricted-syntax` on colour literals and numeric `fontSize` in `*.tsx` is
  worth adding once the app is scaffolded), the rule is upheld by review.
- The theme has more surface than a CSS `:root` — band triplets, hitSlop presets, per-role
  point-converted tracking. It is more to read before the first component.

**Neutral**

- The glyph set for tab icons is deliberately still open. The system specifies the 16pt box
  and the position; `@expo/vector-icons` ships with Expo and is the likely answer, but
  choosing it is a separate decision and squares remain the honest placeholder until then.
- The demand/level concepts these surfaces render — bands, confidence, match fit, holds —
  are **not yet in the shared glossary**; Bookings, Courts and Matches are Part 2 of
  [`CONTEXT.md`](../../CONTEXT.md). The design doc uses interface names and says so. As with
  ADR-0011, the design system is explicitly **not** where domain naming gets settled.
