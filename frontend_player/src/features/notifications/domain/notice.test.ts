/**
 * Where a notice opens (#559; the screens A9: *tapping a notice opens the game it is about — the
 * deck opens with the card on top for You complete it and Challenges*), and when it was given, as
 * the list says it.
 */

import { givenWhen, targetOf } from './notice';

const FACTS = {
  gameId: '7a1c2f0e-3b4d-4e5f-8a9b-0c1d2e3f4a5b',
  poolId: '9b8a7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d',
  sport: 'padel',
  kind: 'competitive',
} as const;

describe('where a notice opens', () => {
  it('a booked game opens its details, by the booking — which is the game’s own id', () => {
    expect(targetOf('SOMEONE_LEFT', 'BOOKING', FACTS)).toEqual({
      opens: 'booking',
      bookingId: FACTS.gameId,
    });
  });

  // The backend sends a Fill in alert as `BOOKING` — the booked game — to a reader who is not in it,
  // so its details are the ones a Seats to fill row opens: a rescue seen from outside (A4.3).
  it('a Fill in alert opens the booked game’s open seat, seen from outside, in its group', () => {
    expect(targetOf('FILL_IN_ALERT', 'BOOKING', FACTS)).toEqual({
      opens: 'rescue',
      groupId: FACTS.poolId,
      bookingId: FACTS.gameId,
    });
  });

  it('a game still filling — or one that did not fill — opens its details in its group', () => {
    expect(targetOf('POST_DID_NOT_FILL', 'PROPOSAL', FACTS)).toEqual({
      opens: 'game',
      groupId: FACTS.poolId,
      proposalId: FACTS.gameId,
      sport: 'padel',
      kind: 'competitive',
    });
  });

  it('a card waiting for you opens the group’s deck, in its sport and kind, with it on top', () => {
    expect(targetOf('CHALLENGE', 'DECK', FACTS)).toEqual({
      opens: 'deck',
      groupId: FACTS.poolId,
      proposalId: FACTS.gameId,
      sport: 'padel',
      kind: 'competitive',
    });
  });
});

describe('when a notice was given', () => {
  // 2026-10-02 18:30 in Warsaw (CEST, UTC+2).
  const NOW = '2026-10-02T16:30:00Z';

  it('today is only its clock, in the platform zone', () => {
    expect(givenWhen('2026-10-02T12:05:00Z', NOW)).toEqual({ day: 'today', clock: '14:05' });
  });

  it('yesterday is said so, with its clock', () => {
    expect(givenWhen('2026-10-01T20:00:00Z', NOW)).toEqual({ day: 'yesterday', clock: '22:00' });
  });

  it('is yesterday by the Warsaw calendar, not by the hours since', () => {
    // 23:30 in Warsaw on the 1st — nineteen hours ago, and still yesterday.
    expect(givenWhen('2026-10-01T21:30:00Z', NOW)?.day).toBe('yesterday');
    // 00:30 in Warsaw on the 2nd — sixteen hours ago, and today.
    expect(givenWhen('2026-10-01T22:30:00Z', NOW)?.day).toBe('today');
  });

  it('within the week is its weekday', () => {
    expect(givenWhen('2026-09-28T07:00:00Z', NOW)).toEqual({
      day: 'weekday',
      weekday: 1,
      clock: '09:00',
    });
  });

  it('older is its date', () => {
    expect(givenWhen('2026-09-20T07:00:00Z', NOW)).toEqual({
      day: 'date',
      date: '2026-09-20',
      clock: '09:00',
    });
  });

  it('a time it cannot read is nothing said', () => {
    expect(givenWhen('not a time', NOW)).toBeUndefined();
  });
});
