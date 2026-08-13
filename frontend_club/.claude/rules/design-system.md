---
paths:
  - "src/shared/ui/**"
  - "src/features/*/ui/**"
  - "src/app/**/*.tsx"
  - "**/*.module.css"
---

# Design system — locked

Full rules: [`docs/design-system.md`](../../docs/design-system.md). The decision:
[ADR-0011](../../../docs/adr/0011-club-console-design-system.md). The standard's §39 says
exactly what ADR-0011 already decided.

Three artefacts that **change together, in the same commit**:

| File | Is |
| --- | --- |
| `src/shared/ui/tokens.css` | The source of every value. Imported once, from `app/layout.tsx`. |
| `docs/design-system.md` | The rules — meanings, containers, surfaces, copy. |
| `docs/design-system-v7-prototype-audit.md` | Archived measurement of the prototype. **Not the rules.** |

**Styling is CSS Modules colocated with the component** (`Card.tsx` + `Card.module.css`),
referencing `var(--…)`. No Tailwind, no CSS-in-JS, no runtime-injected CSS. **A component
never contains a literal value.**

`shared/ui/` primitives must not know what a booking is. A `BookingStatusBadge` or
`CourtAvailabilityGrid` belongs to its feature's `ui/`, composed from those primitives.
Accessibility is encoded **once** in the primitives so features cannot reimplement it
wrongly. *(§39.2, §39.3)*

## The rules an agent gets wrong

- **`--line` bounds a thing; `--line2` separates rows within a thing.** The single most
  common visual error — a card whose internal rows use `--line` reads as five cards.
- **11 between things · 14 inside things · 13 radius on cards.** Everything else follows.
- **Colour is picked by meaning, never appearance.** coral = live · mint = settled · amber =
  provisional · red = failed. Amber and red are not a severity gradient: amber means *the
  clock may still resolve this*, red means *this failed*.
- **Rule C — white text never sits on `--coral` or `--mint`** (3.89:1 and 4.07:1). Use
  `--coral-ink` / `--mint-ink` / `--mint-deep`. `--ink` is the only dark that may sit on
  coral (4.50:1).
- **`--volt` on dark surfaces only.** On paper it is ~1.3:1.
- **Eleven type sizes exist. A twelfth is a bug** — change the scale deliberately, in
  `tokens.css` and the doc, or use an existing step.
- **Cards cast no shadow.** Only the sheet, drawer, toast and mobile nav do.
- **Every state carries a word**, not just a colour — that is what a tag is for.
- **Every number carries a sentence.** A stat description is not optional; a tile that
  cannot justify itself in one line is a vanity metric.
- **Never remove the global `:focus-visible` outline.**
- Copy follows Part 12: *off sale*, not soft-held. *Booked*, not confirmed. *Unearned*, not
  lost revenue. Polish number formatting — `2 474,25 zł`, `1 h`, `65%`, `09:00`.

Before building a new component, check the **five containers** (card · stat · note · row
list · action row). The system's coherence comes from re-use, not new parts.

## Accessibility *(§24)*

WCAG 2.2 AA. Semantic HTML first; keyboard operability; visible focus; associated labels;
accessible names on icon buttons; dialog focus trap and restoration; table semantics; status
never by colour alone; live regions for async feedback; reduced-motion respect.

Desktop does not mean mouse-only — club staff work keyboard-heavy. Prefer contextual
skeletons over blank pages. Make destructive actions proportionally resistant to accidental
clicks.

This design system covers `frontend_club/` **only.** The player app has its own; the
palettes converge because it is one brand, but the values are never shared.
