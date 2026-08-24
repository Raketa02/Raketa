/**
 * The pad: five rows of two cells, and the keys that fill them.
 *
 * `ADR-0060` §5's constraint is a score typed *"standing on a court, one-handed, in
 * the dark"*, which is why this is a pad and not the system keyboard — free text
 * was refused outright, because *"two people cannot meaningfully disagree about
 * strings"*.
 *
 * **One pad for every sport, and that is a gap rather than a preference.** The ADR
 * specifies it per sport, and the sport is **not on the wire** — neither the card's
 * spine nor this screen carries it — so the pad ships as the widest of the four it
 * names (`Raketa02/Raketa#120`). `domain/scorePad.ts` carries the reasoning and the
 * cost.
 *
 * **The columns are named by the sides**, hers first, exactly as the scoreboard
 * above them is: a grid of digits with no names is the unlabelled `6-4, 3-6, 6-2`
 * `ADR-0060` exists to refuse.
 *
 * **A cell announces its whole coordinate.** A screen reader moving across a grid
 * has no rows and no columns, so *Set 2, your side, 6* is the only thing that makes
 * one cell distinguishable from the nine beside it.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { PAD_MAX, type ScorePad } from '../domain/scorePad';

import { PAD_HEADING, PAD_HINT, padCellLabel, padKeyLabel } from './resultCopy';

export const PAD_ID = 'result-score-pad';

/** One cell, addressed the way the pad addresses it. */
export function padCellId(row: number, side: number): string {
  return `result-pad-cell-${row}-${side}`;
}

/** One key. Keyed by its value, because that is what a test presses. */
export function padKeyId(value: number): string {
  return `result-pad-key-${value}`;
}

const KEYS: readonly number[] = Array.from({ length: PAD_MAX + 1 }, (_unused, value) => value);

export interface ScorePadViewProps {
  readonly pad: ScorePad;
  /** The two sides, hers first, in the words the scoreboard uses. */
  readonly sides: readonly string[];
  readonly onType: (value: number) => void;
  readonly onSelect: (row: number, side: number) => void;
}

export function ScorePadView({ pad, sides, onType, onSelect }: ScorePadViewProps) {
  return (
    <View style={s.pad} testID={PAD_ID}>
      <Text style={s.heading} accessibilityRole="header">
        {PAD_HEADING}
      </Text>
      <Text style={s.hint}>{PAD_HINT}</Text>

      <View style={s.grid}>
        {pad.rows.map((row, index) => (
          <View key={index} style={s.row}>
            <Text style={s.setNumber}>{index + 1}</Text>
            {row.map((value, side) => (
              <Pressable
                key={side}
                accessibilityRole="button"
                accessibilityLabel={padCellLabel(index + 1, sides[side] ?? '', value)}
                accessibilityState={{ selected: isActive(pad, index, side) }}
                onPress={() => onSelect(index, side)}
                style={[s.cell, isActive(pad, index, side) ? s.cellActive : undefined]}
                testID={padCellId(index, side)}
              >
                {/* An untyped cell draws a dash rather than nothing: an empty box
                    and a box holding a space are the same picture, and the dash is
                    what makes *there is no number here* visible. */}
                <Text style={s.cellValue}>{value === undefined ? '–' : value}</Text>
              </Pressable>
            ))}
          </View>
        ))}
      </View>

      <View style={s.keys}>
        {KEYS.map((value) => (
          <Pressable
            key={value}
            accessibilityRole="button"
            accessibilityLabel={padKeyLabel(value)}
            onPress={() => onType(value)}
            style={({ pressed }) => [s.key, pressed ? s.keyPressed : undefined]}
            testID={padKeyId(value)}
          >
            <Text style={s.keyValue}>{value}</Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

function isActive(pad: ScorePad, row: number, side: number): boolean {
  return pad.active.row === row && pad.active.side === side;
}

const s = StyleSheet.create({
  pad: { gap: theme.space.xs },
  heading: { ...theme.type.h2, color: theme.color.ink },
  hint: { ...theme.type.tiny, color: theme.color.muted },
  grid: { gap: theme.space.xxs },
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  setNumber: {
    ...theme.type.rlLabel,
    color: theme.color.muted,
    minWidth: theme.space.md,
  },
  cell: {
    flex: 1,
    height: theme.size.btn,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.line2,
  },
  // The live cell carries a border as well as a fill, because a fill alone is
  // colour doing the work on its own — every state carries a word or a shape.
  cellActive: {
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.coral,
  },
  cellValue: { ...theme.num.s, ...theme.tabular, color: theme.color.ink },
  // Wrapping rather than a fixed grid: twenty-two keys at the minimum reachable
  // size lay out as six columns on a 390pt phone and five on a 320pt one, and a
  // hard-coded column count would push the last key off the narrow screen.
  keys: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xxs },
  key: {
    flexGrow: 1,
    flexBasis: theme.size.minTouch,
    height: theme.size.minTouch,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.btn,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
  },
  keyPressed: { backgroundColor: theme.color.line2 },
  keyValue: { ...theme.num.s, ...theme.tabular, color: theme.color.ink },
});
