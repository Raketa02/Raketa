/**
 * *We are playing on this day.*
 *
 * A local day in the platform's one zone, chosen from the row the horizon clamps. The clamp is
 * re-applied server-side — `the_day_is_past_the_horizon` — which is what makes the row a
 * convention rather than a promise this client is keeping on its own.
 */

import { putDay } from '../api/plansApi';
import type { Plan } from '../domain/slots';
import { toPlan } from '../mappers/planMappers';

export interface SetDayAsk {
  readonly gameId: string;
  /** `YYYY-MM-DD`, off `offeredDays`. */
  readonly day: string;
}

export function setDay({ gameId, day }: SetDayAsk): Promise<Plan> {
  return putDay(gameId, { day }).then(toPlan);
}
