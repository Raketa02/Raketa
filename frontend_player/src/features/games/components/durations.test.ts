/**
 * How long is left, measured **from `read_at` and never from this phone's clock**.
 *
 * The list carries the instant every standing on it was folded against precisely so the
 * countdown and the standing beside it cannot come from two readings of the clock. A duration
 * taken from `Date.now()` would drift out of agreement with the word printed next to it, which
 * is the one failure the field exists to prevent.
 *
 * It **floors** rather than rounds, because a deadline is a promise: 23 h 50 m left reads as
 * *23 hours*, where rounding would say 24 and be wrong in the direction that costs somebody
 * their turn.
 */

import { durationLeft, durationSince } from './durations';

const READ_AT = '2026-09-05T09:00:00Z';

describe('the duration a screen prints', () => {
  it('counts hours up to two days, so a day and a half is not rounded into “a day”', () => {
    expect(durationLeft('2026-09-06T08:00:00Z', READ_AT)).toBe('23 hours');
    expect(durationLeft('2026-09-07T08:00:00Z', READ_AT)).toBe('47 hours');
  });

  it('counts days beyond that', () => {
    expect(durationLeft('2026-09-07T09:00:00Z', READ_AT)).toBe('2 days');
    expect(durationLeft('2026-09-12T09:00:00Z', READ_AT)).toBe('7 days');
  });

  it('counts minutes under an hour', () => {
    expect(durationLeft('2026-09-05T09:45:00Z', READ_AT)).toBe('45 minutes');
  });

  it('takes the singular through the app’s one pluralisation seam', () => {
    expect(durationLeft('2026-09-05T10:00:00Z', READ_AT)).toBe('1 hour');
    expect(durationLeft('2026-09-05T09:01:30Z', READ_AT)).toBe('1 minute');
  });

  it('floors, because a deadline stated long is a turn somebody loses', () => {
    expect(durationLeft('2026-09-06T08:50:00Z', READ_AT)).toBe('23 hours');
  });

  /**
   * A deadline at or behind `read_at` cannot happen on a standing that says the window is
   * open — the two were folded together — but a list can be a minute old on screen, and *0
   * hours* would be the sentence that made a player think they had missed it.
   */
  it('says less than a minute rather than nought of anything', () => {
    expect(durationLeft(READ_AT, READ_AT)).toBe('less than a minute');
    expect(durationLeft('2026-09-05T08:00:00Z', READ_AT)).toBe('less than a minute');
  });
});

describe('the duration something happened ago', () => {
  it('is the same ladder read the other way', () => {
    expect(durationSince('2026-09-01T09:00:00Z', READ_AT)).toBe('4 days');
    expect(durationSince('2026-09-04T20:00:00Z', READ_AT)).toBe('13 hours');
  });
});
