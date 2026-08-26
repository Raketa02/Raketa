/**
 * The chip, per design-system 6.2 — the filter pill, and the only true pill in the app.
 *
 * **Specified since the document was locked and built only now** (Part 16, 2026-08-25).
 * The app shipped the tag first, which is deliberately never pressable, so the rule *a
 * pressable pill is a chip* had nothing to point at until the social tags step wanted
 * nineteen of them.
 *
 * **Selected is ink-filled, not coral.** Coral is the action colour and a selected filter
 * is a state — the same argument `PressableCard` makes for the selected card (5.1).
 *
 * **Selection is not carried by colour.** The fill inverts — `ink` on `surface` becomes
 * `surface` on `ink`, a 17,50:1 *luminance* change rather than a change of hue — and
 * `accessibilityState.selected` carries the same fact for whoever sees neither. That
 * pairing is what Part 13's *never colour alone* asks for here, and Part 16 re-read it
 * against the rule at the moment the chip came into use.
 *
 * **It holds no selection of its own.** `selected` is the caller's, and every press is
 * reported — including a press on a chip that is already selected. Only whoever counts
 * the selection can enforce a floor or a ceiling on it, and a chip that swallowed that
 * press would take away removing a tag as well as adding one.
 *
 * 6.2's **small chip is not built**: nothing needs one, and its 10pt label is a size Part
 * 3.3 carries no role for. It arrives with the first screen that wants it, together with
 * the type role — theme and document in one commit (Part 15.3). There is no **disabled**
 * chip either, because 6.2 specifies none: the step that needed this control refuses a
 * seventh tag out loud rather than by greying the other twelve.
 */

import { Pressable, StyleSheet, Text, type StyleProp, type ViewStyle } from 'react-native';

import { theme } from './theme';

export interface ChipProps {
  readonly label: string;
  /** Fires on every press, selected or not. The chip reports; the caller decides. */
  readonly onPress: () => void;
  /** Drawn ink-filled and announced as selected. Owned by the caller. */
  readonly selected?: boolean;
  /** Defaults to `label`. Set it when the word alone is cryptic out of context. */
  readonly accessibilityLabel?: string;
  readonly accessibilityHint?: string;
  readonly style?: StyleProp<ViewStyle>;
}

export function Chip({
  label,
  onPress,
  selected = false,
  accessibilityLabel,
  accessibilityHint,
  style,
}: ChipProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityHint={accessibilityHint}
      // Always present, never omitted when false: a chip that announced nothing while
      // unselected would leave "not chosen" indistinguishable from "not a choice".
      accessibilityState={{ selected }}
      onPress={onPress}
      // 27 + 9 + 9 = 45. The visual stays small and the target grows (6.5); the 3pt of
      // horizontal slop is what a 6pt gap between neighbours allows.
      hitSlop={theme.hit.chip}
      // Touch has no hover, so the pressed appearance is declared rather than inherited
      // (6.6). Immediate, not animated — the prototype's 120ms is a mouse transition.
      style={({ pressed }) => [
        s.chip,
        selected ? s.selected : undefined,
        pressed ? s.pressed : undefined,
        style,
      ]}
    >
      <Text style={[s.label, selected ? s.labelSelected : undefined]}>{label}</Text>
    </Pressable>
  );
}

const s = StyleSheet.create({
  chip: {
    // `minHeight` and a vertical pad, never a fixed 27: at large OS text sizes the label
    // has to grow the pill rather than be clipped by it, and the label is the choice
    // itself here — the tag truncates because a status must not reflow a row, which is
    // not the same obligation. `radius.pill` holds at whatever height that lands on.
    minHeight: theme.size.chip,
    paddingHorizontal: theme.space.md,
    paddingVertical: theme.space.xxs,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
    alignItems: 'center',
    justifyContent: 'center',
    // `alignSelf`, so a chip in a row is its own width rather than the row's.
    alignSelf: 'flex-start',
  },
  selected: { backgroundColor: theme.color.ink, borderColor: theme.color.ink },
  pressed: { opacity: 0.7 },
  label: { ...theme.type.chip, color: theme.color.ink },
  // `surface` is the app's one white; there is no separate `white` token, deliberately.
  labelSelected: { color: theme.color.surface },
});
