/**
 * **The record sheet's three blocks** — the Player Score, the run of five and the count the
 * Level rests on, under the band bar
 * ([7.13](../../../../docs/design-system.md#713-the-record-block)).
 *
 * ```
 * Player reliability   Last 5            Counted
 * 75                   ■ ■ ▨ ■ ▨         5
 * High
 * ```
 *
 * ## It is the competitive card's row, on a second surface
 *
 * The same three facts under the same three names in the same recessed box — because they *are*
 * the same three facts, and a reader who has just closed a shortlist and tapped a face must not
 * be shown them twice in two shapes. What is imported is `shared/ui`'s `StatBox`; what is not is
 * `features/play/`, which this feature may not deep-import and which is in any case the wrong
 * direction — Play is what opens this sheet.
 *
 * **The words are this feature's own** (`recordPresentation`), because a screen is assembled
 * from words that live in one place. The two decks agree today and the day one of them changes
 * is the day somebody decides whether the other should.
 *
 * ## It is a row of the sheet and not part of the skill card, and the reason is an absence
 *
 * Two of the three are that sport's — the run and the count come off `skill` — and Player
 * reliability is about the **whole person**, folded from games and bookings across every sport.
 * So the row cannot live inside a card that is drawn only when a Level resolves: a player who
 * holds no rating at all still has a figure — 100 to start — and a block nested in that card
 * would take it down with the sport.
 *
 * That is the sheet's standing rule about its absences, applied to a row rather than to a zone:
 * **they do not move together, and nothing may make one imply another.**
 *
 * ## The figure says its band, or *New*, and nothing here is tinted
 *
 * Under the figure, the band's word — *Very high*, *High*, *Medium*, *Low* — or *New* in its
 * place ([#660](https://github.com/Raketa02/Raketa/issues/660), ADR-0195 §1): a group-mate who
 * opens somebody's record reads what they read about themselves, and *New* is what tells them a
 * 100 has not been tested yet. On its own line, in the key-value row's value role, so a
 * *Very high* never has to share a third of the width with the figure. Both are `ink` — 7.13
 * fixes the figure's colour — and the band's tone is the Members tag's alone, on the one list
 * that compares people at a glance.
 *
 * ## Each block is hidden when its fact is absent, and never zeroed
 *
 * The run and the count are omitted on the wire rather than sent as `0`, so a player with no
 * rating draws the reliability block alone, filling the width. Player reliability itself is
 * always on a record; a surface that draws the blocks before the record is in passes none, and
 * the row waits rather than drawing a nought.
 */

import { StyleSheet, Text, View } from 'react-native';

import { RunOfForm, StatBox, StatFigure, StatRow, theme } from '@/shared/ui';

import {
  COUNTED_BLOCK,
  LAST_FIVE_BLOCK,
  PLAYER_SCORE_BLOCK,
  recordBlocksLabel,
  reliabilityMark,
  type RecordBlockFacts,
} from './recordPresentation';

export type RecordBlocksProps = RecordBlockFacts;

export function RecordBlocks({ reliability, lastFive, countedGames }: RecordBlocksProps) {
  // A run the wire omitted and an empty one are one absence here, exactly as they are at the
  // mapper: a run's length is a claim, so nought squares is nothing to draw rather than a box
  // of nothing. The three are asked the same question and the spoken label asks it again.
  const run = lastFive === undefined || lastFive.length === 0 ? undefined : lastFive;

  if (reliability === undefined && run === undefined && countedGames === undefined) return null;
  const mark = reliability === undefined ? undefined : reliabilityMark(reliability);

  return (
    // §20.1: no block is an action, so the row is one element and every box is a clause of its
    // label. The boxes themselves are plain `Text` and announce nothing, which is the rule
    // `StatBox` ships with — *do not draw one the label does not speak*.
    <View
      accessible
      accessibilityLabel={recordBlocksLabel({
        ...(reliability === undefined ? {} : { reliability }),
        ...(run === undefined ? {} : { lastFive: run }),
        ...(countedGames === undefined ? {} : { countedGames }),
      })}
    >
      <StatRow>
        {reliability === undefined ? null : (
          <StatBox label={PLAYER_SCORE_BLOCK}>
            <StatFigure>{String(reliability.playerScore)}</StatFigure>
            {/* The band's word or *New*, under the figure — the bare figure where this build
                could not name the band, never a guessed word. */}
            {mark === undefined ? null : <Text style={s.mark}>{mark}</Text>}
          </StatBox>
        )}

        {run === undefined ? null : (
          <StatBox label={LAST_FIVE_BLOCK}>
            {/* Never padded: three squares means three counted results, and the gap at the end
                — where the newest results are not yet — is the honest statement. */}
            <RunOfForm results={run} />
          </StatBox>
        )}

        {countedGames === undefined ? null : (
          <StatBox label={COUNTED_BLOCK}>
            {/* The figure alone. *5 counted games* is the clause a listener gets, and printing
                the noun under a box named *Counted* would say the word twice. */}
            <StatFigure>{String(countedGames)}</StatFigure>
          </StatBox>
        )}
      </StatRow>
    </View>
  );
}

const s = StyleSheet.create({
  // 5.5's value role: a word under a figure, read as the figure's answer.
  mark: { ...theme.type.rlValue, color: theme.color.ink },
});
