/**
 * **The day row** — seven chips, today + 6, shrinking as the horizon runs out.
 *
 * A day is a tap and not a form, so pressing one **is** the write: there is no *Set the day*
 * beside it, and the sheet closes on the press. What reports the write is the slot chip on the
 * card behind, which is [#366](https://github.com/Raketa02/Raketa/issues/366)'s *the chip shows
 * pending*.
 *
 * **The row can be empty, and that is the honest drawing of a real state.** Inside the game's
 * 24-hour entry grace the horizon has run out and no day may be set — *the only act left is
 * `We played`* — so the row draws no chips and the sentence beneath it says why. An absence with
 * nothing under it would read as a screen that failed to load.
 *
 * **The day already agreed is drawn selected**, which is 6.2's inverted fill plus
 * `accessibilityState.selected`, and it is still pressable: a chip that swallowed a press on the
 * current value would be this component holding an opinion about a write the server answers `200`
 * to and records nothing for.
 *
 * The chips **wrap** rather than scrolling: seven three-letter pills fit two lines on the
 * narrowest phone, and a horizontal strip would hide the end of the week behind a gesture on the
 * one row where every option matters equally.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Chip, theme } from '@/shared/ui';

import { dayChipLabel, dayChipName, NO_DAY_LEFT_TO_SET } from './planPresentation';

export interface DayChipsProps {
  /** `YYYY-MM-DD`, off `offeredDays` — already clamped to the game's own horizon. */
  readonly days: readonly string[];
  /** The day this plan already names, so the chip for it is drawn selected. */
  readonly agreed?: string;
  readonly onPick: (day: string) => void;
}

export function DayChips({ days, agreed, onPick }: DayChipsProps) {
  if (days.length === 0) return <Text style={s.refusal}>{NO_DAY_LEFT_TO_SET}</Text>;

  return (
    <View style={s.row}>
      {days.map((day) => (
        <Chip
          key={day}
          label={dayChipLabel(day)}
          accessibilityLabel={dayChipName(day)}
          selected={day === agreed}
          onPress={() => onPick(day)}
        />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs, paddingTop: theme.space.sm },
  refusal: { ...theme.type.tiny, color: theme.color.ink, paddingTop: theme.space.sm },
});
