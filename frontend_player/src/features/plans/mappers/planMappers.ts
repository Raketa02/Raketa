/**
 * The wire boundary: `PlanListResponse` in, {@link Plan}s out — and **one field is respelled.**
 *
 * **`locked_at` crosses as it is**, an instant and never an adjective: the wire sends the moment
 * somebody said *we are agreed* and nothing about what the plan may still do, because a locked
 * plan is not a frozen one (ADR-0155). It is the one value here that is not a slot, and `null`
 * collapses to absent like every other, since there is no unlock for a `null` to be the record of.
 *
 * ## The hour arrives as a clock face with seconds on it, and leaves as `HH:MM`
 *
 * `PlanSchema.hour` is a `format: time`, which the server writes as `18:00:00` and the system line
 * for the same value writes as `18:00`. The chip and the line are the same fact in two places, so
 * the mapper is where they are made to agree — and it agrees with the **shorter** one, because
 * that is the spelling the offered grid uses, the spelling a chip is compared against, and the
 * spelling a player would say out loud. A second `split(':')` in a component is how a slot chip
 * and the line announcing it start disagreeing about 18:00.
 *
 * **Only the shape is checked, never the grid.** An hour off the half-hour or a day past the
 * horizon are the server's refusals, and a client that re-applied them on the way **in** would be
 * refusing to draw a value the platform accepted — the plan would read as unset while the room's
 * own line said somebody had set it.
 *
 * ## An unreadable value is dropped, and that is the opposite call to a system line's
 *
 * A `DAY_RECORDED` line whose value is not a calendar date draws
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §3's **named gap**, because
 * a line *is* the whole of the slot it is drawn in and there is nothing else to say. A **slot** is
 * not: the chip beside it is a control, and drawing the slot as unfilled puts the one remedy that
 * exists — setting it again — under the player's thumb. Neither answer invents anything; they
 * differ because one surface can act and the other cannot.
 *
 * ## `null` is *this response said nothing*, and it collapses to absent
 *
 * Every optional here arrives as `T | null | undefined` and every one becomes `undefined`, so no
 * screen has two spellings of one absence to branch on — and **a slot is never emptied**, so an
 * absent value is one that has never been filled rather than one somebody cleared.
 */

import type { components } from '@/generated/schema';

import type { Plan } from '../domain/slots';

type PlanListResponse = components['schemas']['PlanListResponse'];
type PlanSchema = components['schemas']['PlanSchema'];

/** `YYYY-MM-DD`, which is the whole of what a calendar day is allowed to look like. */
const CALENDAR_DAY = /^\d{4}-\d{2}-\d{2}$/;

/** A clock face with optional seconds, which is what a `format: time` can arrive as. */
const CLOCK_FACE = /^(\d{2}:\d{2})(?::\d{2}(?:\.\d+)?)?$/;

/** Your plans, in the order they were answered. The order is the server's and is not re-sorted. */
export function toPlans(response: PlanListResponse): readonly Plan[] {
  return response.plans.map(toPlan);
}

export function toPlan(schema: PlanSchema): Plan {
  const day = schema.day ?? undefined;
  const hour = toClockFace(schema.hour ?? undefined);

  return {
    gameId: schema.game_id,
    ...(schema.place == null ? {} : { place: schema.place }),
    ...(day !== undefined && CALENDAR_DAY.test(day) ? { day } : {}),
    ...(hour === undefined ? {} : { hour }),
    ...(schema.agreed_point == null ? {} : { agreedPoint: schema.agreed_point }),
    ...(schema.locked_at == null ? {} : { lockedAt: schema.locked_at }),
  };
}

/** `18:00:00` and `18:00` both become `18:00`; anything else is a value this build cannot read. */
function toClockFace(hour: string | undefined): string | undefined {
  const matched = hour === undefined ? null : CLOCK_FACE.exec(hour);

  return matched?.[1];
}
