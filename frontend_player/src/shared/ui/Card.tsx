/**
 * The card, per design-system 5.1 — the workhorse surface.
 *
 * Cards never cast a shadow: depth on paper comes from the surface change and the 1pt
 * `line` border. The three shadows in the system are for things that genuinely float.
 *
 * `PressableCard` is the same object with a press state. Pressed is `coral` because
 * coral is the *action* colour; a card that is *selected* takes `ink`, for the same
 * reason a selected chip is ink-filled (6.2) — selection is a state, not an action.
 */

import {
  Pressable,
  StyleSheet,
  View,
  type StyleProp,
  type ViewStyle,
} from "react-native";
import type { ReactNode } from "react";

import { theme } from "./theme";

export interface CardProps {
  readonly children: ReactNode;
  readonly style?: StyleProp<ViewStyle>;
}

export function Card({ children, style }: CardProps) {
  return <View style={[s.card, style]}>{children}</View>;
}

export interface PressableCardProps extends CardProps {
  readonly onPress: () => void;
  /** Drawn with the selected border and announced as selected. */
  readonly selected?: boolean;
  readonly disabled?: boolean;
  readonly accessibilityLabel: string;
  readonly accessibilityHint?: string;
}

export function PressableCard({
  children,
  style,
  onPress,
  selected = false,
  disabled = false,
  accessibilityLabel,
  accessibilityHint,
}: PressableCardProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      // Selection reaches a screen reader as state. The border is the sighted half of
      // the same fact — never the only half, which is why callers also carry a word.
      accessibilityState={{ selected, disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        s.card,
        selected ? s.selected : undefined,
        pressed && !disabled ? s.pressed : undefined,
        style,
      ]}
    >
      {children}
    </Pressable>
  );
}

const s = StyleSheet.create({
  card: {
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
    padding: theme.space.md,
  },
  selected: { borderColor: theme.color.ink },
  pressed: { borderColor: theme.color.coral },
});
