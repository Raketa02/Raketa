/**
 * The tick box — [6.11](../../../docs/design-system.md#611-the-tick-box).
 *
 * One box, one claim beside it, for a statement a player either makes or does not.
 * **Not a settings switch and not a filter**: a switch turns something on, and a chip
 * narrows what is already on screen ([6.2](../../../docs/design-system.md#62-chip--the-filter-pill)).
 * This is the shape for a sentence the player asserts.
 *
 * It borrows rather than invents: the selected state is
 * [6.8](../../../docs/design-system.md#68-the-availability-grid)'s cell — a fill inversion
 * *and* a tick — because the inversion is a 17,50:1 luminance change that survives colour
 * blindness while the tick is the shape [Part 13](../../../docs/design-system.md#part-13--accessibility)
 * asks for. A box carrying its state in fill alone is a stain, not an answer.
 *
 * **The box is the sign-up mocks' rounded square** ([#785](https://github.com/Rakieta02/Rakieta/issues/785),
 * mocks 4 and 6): 22pt with the cell's 6pt corner, white on a `line` border, filled `ink` with a
 * white tick when ticked. *Start playing* draws this same box, because it is the same claim.
 *
 * **The whole row is the target**, box and words together. A 22pt square is well under the
 * 44pt minimum on its own, and a label that is not part of the control is a word beside the
 * thing to hit rather than the thing itself.
 *
 * **It has no pre-ticked state to offer.** `checked` is the caller's and this component has
 * no default for it — a box that arrives ticked is a claim the player never made.
 *
 * `checkbox` rather than `button`, with `checked` always present rather than omitted when
 * false, for 6.8's reason: the state is the point, and *not ticked* and *not a choice* are
 * different things to be told. The accessible name is the label, so what is announced is
 * the sentence being asserted.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from './theme';
import { Tick } from './Tick';

const geometry = theme.size.tickBox;

export interface TickBoxProps {
  /** The claim, in the player's own voice. Also the accessible name. */
  readonly label: string;
  readonly checked: boolean;
  readonly onChange: (checked: boolean) => void;
  /** Shown under the control and announced. Absent when the answer is fine. */
  readonly error?: string;
  readonly disabled?: boolean;
}

export function TickBox({ label, checked, onChange, error, disabled = false }: TickBoxProps) {
  return (
    <View style={s.field}>
      <Pressable
        accessibilityRole="checkbox"
        accessibilityLabel={label}
        accessibilityState={{ checked }}
        disabled={disabled}
        onPress={() => onChange(!checked)}
        // Touch has no hover, so the pressed appearance is declared rather than inherited
        // (6.6), and it sits over either state.
        style={({ pressed }) => [s.row, pressed ? s.rowPressed : undefined]}
      >
        {/* The refused border is drawn only while the box is unticked: once it is
            ticked there is nothing left to fix, and a red outline around a satisfied
            control contradicts the answer inside it. */}
        <View
          style={[
            s.box,
            checked ? s.boxChecked : undefined,
            error !== undefined && !checked ? s.boxError : undefined,
          ]}
        >
          {checked ? <Tick /> : null}
        </View>
        <Text style={s.label}>{label}</Text>
      </Pressable>

      {error !== undefined ? (
        <Text style={s.error} accessibilityRole="alert">
          {error}
        </Text>
      ) : null}
    </View>
  );
}

const s = StyleSheet.create({
  field: { gap: theme.space.xxs },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    minHeight: geometry.row,
  },
  rowPressed: { opacity: 0.7 },
  box: {
    width: geometry.box,
    height: geometry.box,
    borderRadius: theme.radius.availabilityCell,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  boxChecked: { backgroundColor: theme.color.ink, borderColor: theme.color.ink },
  boxError: { borderColor: theme.color.red },
  // `flex: 1` so a long claim wraps inside the row instead of pushing the box off it, and
  // `rlValue` because it is a sentence the player reads rather than a label on a field
  // (3.3: `flab` labels a control, and here the sentence IS the control).
  label: { ...theme.type.rlValue, color: theme.color.ink, flex: 1 },
  error: { ...theme.type.tiny, color: theme.color.red },
});
