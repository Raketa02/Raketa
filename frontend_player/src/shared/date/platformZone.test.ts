/**
 * The conversions that turn an instant or a calendar square into the platform’s own day and clock.
 *
 * Each is a place a build can be **wrong** rather than merely wordless, and every one of them is
 * wrong in the same way: by consulting the device. So the device's zone is moved about here on
 * purpose, and **restored in `afterEach` rather than at the end of the test that moves it** —
 * a failing expectation would otherwise leak a zone into every suite after it, and the ones it
 * would break are the ones about days.
 */

import { setDeviceZone } from '@/test-support/deviceZone';

import { daysAfter, daysBetween, platformClock, platformDay, weekdayOf } from './platformZone';

const DEVICE_ZONE = process.env.TZ;

afterEach(() => {
  setDeviceZone(DEVICE_ZONE);
});

describe('which weekday a calendar day is', () => {
  it('reads a calendar date, Monday-first', () => {
    expect(weekdayOf('2026-09-07')).toBe(1);
    expect(weekdayOf('2026-09-12')).toBe(6);
    expect(weekdayOf('2026-09-13')).toBe(7);
  });

  /**
   * The value has no time in it, so which day it names cannot depend on the phone. Read as an
   * instant in a negative offset it would come back a day early, which is one room reading two
   * different days on two phones.
   */
  it('does not move with the device zone', () => {
    const zones = ['UTC', 'Pacific/Kiritimati', 'Pacific/Midway', 'Europe/Warsaw'];
    const read = zones.map((zone) => {
      setDeviceZone(zone);
      return weekdayOf('2026-09-12');
    });

    expect(new Set(read)).toEqual(new Set([6]));
  });

  it('answers nothing for a value that is not a calendar date', () => {
    expect(weekdayOf('Saturday')).toBeUndefined();
    expect(weekdayOf('2026-13-40')).toBeUndefined();
    expect(weekdayOf('2026-09-12T18:00:00Z')).toBeUndefined();
    expect(weekdayOf('')).toBeUndefined();
  });
});

describe('which day an instant falls on', () => {
  /** The zone is the platform's, so the answer cannot be a fact about where the phone is. */
  it('reads the platform zone and never the device one', () => {
    const zones = ['UTC', 'Pacific/Kiritimati', 'Pacific/Midway', 'America/Los_Angeles'];
    const read = zones.map((zone) => {
      setDeviceZone(zone);
      return platformDay('2026-09-12T21:30:00Z');
    });

    expect(new Set(read)).toEqual(new Set(['2026-09-12']));
  });

  /** 22:00 UTC is already the 13th in Warsaw, which is the whole point of converting. */
  it("rolls over on the platform's own midnight, in summer", () => {
    expect(platformDay('2026-09-12T21:59:00Z')).toBe('2026-09-12');
    expect(platformDay('2026-09-12T22:01:00Z')).toBe('2026-09-13');
  });

  /** CET, so midnight in Warsaw is 23:00 UTC — one hour earlier than it is in September. */
  it('rolls over an hour earlier in winter', () => {
    expect(platformDay('2026-01-12T22:59:00Z')).toBe('2026-01-12');
    expect(platformDay('2026-01-12T23:01:00Z')).toBe('2026-01-13');
  });

  /**
   * The EU's own rule, and the one thing about this arithmetic that is not a constant: summer
   * time runs from 01:00 UTC on the last Sunday in March to 01:00 UTC on the last Sunday in
   * October. 2026 puts those on the 29th and the 25th.
   */
  it('changes over on the last Sunday of March and of October, at 01:00 UTC', () => {
    // A minute before the spring change it is still CET, so 00:59 UTC is 01:59 and the same day.
    expect(platformDay('2026-03-29T00:59:00Z')).toBe('2026-03-29');
    expect(platformDay('2026-03-28T23:30:00Z')).toBe('2026-03-29');
    // A minute after it is CEST, so 22:30 UTC has already become the next day.
    expect(platformDay('2026-03-29T22:30:00Z')).toBe('2026-03-30');

    // And back: 22:30 UTC on the day of the autumn change is still the same day under CET.
    expect(platformDay('2026-10-25T22:30:00Z')).toBe('2026-10-25');
    expect(platformDay('2026-10-24T22:30:00Z')).toBe('2026-10-25');
  });

  /** Every year the app will run in, so a leap year or a five-Sunday March cannot move it. */
  it('finds the last Sunday of the month in every year it is asked about', () => {
    for (let year = 2024; year <= 2035; year += 1) {
      // The last instant of CET and the first of CEST, an hour apart across the change.
      expect(platformDay(`${year}-06-15T21:30:00Z`)).toBe(`${year}-06-15`);
      expect(platformDay(`${year}-06-15T22:30:00Z`)).toBe(`${year}-06-16`);
      expect(platformDay(`${year}-12-15T22:30:00Z`)).toBe(`${year}-12-15`);
      expect(platformDay(`${year}-12-15T23:30:00Z`)).toBe(`${year}-12-16`);
    }
  });

  it('answers nothing for a value that is not an instant', () => {
    expect(platformDay('Saturday')).toBeUndefined();
    expect(platformDay('')).toBeUndefined();
  });
});

