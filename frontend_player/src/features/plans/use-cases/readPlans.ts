/**
 * Your plans, as the app talks about them.
 *
 * A pass-through with a mapping, which is what ADR-0009's uniform-strict escape hatch is for:
 * there is no rule the client is entitled to apply to this list. **It is not re-sorted** — the
 * order is *newest arrangement first* and it is the server's — and it is not filtered, because a
 * game with nothing agreed is already absent from it.
 */

import type { Cancellable } from '../api/plansApi';
import { getPlans } from '../api/plansApi';
import type { Plan } from '../domain/slots';
import { toPlans } from '../mappers/planMappers';

export function readPlans(options: Cancellable = {}): Promise<readonly Plan[]> {
  return getPlans(options).then(toPlans);
}
