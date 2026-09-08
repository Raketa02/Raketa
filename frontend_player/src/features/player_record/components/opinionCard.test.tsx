/**
 * **The second block**, and the three claims a build session could quietly undo.
 *
 * The block exists so the card above it can keep saying *counted by the system, not written by
 * people*. That promise is one heading away from false at all times: what other players typed
 * has to be **outside** that card, under a heading naming its own author, and neither the
 * figure nor the count may ever appear on the record of the person they are about.
 */

import { render, screen } from '@testing-library/react-native';

import type { Opinion } from '../domain/playerRecord';

import { OpinionCard } from './OpinionCard';
import { RecordCard } from './RecordCard';
import {
  OPINION_BAND_NAME,
  OPINION_CARD_TITLE_DRAWN,
  RECORD_CARD_TITLE_DRAWN,
  WRITTEN_BY_PLAYERS,
  opinionCardLabel,
  opinionFigure,
} from './recordPresentation';

const SAID = { average: 4.7, raters: 17 } as const;
const FIGURE: Opinion = { kind: 'figure', ...SAID };
const BAND: Opinion = { kind: 'band', band: 'GOOD' };

describe('what opponents said', () => {
  it('draws the figure and the count of people it rests on, under its own heading', () => {
    render(<OpinionCard opinion={FIGURE} />);

    expect(screen.getByText(OPINION_CARD_TITLE_DRAWN)).toBeTruthy();
    expect(screen.getByText(opinionFigure(SAID))).toBeTruthy();
  });

  /**
   * **A band and nothing else.** An average beside a count lets the subject subtract each new
   * rating out and name it — and they know who they played, so every answer would be
   * identifiable by the one person who must never see it.
   */
  it('draws a band on your own record, and no figure and no count anywhere on it', () => {
    render(<OpinionCard opinion={BAND} />);

    expect(screen.getByText(OPINION_BAND_NAME.GOOD)).toBeTruthy();
    expect(screen.queryByText(opinionFigure(SAID))).toBeNull();
    expect(screen.getByLabelText(opinionCardLabel(BAND))).toBeTruthy();
  });

  /**
   * Rating is a favour and nothing records that somebody did not answer, so most people have no
   * block. It is the same absence every zone on this sheet spells: nothing drawn, and no
   * sentence explaining the gap.
   */
  it('draws nothing at all for a subject nobody has rated', () => {
    render(<OpinionCard />);

    expect(screen.queryByText(OPINION_CARD_TITLE_DRAWN)).toBeNull();
  });

  /**
   * **The heading above is a promise about authorship, and this block is what keeps it.** The
   * counted card draws its own rows under its own title and never this one — a figure people
   * typed sitting beneath *counted by the system* would make that title false.
   */
  it('stands outside the counted card, which draws no opinion of any kind', () => {
    render(
      <RecordCard
        reliability={{
          playerScore: 93,
          strands: [
            { strand: 'SHOWS_UP', good: 9, opportunities: 9, pct: 100 },
            { strand: 'SPORTSMANSHIP', good: 47, opportunities: 50, pct: 94 },
          ],
        }}
      />,
    );

    expect(screen.getByText(RECORD_CARD_TITLE_DRAWN)).toBeTruthy();
    expect(screen.queryByText(OPINION_CARD_TITLE_DRAWN)).toBeNull();
    expect(screen.queryByText(WRITTEN_BY_PLAYERS)).toBeNull();
  });
});
