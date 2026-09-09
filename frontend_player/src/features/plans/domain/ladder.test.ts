/**
 * **The four rungs, and that they are read in order.**
 *
 * Three of the four assertions here are about *precedence* rather than about a rung's own
 * condition, because that is the whole of what the ladder is: a game whose agreed point has
 * passed is `Needs result` even with an empty plan, and a game arranged for today is `Today`
 * even with three slots filled. The conditions overlap on purpose and the order is what
 * resolves them ([`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md)
 * §3.3).
 */

import { agreedPoint, rungOf } from './ladder';
import type { Plan } from './slots';

const GAME = '11111111-0000-4000-8000-000000000001';

function plan(over: Partial<Plan> = {}): Plan {
  return { gameId: GAME, ...over };
}

/** 09:00 UTC on the 12th is the 12th in Warsaw, whatever the phone thinks. */
const READ_AT = '2026-09-12T09:00:00Z';

describe('the agreed point', () => {
  it('is the plan’s own, and is never recomputed here', () => {
    expect(agreedPoint(plan({ agreedPoint: '2026-09-12T16:00:00Z' }))).toBe('2026-09-12T16:00:00Z');
  });

  it('is nothing where no day is agreed, which is what the wire spells by omitting it', () => {
    expect(agreedPoint(plan({ place: 'Zabłocie Sport' }))).toBeUndefined();
    expect(agreedPoint(undefined)).toBeUndefined();
  });
});

describe('the four rungs, read in order', () => {
  it('is Planning where something is still to agree and no clock has run', () => {
    expect(rungOf(undefined, READ_AT)).toBe('planning');
    expect(rungOf(plan({ place: 'Zabłocie Sport' }), READ_AT)).toBe('planning');
  });

  it('is Game on once all three are filled and the day is still ahead', () => {
    const agreed = plan({
      place: 'Zabłocie Sport',
      day: '2026-09-19',
      hour: '18:00',
      agreedPoint: '2026-09-19T16:00:00Z',
    });

    expect(rungOf(agreed, READ_AT)).toBe('game-on');
  });

  /**
   * #324's second amendment dropped *Today*'s three-slot requirement: its test is *the agreed
   * day is today*, so a Today card may genuinely have no hour and no place.
   */
  it('is Today on the agreed day, whatever else is still to agree', () => {
    expect(rungOf(plan({ day: '2026-09-12' }), READ_AT)).toBe('today');
  });

  it('outranks Game on with Today, because the clock outranks the checklist', () => {
    const full = plan({
      place: 'Zabłocie Sport',
      day: '2026-09-12',
      hour: '18:00',
      agreedPoint: '2026-09-12T16:00:00Z',
    });

    expect(rungOf(full, READ_AT)).toBe('today');
  });

  it('is Needs result the moment the agreed point has passed, whatever the day says', () => {
    const played = plan({
      place: 'Zabłocie Sport',
      day: '2026-09-12',
      hour: '08:00',
      agreedPoint: '2026-09-12T06:00:00Z',
    });

    expect(rungOf(played, READ_AT)).toBe('needs-result');
  });

  /**
   * The point is the *start of the following local day* where only a day is agreed, so a game
   * with no hour is never asked for a result on the day it is being played.
   */
  it('leaves a day-only game on Today until its own point has passed', () => {
    const tonight = plan({ day: '2026-09-12', agreedPoint: '2026-09-12T22:00:00Z' });
    const yesterday = plan({ day: '2026-09-11', agreedPoint: '2026-09-11T22:00:00Z' });

    expect(rungOf(tonight, READ_AT)).toBe('today');
    expect(rungOf(yesterday, READ_AT)).toBe('needs-result');
  });

  it('reads today in the platform zone, never the device one', () => {
    const zones = ['Pacific/Kiritimati', 'Pacific/Midway', 'UTC'];
    const held = process.env.TZ;

    const read = zones.map((zone) => {
      process.env.TZ = zone;
      return rungOf(plan({ day: '2026-09-12' }), READ_AT);
    });

    process.env.TZ = held;
    expect(read).toEqual(['today', 'today', 'today']);
  });

  it('treats an instant it cannot read as one that has not passed', () => {
    expect(rungOf(plan({ day: '2026-09-19', agreedPoint: 'the day after' }), READ_AT)).toBe(
      'planning',
    );
  });
});
