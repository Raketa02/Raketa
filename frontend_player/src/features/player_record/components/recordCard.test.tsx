/**
 * The record card, and the three claims a build session could quietly undo.
 *
 * **One tone rule, and now exactly one drawing of it.** The ladder tinted two things — the
 * header's pill and every bar under it — and the assertion was that two independently drawn
 * things agreed. The pill went when the Player Score became a 7.13 block, whose figure is `ink`
 * by specification, so what is left is the bars at the ladder's own boundaries **and the claim
 * that the block draws no tone at all**. That second half is the one worth pinning: tinting the
 * block back is the obvious-looking improvement, and it would offer a coarse three-step colour
 * as a second score on the one screen a held player opens to find out what holds them back.
 *
 * **And a card with nothing to say is not drawn.** *We have not seen enough* and *they are bad
 * at this* are different facts, and the whole sheet is built so a newcomer's record reads as
 * new rather than as poor. A panel of noughts is the failure; an absent card is the answer.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, View, type ViewStyle } from 'react-native';

import { METER_TONE_FILL, theme, type MeterTone } from '@/shared/ui';

import type { StrandRow } from '../domain/playerRecord';
import { SCORE_FLOOR, SCORE_STRONG } from '../domain/scoreTone';

import { RecordBlocks } from './RecordBlocks';
import { RecordCard } from './RecordCard';
import {
  COUNTED_BLOCK,
  LAST_FIVE_BLOCK,
  PLAYER_SCORE_BLOCK,
  VARIETY_LABEL,
  recordCardLabel,
  strandFraction,
  varietyValue,
} from './recordPresentation';

const row = (over: Partial<StrandRow> = {}): StrandRow => ({
  strand: 'SHOWS_UP',
  good: 9,
  opportunities: 9,
  pct: 100,
  ...over,
});

const flatten = (style: unknown) => StyleSheet.flatten(style as ViewStyle);

const grounds = (): readonly string[] =>
  screen
    .UNSAFE_getAllByType(View)
    .map((box) => flatten(box.props.style)?.backgroundColor)
    .filter((fill): fill is string => typeof fill === 'string');

/**
 * The three grounds the ladder is capable of painting, whichever surface paints them. Written
 * out here rather than imported from `Meter`, because the point of the two tests below is that
 * one drawing uses exactly one of them and the other uses **none**: reading the table off the
 * component under test would assert nothing in either direction.
 */
const TONE_GROUND: Readonly<Record<MeterTone, string>> = {
  good: theme.color.mintSoft,
  neutral: theme.color.line2,
  poor: theme.color.redSoft,
};

/** Which tone a rendering is in, read off what it actually painted. */
function toneOf(drawn: readonly string[], table: Readonly<Record<MeterTone, string>>): MeterTone {
  const found = (['good', 'neutral', 'poor'] as const).filter((tone) =>
    drawn.includes(table[tone]),
  );
  if (found.length !== 1 || found[0] === undefined) {
    throw new Error(`expected exactly one tone to be drawn, found ${found.join(', ') || 'none'}`);
  }
  return found[0];
}

function barTone(pct: number): MeterTone {
  render(<RecordCard reliability={{ playerScore: pct, strands: [row({ pct })] }} />);
  return toneOf(grounds(), METER_TONE_FILL);
}

describe('one tone rule, drawn by the bars', () => {
  /**
   * The lower step is not a drawing decision: it is where the matcher starts holding somebody
   * back. A bar that turned red a point after the ladder said so would tell a player their
   * penalty had not begun on the day it had — on the one screen built so they can watch it lift.
   */
  it.each([
    [SCORE_FLOOR - 1, 'poor'],
    [SCORE_FLOOR, 'neutral'],
    [SCORE_STRONG - 1, 'neutral'],
    [SCORE_STRONG, 'good'],
  ] as const)('draws %i as %s', (figure, expected) => {
    expect(barTone(figure)).toBe(expected);
  });

  /**
   * **The block is the ladder's non-consumer, and that is deliberate.** 7.13 fixes a block's
   * figure at `ink` on `paper2`, and the sheet's one ladder belongs to the number the matcher
   * acts on as it is *accounted for* — the rows below — rather than to the headline figure. A
   * three-step colour on the block would read as a second score beside the strands that explain
   * the first, so this asserts the absence at every step of the ladder rather than at one.
   */
  it.each([SCORE_FLOOR - 1, SCORE_FLOOR, SCORE_STRONG - 1, SCORE_STRONG] as const)(
    'draws %i in the block with no tone at all',
    (figure) => {
      render(<RecordBlocks playerScore={figure} />);

      const painted = grounds();
      for (const tone of ['good', 'neutral', 'poor'] as const) {
        expect(painted).not.toContain(TONE_GROUND[tone]);
      }
    },
  );
});

