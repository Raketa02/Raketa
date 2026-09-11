/**
 * The date beside the weekday, read off the string — the first date this app draws
 * ([#413](https://github.com/Raketa02/Raketa/issues/413)).
 */

import { dayDate } from './calendarDay';
import { weekdayOf } from './platformZone';

describe('dayDate', () => {
  it('is the day of the month and a short month, with no leading zero', () => {
    expect(dayDate('2026-08-09')).toBe('9 Aug');
    expect(dayDate('2026-09-12')).toBe('12 Sep');
    expect(dayDate('2026-12-31')).toBe('31 Dec');
    expect(dayDate('2027-01-01')).toBe('1 Jan');
  });

  /**
   * A calendar day has no zone in it, so no zone is consulted: the same square `weekdayOf` reads
   * at UTC, on a phone anywhere. The last Sunday of October 2026 is the 25th — the day the clocks
   * change — and both readings are of the calendar, not of a clock.
   */
  it('agrees with the weekday about which square it is, across a clock change', () => {
    expect(weekdayOf('2026-10-25')).toBe(7);
    expect(dayDate('2026-10-25')).toBe('25 Oct');
  });

  /** The mapper would have dropped it; this is the belt rather than the braces. */
  it('prints a value it cannot read as a calendar day rather than inventing a date', () => {
    expect(dayDate('someday')).toBe('someday');
    expect(dayDate('2026-13-01')).toBe('2026-13-01');
  });
});
