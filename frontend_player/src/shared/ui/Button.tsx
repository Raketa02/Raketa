/**
 * The button, per design-system 6.1.
 *
 * Three variants, four heights, and one rule that is easy to miss: **the primary button
 * is filled `coralInk` and brightens to `coral` when pressed** — the inverse of the
 * prototype, which put white 12pt text on `coral` at 3.89:1. Coral still reads as the
 * accent; the label is legible (Rule C).
 *
 * Press feedback is immediate rather than animated, which is also why nothing here
 * branches on reduced motion: there is no motion to reduce.
 *
 * `theme.color.surface` is the app's one white (design-system correction #1), so it is
 * what a label on a saturated fill uses. There is no separate `white` token, deliberately.
 */

import {
  Pressable,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type ViewStyle,
} from "react-native";

import { theme } from "./theme";

export type ButtonVariant = "primary" | "dark" | "secondary";

/**
 * 32 tertiary-in-card · 34 default · 40 screen action · 42 the primary action on a
 * result screen. All four clear the 44pt reachable minimum once `hit.btn` is applied.
 */
export type ButtonSize = "sm" | "md" | "lg" | "xl";

export interface ButtonProps {
  readonly label: string;
  readonly onPress: () => void;
  readonly variant?: ButtonVariant;
  readonly size?: ButtonSize;
  readonly disabled?: boolean;
  /** Blocks presses and swaps the label. A busy button is not a disabled button. */
  readonly busy?: boolean;
  readonly busyLabel?: string;
  /** Defaults to `label`. Set it when the visible label needs context to make sense. */
  readonly accessibilityLabel?: string;
  readonly accessibilityHint?: string;
  readonly style?: StyleProp<ViewStyle>;
}

export function Button({
  label,
  onPress,
  variant = "primary",
  size = "md",
  disabled = false,
  busy = false,
  busyLabel,
  accessibilityLabel,
  accessibilityHint,
  style,
}: ButtonProps) {
  const blocked = disabled || busy;
  // The accessible name follows what is drawn. A button reading "Starting…" while it
  // announces "Rate 1 sport" hands two different apps to two different players.
  const shown = busy ? (busyLabel ?? label) : label;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? shown}
      accessibilityHint={accessibilityHint}
      // Disabled and busy reach a screen reader as state. The 40% fill below is the
      // sighted half of the same fact, never the whole of it.
      accessibilityState={{ disabled: blocked, busy }}
      disabled={blocked}
      onPress={onPress}
      hitSlop={theme.hit.btn}
      style={({ pressed }) => [
        s.base,
        HEIGHT[size],
        FILL[variant],
        pressed && !blocked ? PRESSED[variant] : undefined,
        blocked ? s.blocked : undefined,
        style,
      ]}
    >
      <View style={s.labelBox}>
        <Text style={[s.label, LABEL[variant]]} numberOfLines={1}>
          {shown}
        </Text>
      </View>
    </Pressable>
  );
}

const s = StyleSheet.create({
  base: {
    borderRadius: theme.radius.btn,
    paddingHorizontal: theme.space.lg,
    alignItems: "center",
    justifyContent: "center",
  },
  // `minHeight`, never `height`: at large OS text sizes the label has to grow the button
  // rather than be clipped by it.
  labelBox: { paddingVertical: theme.space.xs },
  label: { ...theme.type.btn },
  blocked: { opacity: 0.4 },
});

const HEIGHT = StyleSheet.create({
  sm: { minHeight: theme.size.btnSm },
  md: { minHeight: theme.size.btn },
  lg: { minHeight: theme.size.btnLg },
  xl: { minHeight: theme.size.btnXl },
});

const FILL = StyleSheet.create({
  primary: { backgroundColor: theme.color.coralInk },
  dark: { backgroundColor: theme.color.night },
  secondary: {
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
  },
});

const PRESSED = StyleSheet.create({
  primary: { backgroundColor: theme.color.coral },
  dark: { backgroundColor: theme.color.night2 },
  secondary: { backgroundColor: theme.color.line2 },
});

const LABEL = StyleSheet.create({
  primary: { color: theme.color.surface },
  dark: { color: theme.color.surface },
  secondary: { color: theme.color.ink },
});
