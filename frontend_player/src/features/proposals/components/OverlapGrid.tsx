/**
 * **The overlap grid** — the week of the people on a card, as seven days by three parts of the day
 * (the screens A2.3; mocks 2–10; the mechanics §8.1).
 *
 * ```
 *              Slim overlap                   the grade — volt for High and Good, amber for Slim
 *   M    T    W    T    F    S    S           today's letter white, the rest grey
 *  ▭▭▭  ▭▭▭  ▭▭▭  ▭▭▭  ▭▭▭  ███  ▭▭▭          Morning 07–12
 *  ▭▭▭  ▭▭▭  ▭▭▭  ▭▭▭  ▒▒▒  ███  ▒▒▒          Afternoon 12–17
 *  ▒▒▒ [▒▒▒] ▒▒▒  ▭▭▭  ▒▒▒  ███  ▒▒▒          Evening 17–23 — the game's own cell ringed in coral
 * ```
 *
 * **Every shade is the server's** (`ReadGroupDeck`'s `overlap`, #539): *bright* where everybody on
 * the card is free together for a whole hour of the range, *dim* where all but one are, *dark*
 * where fewer. Nothing is re-derived from anybody's week here — the grid draws what it was sent,
 * and a cell it was not sent is dark.
 *
 * **One element to a listener** (`overlapLabel`): the grade, where everybody is free, where all but
 * one are, and when the game is. The cells are shades, and 2.07 between the dim and the dark is a
 * shade read beside its neighbours — Part 13's *never colour alone* is kept by the sentence, which
 * is the grid's whole meaning in words.
 *
 * **The ring stands proud of its row**, as every mock draws it: the game's cell grows `ringOut`
 * past its slot on each side, over its neighbours, rather than pushing the row apart — a grid whose
 * rows moved with the game's hour would draw the same week two ways on two cards.
 *
 * **On a short deck card its cells shrink with the card's other boxes, and keep their shape**
 * (#865; `deckCardGeometry`'s `scale`): each row of cells, the gaps between the cells, and the width
 * of the cells and the day letters over them, all at one share, centred — the words at their size,
 * and the grade across the grid's whole width, where no share can make it wrap. So the card measures
 * the grid by its words alone (`onWordsLaidOut`): the grade over the day letters, which no share
 * moves.
 */

import { memo } from 'react';
import { StyleSheet, Text, View, type LayoutChangeEvent, type ViewStyle } from 'react-native';

import { theme } from '@/shared/ui';
import { WEEKDAYS, type Weekday } from '@/shared/vocabulary/week';

import type { Overlap } from '../domain/deck';
import { DAY_RANGES, type DayRange, type OverlapShade } from '../domain/vocabulary';

import { overlapLabel } from './deckPresentation';
import { PROPOSALS_COPY } from './proposalsCopy';

const COPY = PROPOSALS_COPY;
const { cell: CELL, cellGap: GAP, ring: RING, ringOut: OUT } = theme.size.gameCard;

export interface OverlapGridProps {
  readonly overlap: Overlap;
  /** The weekday the deck was read on — its letter is drawn white. */
  readonly today: Weekday | undefined;
  /**
   * The share of their size the cells, their gaps and the grid's width are drawn at — a short deck
   * card's (`deckCardGeometry`). 1, at rest, unless said.
   */
  readonly scale?: number;
  /** The grid's words were laid out — the deck's card measures them (`deckCardGeometry`). */
  readonly onWordsLaidOut?: (event: LayoutChangeEvent) => void;
}

/**
 * Drawn again only for another week, another day or another share — the deck's card resizes its
 * gaps once it has measured itself (`deckCardGeometry`), and that moves the grid without drawing it
 * again.
 */
export const OverlapGrid = memo(function OverlapGrid({
  overlap,
  today,
  scale = 1,
  onWordsLaidOut,
}: OverlapGridProps) {
  const shadeOf = (day: Weekday, range: DayRange): OverlapShade =>
    overlap.cells.find((cell) => cell.day === day && cell.range === range)?.shade ?? 'DARK';

  // At rest the grid's own styles; on a short card every box at the card's share — see the note.
  // The cells and the day letters over them take the narrower width, centred, and the grade keeps
  // the grid's whole width: a grade narrowed with the boxes could wrap, and its words would then
  // change with the share they are measured to set.
  const gap = { gap: GAP * scale };
  const narrow: ViewStyle | undefined =
    scale < 1 ? { width: `${scale * 100}%`, alignSelf: 'center' } : undefined;
  const row = [s.days, gap, narrow, { height: CELL * scale }];

  return (
    <View
      style={gap}
      accessible
      accessibilityRole="image"
      accessibilityLabel={overlapLabel(overlap)}
      testID="overlap-grid"
    >
      <View
        style={s.words}
        testID="overlap-words"
        {...(onWordsLaidOut === undefined ? {} : { onLayout: onWordsLaidOut })}
      >
        <Text style={[s.grade, overlap.grade === 'SLIM' ? s.slim : s.good]}>
          {COPY.grade[overlap.grade]}
        </Text>

        <View style={[s.days, gap, narrow]}>
          {WEEKDAYS.map((day) => (
            <Text key={day} style={[s.letter, day === today ? s.today : undefined]}>
              {COPY.dayLetters[day - 1]}
            </Text>
          ))}
        </View>
      </View>

      {DAY_RANGES.map((range) => (
        <View key={range} style={row} testID={`overlap-row-${range}`}>
          {WEEKDAYS.map((day) => {
            const game = overlap.game.day === day && overlap.game.range === range;
            return (
              <View key={day} style={s.slot}>
                <View
                  style={[s.cell, SHADE[shadeOf(day, range)], game ? s.ringed : undefined]}
                  testID={game ? 'overlap-game-cell' : `overlap-${day}-${range}`}
                />
              </View>
            );
          })}
        </View>
      ))}
    </View>
  );
});

const s = StyleSheet.create({
  // The grade over the day letters: words, so their step stays at rest at any share.
  words: { gap: GAP },
  grade: { ...theme.type.h2, textAlign: 'center', marginBottom: theme.space.xs },
  good: { color: theme.color.volt },
  slim: { color: theme.color.gameAmber },
  days: { flexDirection: 'row' },
  letter: {
    ...theme.type.flab,
    flex: 1,
    textAlign: 'center',
    color: theme.color.onDarkEyebrow,
  },
  today: { color: theme.color.surface },
  // As tall as its row, which is `cell` at the card's share.
  slot: { flex: 1 },
  cell: { flex: 1, borderRadius: theme.radius.availabilityCell / 2 },
  // Proud of its slot on every side, over its neighbours — see the module note.
  ringed: {
    position: 'absolute',
    top: -OUT,
    bottom: -OUT,
    left: -OUT / 2,
    right: -OUT / 2,
    borderWidth: RING,
    borderColor: theme.color.coral,
    borderRadius: theme.radius.availabilityCell,
    zIndex: 1,
  },
});

const SHADE = StyleSheet.create({
  BRIGHT: { backgroundColor: theme.color.volt },
  DIM: { backgroundColor: theme.color.gameCellDim },
  DARK: { backgroundColor: theme.color.gameCellDark },
});