describe('a day and a number of days after it', () => {
  it('walks the calendar, over a month end and over a year end', () => {
    expect(daysAfter('2026-09-12', 0)).toBe('2026-09-12');
    expect(daysAfter('2026-09-12', 6)).toBe('2026-09-18');
    expect(daysAfter('2026-09-28', 6)).toBe('2026-10-04');
    expect(daysAfter('2026-12-29', 6)).toBe('2027-01-04');
  });

  /** A leap day is a day like any other, and it is where a naive month walk goes wrong. */
  it('crosses a leap day', () => {
    expect(daysAfter('2028-02-27', 3)).toBe('2028-03-01');
  });

  /**
   * The arithmetic is on the calendar and never on a clock, so the two days a year Warsaw's day
   * is 23 or 25 hours long cannot move it — which is what a local-instant `+ 24h` would do.
   */
  it('does not move with the device zone or with a clock change', () => {
    const zones = ['UTC', 'Pacific/Kiritimati', 'Pacific/Midway', 'America/Los_Angeles'];
    const read = zones.map((zone) => {
      setDeviceZone(zone);
      return daysAfter('2026-03-28', 2);
    });

    expect(new Set(read)).toEqual(new Set(['2026-03-30']));
    expect(daysAfter('2026-10-24', 2)).toBe('2026-10-26');
  });

  it('answers nothing for a value that is not a calendar date', () => {
    expect(daysAfter('2026-09-12T00:00:00Z', 1)).toBeUndefined();
    expect(daysAfter('', 1)).toBeUndefined();
  });
});

describe('the wall clock an instant reads in the platform zone', () => {
  it('is the hour and minute in Warsaw, whatever the device says', () => {
    setDeviceZone('America/Los_Angeles');

    // 17:00 UTC in summer is 19:00 in Warsaw; in winter 18:00.
    expect(platformClock('2026-09-29T17:00:00Z')).toBe('19:00');
    expect(platformClock('2026-12-01T17:05:00Z')).toBe('18:05');
  });

  it('answers nothing for a value that is not an instant', () => {
    expect(platformClock('19:00')).toBeUndefined();
  });
});

describe('how many days apart two calendar days are', () => {
  it('counts forward and back over a month end, on the calendar', () => {
    expect(daysBetween('2026-09-30', '2026-09-30')).toBe(0);
    expect(daysBetween('2026-09-30', '2026-10-01')).toBe(1);
    expect(daysBetween('2026-09-30', '2026-10-07')).toBe(7);
    expect(daysBetween('2026-10-01', '2026-09-30')).toBe(-1);
  });

  it('is not moved by the clock change', () => {
    expect(daysBetween('2026-10-24', '2026-10-26')).toBe(2);
  });

  it('answers nothing for a value that is not a calendar date', () => {
    expect(daysBetween('2026-09-30', 'tomorrow')).toBeUndefined();
  });
});
