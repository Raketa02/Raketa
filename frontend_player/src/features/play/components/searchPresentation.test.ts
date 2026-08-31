/**
 * The windows, the ladder's offers, the sorts and the forecast's caveat.
 *
 * Two refusals are asserted. **A rung's letter is never printed** — it is not even a parameter
 * — and **`ANY` claims nothing**, because an empty grid reads `ANY` and *Whenever suits* must
 * not read as an enthusiastic answer to a question nobody answered.
 */

import { SORT_OPTIONS, WINDOWS } from '../domain/vocabulary';

import {
  forecastAssumption,
  modeWord,
  relaxationOffer,
  sortLabel,
  windowLabel,
} from './searchPresentation';

describe('the five windows', () => {
  it('gives each its own name, in title case', () => {
    expect(WINDOWS.map(windowLabel)).toEqual([
      'Tonight',
      'Tomorrow',
      'This weekend',
      'This week',
      'Whenever suits',
    ]);
  });

  it('lets the one that claims nothing claim nothing', () => {
    const anytime = windowLabel('ANY');

    expect(anytime).toBe('Whenever suits');
    expect(anytime).not.toMatch(/!|any time|flexible/i);
  });
});

describe('a rung of the ladder', () => {
  it('asks for the week, or for the radius the offer carries', () => {
    expect(relaxationOffer({ ask: 'TIMES' })).toBe('Look outside your week');
    expect(relaxationOffer({ ask: 'RADIUS', radiusKm: 25 })).toBe('Look out to 25 km');
  });

  it('never prints the rung', () => {
    // Letters rather than numbers precisely so nobody lines them up against a struck rung;
    // printing either spelling would publish an engine-internal ordering.
    const offers = [
      relaxationOffer({ ask: 'TIMES' }),
      relaxationOffer({ ask: 'RADIUS', radiusKm: 25 }),
    ];

    for (const offer of offers) expect(offer).not.toMatch(/\brung\b|\b[ABC]\b/);
  });
});

describe('the sorts', () => {
  it('names all four, including the two nothing can reach today', () => {
    // Exhaustive by type is the point: the day one becomes offerable is a change to nothing.
    expect(SORT_OPTIONS.map(sortLabel)).toEqual([
      'Best fit',
      'Closest',
      'Evenest',
      'Most reliable',
    ]);
  });
});

describe('a provisional forecast', () => {
  it('carries §F2 #6 verbatim, as the figure’s own caveat', () => {
    expect(forecastAssumption('EMPTY_SEAT_MATCHES_ITS_PARTNER')).toBe(
      'Runs on what is seated so far, reading each half-empty side as if the missing player ' +
        'matched the one already there. It settles as you add.',
    );
  });
});

describe('the mode inside a sentence', () => {
  it('is a lower-case reading, not a control’s label', () => {
    expect(modeWord('COMPETITIVE')).toBe('competitive');
    expect(modeWord('FOR_FUN')).toBe('for fun');
  });
});
