/**
 * The record card and the block over it, and the claims a build session could quietly undo
 * ([#660](https://github.com/Raketa02/Raketa/issues/660), ADR-0195 §1).
 *
 * **Counts, and no meters.** Player reliability is points now, and what the record shows beside
 * them is four counts over the last 6 months — *Shows up*, *Keeps plans*, *Being late*, *Results
 * left in dispute*. The metered rows of weighted strands are gone, and so is the tone ladder that
 * painted them: nothing on the card is a bar, and nothing on it is tinted.
 *
 * **The block says the band, or New.** The figure was a bare number in 7.13's box; a group-mate
 * opening somebody's record reads the band's word under it, and *New* where it applies — the
 * word that tells them a 100 has not been tested yet.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, View, type ViewStyle } from 'react-native';

import { METER_TONE_FILL, Meter, theme } from '@/shared/ui';

import type { ReliabilityCounts } from '../domain/playerRecord';

import { RecordBlocks } from './RecordBlocks';
import { RecordCard } from './RecordCard';
import {
  COUNTED_BLOCK,
  LAST_FIVE_BLOCK,
  PLAYER_SCORE_BLOCK,
  SPORTSMANSHIP_LABEL,
  VARIETY_LABEL,
  countLines,
  opinionFigure,
  recordBlocksLabel,
  recordCardLabel,
  varietyValue,
} from './recordPresentation';

/** Sergio's six months: turned up 12 of 13, kept 13 of 14, late once, nothing in dispute. */
const SERGIO: ReliabilityCounts = {
  turnedUp: 12,
  turnedUpOf: 13,
  late: 1,
  kept: 13,
  keptOf: 14,
  leftInDispute: 0,
};

/** Nerea's: nothing has happened to her yet. */
const NEREA: ReliabilityCounts = {
  turnedUp: 0,
  turnedUpOf: 0,
  late: 0,
  kept: 0,
  keptOf: 0,
  leftInDispute: 0,
};

const flatten = (style: unknown) => StyleSheet.flatten(style as ViewStyle);

const grounds = (): readonly string[] =>
  screen
    .UNSAFE_getAllByType(View)
    .map((box) => flatten(box.props.style)?.backgroundColor)
    .filter((fill): fill is string => typeof fill === 'string');

/**
 * Every tone a figure could be painted in — the retired meters' three fills, and the score tag's
 * three toned tints. Read off the meter rather than spelled, and asserted absent: nothing on the
 * card or the block is toned.
 */
const TONES = [
  ...Object.values(METER_TONE_FILL),
  theme.color.mintSoft,
  theme.color.amberSoft,
  theme.color.redSoft,
] as const;

describe('the record card', () => {
  it('draws Shows up, Keeps plans, Being late and Results left in dispute, each as a count', () => {
    render(<RecordCard counts={SERGIO} />);

    for (const line of countLines(SERGIO)) {
      expect(screen.getByText(line.label)).toBeTruthy();
      expect(screen.getByText(line.value)).toBeTruthy();
    }
    expect(screen.getByText('turned up 12 of 13')).toBeTruthy();
    expect(screen.getByText('kept 13 of 14')).toBeTruthy();
    expect(screen.getByText('late 1 time')).toBeTruthy();
  });

  /**
   * **No meter and no tone.** A bar drew a ratio, and the figure is points now: the counts are
   * the account, in words, and no row is painted in a ladder that has gone.
   */
  it('draws no bar and paints no row', () => {
    render(<RecordCard counts={SERGIO} />);

    expect(screen.UNSAFE_queryAllByType(Meter)).toHaveLength(0);
    const painted = grounds();
    for (const tone of TONES) expect(painted).not.toContain(tone);
    // The strands' names are gone with them.
    expect(screen.queryByText(/Answers about results|Answers challenges|Settles up/)).toBeNull();
  });

  /**
   * **A new player's card is drawn, and reads what is true.** Everyone has a figure from the
   * start, so the counts are always there — nought of nought for somebody nothing has fallen due
   * for, which is what the *New* beside their figure explains.
   */
  it('draws a new player’s counts as they are served', () => {
    render(<RecordCard counts={NEREA} />);

    expect(screen.getByText('turned up 0 of 0')).toBeTruthy();
    expect(screen.getByText('late 0 times')).toBeTruthy();
  });

  it('draws the variety row under the counts', () => {
    render(<RecordCard counts={SERGIO} variety={{ distinctOpponents: 14, timesOnCourt: 20 }} />);

    expect(screen.getByText(VARIETY_LABEL)).toBeTruthy();
    expect(
      screen.getByText(varietyValue({ distinctOpponents: 14, timesOnCourt: 20 })),
    ).toBeTruthy();
  });

  /**
   * **What other players said is one row, drawn the same for everybody** — the label naming its
   * author and the figure with its count, in the card's mono figure role, spoken as one clause of
   * the card (ADR-0179 §5, [#473](https://github.com/Raketa02/Raketa/issues/473)).
   */
  it('draws the sportsmanship row as the figure and its count', () => {
    render(<RecordCard counts={SERGIO} opinion={{ average: 4.3, raters: 12 }} />);

    expect(screen.getByText(SPORTSMANSHIP_LABEL)).toBeTruthy();
    expect(screen.getByText(opinionFigure({ average: 4.3, raters: 12 }))).toBeTruthy();
  });

  /** §20.1: the sheet has no action inside the card, so the card is one element. */
  it('is one element, spoken one clause a row', () => {
    const facts = {
      counts: SERGIO,
      variety: { distinctOpponents: 14, timesOnCourt: 20 },
      opinion: { average: 4.3, raters: 12 },
    };
    render(<RecordCard {...facts} />);

    expect(screen.getByLabelText(recordCardLabel(facts))).toBeTruthy();
  });
});

