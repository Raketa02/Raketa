/**
 * *We are playing at this time.*
 *
 * A clock face off the offered grid. **`HH:MM` is what crosses** — the route takes a `format:
 * time` and reads either spelling, and the shorter one is what the mapper hands back and what the
 * room's own line prints, so one value is spelled one way everywhere it is seen.
 */

import { putHour } from '../api/plansApi';
import type { Plan } from '../domain/slots';
import { toPlan } from '../mappers/planMappers';

export interface SetHourAsk {
  readonly gameId: string;
  /** `HH:MM`, off `HOURS_OFFERED`. */
  readonly hour: string;
}

export function setHour({ gameId, hour }: SetHourAsk): Promise<Plan> {
  return putHour(gameId, { hour }).then(toPlan);
}
