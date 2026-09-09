/**
 * The wire boundary, and the two values it narrows.
 *
 * The hour is the interesting one: the wire writes it as a `format: time` with seconds on it and
 * the room's own line for the same value writes it as `HH:MM`, so this is where the chip and the
 * line are made to agree.
 */

import type { Wire } from '@/test-support/transport';

import { toPlan, toPlans } from './planMappers';

const GAME = '11111111-0000-4000-8000-000000000001';

function schema(over: Partial<Wire['PlanSchema']> = {}): Wire['PlanSchema'] {
  return { game_id: GAME, place: null, day: null, hour: null, agreed_point: null, ...over };
}

describe('a plan', () => {
  it('keeps the three slots and the moment they name', () => {
    const plan = toPlan(
      schema({
        place: 'Zabłocie Sport, court 3',
        day: '2026-09-13',
        hour: '18:00:00',
        agreed_point: '2026-09-13T16:00:00Z',
      }),
    );

    expect(plan).toEqual({
      gameId: GAME,
      place: 'Zabłocie Sport, court 3',
      day: '2026-09-13',
      hour: '18:00',
      agreedPoint: '2026-09-13T16:00:00Z',
    });
  });

  /** `null` is *this response said nothing*, and a slot is never emptied — so absent it is. */
  it('collapses every null to absent', () => {
    expect(toPlan(schema())).toEqual({ gameId: GAME });
  });

  /** The wire may or may not carry seconds; the offered grid and the room's line never do. */
  it('spells the hour the way the grid and the system line spell it', () => {
    expect(toPlan(schema({ hour: '18:00' })).hour).toBe('18:00');
    expect(toPlan(schema({ hour: '06:30:00' })).hour).toBe('06:30');
  });

  /**
   * Only the **shape** is checked. An hour off the half-hour is the server's refusal, and a client
   * that refused it on the way in would draw a slot as unset while the room's own line said
   * somebody had set it.
   */
  it('keeps a well-formed value the offered grid does not hold', () => {
    expect(toPlan(schema({ hour: '18:15:00' })).hour).toBe('18:15');
  });

  it('drops a value it cannot read at all, leaving the slot to be set again', () => {
    expect(toPlan(schema({ day: 'Saturday' })).day).toBeUndefined();
    expect(toPlan(schema({ hour: 'sixish' })).hour).toBeUndefined();
  });
});

describe('the list', () => {
  it('is kept in the order it was answered', () => {
    const plans = toPlans({ plans: [schema(), schema({ game_id: 'second' })] });

    expect(plans.map((plan) => plan.gameId)).toEqual([GAME, 'second']);
  });
});
