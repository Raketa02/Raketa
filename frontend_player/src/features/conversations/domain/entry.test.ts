/**
 * The three narrowings a system line's own fields need, and the one that is about a clock.
 *
 * Each is a place a build can be **wrong** rather than merely wordless: a code, a departure and a
 * count are closed vocabularies an older phone may not know, and a recorded day is a value whose
 * reading must not depend on where the phone is.
 */

import {
  departureOf,
  entryMoment,
  invitedCount,
  platformDay,
  separatorBefore,
  toSystemLineCode,
  weekdayOf,
  SYSTEM_LINE_CODES,
  type Entry,
} from './entry';

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

describe('which day an instant falls on', () => {
  /** The zone is the platform's, so the answer cannot be a fact about where the phone is. */
  it('reads the platform zone and never the device one', () => {
    const zones = ['UTC', 'Pacific/Kiritimati', 'Pacific/Midway', 'America/Los_Angeles'];
    const read = zones.map((zone) => {
      process.env.TZ = zone;
      return platformDay('2026-09-12T21:30:00Z');
    });
    process.env.TZ = 'UTC';

    expect(new Set(read)).toEqual(new Set(['2026-09-12']));
  });

  /** 23:30 UTC is already the 13th in Warsaw, which is the whole point of converting. */
  it("rolls over on the platform's own midnight", () => {
    expect(platformDay('2026-09-12T21:59:00Z')).toBe('2026-09-12');
    expect(platformDay('2026-09-12T22:01:00Z')).toBe('2026-09-13');
  });

  it('answers nothing for a value that is not an instant', () => {
    expect(platformDay('Saturday')).toBeUndefined();
    expect(platformDay('')).toBeUndefined();
  });
});

function message(seq: number, sentAt: string): Entry {
  return { kind: 'message', seq, authorId: 'a', sentAt, text: 'x', clientMessageId: 'c' };
}

function line(seq: number, occurredAt: string): Entry {
  return { kind: 'system-line', seq, code: 'SEAT_ACCEPTED', occurredAt, values: {} };
}

describe('when an entry happened', () => {
  /** One field spelled two ways on the wire, and one reading of it above the mapper. */
  it('is the same fact whichever arm it is', () => {
    expect(entryMoment(message(1, '2026-09-12T08:00:00Z'))).toBe('2026-09-12T08:00:00Z');
    expect(entryMoment(line(2, '2026-09-12T09:00:00Z'))).toBe('2026-09-12T09:00:00Z');
  });
});

describe('the day separator', () => {
  it('is drawn above the oldest entry being held', () => {
    expect(separatorBefore(message(1, '2026-09-12T08:00:00Z'), undefined)).toBe(6);
  });

  it('is drawn where the local day changes, and nowhere else', () => {
    const friday = message(1, '2026-09-11T21:00:00Z');
    const alsoSaturday = message(2, '2026-09-11T22:30:00Z');
    const saturdayLater = message(3, '2026-09-12T09:00:00Z');

    // 21:00 UTC is still Friday in Warsaw; 22:30 is already Saturday.
    expect(separatorBefore(alsoSaturday, friday)).toBe(6);
    expect(separatorBefore(saturdayLater, alsoSaturday)).toBeUndefined();
  });

  /** Nothing is invented for a moment that cannot be read — a separator is a claim about when. */
  it('draws nothing for an unreadable moment', () => {
    expect(separatorBefore(message(1, 'whenever'), undefined)).toBeUndefined();
  });
});
