/**
 * The hairline, per design-system 5.3 — the internal divider.
 *
 * It is a **wrapper around the second section**, not a free-standing line: the spec's four
 * values (`borderTopWidth 1`, `borderTopColor line2`, `marginTop 9`, `paddingTop 9`)
 * describe the block below the fold, and expressing it that way is what makes the spacing
 * on both sides of the line impossible to get wrong.
 *
 * `line2` rather than `line`, so it reads as a fold inside one object rather than a
 * boundary between two — which is the whole distinction between the two line tokens.
 */

import { StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';
import type { ReactNode } from 'react';

import { theme } from './theme';

export type HairlineVariant = 'base' | 'onDark';

export interface HairlineProps {
  /** The section below the fold. */
  readonly children: ReactNode;
  /** 5.2's repaint: a fold inside a dark card is drawn in the on-dark hairline. */
  readonly variant?: HairlineVariant;
  readonly style?: StyleProp<ViewStyle>;
}

export function Hairline({ children, variant = 'base', style }: HairlineProps) {
  return <View style={[s.section, FOLD[variant], style]}>{children}</View>;
}

const s = StyleSheet.create({
  section: {
    borderTopWidth: 1,
    marginTop: theme.space.sm,
    paddingTop: theme.space.sm,
  },
});

const FOLD = StyleSheet.create({
  base: { borderTopColor: theme.color.line2 },
  onDark: { borderTopColor: theme.color.onDarkHair },
});
