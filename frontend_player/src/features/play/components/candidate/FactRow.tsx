/**
 * One fact a card states about the person on it — a label, and the value under discussion.
 *
 * The three cards state different facts and state them in the same shape, which is what makes
 * three components cheap rather than three near-duplicates: the level row, the meta line, the
 * *Predicted balance* row and the *You overlap* row are all this.
 *
 * **A row is not a reason line, and the difference is the register.** A row is a fact the card
 * states unconditionally; a reason line answers *why this person* and is **selected**, ranked
 * and capped. That is also the whole mechanism of the de-duplication filter: a card that draws
 * a term as a row declares that term in its own drawn set, and the sentence for it is dropped
 * before the cap rather than after it
 * ([`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md) §5, §10).
 *
 * **The label is optional because two of the four rows are whole sentences.** `2,71 ·
 * Established · likely 2,55 – 2,87` and `In your area · 4,3 km` name what they are; *You
 * overlap* and *Predicted balance* do not, and a label over the first two would be the
 * restatement §10 forbids in the one place it is easiest to write.
 *
 * It announces nothing of its own — §20.1 merges it into the card body, whose name states
 * every one of these facts in the order §20.3 fixed.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

export interface FactRowProps {
  /** Omitted where the value is already a sentence about itself. See the module note. */
  readonly label?: string;
  readonly value: string;
}

export function FactRow({ label, value }: FactRowProps) {
  return (
    <View style={s.row}>
      {label === undefined ? null : <Text style={s.label}>{label}</Text>}
      {/* Two lines, because a 64-character handle is not the only thing on a card that can
          be long: a slot name and an area clause together outrun one line on the narrowest
          phone, and a truncated fact is a fact with its qualifier missing. */}
      <Text style={[s.value, label === undefined ? undefined : s.valueRight]} numberOfLines={2}>
        {value}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    gap: theme.space.xs,
  },
  label: { ...theme.type.rlLabel, color: theme.color.muted },
  value: { ...theme.type.rlValue, color: theme.color.ink, flexShrink: 1 },
  // Only when there is a label to sit opposite; a lone value starts at the card's edge.
  valueRight: { textAlign: 'right' },
});
