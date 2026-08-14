# `src/shared/ui/` — design-system primitives

The player app's design system, in code. Generic and feature-agnostic: if something here
starts to know about courts, bookings or matches, it belongs in a feature instead.

**The rules live in [`../../../docs/design-system.md`](../../../docs/design-system.md).**
Read it before adding anything here — in particular its Part 0, which separates the
prototype's _harness_ from the product. The decision is
[ADR-0012](../../../../docs/adr/0012-player-app-design-system.md).

## `theme.ts` — the source of values

Every colour, type role, spacing step, radius, metric, shadow and duration. Frozen,
typed, and imported directly by components:

```tsx
import { StyleSheet } from 'react-native';
import { theme } from '@/shared/ui/theme';

const s = StyleSheet.create({
  card: {
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
    padding: theme.space.md,
    marginBottom: theme.space.sm,
  },
});
```

A literal in a component — `'#E8482B'`, `fontSize: 12`, `padding: 10` — is a bug. If a
value you need genuinely does not exist, that is a change to `theme.ts` **and** to the
design-system doc, in the same commit.

## Four React Native traps this system exists to prevent

1. **`fontWeight` is ignored on Android** when a custom `fontFamily` is set. Weight is a
   _family name_: use `theme.font.sans[700]`, never `fontWeight: '700'`. This is the most
   common way an RN app silently loses its typography on one platform.
2. **`letterSpacing` and `lineHeight` are in points**, not em or multiples. `theme.type`
   and `theme.num` carry pre-converted values — never re-derive them.
3. **Touch targets.** Nothing tappable may have a reachable area under **44 × 44pt**. The
   visual stays small; use `theme.hit.*` to grow the target.
4. **There is no hover.** Every pressable declares its pressed appearance explicitly —
   see the design system's 6.6.

## Non-negotiables

- `line` **bounds a thing**; `line2` is a **fold inside one thing**.
- **9 between stacked cards, 15 at the gutter.** Everything else from the 3pt grid.
- **Rule C:** white text never sits on `coral` or `mint` — it needs `coralInk` or
  `mintInk`. `ink` is the only dark permitted on `coral`.
- `volt` on dark surfaces only.
- **Cards never cast a shadow.** Three shadows exist; all are for things that float.
- **Every number is mono and tabular.** That is the mechanism that stops a row reflowing
  when a level changes from 2,71 to 2,80.
- **Every state carries a word or a shape**, never colour alone.
- **Content width is screen width − 30.** Never a fixed 362 or 392 — those are the
  prototype's phone picture.
- Band **`ink`** for text and rails; `tint`/`deep` for the bar only.

## Fonts

Archivo (400–800) and IBM Plex Mono (400–600), loaded with `expo-font` in the root layout
and **awaited before the splash screen hides** — a font that arrives late reflows every
number on screen.

## Components are built with the features that need them

This folder is deliberately not pre-populated, with one exception worth knowing: the
**match card**, the **state card**, the **level bar** and the **popover** are shared
components from the start. The prototype maintained a second copy of each in its deck and
recorded that they had drifted — one implementation, used everywhere.

Built so far, by the onboarding slice: `Button`, `Card` (+ `PressableCard`), `Note`,
`Bar`, `ScreenHeader`, `Tag`, `Hairline`, `BottomSheet`, `CloseControl`, `DarkCard`,
`Row`, `LevelBar`, `ConfidenceRing`, `Popover` (+ `InfoMark`) and `InfoGlyph`. Import them
from `@/shared/ui`.

**Overlays.** `BottomSheet` and `Popover` are both real modals, and 9.1's and 7.6's "it is
a real modal" is three separate obligations rather than one prop — read `overlay.ts` and
either docblock before adding a third. Two of them are the caller's: the screen behind
spreads `behindOverlay(open)`, and the overlay is rendered as that screen's _sibling_,
never inside it. `CloseControl` is 9.1's close circle, shared because the header control
that opens a sheet, the sheet's own close and the popover's are the same 28pt object;
`InfoGlyph` is shared for the same reason between the info note and the popover's mark.

**Drawn objects.** `LevelBar` (7.5) and `ConfidenceRing` (7.8) are geometry, not styling —
their values are `theme.size.levelBar` and `theme.size.ring*`, and both keep a fixed scale
(1,00–5,00 and 0–100) so a value lands in the same place on every screen that draws one.
`ConfidenceRing` is the only component that needs `react-native-svg`. Both take a
`variant`/repaint for the dark card, because React Native has no colour cascade.

**A feature never keeps a second copy of one of these.** If a primitive does not do what
a screen needs, extend the primitive — the two auth-form controls that remain in
`features/auth/components/AuthControls.tsx` are there because the design system genuinely
specifies no text field and no _ended badly_ note variant, and each says so in place.
