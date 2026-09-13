/**
 * Your plans, as the app talks about them.
 *
 * A pass-through with a mapping, which is what ADR-0009's uniform-strict escape hatch is for:
 * there is no rule the client is entitled to apply to this list. **It is not re-sorted** — the
 * order is *newest arrangement first* and it is the server's — and it is not filtered, because
 * every row is a court the reader may plan, written or not (ADR-0164 §4).
 */

import type { Cancellable } from '../api/plansApi';
import { getPlans } from '../api/plansApi';
import type { Plan } from '../domain/slots';
import { toPlans } from '../mappers/planMappers';

export function readPlans(options: Cancellable = {}): Promise<readonly Plan[]> {
  return getPlans(options).then(toPlans);
}
