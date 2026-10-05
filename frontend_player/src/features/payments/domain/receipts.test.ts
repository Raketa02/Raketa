/** How a receipt names its game's day, on the platform's calendar (Warsaw). */

import { receiptDayOf } from './receipts';

/** Wednesday 30 September 2026, 10:00 in Warsaw. */
const NOW = Date.parse('2026-09-30T08:00:00Z');

describe('receiptDayOf', () => {
  it('says Today for a game today — the mock’s own row', () => {
    expect(receiptDayOf('2026-09-30T14:00:00Z', NOW)).toEqual({ kind: 'today' });
  });

  it('says Tomorrow and Yesterday a day either way, on Warsaw’s calendar', () => {
    expect(receiptDayOf('2026-10-01T05:00:00Z', NOW)).toEqual({ kind: 'tomorrow' });
    // 23:30 UTC on the 29th is already the 30th in Warsaw — today, not yesterday.
    expect(receiptDayOf('2026-09-29T22:30:00Z', NOW)).toEqual({ kind: 'today' });
    expect(receiptDayOf('2026-09-29T17:00:00Z', NOW)).toEqual({ kind: 'yesterday' });
  });

  it('names the weekday within the week ahead, and the date beyond it or further back', () => {
    expect(receiptDayOf('2026-10-03T14:00:00Z', NOW)).toEqual({ kind: 'weekday', weekday: 6 });
    expect(receiptDayOf('2026-10-07T14:00:00Z', NOW)).toEqual({ kind: 'dated', day: '2026-10-07' });
    expect(receiptDayOf('2026-09-26T14:00:00Z', NOW)).toEqual({ kind: 'dated', day: '2026-09-26' });
  });

  it('names nothing for a value that is not an instant', () => {
    expect(receiptDayOf('not a time', NOW)).toBeUndefined();
  });
});
