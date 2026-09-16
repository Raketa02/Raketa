import type { Candidate } from './candidate';
import { drawOrder, selectionOn, sportRows, type RadarRow } from './reading';

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
