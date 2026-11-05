/**
 * **Deal a group now** — a pass-through to `POST /pools/{id}/deal`, honestly: the route runs the
 * card-builder the jobs run, and nothing is decided on the way out (ADR-0201 §5). The
 * uniform-strict escape hatch, not an invariant invented to fill the folder. The pool is filed
 * under the group's id, as the deck's is.
 */

import { postDeal } from '../api/proposalsApi';

export function dealTheGroupNow(groupId: string): Promise<void> {
  return postDeal(groupId);
}
