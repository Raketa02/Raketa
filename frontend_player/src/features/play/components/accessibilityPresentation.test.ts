/**
 * What each Play control announces — `the-words.md` §20.
 *
 * The assertions are the section's rulings, one apiece: the card is spoken in a different
 * order than it is drawn, Fit states its denominator, no seat carries an index, the two
 * glyphs are never spoken, and there are three live regions and no fourth.
 */

import { OUT_OF_DATE_GAP } from '@/shared/vocabulary/outOfDate';

import { SEAT_PLACES } from '../domain/lineup';

import {
  PLAY_LIVE_REGIONS,
  SWAP_TOGGLE_LABEL,
  availabilityDiffCellLabel,
  candidateActionLabel,
  candidateCardLabel,
  clearSeatLabel,
  courtSummaryLabel,
  deckAnswerLabels,
  fitSentence,
  provisionalForecastAnnouncement,
  seatLabel,
  whyFitRowLabel,
  whyFitSheetLabel,
} from './accessibilityPresentation';

const MAREK = {
  name: 'Marek',
  fit: 78,
  level: { level: 2.71, band: 'Established', range: { low: 2.55, high: 2.87 } },
  meta: { km: 4, theirAreaCode: 'A+050612+0019938', myAreaCode: 'A+050612+0019938' },
  reasons: ['0,12 above you', '3 slots you both ticked · next Tue evening'],
  concerns: ['A long way out'],
} as const;

describe('the candidate card', () => {
  it('is spoken in a different order than it is drawn', () => {
    const label = candidateCardLabel(MAREK);

    // Identifying facts lead, the argument follows. §20.1's one recorded divergence from
    // visual order in the feature.
    const order = [
      label.indexOf('Marek'),
      label.indexOf('Fit 78'),
      label.indexOf('Established'),
      label.indexOf('4 km'),
      label.indexOf('0,12 above you'),
      label.indexOf('A long way out'),
    ];

    expect(order).toEqual([...order].sort((a, b) => a - b));
    expect(order).not.toContain(-1);
  });

  it('merges the fit pill rather than announcing it separately', () => {
    expect(candidateCardLabel(MAREK)).toContain('Fit 78 out of 100');
  });

  it("never speaks the pill's glyph", () => {
    expect(candidateCardLabel(MAREK)).not.toContain('✦');
  });

  it('keeps the reason lines rather than dropping them to a word count', () => {
    // §10 is titled "Why this person is on the list" — cutting the argument to satisfy a cap
    // would delete what the card is for.
    for (const reason of MAREK.reasons) expect(candidateCardLabel(MAREK)).toContain(reason);
  });

  it('draws no empty sentence when the reason row is hidden', () => {
    const label = candidateCardLabel({ ...MAREK, reasons: [], concerns: [] });

    expect(label).not.toMatch(/\.\s*\./);
    expect(label.endsWith('.')).toBe(true);
  });

  it('names the subject on the primary button, which twenty cards otherwise share', () => {
    expect(candidateActionLabel('ADD_TO_COURT', 'Marek')).toBe('Add Marek to the court');
    expect(candidateActionLabel('CHALLENGE', 'Marek')).toBe('Challenge Marek');
  });
});

describe('the deck', () => {
  it('names the subject on both answers and speaks neither glyph', () => {
    const { pass, accept } = deckAnswerLabels('Marek');

    expect(pass).toBe('Not today, Marek');
    expect(accept).toBe("Let's play, Marek");
    expect(accept).not.toContain('🎾');
  });
});

