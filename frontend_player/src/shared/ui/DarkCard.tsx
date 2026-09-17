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
 * passport, and the You tab's header card. The confidence ring appears **only** inside one,
 * because `volt` is legible nowhere else.
 *
 * ## The pressable one is the same card
 *
 * `PressableDarkCard` is `PressableCard`'s shape on this surface — one `button`, one spoken
 * name, the fill, corner and padding read from the same table — for the You tab's header card,
 * which is one press whose whole content is a fact (ADR-0179 §1). Its pressed state is 6.6's
 * opacity rather than a second fill: `night` has no darker companion that is not `ink`, and a
 * border on a dark card would be the first stroke on one.
 */

import { Pressable, StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';
import type { ReactNode } from 'react';

import { theme } from './theme';

export interface DarkCardProps {
  readonly children: ReactNode;
  readonly style?: StyleProp<ViewStyle>;
}

export function DarkCard({ children, style }: DarkCardProps) {
  return <View style={[s.card, style]}>{children}</View>;
}

export interface PressableDarkCardProps extends DarkCardProps {
  readonly onPress: () => void;
  readonly accessibilityLabel: string;
  readonly accessibilityHint?: string;
}

export function PressableDarkCard({
  children,
  style,
  onPress,
  accessibilityLabel,
  accessibilityHint,
}: PressableDarkCardProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      onPress={onPress}
      style={({ pressed }) => [s.card, pressed ? s.pressed : undefined, style]}
    >
      {children}
    </Pressable>
  );
}

const s = StyleSheet.create({
  card: {
    backgroundColor: theme.color.night,
    borderRadius: theme.radius.cardDark,
    padding: theme.space.lg,
  },
  pressed: { opacity: 0.7 },
});
