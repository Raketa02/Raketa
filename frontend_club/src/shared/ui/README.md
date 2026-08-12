# `src/shared/ui/` — design-system primitives

The club console's design system, in code. Generic and feature-agnostic: if something
here starts to know about courts, bookings or clubs, it belongs in a feature instead.

**The rules live in [`../../../docs/design-system.md`](../../../docs/design-system.md).**
Read it before adding anything here. The decision to have a locked design system at all
is [ADR-0011](../../../../docs/adr/0011-club-console-design-system.md).

## `tokens.css` — the source of values

Every colour, type size, spacing step, radius, shadow, duration and z-index in the app.
Imported **once**, from `src/app/layout.tsx`. Never imported by a feature.

```tsx
// src/app/layout.tsx
import '@/shared/ui/tokens.css';
```

`tokens.css` and `docs/design-system.md` change **together, in the same commit**. A value
in one and not the other is the failure mode this whole setup exists to prevent.

## Styling approach

**CSS Modules**, colocated with the component (`Card.tsx` + `Card.module.css`). No
Tailwind, no CSS-in-JS runtime, no styles injected at runtime.

```css
/* Card.module.css */
.card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  padding: var(--s-6);
}
```

A literal in a component stylesheet — `#E8482B`, `font-size: 12px`, `gap: 10px` — is a
bug. If a value you need genuinely does not exist, that is a change to `tokens.css` and
to the design-system doc, not a local override.

## The five containers

Nearly every screen is built from these. **Check this list before building anything new** —
the system's coherence comes from re-use, not from new parts.

| Container | Purpose |
| --- | --- |
| **Card** | The default surface. 1px `--line` on `--surface`, 13px radius, 14px padding. Never a shadow. |
| **Stat tile** | key → value → description. The description is not optional. |
| **Note** | Reasoning. The one place a paragraph is acceptable. Square left, rounded right. |
| **Row list** | The label/value workhorse. `border-top` with a `:first-child` reset. |
| **Action row** | A 4px severity rail plus a body. The only vertical colour bar in the system. |

Plus the controls: button, chip, pill, segmented control, toggle, tag, avatar, progress,
empty state — specified in Part 5 and Part 6 of the design-system doc.

## Non-negotiables

- `--line` **bounds a thing**; `--line2` **separates rows within a thing**. Getting this
  wrong makes one card read as five.
- **11 between things, 14 inside things, 13 radius on cards.**
- **Rule C:** white text never sits on `--coral` or `--mint`. It needs `--coral-ink`,
  `--mint-ink` or `--mint-deep`. `--ink` is the only dark that may sit on `--coral`.
- `--volt` on dark surfaces only.
- **Every state carries a word**, not just a colour.
- **Every number carries a sentence.**
- Never remove the global `:focus-visible` outline.
- Cards cast no shadow. Only the sheet, drawer, toast and mobile nav do.

## Components are built with the features that need them

This folder is deliberately not pre-populated. A primitive lands here when a second
feature needs it — before that, it lives in the feature and has one real caller to
validate its shape.
