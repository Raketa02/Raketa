/**
 * The dark card, per design-system 5.2.
 *
 * ```
 * background  night          color   #fff
 * radius      15             padding 15
 * ```
 *
 * **The repaint is the part that does not survive the port unchanged.** 5.2 says the dark
 * card repaints its children — `tiny` to white .68, `eyebrow` to white .52, hairlines to
 * white .15 — which in CSS is inheritance and a descendant selector. React Native has
 * neither: colour does not cascade past a `Text`, and there is no selector to reach a
 * child with. So the repaint is expressed as the `onDark*` tokens, which the design system
 * already enumerates for exactly this reason, and the components that can sit on either
 * surface take a variant (`Row`, `Tag`, `InfoGlyph`) rather than reading a context.
 *
 * A card never casts a shadow, dark or light: depth on paper comes from the surface
 * change. Spacing between stacked cards is the parent's `gap`, as it is for `Card`.
 *
 * Used for: the onboarding result, the state card on a match, the level card on the
 * passport. The confidence ring appears **only** inside one, because `volt` is legible
 * nowhere else.
 */

import { StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';
import type { ReactNode } from 'react';

import { theme } from './theme';

export interface DarkCardProps {
  readonly children: ReactNode;
  readonly style?: StyleProp<ViewStyle>;
}

export function DarkCard({ children, style }: DarkCardProps) {
  return <View style={[s.card, style]}>{children}</View>;
}

const s = StyleSheet.create({
  card: {
    backgroundColor: theme.color.night,
    borderRadius: theme.radius.cardDark,
    padding: theme.space.lg,
  },
});
