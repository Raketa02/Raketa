/**
 * **The hour row** — 30-minute steps between 06:00 and 23:00, and the same thirty-five the server
 * accepts.
 *
 * *Bounded chips the platform offered, never a free instant*: the grid is a convention and
 * `the_hour_is_not_offered` is what makes it true, so there is no picker, no wheel and nothing
 * that could produce a value between two of these.
 *
 * A press **is** the write, exactly as the day row's is, and the grid never narrows: **a plan is
 * never unmade**, so every hour stays offered whatever is already recorded, and the one that is
 * set is drawn selected rather than removed.
 *
 * They wrap into a block rather than scrolling. Thirty-five pills are a paragraph of numbers, and
 * a paragraph is what the sheet's own scroll is for — a horizontal strip would put half the
 * evening behind a gesture.
 */

import { StyleSheet, View } from 'react-native';

import { Chip, theme } from '@/shared/ui';

export interface HourChipsProps {
  /** `HH:MM`, off `HOURS_OFFERED`. */
  readonly hours: readonly string[];
  /** The hour this plan already names, so the chip for it is drawn selected. */
  readonly agreed?: string;
  readonly onPick: (hour: string) => void;
}

export function HourChips({ hours, agreed, onPick }: HourChipsProps) {
  return (
    <View style={s.grid}>
      {hours.map((hour) => (
        <Chip key={hour} label={hour} selected={hour === agreed} onPress={() => onPick(hour)} />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs, paddingTop: theme.space.sm },
});
