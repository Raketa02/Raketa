/**
 * The competitive card's **three record blocks** — what the platform has watched this person
 * do ([#312](https://github.com/Raketa02/Raketa/issues/312)).
 *
 * ```
 * Player Score      Last 5            Counted
 * 74                ■ ■ ▨ ■           29
 *
 * (Four squares and not five: they have four counted results, and the fifth is a gap. ▨ is a
 * loss — a paler fill, never a different hue.)
 * ```
 *
 * **Player Score** is reliability out of a hundred — turning up, answering challenges,
 * confirming results — and it is **nothing to do with skill**. The card prints a Level twice
 * already, hugely on the panel and again in the band, so the block is recessed onto `paper2`
 * and its figure is two type steps down: what the platform watched, drawn apart from what the
 * player published. **Counted** is the honesty figure beside it — *a 2,95 built on 29 games
 * means much more than one built on three*.
 *
 * ## Each block is hidden when its fact is absent, and never zeroed
 *
 * The three fields are **omitted** rather than sent as `0`, which is `distance_km`'s spelling
 * and the discipline the reason list, the meta line and the sort row all already take. A card
 * for a brand-new player draws none of the three and is a correct card — so this component
 * draws nothing at all rather than a row of empty boxes, and a card that has one block draws
 * one block filling the width.
 *
 * ## The gap is the statement, so the run is never padded
 *
 * *Last 5* is one square per counted-and-agreed result, oldest to newest. **Fewer than five is
 * a real answer**: three squares means three results, and the space where the other two would
 * be is drawn as a gap because padding it would claim two games nobody played. The row is
 * left-aligned in its box for exactly that reason — the missing squares are missing at the
 * end, where the newest results are not yet.
 *
 * ## Fill, and what a listener gets instead of it
 *
 * A win is `ink` and a loss is `muted`: 3,24:1 between them and 14,57 / 4,49 against the
 * block's ground, all three clearing
 * [1.4.11](../../../../../docs/design-system.md#25-contrast--computed)'s 3:1 for a graphical
 * object, and the difference is **lightness** rather than hue — so the run survives being read
 * in one colour. It does not survive being read aloud, which is the half
 * [Part 13](../../../../../docs/design-system.md#part-13--accessibility) is about: the squares
 * carry no words, so the whole row reaches the listener as one clause counting them —
 * *3 of the last 5 won* — rather than as five elements read like a table. That clause is
 * `lastFiveReading`'s and is composed into the card's spoken name beside the other two blocks.
 */

import { StyleSheet, View } from 'react-native';

import { theme } from '@/shared/ui';

import type { GameResult } from '../../domain/vocabulary';
import {
  COUNTED_BLOCK,
  LAST_FIVE_BLOCK,
  PLAYER_SCORE_BLOCK,
  type RecordBlockFacts,
} from '../playerCardPresentation';

import { StatBox, StatFigure, StatRow } from './StatBox';

export interface RecordBlocksProps {
  /**
   * The three facts, as `candidateFacts` resolved them — **and `undefined` on the two cards
   * that draw no record**.
   *
   * The value rather than the candidate, for the reason the Social tag row takes one: the
   * card's spoken name is composed from these same three, and a component that read them off
   * `player_card` itself would be the second read the label could disagree with.
   */
  readonly record?: RecordBlockFacts;
}

export function RecordBlocks({ record }: RecordBlocksProps) {
  const { playerScore, lastFive, countedGames } = record ?? {};

  // Three absences, one question. A run the wire omitted, a run this build could only half read
  // and an empty one all arrive as an absent field (`candidateMappers`), so the block asks the
  // same thing of all three fields — and the spoken clause asks it once more, of this same value.
  if (playerScore === undefined && lastFive === undefined && countedGames === undefined) {
    return null;
  }

  return (
    <StatRow>
      {playerScore === undefined ? null : (
        <StatBox label={PLAYER_SCORE_BLOCK}>
          <StatFigure>{String(playerScore)}</StatFigure>
        </StatBox>
      )}

      {lastFive === undefined ? null : (
        <StatBox label={LAST_FIVE_BLOCK}>
          <View style={s.run}>
            {lastFive.map((result, at) => (
              <View key={`result-${at}`} style={[s.square, squareOf(result)]} />
            ))}
          </View>
        </StatBox>
      )}

      {countedGames === undefined ? null : (
        <StatBox label={COUNTED_BLOCK}>
          {/* The figure alone. *29 counted games* is the clause a listener gets, and
              printing it under a box named *Counted* would say the word twice. */}
          <StatFigure>{String(countedGames)}</StatFigure>
        </StatBox>
      )}
    </StatRow>
  );
}

/** Won or lost, as a fill. The two are a lightness step apart — see the module note. */
function squareOf(result: GameResult) {
  return result === 'WIN' ? s.won : s.lost;
}

const s = StyleSheet.create({
  run: {
    flexDirection: 'row',
    gap: theme.space.xxs,
    alignItems: 'center',
    // The figure's own line, so a box of squares stands exactly as tall as a box of digits.
    height: theme.num.s.lineHeight,
  },
  square: {
    width: theme.size.recordSquare,
    height: theme.size.recordSquare,
    borderRadius: theme.radius.recordSquare,
  },
  won: { backgroundColor: theme.color.ink },
  lost: { backgroundColor: theme.color.muted },
});
