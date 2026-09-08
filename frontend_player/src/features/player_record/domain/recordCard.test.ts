import type { OpponentVariety, StrandRow } from './playerRecord';
import { countedRows, varietyShare } from './recordCard';

const row = (over: Partial<StrandRow> = {}): StrandRow => ({
  strand: 'SHOWS_UP',
  good: 9,
  opportunities: 9,
  pct: 100,
  ...over,
});

describe('what the record card may print under its own heading', () => {
  it('keeps the counted rows, in the order they were served', () => {
    const served = [
      row({ strand: 'SHOWS_UP' }),
      row({ strand: 'ANSWERS_CHALLENGES' }),
      row({ strand: 'ANSWERS_RESULTS' }),
    ];

    expect(countedRows(served).map((kept) => kept.strand)).toEqual([
      'SHOWS_UP',
      'ANSWERS_CHALLENGES',
      'ANSWERS_RESULTS',
    ]);
  });

  /**
   * **The one row that would make the heading false.** Everything else on this card is a ratio
   * the platform observed; stars are what people typed, and they have a block of their own that
   * says so. The contract states this row never crosses here — which is exactly the kind of
   * statement a heading should not have to trust a remote service for.
   */
  it('drops a strand that is somebody’s opinion, whatever the wire says', () => {
    const kept = countedRows([row(), row({ strand: 'SPORTSMANSHIP', pct: 96 })]);

    expect(kept.map((one) => one.strand)).toEqual(['SHOWS_UP']);
  });

  /**
   * The other two names with no provider today are **counted** — plans kept, money settled —
   * so the day one of them lights up it draws, and the rows go on agreeing with the pill above
   * them. A filter that took the whole absent half would have made that a silent disagreement.
   */
  it('keeps a counted strand this build has never been served', () => {
    expect(countedRows([row({ strand: 'KEEPS_PLANS' })])).toHaveLength(1);
  });

  it('draws no rows from no strands', () => {
    expect(countedRows([])).toEqual([]);
  });
});

describe('how widely somebody spreads their games', () => {
  const variety = (over: Partial<OpponentVariety> = {}): OpponentVariety => ({
    distinctOpponents: 14,
    gamesPlayed: 20,
    ...over,
  });

  it('is one division of the pair the platform served', () => {
    expect(varietyShare(variety())).toBe(70);
  });

  it('rounds where every other percentage in the app rounds, and nowhere else', () => {
    // 2 of 3 is 66,67, and the app prints whole percentages — the rounding is the formatter's,
    // so this returns the share and lets one function in the app decide how it is written.
    expect(varietyShare(variety({ distinctOpponents: 2, gamesPlayed: 3 }))).toBeCloseTo(66.67, 2);
  });

  it('answers at both ends: everybody different, and the same person every time', () => {
    expect(varietyShare(variety({ distinctOpponents: 20, gamesPlayed: 20 }))).toBe(100);
    expect(varietyShare(variety({ distinctOpponents: 1, gamesPlayed: 20 }))).toBe(5);
  });

  /**
   * **A doubles game is played against three people**, and the pair counts everybody who was
   * on the court — partner included — over the games they were on it for. So the division runs
   * past a hundred on any ordinary doubles record, and the definition's own worked example is a
   * singles one. A hundred already means *as widely as this gets*; `250%` reads as a bug, and
   * a reader learns nothing from it they did not learn from the pair printed beside it.
   */
  it('caps a doubles record at the widest it can mean, rather than printing 250%', () => {
    expect(varietyShare(variety({ distinctOpponents: 25, gamesPlayed: 10 }))).toBe(100);
  });
});
