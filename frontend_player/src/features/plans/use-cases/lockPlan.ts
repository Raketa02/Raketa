/**
 * *We are agreed.*
 *
 * A pass-through with a mapping, and honestly so: the one rule there is — all three slots must be
 * set — is the server's guard, re-applied here only as the control's greyed state
 * (`domain/lock.ts`), because *the button is UX and the server is the correctness mechanism*. A
 * client that refused the request itself would be a second guard that could disagree with the
 * first about what a filled slot is.
 *
 * **It carries no value**, which is what makes it the one plan write with nothing to tidy.
 */

import { putLock } from '../api/plansApi';
import type { Plan } from '../domain/slots';
import { toPlan } from '../mappers/planMappers';

export interface LockPlanAsk {
  readonly gameId: string;
}

export function lockPlan({ gameId }: LockPlanAsk): Promise<Plan> {
  return putLock(gameId).then(toPlan);
}
