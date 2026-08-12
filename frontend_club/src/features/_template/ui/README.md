# `ui/` — this feature's components

Rendering and interaction only. Feature **composites** (`BookingStatusBadge`,
`CourtAvailabilityGrid`) built from the primitives in `@/shared/ui`.

> This README is part of `_template` and travels into every feature you create. Do not
> delete it — it is the local reminder that the design system is not optional.

## Read this before you write a component

**The design system is locked.** Its rules are in
[`docs/design-system.md`](../../../../docs/design-system.md) — 14 parts, ~1150 lines,
readable in one pass. Its values are in
[`src/shared/ui/tokens.css`](../../../shared/ui/tokens.css). The decision to lock it is
[ADR-0011](../../../../../docs/adr/0011-club-console-design-system.md).

**You are not designing. You are assembling from a system that already made these
decisions.** Building a surface the document does not describe means extending the system
deliberately (design-system.md Part 13/14), not inventing beside it.

## The rules that get broken here

- **A literal value is a bug.** `#E8482B`, `font-size: 12px`, `gap: 10px` — every colour,
  size, space, radius, shadow, duration and z-index comes from `tokens.css` as `var(--…)`.
  If the value you need genuinely does not exist, that is a change to `tokens.css` **and**
  to the design-system doc, in the same commit — never a local override.
- **Styling is CSS Modules, colocated** — `BookingTable.tsx` + `BookingTable.module.css`.
  No Tailwind, no CSS-in-JS, no runtime-injected styles.
- **Check the five containers first** — card · stat tile · note · row list · action row
  (Part 5). Nearly every screen is one of these. The system's coherence comes from re-use,
  not new parts.
- **`--line` bounds a thing; `--line2` separates rows within a thing.** The most common
  visual error: a card whose internal rows use `--line` reads as five cards.
- **11 between things · 14 inside things · 13 radius on cards.**
- **Colour is picked by meaning, never appearance.** coral = live · mint = settled ·
  amber = provisional · red = failed. Amber and red are not a severity gradient.
- **Rule C — white text never sits on `--coral` or `--mint`.** Use `--coral-ink` /
  `--mint-ink` / `--mint-deep`. `--ink` is the only dark that may sit on coral.
- **`--volt` on dark surfaces only.**
- **Every state carries a word**, not just a colour. **Every number carries a sentence.**
- **Cards cast no shadow.** Only sheet, drawer, toast and mobile nav do.
- **Never remove the global `:focus-visible` outline.**
- Copy follows Part 12: *off sale*, not soft-held. *Booked*, not confirmed. Polish number
  formatting — `2 474,25 zł`, `1 h`, `65%`, `09:00`.

## A primitive is promoted, not predicted

A component lands in `@/shared/ui` when a **second** feature needs it. Before that it
lives here, with one real caller to validate its shape. A primitive in `shared/ui` must
not know what a booking is; anything that does belongs here.

## Boundaries

`ui/` may import `model/`, `state/`, `schemas/` and `@/shared/ui`. It must **never**
import `api/`, `server/` or `@/generated` — a component that touches a generated response
type welds the backend's serialization shape to the UI.

Accessibility is not a later pass: keyboard operability, visible focus, associated labels,
accessible names on icon buttons, dialog focus trapping, table semantics, and status never
signalled by colour alone.