/**
 * **The block row's three absences, which do not move together** — and the figure's word.
 *
 * Two of the three come off `skill` and Player reliability comes off the whole person, and it is
 * always there now (ADR-0195 §1): a newcomer with no rating at all draws one box, and it says
 * *New*.
 */
describe('the record blocks', () => {
  it('draws the figure with the band’s word under it', () => {
    render(<RecordBlocks reliability={{ playerScore: 75, band: 'HIGH', isNew: false }} />);

    expect(screen.getByText(PLAYER_SCORE_BLOCK)).toBeTruthy();
    expect(screen.getByText('75')).toBeTruthy();
    expect(screen.getByText('High')).toBeTruthy();
    expect(screen.queryByText(LAST_FIVE_BLOCK)).toBeNull();
    expect(screen.queryByText(COUNTED_BLOCK)).toBeNull();
  });

  /** *100 · New* — so a group-mate knows this 100 has not been tested yet (PRD #649, story 33). */
  it('draws New in the band’s place for a player who is new', () => {
    render(<RecordBlocks reliability={{ playerScore: 100, band: 'VERY_HIGH', isNew: true }} />);

    expect(screen.getByText('100')).toBeTruthy();
    expect(screen.getByText('New')).toBeTruthy();
    expect(screen.queryByText('Very high')).toBeNull();
  });

  /** A band this build cannot name: the figure alone, never a guessed word. */
  it('draws the bare figure where the band could not be named', () => {
    const figure = { playerScore: 42, isNew: false };
    render(<RecordBlocks reliability={figure} />);

    expect(screen.getByText('42')).toBeTruthy();
    expect(screen.getByLabelText(recordBlocksLabel({ reliability: figure }))).toBeTruthy();
  });

  /**
   * **The block's figure is `ink`, whatever the band** — 7.13 fixes it, and the tone the band
   * carries is the Members tag's, on the one list that compares people at a glance.
   */
  it.each(['VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW'] as const)(
    'paints no tint in the block for %s',
    (band) => {
      render(<RecordBlocks reliability={{ playerScore: 60, band, isNew: false }} />);

      const painted = grounds();
      for (const tone of TONES) expect(painted).not.toContain(tone);
    },
  );

  it('draws a count beside the figure, and speaks the three as one element', () => {
    const facts = {
      reliability: { playerScore: 91, band: 'VERY_HIGH', isNew: false },
      countedGames: 5,
      lastFive: ['WIN', 'LOSS'],
    } as const;
    render(<RecordBlocks {...facts} />);

    expect(screen.getByText(COUNTED_BLOCK)).toBeTruthy();
    expect(screen.getByLabelText(recordBlocksLabel(facts))).toBeTruthy();
  });

  /** The passport's blocks before the record is in: no reliability box, never a nought. */
  it('draws nothing at all where none of the three is in', () => {
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
