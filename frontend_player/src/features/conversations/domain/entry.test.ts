/**
 * The three narrowings a system line's own fields need, and the one that is about a clock.
 *
 * Each is a place a build can be **wrong** rather than merely wordless: a code, a departure and a
 * count are closed vocabularies an older phone may not know, and a recorded day is a value whose
 * reading must not depend on where the phone is.
 */

import { departureOf, invitedCount, toSystemLineCode, weekdayOf, SYSTEM_LINE_CODES } from './entry';

describe('the code', () => {
  it('reads all seven, and nothing else', () => {
    for (const code of SYSTEM_LINE_CODES) {
      expect(toSystemLineCode(code)).toBe(code);
    }

    expect(toSystemLineCode('GAME_ON')).toBeUndefined();
    expect(toSystemLineCode('')).toBeUndefined();
  });
});

describe('how a seat left', () => {
  /** One code, two facts. A lapse is not a decline, one layer down from §13. */
  it('keeps a decline and a lapse apart, and refuses anything else', () => {
    expect(departureOf({ departure: 'DECLINED' })).toBe('DECLINED');
    expect(departureOf({ departure: 'LAPSED' })).toBe('LAPSED');
    expect(departureOf({ departure: 'WITHDRAWN' })).toBeUndefined();
    expect(departureOf({})).toBeUndefined();
  });
});

describe('how many were asked', () => {
  it('is a whole count above zero, or nothing at all', () => {
    expect(invitedCount({ count: '2' })).toBe(2);
    expect(invitedCount({ count: '0' })).toBeUndefined();
    expect(invitedCount({ count: '1.5' })).toBeUndefined();
    expect(invitedCount({ count: 'two' })).toBeUndefined();
    expect(invitedCount({})).toBeUndefined();
  });
});

describe('which weekday a recorded day is', () => {
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
      process.env.TZ = zone;
      return weekdayOf('2026-09-12');
    });
    process.env.TZ = 'UTC';

    expect(new Set(read)).toEqual(new Set([6]));
  });

  it('answers nothing for a value that is not a calendar date', () => {
    expect(weekdayOf('Saturday')).toBeUndefined();
    expect(weekdayOf('2026-13-40')).toBeUndefined();
    expect(weekdayOf('2026-09-12T18:00:00Z')).toBeUndefined();
    expect(weekdayOf('')).toBeUndefined();
  });
});
