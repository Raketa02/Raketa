/**
 * **− 4 +** — two keys either side of a figure, in one outlined box: Games & money's games a week
 * (mock 38, #554) and *Post a game*'s two level bounds (mock 19, #558). Feature-local: the two are
 * this feature's, and a third caller elsewhere is what would move it to `shared/ui`.
 *
 * Each key is a button named for what it does, carrying the value, so a listener hears the new
 * figure on the key they just pressed. A key whose press would move nothing is **shut** — drawn at
 * 6.1's disabled and announced so — and the caller decides which those are: Games & money shuts
 * both ends of its range, while a level bound shuts only where it would pass the other and lets the
 * outward key **bounce** at the engine's own (the box nudges; the caller says why).
 */

import Feather from '@expo/vector-icons/Feather';
import { Animated, Pressable, StyleSheet, Text } from 'react-native';

import { theme } from '@/shared/ui';

export interface StepKeyProps {
  readonly glyph: 'minus' | 'plus';
  /** What the key does — *Fewer games*, *Raise the lowest level*. */
  readonly label: string;
  /** The figure, spoken, as it stands. */
  readonly value: string;
  /** `undefined` shuts the key. */
  readonly onPress: (() => void) | undefined;
}

export interface StepperProps {
  readonly figure: string;
  readonly fewer: StepKeyProps;
  readonly more: StepKeyProps;
  /** The box's sideways nudge — a bounce, driven by the caller; at rest without one. */
  readonly nudge?: Animated.Value;
}

export function Stepper({ figure, fewer, more, nudge }: StepperProps) {
  return (
    <Animated.View
      style={[s.stepper, nudge === undefined ? undefined : { transform: [{ translateX: nudge }] }]}
    >
      <StepKey {...fewer} />
      <Text style={s.figure} accessibilityElementsHidden importantForAccessibility="no">
        {figure}
      </Text>
      <StepKey {...more} />
    </Animated.View>
  );
}

function StepKey({ glyph, label, value, onPress }: StepKeyProps) {
  const shut = onPress === undefined;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityValue={{ text: value }}
      accessibilityState={{ disabled: shut }}
      disabled={shut}
      onPress={onPress}
      hitSlop={theme.hit.btn}
      style={({ pressed }) => [s.key, shut ? s.shut : undefined, pressed ? s.pressed : undefined]}
    >
      <Feather
        name={glyph}
        size={theme.size.rowLeadGlyph}
        color={theme.color.ink}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
    </Pressable>
  );
}

const s = StyleSheet.create({
  stepper: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: theme.space.xxs,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
    backgroundColor: theme.color.surface,
  },
  // 6.5 by geometry across and by `hit.btn` up and down: 44 wide, 40 tall and 50 to the finger.
  key: {
    width: theme.size.minTouch,
    height: theme.size.btnLg,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.paper2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // 6.1's disabled: the key is there and shut, not gone — the end of the range is visible.
  shut: { opacity: 0.4 },
  pressed: { opacity: 0.7 },
  figure: {
    ...theme.num.xl,
    ...theme.tabular,
    minWidth: theme.size.btnLg,
    color: theme.color.ink,
    textAlign: 'center',
  },
});
