/**
 * A score somebody has already put up — **variant C's table: one row per side, named.**
 *
 * `6-4 3-6 6-2` is not a score until you know whose 6 it is, and in a doubles game with four
 * people and two sides an unlabelled string is unusable. The prototype drew the answer as a row
 * per side with the name at the head of it and the figures across, which reads the way people
 * say a score out loud, and it is what every screen in this feature uses. The reader's side is
 * always the top row, and the flip out of the wire's absolute `a`/`b` happens **here and nowhere
 * else**.
 *
 * **The winning row is marked with a word, not a tick.** The prototype drew `✓`, and this app
 * has already found out what that costs: **Archivo ships no U+2713**, which is why the on-court
 * mark is words. The app's own drawn tick is `surface` on `ink` and would be invisible on paper.
 * So the mark is `won`, which also discharges Part 13 by itself — the figures' weight is the
 * second cue and never the only one.
 *
 * It is **one accessibility element**. Read cell by cell the table is *six, four, three, six* —
 * a row of numbers with no statement in it — so the whole score goes into one name, with both
 * sides said in every set because a listener has no column heads to look back at. That is
 * `the-words.md` §20.1: nothing here has an action of its own.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Score } from '../domain/game';
import { setsWon } from '../domain/score';
import { otherSide, scoreColumn, type GameSide } from '../domain/vocabulary';

import { scoreLabel, type SpokenSides } from './gameAccessibility';
import { WON_MARK } from './gamePresentation';

export interface ScoreTableProps {
  readonly score: Score;
  readonly sport: Sport;
  /** Which side of the net is the reader's. The flip into `a`/`b` happens here, once. */
  readonly mine: GameSide;
  readonly sides: SpokenSides;
  /** What this score **is** — *the agreed score*, *the score on the table*. Spoken first. */
  readonly lead: string;
  /**
   * Quiet where this score is context rather than the subject — standing beside a score being
   * typed, and the reader's own beside the other side's on a disagreement, where the one control
   * on the screen agrees with the other one.
   */
  readonly quiet?: boolean;
}

export function ScoreTable({ score, sport, mine, sides, lead, quiet = false }: ScoreTableProps) {
  const rows = [
    { column: scoreColumn(mine), name: sides.ours },
    { column: scoreColumn(otherSide(mine)), name: sides.theirs },
  ] as const;

  return (
    <View
      style={[s.table, quiet ? s.tableQuiet : null]}
      accessible
      accessibilityLabel={scoreLabel(lead, { score, sport, mine, sides })}
    >
      {rows.map(({ column, name }) => {
        const won = setsWon(score, column) > setsWon(score, column === 'a' ? 'b' : 'a');
        return (
          <View key={name} style={s.row}>
            <Text style={[s.name, won ? s.nameWon : null]} numberOfLines={1}>
              {name}
            </Text>
            {score.sets.map((set, index) => (
              <Text
                key={`${name}-${String(index)}`}
                style={[s.figure, quiet ? s.figureQuiet : null, won ? null : s.figureLost]}
              >
                {column === 'a' ? set.a : set.b}
              </Text>
            ))}
            {/* A fixed slot either way, so the loser's figures do not shift left under the
                winner's. A word rather than a mark, and never colour alone. */}
            {won ? <Text style={s.mark}>{WON_MARK}</Text> : <View style={s.mark} />}
          </View>
        );
      })}
    </View>
  );
}

/**
 * The two fixed columns, so both rows line up whatever is in them.
 *
 * Named here rather than in `theme.ts` on `CANDIDATE_PANEL`'s precedent: they are this drawing's
 * geometry, not a value the design system has an opinion about. `figure` fits `99` at `num.m`;
 * `mark` fits {@link WON_MARK} at `type.tag`, and it is reserved on the losing row too so the
 * figures above and below it do not shift.
 */
const COLUMN = { figure: 22, mark: 26 } as const;

const s = StyleSheet.create({
  table: {
    gap: theme.space.xs,
    backgroundColor: theme.color.surface,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.color.line,
    padding: theme.space.md,
  },
  tableQuiet: { backgroundColor: theme.color.paper2, borderColor: theme.color.line2 },
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  name: { ...theme.type.rlLabel, color: theme.color.muted, flex: 1 },
  nameWon: { ...theme.type.rlValue, color: theme.color.ink },
  figure: {
    ...theme.num.m,
    ...theme.tabular,
    color: theme.color.ink,
    minWidth: 22,
    textAlign: 'right',
  },
  figureQuiet: { ...theme.num.s, ...theme.tabular },
  figureLost: { color: theme.color.muted },
  mark: {
    ...theme.type.tag,
    color: theme.color.mintInk,
    textTransform: 'uppercase',
    width: COLUMN.mark,
  },
});
