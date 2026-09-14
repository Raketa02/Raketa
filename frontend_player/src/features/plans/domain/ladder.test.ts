/**
 * **The five rungs, and that they are read in order.**
 *
 * Most of the assertions here are about *precedence* rather than about a rung's own condition,
 * because that is the whole of what the ladder is: a game whose agreed point has passed is
 * `Needs result` even with an empty plan, a game arranged for today is `Today` even with three
 * slots filled, and a court with a seat open is `Needs a player` whatever the plan and the clock
 * say. The conditions overlap on purpose and the order is what resolves them
 * ([`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §3.3).
 */

import type { Game } from '@/features/games/types';
import { setDeviceZone } from '@/test-support/deviceZone';

import { agreedPoint, momentHasPassed, rungOf } from './ladder';
import type { Plan } from './slots';

const CHALLENGE = '11111111-0000-4000-8000-000000000001';

function plan(over: Partial<Plan> = {}): Plan {
  return { challengeId: CHALLENGE, anchor: '2026-09-08T09:00:00Z', ...over };
}

/** 09:00 UTC on the 12th is the 12th in Warsaw, whatever the phone thinks. */
const READ_AT = '2026-09-12T09:00:00Z';

/** A full court, read at that instant — the court every clock rung below is read on. */
const FULL: Pick<Game, 'readAt' | 'seats'> = {
  readAt: READ_AT,
  seats: [
    { side: 'A', playerId: 'me', nickname: 'me_' },
    { side: 'B', playerId: 'them', nickname: 'tomek.p' },
  ],
};

/** The same court after the opponent left: their seat open, nobody in it. */
const SHORT: Pick<Game, 'readAt' | 'seats'> = {
  readAt: READ_AT,
  seats: [{ side: 'A', playerId: 'me', nickname: 'me_' }, { side: 'B' }],
};

describe('the agreed point', () => {
  it('is the plan’s own, and is never recomputed here', () => {
    expect(agreedPoint(plan({ agreedPoint: '2026-09-12T16:00:00Z' }))).toBe('2026-09-12T16:00:00Z');
  });

  it('is nothing where no day is agreed, which is what the wire spells by omitting it', () => {
    expect(agreedPoint(plan({ place: 'Zabłocie Sport' }))).toBeUndefined();
    expect(agreedPoint(undefined)).toBeUndefined();
  });
});

describe('the four clock rungs, read in order', () => {
  it('is Planning where something is still to agree and no clock has run', () => {
    expect(rungOf(undefined, FULL)).toBe('planning');
    expect(rungOf(plan({ place: 'Zabłocie Sport' }), FULL)).toBe('planning');
  });

  it('is Game on once all three are filled and the day is still ahead', () => {
    const agreed = plan({
      place: 'Zabłocie Sport',
      day: '2026-09-19',
      hour: '18:00',
      agreedPoint: '2026-09-19T16:00:00Z',
    });

    expect(rungOf(agreed, FULL)).toBe('game-on');
  });

  /**
   * #324's second amendment dropped *Today*'s three-slot requirement: its test is *the agreed
   * day is today*, so a Today card may genuinely have no hour and no place.
   */
  it('is Today on the agreed day, whatever else is still to agree', () => {
    expect(rungOf(plan({ day: '2026-09-12' }), FULL)).toBe('today');
  });

  it('outranks Game on with Today, because the clock outranks the checklist', () => {
    const full = plan({
      place: 'Zabłocie Sport',
      day: '2026-09-12',
      hour: '18:00',
      agreedPoint: '2026-09-12T16:00:00Z',
    });

    expect(rungOf(full, FULL)).toBe('today');
  });

  it('is Needs result the moment the agreed point has passed, whatever the day says', () => {
    const played = plan({
      place: 'Zabłocie Sport',
      day: '2026-09-12',
      hour: '08:00',
      agreedPoint: '2026-09-12T06:00:00Z',
    });

    expect(rungOf(played, FULL)).toBe('needs-result');
  });

  /**
   * The point is the *start of the following local day* where only a day is agreed, so a game
   * with no hour is never asked for a result on the day it is being played.
   */
  it('leaves a day-only game on Today until its own point has passed', () => {
    const tonight = plan({ day: '2026-09-12', agreedPoint: '2026-09-12T22:00:00Z' });
    const yesterday = plan({ day: '2026-09-11', agreedPoint: '2026-09-11T22:00:00Z' });

    expect(rungOf(tonight, FULL)).toBe('today');
    expect(rungOf(yesterday, FULL)).toBe('needs-result');
  });

  it('reads today in the platform zone, never the device one', () => {
    const zones = ['Pacific/Kiritimati', 'Pacific/Midway', 'UTC'];
    const held = process.env.TZ;

    const read = zones.map((zone) => {
      setDeviceZone(zone);
      return rungOf(plan({ day: '2026-09-12' }), FULL);
    });

    setDeviceZone(held);
    expect(read).toEqual(['today', 'today', 'today']);
  });

  it('treats an instant it cannot read as one that has not passed', () => {
    expect(rungOf(plan({ day: '2026-09-19', agreedPoint: 'the day after' }), FULL)).toBe(
      'planning',
    );
  });
});

/**
 * **The fifth rung, and it is above the clock** (#411 rule 5, ADR-0162). A seat somebody left is
 * a fact about the court and not about the plan, and the game cannot be played — or recorded —
 * until somebody is in it; so it outranks every rung the plan and the clock would otherwise
 * name, the passed agreement included.
 */
describe('the open seat, above the clock', () => {
  it('is Needs a player whatever the plan says', () => {
    expect(rungOf(undefined, SHORT)).toBe('needs-a-player');
    expect(rungOf(plan({ place: 'Zabłocie Sport', day: '2026-09-19', hour: '18:00' }), SHORT)).toBe(
      'needs-a-player',
    );
  });

  it('is Needs a player on the agreed day, and once the agreed point has passed', () => {
    expect(rungOf(plan({ day: '2026-09-12' }), SHORT)).toBe('needs-a-player');
    expect(rungOf(plan({ agreedPoint: '2026-09-11T18:00:00Z' }), SHORT)).toBe('needs-a-player');
  });
});

/**
 * The first clock rung's own test, exported for the one control that is drawn only while the
 * agreed moment is ahead — and read against the games list's instant, never the phone's.
 */
describe('whether the agreed moment has passed', () => {
  it('has, once the agreed point is behind the instant the list was read at', () => {
    expect(momentHasPassed(plan({ agreedPoint: '2026-09-11T18:00:00Z' }), READ_AT)).toBe(true);
    expect(momentHasPassed(plan({ agreedPoint: READ_AT }), READ_AT)).toBe(true);
  });

  it('has not while the point is ahead, where no day is agreed, and where it cannot be read', () => {
    expect(momentHasPassed(plan({ agreedPoint: '2026-09-19T16:00:00Z' }), READ_AT)).toBe(false);
    expect(momentHasPassed(undefined, READ_AT)).toBe(false);
    expect(momentHasPassed(plan({ agreedPoint: 'the day after' }), READ_AT)).toBe(false);
  });
});
