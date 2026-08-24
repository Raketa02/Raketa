/**
 * A score, as two named rows of games.
 *
 * **Both sides are named, and the viewer's is first.** `ADR-0060` fixes that for
 * every surface that shows a score at all — *"with four people and two sides an
 * unlabelled string is unusable"* — so the rows arrive named and this draws them in
 * the order it was given. It sorts nothing and it flips nothing: which side is
 * first is the server's composition, and a second opinion about it here would be a
 * scoreboard that disagreed with the one on the card.
 *
 * **It takes rows and not a score**, so this primitive holds no domain type and no
 * copy: transposing a set's two integers into two rows, and naming a side with no
 * players left on it, are both the caller's — and there is exactly one caller-side
 * function doing them, so the two surfaces that draw a score cannot name a side two
 * ways.
 *
 * **A row is one accessibility element.** A name and a column of digits read a
 * screen apart mean nothing, which is the same rule the departure screen's outcome
 * table applies to a mark beside a sentence.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from './theme';

/** One side of the net: who was on it, and what it scored in each set. */
export interface ScoreBoardRow {
  readonly name: string;
  readonly games: readonly number[];
}

export interface ScoreBoardProps {
  readonly rows: readonly ScoreBoardRow[];
}

export const SCORE_BOARD_ROW_ID = 'score-board-row';

export function ScoreBoard({ rows }: ScoreBoardProps) {
  return (
    <View style={s.board}>
      {rows.map((row, index) => (
        <View
          // The name, because two rows of one board are two different sides and a
          // positional key would reuse a row across a fresh score.
          key={`${index}:${row.name}`}
          style={s.row}
          accessible
          accessibilityLabel={`${row.name}, ${row.games.join(', ')}`}
          testID={SCORE_BOARD_ROW_ID}
        >
          <Text style={s.name} numberOfLines={1}>
            {row.name}
          </Text>
          {row.games.map((games, set) => (
            <Text key={set} style={s.games}>
              {games}
            </Text>
          ))}
        </View>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  board: { gap: theme.space.xxs },
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  // The name takes the room and the digits sit in fixed columns, so the two rows'
  // sets line up under each other without anybody measuring.
  name: { ...theme.type.rlValue, color: theme.color.ink, flex: 1 },
  games: {
    ...theme.num.s,
    ...theme.tabular,
    color: theme.color.ink,
    minWidth: theme.space.xxl,
    textAlign: 'right',
  },
});
