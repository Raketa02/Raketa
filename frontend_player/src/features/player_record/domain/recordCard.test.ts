import type { OpponentVariety } from './playerRecord';
import { varietyShare } from './recordCard';

describe('how widely somebody spreads their games', () => {
  const variety = (over: Partial<OpponentVariety> = {}): OpponentVariety => ({
    distinctOpponents: 14,
    timesOnCourt: 20,
    ...over,
  });

  it('is one division of the pair the platform served', () => {
    expect(varietyShare(variety())).toBe(70);
  });

  it('rounds where every other percentage in the app rounds, and nowhere else', () => {
    // 2 of 3 is 66,67, and the app prints whole percentages — the rounding is the formatter's,
    // so this returns the share and lets one function in the app decide how it is written.
    expect(varietyShare(variety({ distinctOpponents: 2, timesOnCourt: 3 }))).toBeCloseTo(66.67, 2);
  });

  it('answers at both ends: everybody different, and the same person every time', () => {
    expect(varietyShare(variety({ distinctOpponents: 20, timesOnCourt: 20 }))).toBe(100);
    expect(varietyShare(variety({ distinctOpponents: 1, timesOnCourt: 20 }))).toBe(5);
  });

  /**
   * **The cap is gone, and its absence is the assertion.**
   *
   * The denominator used to be a count of *games*, which is only divisible in singles: a
   * doubles evening puts three people on the court, so one game published `3 of 1` and this
   * function clamped a share of 300% down to a full bar. The wire counts **times on a court**
   * now and the backend refuses a pair whose numerator exceeds it — so a share over a hundred
   * is unrepresentable upstream, and a clamp here would only hide the next such defect.
   *
   * Ten seats opposite, five different people: half the faces were somebody met twice.
   */
  it('divides a doubles record honestly, because the pair is now divisible', () => {
    expect(varietyShare(variety({ distinctOpponents: 5, timesOnCourt: 10 }))).toBe(50);
    expect(varietyShare(variety({ distinctOpponents: 3, timesOnCourt: 3 }))).toBe(100);
  });
});
