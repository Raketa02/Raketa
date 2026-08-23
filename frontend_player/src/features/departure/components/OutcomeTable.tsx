/**
 * All four outcomes, each with a marker, in the order the quote's timeline runs.
 *
 * **All four, always** (`ADR-0086`). Not the reachable ones: *"a table that
 * quietly drops forfeited once it is unreachable is also a table that never showed
 * it while it was."* A private court sends two rows, and this draws what it was
 * sent — the count is the server's and the client never pads it to four.
 *
 * **Nothing here sorts.** The rows arrive ordered by the quote's own timeline, so
 * a row above the searching one is behind her and a row below it is ahead, and
 * that reading is the server's composition rather than a comparison made here.
 *
 * **The mark is decoration and the note carries the state.** Two of the four marks
 * are open circles, which is fine because the sentence beside them is the cue: *In
 * 2 h 14 min* and *Once the match fills* are not close to each other. Every mark is
 * hidden from assistive technology, and the row is one accessibility element whose
 * label is the outcome and its standing read together — a name and a standing read
 * a screen apart mean nothing.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Hairline, theme } from '@/shared/ui';

import type { OutcomeRow } from '../domain/Departure';

export const OUTCOME_ROW_ID = 'departure-outcome-row';

export interface OutcomeTableProps {
  readonly outcomes: readonly OutcomeRow[];
  /**
   * How long until a row's moment, for the one standing that names one.
   *
   * Passed in rather than computed here, because the screen holds one clock and
   * four rows each reading their own would be four readings of *now*.
   */
  readonly countdownFor: (row: OutcomeRow) => string | undefined;
}

export function OutcomeTable({ outcomes, countdownFor }: OutcomeTableProps) {
  return (
    <View style={s.table}>
      {outcomes.map((row, index) => (
        <OutcomeRowView
          key={row.outcome}
          row={row}
          divided={index > 0}
          countdown={countdownFor(row)}
        />
      ))}
    </View>
  );
}

/**
 * One row: a mark, what the outcome is, and where it stands.
 *
 * **An outcome this build has never heard of is dropped**, the same answer an
 * unknown situation gets. A row with a blank name over a standing is a defect
 * where a missing row is a loss — and the row it would be describing is one this
 * build cannot state the consequence of, which is exactly the thing not to guess
 * at on a screen about an irreversible act.
 */
function OutcomeRowView({
  row,
  divided,
  countdown,
}: {
  readonly row: OutcomeRow;
  readonly divided: boolean;
  readonly countdown: string | undefined;
}) {
  const name = row.name;
  const standing = row.standing;
  if (name === undefined || standing === undefined) return null;

  const note = standing.note(countdown);

  const body = (
    <View
      style={s.row}
      // A name and a standing read a screen apart mean nothing, so the row is one
      // element and the label is the two read together.
      accessible
      accessibilityLabel={`${name}. ${note}.`}
      testID={OUTCOME_ROW_ID}
    >
      <Text style={s.mark} accessibilityElementsHidden importantForAccessibility="no">
        {standing.mark}
      </Text>
      <Text style={s.name}>{name}</Text>
      <Text style={s.note} numberOfLines={1}>
        {note}
      </Text>
    </View>
  );

  // The fold is drawn from the second row onward, never as a border on every row:
  // the first row then has no rule above it and the last none below it, without
  // anybody counting. `Row`'s own rule, applied to a row `Row` cannot draw.
  return divided ? <Hairline>{body}</Hairline> : body;
}

const s = StyleSheet.create({
  table: { gap: theme.space.xxs },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingVertical: theme.space.xs,
  },
  mark: { ...theme.type.tag, color: theme.color.muted, minWidth: theme.space.sm },
  // The outcome takes the room; the standing sits at the end of the line, which
  // is what makes the column of marks and the column of standings both readable.
  name: { ...theme.type.rlValue, color: theme.color.ink, flex: 1 },
  note: { ...theme.type.rlLabel, color: theme.color.muted },
});
