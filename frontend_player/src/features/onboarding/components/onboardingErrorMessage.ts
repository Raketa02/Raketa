/**
 * A failure, as a sentence a player can act on.
 *
 * **The sentences are `shared/errors`' now.** This file held the second copy of the
 * recovery table and recorded the rule that a third copy is the signal to move it; the
 * Player profile was the third. What is left here is this feature's *place* for the `code`
 * table above that fallback — the codes that need their own copy arrive with the question
 * loop (#24), where a duplicate submission and a stale question are two conflicts with
 * opposite recoveries, and they belong beside the feature they are about rather than in
 * `shared/`.
 */

import { recoveryMessage, type AppError } from '@/shared/errors';

export function onboardingErrorMessage(error: AppError): string {
  return recoveryMessage(error);
}
