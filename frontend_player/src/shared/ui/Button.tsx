/**
 * The button, per design-system 6.1.
 *
 * Five variants, four heights, and one rule that is easy to miss: **the primary button
 * is filled `coralInk` and brightens to `coral` when pressed** — the inverse of the
 * prototype, which put white 12pt text on `coral` at 3.89:1. Coral still reads as the
 * accent; the label is legible (Rule C).
 *
 * Press feedback is immediate rather than animated, which is also why nothing here
 * branches on reduced motion: there is no motion to reduce.
 *
 * `theme.color.surface` is the app's one white (design-system correction #1), so it is
 * what a label on a saturated fill uses. There is no separate `white` token, deliberately.
 *
 * **`settled` is a fourth variant and an amendment to 6.1** (added for the location step).
 * It is the button whose *state* is the message: the thing it asked for has been obtained,
 * and pressing it again would only obtain it a second time. Mint is the system's word for
 * *settled, safe, covered* (1.3), so it is the one colour that could carry it — and it is
 * `mintInk` rather than `mint` because Rule C forbids white on `mint` at 4.07:1. It
 * brightens to `mint` on press exactly as `primary` brightens to `coral`, for the same
 * reason and with the same momentary exception. **The colour is never the whole fact:** a
 * control that turns green must also change its words, and the screen that uses this is
 * responsible for that half.
 *
 * **`volt` is a fifth variant and the one that does not have the others' shape** (added for
 * Play's *they want you* signal). Volt is a **fill anywhere and a stroke only on dark** (2.2):
 * as a foreground on paper it is ~1.3:1 and invisible, but `ink` on it is 13.96:1, so the
 * fill inverts exactly the problem the stroke has. Its label is therefore `ink` and never
 * white. Its press is **`opacity: .7`** rather than a second fill — the system's answer for a
 * pressed surface with no darker companion (6.6: chip, segment, availability cell, photo
 * tile, tick-box row) — because volt is already the brightest value in the palette, and a
 * seventh hex invented to satisfy *the variant's pressed fill* would be a colour added to
 * describe a press.
 */

import { Pressable, StyleSheet, Text, View, type StyleProp, type ViewStyle } from 'react-native';

import { theme } from './theme';

export type ButtonVariant = 'primary' | 'dark' | 'secondary' | 'settled' | 'volt';

/**
 * 32 tertiary-in-card · 34 default · 40 screen action · 42 the primary action on a
 * result screen. All four clear the 44pt reachable minimum once `hit.btn` is applied.
 */
export type ButtonSize = 'sm' | 'md' | 'lg' | 'xl';

export interface ButtonProps {
  readonly label: string;
  readonly onPress: () => void;
  readonly variant?: ButtonVariant;
  readonly size?: ButtonSize;
  readonly disabled?: boolean;
  /** Blocks presses and swaps the label. A busy button is not a disabled button. */
  readonly busy?: boolean;
  readonly busyLabel?: string;
  /**
   * Announced as `accessibilityState.selected`, for a button that is one of a set of
   * answers rather than an action.
   *
   * **Omitted unless set**, because *not selected* and *not a choice* are different facts
   * and every other button in the app is the second one. The drawing is the caller's, as
   * the chip's is: pass a `variant` that shows it, and the state here is the half a screen
   * reader gets.
   */
  readonly selected?: boolean;
  /** Defaults to `label`. Set it when the visible label needs context to make sense. */
  readonly accessibilityLabel?: string;
  readonly accessibilityHint?: string;
  readonly style?: StyleProp<ViewStyle>;
}

export function Button({
  label,
  onPress,
  variant = 'primary',
  size = 'md',
  disabled = false,
  busy = false,
  busyLabel,
  selected,
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
      accessibilityState={{ disabled: blocked, busy, selected }}
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
    alignItems: 'center',
    justifyContent: 'center',
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
  settled: { backgroundColor: theme.color.mintInk },
  volt: { backgroundColor: theme.color.volt },
});

const PRESSED = StyleSheet.create({
  primary: { backgroundColor: theme.color.coral },
  dark: { backgroundColor: theme.color.night2 },
  secondary: { backgroundColor: theme.color.line2 },
  settled: { backgroundColor: theme.color.mint },
  // Not a fill. Volt has no darker companion and does not get one invented for a press.
  volt: { opacity: 0.7 },
});

const LABEL = StyleSheet.create({
  primary: { color: theme.color.surface },
  dark: { color: theme.color.surface },
  secondary: { color: theme.color.ink },
  settled: { color: theme.color.surface },
  volt: { color: theme.color.ink },
});
