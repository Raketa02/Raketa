# ADR-0011 — A locked design system for the club console, expressed as CSS custom properties

- **Status:** Accepted
- **Date:** 2026-08-12

## Context

The club web app was designed before it was built: a v7 HTML prototype
(`raketa-club-console-v7-intent-pool-2.0.html`) established the whole visual language —
36 570 bytes of CSS, 255 selectors, 34 tokens — and it was audited value by value. We
have the unusual luxury of a complete design system arriving *before* the first
component.

That luxury is also the risk. The app will be built largely by AI agents from a fresh
context, one feature at a time. Each session sees a fraction of the UI, and the default
failure mode is obvious: an agent needs a slightly darker green, writes `#0A7355` inline,
and it works. Twenty sessions later there are forty greens, six card paddings and nine
type sizes, and no single change caused it. A design system that lives only in a
reference document does not survive that; the agent must be **unable to reach for a
literal** without it being visibly wrong.

Three further forces:

- **The prototype was not internally consistent.** The audit found six hexes bypassing
  `:root`, two tokens declared and never referenced, 21 type sizes between 7px and 46px,
  nearly every integer from 1 to 16 used as spacing, six contrast pairs below AA at sizes
  where they must pass, and **no `:focus-visible` styles at all** — the app is
  keyboard-hostile as prototyped. Copying it faithfully would copy those in.
- **The prototype injects CSS at runtime in namespaced layers**, where later declarations
  win. It has already produced one live instance of that trap (an active-chip colour
  declared twice). That mechanism must not survive into a real codebase.
- **The colours are load-bearing.** Coral means *live*, mint *settled*, amber
  *provisional*. Colour here is not decoration that can drift a shade; a coral that
  drifts toward red starts to mean *failed*.

Options weighed:

- **Tailwind.** Would re-encode the tokens as utility names, and its arbitrary-value
  escape hatch (`p-[13px]`, `bg-[#E8482B]`) is precisely the door this system needs shut.
- **CSS-in-JS.** A runtime cost and a second source of truth for values, on a product
  whose defining constraint is that a manager scans a dense screen fast.
- **CSS custom properties + CSS Modules.** Zero dependencies, zero runtime, and the
  values live in one file that a reviewer — human or agent — can diff.

## Decision

We will adopt the v7 design system as the club console's **locked** visual contract, in
three artefacts that change together:

1. **`frontend_club/src/shared/ui/tokens.css`** — the single source of every colour, type
   size, spacing step, radius, shadow, duration and z-index. Imported once, from the root
   layout. Components reference `var(--…)`; **a literal hex, px font size or ad-hoc gap
   in a component is a bug.**
2. **`frontend_club/docs/design-system.md`** — the prescriptive rules: the meaning of each
   colour, the five containers, the calendar and demand surfaces, overlays, motion,
   responsive and print behaviour, and the interface copy rules.
3. **`frontend_club/docs/design-system-v7-prototype-audit.md`** — the original
   measurement, kept verbatim and marked archival, because the reason a value was chosen
   is itself information.

Styling is **CSS Modules colocated with the component**. No Tailwind, no CSS-in-JS
runtime, and **no CSS injected at runtime** — the prototype's layering mechanism does not
come with us.

We will **correct the prototype rather than reproduce it**, and every correction is
listed in Part 13 of the design-system doc. The substantive ones:

- **Accessibility.** `--muted` darkens `#6E7F85 → #5C6D73` (3.73 → 4.83 on paper; it is
  the most-referenced token in the system, so one line fixes the two highest-volume
  failures). `--amber` darkens `#9A6A0B → #8A5E09` (4.18 → 5.04 on its soft).
  `--mint-ink` is added (3.54 → 5.08). A **global `:focus-visible`** rule using the
  existing accent closes the keyboard gap.
- **Rule C — white text never sits on `--coral` or `--mint`** (3.89 and 4.07). No text in
  this product reaches WCAG's large-text threshold of 18.66px bold, so "AA-large only"
  means "fails here". White text requires `--coral-ink` / `--mint-ink` / `--mint-deep`;
  `--ink` is the only dark that may sit on coral (4.50). This changes the accent button
  and the hard-hold calendar block — coral and mint remain everywhere they are *marks*
  rather than text beds.
- **Scales, not sets.** Type consolidates from 21 sizes to **11 steps** (every prototype
  use maps within ~1px); spacing consolidates to **10 steps**, keeping the load-bearing
  `11` (between things) and `14` (inside things).
- **Every value becomes a token.** The six raw hexes become `--night-deep`, `--mint-pale`,
  `--mint-deep`, `--coral-line`, `var(--night2)`, `var(--amber)`. Sport tokens resolve
  through `var()` so they cannot drift from the semantic colours they alias, and are
  renamed (`--bad` for badminton collided with the `bad` tag for *at risk*).
- **The demand map's magnitude ramp is quantised into five buckets** with a stated text
  colour per bucket. The prototype's continuous alpha with a flip to white above 0.45
  produced ~2.3:1 text; no continuous ramp can guarantee legible text at every step.

Every contrast ratio quoted was computed against WCAG 2.1, not estimated.

**Scope: the club app only.** The player app has its own design system and its own
tokens. The two apps share a *shape*, never code or values
([ADR-0005](0005-three-app-monorepo-ownership-boundaries.md)).

## Consequences

**Easier**

- An agent with a small context can build a correct-looking screen: pick the meaning,
  take the token, use 11 between and 14 inside. The judgement calls are already made.
- Visual drift becomes reviewable. A literal in a diff is a one-line objection, not an
  argument about taste.
- Rebranding, dark mode or a contrast pass is a change to one file.
- The app is AA-conformant and keyboard-navigable from its first screen, rather than
  after an accessibility audit that finds forty white-on-coral labels.
- The design and the code cannot silently diverge: they are two files with a stated rule
  that they change in the same commit.

**Harder**

- The system is now prescriptive about things engineers usually decide locally — a size
  that is not one of eleven steps requires changing the scale and the doc, deliberately.
  That friction is the point, and it will occasionally be wrong.
- The corrections mean the built app is **not pixel-identical to the prototype**. The
  accent button is `--coral-ink` rather than `--coral`; several sizes shift by up to 1px.
  Anyone comparing against the HTML will see differences and must consult Part 13 rather
  than "fix" them.
- CSS Modules have no compile-time guarantee that a value came from a token. Until a
  linter enforces it (a stylelint rule banning literal colours and font sizes in
  `**/*.module.css` — worth adding when the app is scaffolded), the rule is upheld by
  review.
- Three artefacts must be kept in sync by discipline.

**Neutral**

- Choosing CSS Modules over Tailwind is reversible in principle, but the tokens are the
  durable part; a future Tailwind config would consume the same custom properties.
- The demand surfaces (heat map, demand map, timeline, match cards) are specified
  visually while their **domain** concepts are still unmodelled — Bookings, Courts and
  Matches are Part 2 of [`CONTEXT.md`](../../CONTEXT.md). The design doc uses *interface*
  names and says so; when those contexts are modelled, the domain terms are settled in
  the root glossary first and the UI renames to match. The design system is explicitly
  **not** the place domain naming gets decided.