describe('the court', () => {
  it('places four seats against a summary that says how many are filled', () => {
    expect(courtSummaryLabel({ sportName: 'Padel', filled: 3, seats: 4 })).toBe(
      'Padel, 3 of 4 seats filled.',
    );
  });

  it('announces side and role, and never an index', () => {
    const labels = [
      seatLabel('YOUR_SIDE', { kind: 'you' }),
      seatLabel('YOUR_PARTNER', { kind: 'player', name: 'Marek', level: 2.92 }),
      seatLabel('THEIR_SIDE', { kind: 'player', name: 'Ana', level: 3.1 }),
      seatLabel('THEIR_SIDE', { kind: 'empty', unfilled: null }),
      clearSeatLabel({ name: 'Marek', place: 'YOUR_PARTNER' }),
    ];

    // H-25 puts both squash players on the same half, so seat 3 is not where seat 3 was.
    for (const label of labels) expect(label).not.toMatch(/\bseat\s*\d/i);
    for (const label of labels) expect(label).toMatch(/^(Your|Their) side|from (your|their) side/);
  });

  it('says who is where without a number for a person', () => {
    expect(seatLabel('YOUR_SIDE', { kind: 'you' })).toBe('Your side, you');
    expect(seatLabel('YOUR_PARTNER', { kind: 'player', name: 'Marek', level: 2.92 })).toBe(
      'Your side, your partner, Marek, level 2,92',
    );
    expect(seatLabel('THEIR_SIDE', { kind: 'player', name: 'Ana', level: 3.1 })).toBe(
      'Their side, Ana, level 3,10',
    );
  });

  it('gives an empty seat the obstacle when the engine has one, and nothing when it does not', () => {
    expect(seatLabel('THEIR_SIDE', { kind: 'empty', unfilled: null })).toBe('Their side, empty');
    expect(seatLabel('THEIR_SIDE', { kind: 'empty', unfilled: 'POOL_EXHAUSTED' })).toBe(
      'Their side, empty. Nobody left in range — everybody who fits is already seated',
    );
  });

  it('names the person the clear badge removes, and the side it removes them from', () => {
    expect(clearSeatLabel({ name: 'Marek', place: 'YOUR_PARTNER' })).toBe(
      'Remove Marek from your side',
    );
    expect(clearSeatLabel({ name: 'Ana', place: 'THEIR_SIDE' })).toBe('Remove Ana from their side');
  });

  it('gives every place a phrase, so a place added here cannot ship without words', () => {
    for (const place of SEAT_PLACES) {
      expect(seatLabel(place, { kind: 'empty', unfilled: null })).not.toBe('');
    }
  });

  it('labels the swap toggle by what it does, and lets `checked` carry the state', () => {
    expect(SWAP_TOGGLE_LABEL).toBe('Swap players');
  });
});

describe('the why-fit sheet', () => {
  it('is named without the glyph its visible title draws', () => {
    expect(whyFitSheetLabel(78)).toBe('Why fit 78');
    expect(whyFitSheetLabel(78)).not.toContain('✦');
  });

  it('puts the figure in the row, because the meter beside it is hidden', () => {
    expect(
      whyFitRowLabel({ term: 'Level fit', figure: '×0,22 → 18', reason: '0,12 above you' }),
    ).toBe('Level fit. ×0,22 → 18. 0,12 above you');
  });

  it('drops the reason clause rather than announcing an empty one', () => {
    expect(whyFitRowLabel({ term: 'Level fit', figure: '×0,22 → 18' })).toBe(
      'Level fit. ×0,22 → 18',
    );
  });
});

describe('Fit states the scale it is against', () => {
  it('is out of 100, which is the term CONTEXT.md defines', () => {
    expect(fitSentence(78)).toBe('Fit 78 out of 100');
  });
});

describe("the diff grid's third fact", () => {
  it('says it in words, where the sheet drew it in a colour', () => {
    const cell = { day: 1, part: 'evening' } as const;

    expect(availabilityDiffCellLabel(cell, 'on')).toBe('Monday evening');
    expect(availabilityDiffCellLabel(cell, 'added')).toBe('Monday evening, newly added');
    expect(availabilityDiffCellLabel(cell, 'dropped')).toBe('Monday evening, dropped');
  });

  it('hides a slot that was off and stayed off rather than announcing it empty', () => {
    expect(availabilityDiffCellLabel({ day: 1, part: 'evening' }, 'off')).toBeUndefined();
  });
});

describe('the live regions', () => {
  it('are three, and all polite', () => {
    expect(Object.keys(PLAY_LIVE_REGIONS)).toHaveLength(3);
    expect(Object.values(PLAY_LIVE_REGIONS)).toEqual(['queued', 'queued', 'queued']);
  });

  it('carry the provisional forecast, which changes where the listener is not', () => {
    const announcement = provisionalForecastAnnouncement({
      pct: 74,
      assumption: 'EMPTY_SEAT_MATCHES_ITS_PARTNER',
    });

    expect(announcement).toContain('Fairly even, 74%');
    // ADR-0108: the figure and its caveat are one thing.
    expect(announcement).toContain('It settles as you add.');
  });

  it('names the gap rather than announcing a total with an unexplained assumption', () => {
    expect(provisionalForecastAnnouncement({ pct: 74, assumption: null })).toContain(
      OUT_OF_DATE_GAP,
    );
  });
});
