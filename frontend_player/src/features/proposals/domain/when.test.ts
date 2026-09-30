/**
 * The game's day as the court block names it, and the deck's fortnight — both on the platform's
 * calendar, against the instant the deck was read.
 */

import { setDeviceZone } from '@/test-support/deviceZone';

import { fortnightOf, gameDayOf, gameEndsAt, weekdayAt } from './when';

const DEVICE_ZONE = process.env.TZ;

afterEach(() => {
  setDeviceZone(DEVICE_ZONE);
});

/** Wednesday 30 September 2026, 10:00 in Warsaw. */
const READ_AT = Date.parse('2026-09-30T08:00:00Z');

describe('the game’s day', () => {
  it('is today and tomorrow on the platform’s calendar', () => {
    expect(gameDayOf('2026-09-30T17:00:00Z', READ_AT)).toEqual({ kind: 'today' });
    expect(gameDayOf('2026-10-01T17:00:00Z', READ_AT)).toEqual({ kind: 'tomorrow' });
  });

  it('is the weekday within the week ahead', () => {
    expect(gameDayOf('2026-10-03T14:00:00Z', READ_AT)).toEqual({ kind: 'weekday', weekday: 6 });
    expect(gameDayOf('2026-10-06T17:00:00Z', READ_AT)).toEqual({ kind: 'weekday', weekday: 2 });
  });

  it('carries the date from a week ahead, where the weekday alone names two days', () => {
    expect(gameDayOf('2026-10-07T17:00:00Z', READ_AT)).toEqual({
      kind: 'dated',
      weekday: 3,
      day: '2026-10-07',
    });
  });

  it('turns over at Warsaw’s midnight, whatever the device says', () => {
    setDeviceZone('America/Los_Angeles');
    // 22:30 UTC on the 30th is 00:30 on the 1st in Warsaw.
    expect(gameDayOf('2026-09-30T22:30:00Z', READ_AT)).toEqual({ kind: 'tomorrow' });
  });

  it('names no day for a value that is not an instant', () => {
    expect(gameDayOf('Saturday', READ_AT)).toBeUndefined();
  });
});

describe('the deck’s fortnight', () => {
  it('is this week’s Monday and the next', () => {
    expect(fortnightOf(READ_AT)).toEqual({ thisMonday: '2026-09-28', nextMonday: '2026-10-05' });
  });

  it('counts a Sunday as the end of its week', () => {
    expect(fortnightOf(Date.parse('2026-10-04T12:00:00Z'))).toEqual({
      thisMonday: '2026-09-28',
      nextMonday: '2026-10-05',
    });
  });
});

describe('the hour a game is', () => {
  it('ends an hour after it starts', () => {
    expect(gameEndsAt('2026-10-03T14:00:00Z')).toBe('2026-10-03T15:00:00.000Z');
    expect(gameEndsAt('Saturday')).toBeUndefined();
  });

  it('reads the weekday of an instant on the platform’s calendar', () => {
    expect(weekdayAt(READ_AT)).toBe(3);
    expect(weekdayAt('2026-10-03T14:00:00Z')).toBe(6);
  });
});
