/**
 * *We are agreed.*
 *
 * A pass-through with a mapping, and honestly so: the two rules there are — the court must be
 * whole, and all three slots must be set — are the server's guards, re-applied here only as the
 * control's absent and greyed states (`domain/lock.ts`), because *the button is UX and the server
 * is the correctness mechanism*. A client that refused the request itself would be a second guard
 * that could disagree with the first about what a filled slot, or a whole court, is.
 *
 * **It carries no value**, which is what makes it the one plan write with nothing to tidy.
 */

import { putLock } from '../api/plansApi';
import type { Plan } from '../domain/slots';
import { toPlan } from '../mappers/planMappers';

export interface LockPlanAsk {
  readonly challengeId: string;
}

export function lockPlan({ challengeId }: LockPlanAsk): Promise<Plan> {
  return putLock(challengeId).then(toPlan);
}
