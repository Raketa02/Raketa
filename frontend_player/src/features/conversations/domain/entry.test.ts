/**
 * The three narrowings a system line's own fields need, and the separator drawn over them.
 *
 * Each narrowing is a place a build can be **wrong** rather than merely wordless: a code, a
 * departure and a count are closed vocabularies an older phone may not know.
 *
 * **The two conversions that are about a zone are tested in `shared/date/platformZone.test.ts`**,
 * which is where they moved when the plan's day row became their third caller
 * ([#366](https://github.com/Rakieta02/Rakieta/issues/366)). What is asserted here is the rule they
 * are read by — a separator wherever the platform day changes, and nowhere else.
 */

import {
  departureOf,
  entryMoment,
  invitedCount,
  separatorBefore,
  toSystemLineCode,
  SYSTEM_LINE_CODES,
  type Entry,
} from './entry';

describe('the code', () => {
  it('reads all nine, and nothing else', () => {
    for (const code of SYSTEM_LINE_CODES) {
      expect(toSystemLineCode(code)).toBe(code);
    }

    expect(SYSTEM_LINE_CODES).toHaveLength(9);
    expect(toSystemLineCode('PLAN_LOCKED')).toBe('PLAN_LOCKED');
    // The one line a room is born with, and only a doubles room (ADR-0169 §8).
    expect(toSystemLineCode('SIDE_FORMED')).toBe('SIDE_FORMED');
    expect(toSystemLineCode('GAME_ON')).toBeUndefined();
    expect(toSystemLineCode('PLAN_UNLOCKED')).toBeUndefined();
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
