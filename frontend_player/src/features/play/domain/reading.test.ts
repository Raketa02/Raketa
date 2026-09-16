import type { Candidate, SearchEnvelope } from './candidate';
import {
  drawOrder,
  oneFewerWaitingOnReading,
  selectionOn,
  sportRows,
  withAnswer,
  type RadarRow,
  type Reading,
} from './reading';

const BARE: Omit<Candidate, 'playerId' | 'distanceKm'> = {
  fit: 70,
  card: {
    name: 'Somebody',
    areaCode: 'A+050612+0019938',
    socialTags: [],
    level: 2.6,
    band: 'Established',
    range: { low: 2.4, high: 2.8 },
  },
  terms: [],
  concerns: [],
  livenessReasons: [],
  degradedTerms: [],
  modifiers: [],
};

function row(playerId: string, distanceKm: number, over: Partial<RadarRow> = {}): RadarRow {
  return {
    ...BARE,
    playerId,
    distanceKm,
    bearingDeg: 45,
    ratings: [{ sport: 'padel', level: 2.6 }],
    ...over,
  };
}

describe('the order tiles are painted in', () => {
  it('paints farther players first so nearer ones sit above them', () => {
    const rows = [row('near', 1.2), row('far', 4.8), row('mid', 2.4)];
    expect(drawOrder(rows, undefined).map((r) => r.playerId)).toEqual(['far', 'mid', 'near']);
  });

  it('paints the selected player last, above everybody', () => {
    const rows = [row('near', 1.2), row('far', 4.8), row('mid', 2.4)];
    expect(drawOrder(rows, 'far').map((r) => r.playerId)).toEqual(['mid', 'near', 'far']);
  });

  it('keeps the served id order between two rows at one printed distance', () => {
    const rows = [row('a', 1.9), row('b', 1.9), row('c', 0.6)];
    expect(drawOrder(rows, undefined).map((r) => r.playerId)).toEqual(['a', 'b', 'c']);
  });
});

describe('the card’s sport rows', () => {
  it('lifts the reading’s sport to the top and keeps the registry order under it', () => {
    const marek = row('marek', 4.8, {
      ratings: [
        { sport: 'padel', level: 2.92 },
        { sport: 'tennis', level: 3.4 },
      ],
    });
    expect(sportRows(marek, 'tennis')).toEqual([
      { sport: 'tennis', level: 3.4 },
      { sport: 'padel', level: 2.92 },
    ]);
    expect(sportRows(marek, 'padel')).toEqual([
      { sport: 'padel', level: 2.92 },
      { sport: 'tennis', level: 3.4 },
    ]);
  });

  it('draws every sport they are rated in, not only the ones the viewer shares', () => {
    const three = row('x', 1, {
      ratings: [
        { sport: 'padel', level: 2 },
        { sport: 'squash', level: 3 },
        { sport: 'badminton', level: 4 },
      ],
    });
    expect(sportRows(three, 'padel').map((r) => r.sport)).toEqual(['padel', 'squash', 'badminton']);
  });
});

describe('the selection against the next reading', () => {
  it('keeps a selected player who is still drawn, and drops one who is not — silently', () => {
    const rows = [row('a', 1), row('b', 2)];
    expect(selectionOn(rows, 'a')).toBe('a');
    expect(selectionOn(rows, 'gone')).toBeUndefined();
    expect(selectionOn(rows, undefined)).toBeUndefined();
    expect(selectionOn([], 'a')).toBeUndefined();
  });
});

/** A reading's envelope with the chip's number on it — the deck's number by the deck's rule. */
function envelope(wantToPlayYou: number | undefined): SearchEnvelope {
  return {
    searchId: 'reading-1',
    mode: null,
    pool: {
      radiusKmUsed: 10,
      playersInRange: 2,
      window: null,
      ...(wantToPlayYou === undefined ? {} : { wantToPlayYou }),
    },
    rulesetVersion: 'ruleset-v1',
    engineVersion: 'matchfit-v1',
    radiusClamp: false,
    optimisedFor: null,
    sortsAvailable: [],
    rungOffers: null,
  };
}

function reading(rows: readonly RadarRow[], wantToPlayYou?: number): Reading {
  return { envelope: envelope(wantToPlayYou), rows };
}

describe('a row after an answer', () => {
  /**
   * The person stays on the radar — the radar hides nobody for a pass (ADR-0174 §4) — and the
   * card's last line says what was said. Marking is by person: the reading is the whole reach
   * and an answer is about one row of it.
   */
  it('marks the one row and keeps every row', () => {
    const held = reading([row('filip', 1.9), row('marek', 4.8)]);

    const after = withAnswer(held, 'filip', 'yes');

    expect(after.rows.map((r) => [r.playerId, r.answered])).toEqual([
      ['filip', 'yes'],
      ['marek', undefined],
    ]);
    expect(after.envelope).toBe(held.envelope);
  });

  /** A refused write takes the mark back — the same return the deck's card makes. */
  it('unmarks on the answer being taken back', () => {
    const held = withAnswer(reading([row('filip', 1.9)]), 'filip', 'no');
    expect(withAnswer(held, 'filip', undefined).rows[0]?.answered).toBeUndefined();
  });

  it('leaves a reading that does not hold the person as it was', () => {
    const held = reading([row('marek', 4.8)]);
    expect(withAnswer(held, 'filip', 'yes')).toBe(held);
  });
});

describe('the reading’s chip after a liker’s mutual', () => {
  const liker = row('zofia', 2.2, { inclusionReason: 'INTEREST_LIFT' });

  it('drops by one when the person answered carried the admitting code', () => {
    const held = reading([liker, row('filip', 1.9)], 3);
    expect(oneFewerWaitingOnReading(held, 'zofia').envelope.pool.wantToPlayYou).toBe(2);
  });

  it('is untouched for a stranger, at nought, and where the reading carried no count', () => {
    const stranger = reading([liker, row('filip', 1.9)], 3);
    expect(oneFewerWaitingOnReading(stranger, 'filip')).toBe(stranger);

    const nought = reading([liker], 0);
    expect(oneFewerWaitingOnReading(nought, 'zofia')).toBe(nought);

    const uncounted = reading([liker]);
    expect(oneFewerWaitingOnReading(uncounted, 'zofia')).toBe(uncounted);
  });
});