/**
 * **The block row's three absences, which do not move together.**
 *
 * The row sits outside the skill card precisely so they need not: two of the three come off
 * `skill` and the Player Score comes off `reliability`, which is folded from games and
 * challenges that have no sport in them. A player who has been ghosted on and holds no rating
 * at all has a Player Score and no skill panel — and a block nested inside a card drawn only
 * when a Level resolves would take their one figure down with the sport.
 */
describe('the record blocks', () => {
  it('draws the figure a player has, without the two they have not', () => {
    render(<RecordBlocks playerScore={91} />);

    expect(screen.getByText(PLAYER_SCORE_BLOCK)).toBeTruthy();
    expect(screen.getByText('91')).toBeTruthy();
    expect(screen.queryByText(LAST_FIVE_BLOCK)).toBeNull();
    expect(screen.queryByText(COUNTED_BLOCK)).toBeNull();
  });

  /**
   * A count with no Player Score is the other half of the same independence: somebody whose
   * games were all played and scored, and for whom nothing has ever *fallen due*.
   */
  it('draws a count with no score beside it', () => {
    render(<RecordBlocks countedGames={5} lastFive={['WIN', 'LOSS']} />);

    expect(screen.getByText(COUNTED_BLOCK)).toBeTruthy();
    expect(screen.queryByText(PLAYER_SCORE_BLOCK)).toBeNull();
  });

  /**
   * **No row, rather than a row of noughts** — the sheet's one spelling for every absence on
   * it, read on the newcomer this fixture is: nothing arranged, nothing counted, nothing said.
   */
  it('draws nothing at all where the platform watched none of the three', () => {
    render(<RecordBlocks />);

    expect(screen.toJSON()).toBeNull();
  });

  /** An empty run is no run, exactly as it is at the mapper and in the spoken label. */
  it('draws no run box for a run of nothing', () => {
    render(<RecordBlocks countedGames={0} lastFive={[]} />);

    expect(screen.queryByText(LAST_FIVE_BLOCK)).toBeNull();
    expect(screen.getByText(COUNTED_BLOCK)).toBeTruthy();
  });
});

describe('the record card', () => {
  it('draws one row for a player with one', () => {
    render(<RecordCard reliability={{ playerScore: 100, strands: [row()] }} />);

    expect(screen.getByText(strandFraction(row()))).toBeTruthy();
  });

  /**
   * **No card at all, rather than a card of noughts.** Nothing has ever fallen due for most
   * players on this platform today, and a heading over an empty box is the sheet explaining its
   * own gap — which is the one thing every absence on this sheet is spelled to avoid.
   */
  it('draws nothing at all for a player with no publishable strand', () => {
    render(<RecordCard />);

    // Not *an empty card* — no card. The heading it used to be recognised by is gone, so the
    // assertion is the tree itself rather than the absence of a word.
    expect(screen.toJSON()).toBeNull();
  });

  /**
   * **The two absences do not move together.** Somebody rated in nothing may have played all
   * week, and a plan that dissolved is an opportunity above without being a game anybody
   * played — so a card is drawn for whichever half survives, and the variety row is the half
   * that carries no bar.
   */
  it('draws the variety row alone where that is the only half there is', () => {
    render(<RecordCard variety={{ distinctOpponents: 14, timesOnCourt: 20 }} />);

    expect(screen.getByText(VARIETY_LABEL)).toBeTruthy();
    expect(
      screen.getByText(varietyValue({ distinctOpponents: 14, timesOnCourt: 20 })),
    ).toBeTruthy();
  });

  /**
   * **A build too old to name any strand keeps the figure and loses the rows.** The block is the
   * number the matcher acts on and it is still correct; hiding a true figure because a *label*
   * was missing would take the one actionable fact off the one screen built to show it. So the
   * card goes and the block stays, which is a shorter sheet rather than a wrong one — the same
   * answer the mapper gives one layer down.
   */
  it('keeps the block when every row is a code this build cannot name', () => {
    render(<RecordBlocks playerScore={93} />);
    expect(screen.getByText('93')).toBeTruthy();

    render(<RecordCard reliability={{ playerScore: 93, strands: [] }} />);
    expect(screen.toJSON()).toBeNull();
  });

  /**
   * **The bars are decoration and the card is one element.** The fraction is text two words
   * earlier, so a meter announcing itself would be 6.8's double announcement — the row reaching
   * a listener as *Shows up, 9 of 9, 100%*.
   */
  it('is one element, and no bar inside it is in the tree', () => {
    const strands = [
      row(),
      row({ strand: 'ANSWERS_RESULTS', good: 8, opportunities: 10, pct: 80 }),
    ];
    render(<RecordCard reliability={{ playerScore: 90, strands }} />);

    expect(screen.getByLabelText(recordCardLabel({ rows: strands }))).toBeTruthy();
    // Nothing under the card names itself, and nothing announces a value.
    expect(screen.queryAllByRole('progressbar')).toHaveLength(0);
  });
});
