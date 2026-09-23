/**
 * The one rule under the cold-start refresh: **a return from the background reads the phone
 * again only after a day**, never on a plain foreground (ADR-0174 §6).
 */

import { FOREGROUND_REFRESH_FLOOR_MS, foregroundRefreshDue } from './locationRefresh';

const HOUR = 60 * 60 * 1000;
const READ_AT = Date.UTC(2026, 8, 16, 9, 0, 0);

describe('whether a foreground is old enough to read the phone again', () => {
  it('is a day, and the floor says so in one place', () => {
    expect(FOREGROUND_REFRESH_FLOOR_MS).toBe(24 * HOUR);
  });

  it('is not due on a plain foreground, or on one inside the day', () => {
    expect(foregroundRefreshDue(READ_AT, READ_AT)).toBe(false);
    expect(foregroundRefreshDue(READ_AT, READ_AT + 5 * 60 * 1000)).toBe(false);
    expect(foregroundRefreshDue(READ_AT, READ_AT + 23 * HOUR)).toBe(false);
  });

  /** The floor is a floor: exactly a day is still inside it, and a moment more is not. */
  it('is due once more than a day has passed', () => {
    expect(foregroundRefreshDue(READ_AT, READ_AT + 24 * HOUR)).toBe(false);
    expect(foregroundRefreshDue(READ_AT, READ_AT + 24 * HOUR + 1)).toBe(true);
    expect(foregroundRefreshDue(READ_AT, READ_AT + 25 * HOUR)).toBe(true);
    expect(foregroundRefreshDue(READ_AT, READ_AT + 48 * HOUR)).toBe(true);
  });
});
