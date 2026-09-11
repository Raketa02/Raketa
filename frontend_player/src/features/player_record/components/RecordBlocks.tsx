/**
 * **The record sheet's three blocks** — the Player Score, the run of five and the count the
 * Level rests on, under the band bar
 * ([7.13](../../../../docs/design-system.md#713-the-record-block)).
 *
 * ```
 * Player Score      Last 5            Counted
 * 91                ■ ■ ▨ ■ ▨         5
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
 * Two of the three are that sport's — the run and the count come off `skill` — and the Player
 * Score is about the **whole person**, folded from games and challenges that have no sport in
 * them. So the row cannot live inside a card that is drawn only when a Level resolves: a player
 * who has been ghosted on and holds no rating at all has a Player Score and no skill panel, and
 * a block nested in that card would take their one figure down with the sport.
 *
 * That is the sheet's standing rule about its own four absences, applied to a row rather than to
 * a zone: **they do not move together, and nothing may make one imply another.**
 *
 * ## Nothing here is tinted, and that is the ladder staying where it belongs
 *
 * The figure was a `Tag` in the header, tinted by `scoreTone`. A block's figure is `ink` — 7.13
 * fixes it — and the tone stays on the metered rows below, which is where a reader can act on
 * it: a bar that lifts is the thing a held player came to watch, and the same three colours
 * printed twice on one sheet would offer the pill to be read as a fourth strand.
 *
 * ## Each block is hidden when its fact is absent, and never zeroed
 *
 * The three fields are omitted on the wire rather than sent as `0` — a player nothing was ever
 * arranged for has not failed to turn up — so a newcomer draws no row at all and a player with
 * one fact draws one block filling the width. There is no empty state and no sentence
 * explaining the gap, which is every other absence's spelling on this sheet.
 */

import { View } from 'react-native';

import { RunOfForm, StatBox, StatFigure, StatRow } from '@/shared/ui';

import {
  COUNTED_BLOCK,
  LAST_FIVE_BLOCK,
  PLAYER_SCORE_BLOCK,
  recordBlocksLabel,
  type RecordBlockFacts,
} from './recordPresentation';

export type RecordBlocksProps = RecordBlockFacts;

export function RecordBlocks({ playerScore, lastFive, countedGames }: RecordBlocksProps) {
  // A run the wire omitted and an empty one are one absence here, exactly as they are at the
  // mapper: a run's length is a claim, so nought squares is nothing to draw rather than a box
  // of nothing. The three are asked the same question and the spoken label asks it again.
  const run = lastFive === undefined || lastFive.length === 0 ? undefined : lastFive;

  if (playerScore === undefined && run === undefined && countedGames === undefined) return null;

  return (
    // §20.1: no block is an action, so the row is one element and every box is a clause of its
    // label. The boxes themselves are plain `Text` and announce nothing, which is the rule
    // `StatBox` ships with — *do not draw one the label does not speak*.
    <View
      accessible
      accessibilityLabel={recordBlocksLabel({
        ...(playerScore === undefined ? {} : { playerScore }),
        ...(run === undefined ? {} : { lastFive: run }),
        ...(countedGames === undefined ? {} : { countedGames }),
      })}
    >
      <StatRow>
        {playerScore === undefined ? null : (
          <StatBox label={PLAYER_SCORE_BLOCK}>
            <StatFigure>{String(playerScore)}</StatFigure>
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
