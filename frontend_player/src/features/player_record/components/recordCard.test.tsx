/**
 * The record card, and the two claims a build session could quietly undo.
 *
 * **One tone rule, read twice.** The pill in the header and every bar under it are drawn from
 * the same ladder, so the screen can never show a green bar under a red pill for one ratio.
 * That defect has no symptom anywhere else — both halves look reasonable on their own — so it
 * is asserted here, at **both** boundaries and from **both** sides, over the two drawings
 * together rather than over the rule they share.
 *
 * **And a card with nothing to say is not drawn.** *We have not seen enough* and *they are bad
 * at this* are different facts, and the whole sheet is built so a newcomer's record reads as
 * new rather than as poor. A panel of noughts is the failure; an absent card is the answer.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, View, type ViewStyle } from 'react-native';

import { METER_TONE_FILL, theme, type MeterTone } from '@/shared/ui';

import type { PlayerRecord, StrandRow } from '../domain/playerRecord';
import { SCORE_FLOOR, SCORE_STRONG } from '../domain/scoreTone';

import { RecordCard } from './RecordCard';
import { RecordHeader } from './RecordHeader';
import {
  RECORD_CARD_TITLE_DRAWN,
  recordCardLabel,
  scorePill,
  strandFraction,
  varietyValue,
} from './recordPresentation';

const PLAYER = '9f2a1c44-0000-4000-8000-000000000001';

const row = (over: Partial<StrandRow> = {}): StrandRow => ({
  strand: 'SHOWS_UP',
  good: 9,
  opportunities: 9,
  pct: 100,
  ...over,
});

const record = (over: Partial<PlayerRecord> = {}): PlayerRecord => ({
  isSelf: false,
  nickname: 'cyryl',
  onCourt: false,
  areaCode: 'A+050612+0019938',
  socialTags: [],
  sports: [],
  ...over,
});

const flatten = (style: unknown) => StyleSheet.flatten(style as ViewStyle);

const grounds = (): readonly string[] =>
  screen
    .UNSAFE_getAllByType(View)
    .map((box) => flatten(box.props.style)?.backgroundColor)
    .filter((fill): fill is string => typeof fill === 'string');

/**
 * The three tones as the **pill** draws them — its `Tag` variants' own grounds. Written out
 * here rather than imported, because the point of the test is that two independently drawn
 * things agree: reading both off one table would assert nothing.
 */
const PILL_GROUND: Readonly<Record<MeterTone, string>> = {
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

function pillTone(playerScore: number): MeterTone {
  render(
    <RecordHeader
      record={record({ reliability: { playerScore, strands: [row()] } })}
      playerId={PLAYER}
    />,
  );
  return toneOf(grounds(), PILL_GROUND);
}

function barTone(pct: number): MeterTone {
  render(<RecordCard reliability={{ playerScore: pct, strands: [row({ pct })] }} />);
  return toneOf(grounds(), METER_TONE_FILL);
}

describe('one tone rule, read by the pill and by the bars', () => {
  /**
   * The lower step is not a drawing decision: it is where the matcher starts holding somebody
   * back. A bar that turned red a point after the pill did would tell a player their penalty had
   * not begun on the day it had — on the one screen built so they can watch it lift.
   */
  it.each([
    [SCORE_FLOOR - 1, 'poor'],
    [SCORE_FLOOR, 'neutral'],
    [SCORE_STRONG - 1, 'neutral'],
    [SCORE_STRONG, 'good'],
  ] as const)('draws %i as %s in both places', (figure, expected) => {
    expect(pillTone(figure)).toBe(expected);
    expect(barTone(figure)).toBe(expected);
  });
});

describe('the record card', () => {
  it('draws one row for a player with one', () => {
    render(<RecordCard reliability={{ playerScore: 100, strands: [row()] }} />);

    expect(screen.getByText(RECORD_CARD_TITLE_DRAWN)).toBeTruthy();
    expect(screen.getByText(strandFraction(row()))).toBeTruthy();
  });

  /**
   * **No card at all, rather than a card of noughts.** Nothing has ever fallen due for most
   * players on this platform today, and a heading over an empty box is the sheet explaining its
   * own gap — which is the one thing every absence on this sheet is spelled to avoid.
   */
  it('draws nothing at all for a player with no publishable strand', () => {
    render(<RecordCard />);

    expect(screen.queryByText(RECORD_CARD_TITLE_DRAWN)).toBeNull();
  });

  /**
   * **The two absences do not move together.** Somebody rated in nothing may have played all
   * week, and a plan that dissolved is an opportunity above without being a game anybody
   * played — so a card is drawn for whichever half survives, and the variety row is the half
   * that carries no bar.
   */
  it('draws the variety row alone where that is the only half there is', () => {
    render(<RecordCard variety={{ distinctOpponents: 14, gamesPlayed: 20 }} />);

    expect(screen.getByText(RECORD_CARD_TITLE_DRAWN)).toBeTruthy();
    expect(screen.getByText(varietyValue({ distinctOpponents: 14, gamesPlayed: 20 }))).toBeTruthy();
  });

  /**
   * **A build too old to name any strand keeps the figure and loses the rows.** The pill is the
   * number the matcher acts on and it is still correct; hiding a true figure because a *label*
   * was missing would take the one actionable fact off the one screen built to show it. So the
   * card goes and the pill stays, which is a shorter sheet rather than a wrong one — the same
   * answer the mapper gives one layer down.
   */
  it('keeps the pill when every row is a code this build cannot name', () => {
    const reliability = { playerScore: 93, strands: [] };
    render(<RecordHeader record={record({ reliability })} playerId={PLAYER} />);
    expect(screen.getByText(scorePill(93))).toBeTruthy();

    render(<RecordCard reliability={reliability} />);
    expect(screen.queryByText(RECORD_CARD_TITLE_DRAWN)).toBeNull();
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
