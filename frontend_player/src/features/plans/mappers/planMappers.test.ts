/**
 * The wire boundary, and the two values it narrows.
 *
 * The hour is the interesting one: the wire writes it as a `format: time` with seconds on it and
 * the room's own line for the same value writes it as `HH:MM`, so this is where the chip and the
 * line are made to agree.
 */

import type { Wire } from '@/test-support/transport';

import { toPlan, toPlans } from './planMappers';

const CHALLENGE = '11111111-0000-4000-8000-000000000001';

/** Friday the 11th of September 2026, 09:00 in Warsaw — when the challenge was sent. */
const SENT_AT = '2026-09-11T07:00:00Z';

function schema(over: Partial<Wire['PlanSchema']> = {}): Wire['PlanSchema'] {
  return {
    challenge_id: CHALLENGE,
    anchor: SENT_AT,
    place: null,
    day: null,
    hour: null,
    agreed_point: null,
    ...over,
  };
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
      challengeId: CHALLENGE,
      anchor: SENT_AT,
      place: 'Zabłocie Sport, court 3',
      day: '2026-09-13',
      hour: '18:00',
      agreedPoint: '2026-09-13T16:00:00Z',
    });
  });

  /**
   * **Keyed by the challenge, and the anchor rides on the row** (ADR-0164 §1, §4): the one id the
   * room and the game share, and the instant the day chips run from — the send until the game
   * exists, then `planned_at` — carried rather than derived, so a room with no game can draw them.
   */
  it('is keyed by the challenge and carries the horizon anchor', () => {
    const plan = toPlan(schema({ anchor: '2026-09-12T07:00:00Z' }));

    expect(plan.challengeId).toBe(CHALLENGE);
    expect(plan.anchor).toBe('2026-09-12T07:00:00Z');
    expect(plan).not.toHaveProperty('gameId');
  });

  /** `null` is *this response said nothing*, and a slot is never emptied — so absent it is. */
  it('collapses every null to absent', () => {
    expect(toPlan(schema())).toEqual({ challengeId: CHALLENGE, anchor: SENT_AT });
    expect(toPlan(schema({ locked_at: null }))).toEqual({
      challengeId: CHALLENGE,
      anchor: SENT_AT,
    });
  });

  /** The one value on a plan that is not a slot: the moment somebody said *we are agreed*. */
  it('keeps the moment the plan was locked', () => {
    expect(toPlan(schema({ locked_at: '2026-09-12T10:00:00Z' })).lockedAt).toBe(
      '2026-09-12T10:00:00Z',
    );
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
    const plans = toPlans({ plans: [schema(), schema({ challenge_id: 'second' })] });

    expect(plans.map((plan) => plan.challengeId)).toEqual([CHALLENGE, 'second']);
  });
});
