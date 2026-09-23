/**
 * **One challenge, richly** — the read the screen that answers it is drawn from.
 *
 * `undefined` where the sport is a code this build cannot name, which is the mapper's rule and
 * not this file's: the screen draws its *no challenge of yours has this address* answer, which is
 * the honest thing to say about a record it cannot describe and is already the `404`'s.
 *
 * The **rules** it is read against are `domain/challengeDetail.ts`'s. This is only the fetch,
 * which is the whole of what a use-case owes when the domain owns the question.
 */

import { getChallenge, type Cancellable } from '../api/challengesApi';
import type { ChallengeDetail } from '../domain/challengeDetail';
import { toChallengeDetail } from '../mappers/challengeDetailMappers';

export async function readChallenge(
  challengeId: string,
  { signal }: Cancellable = {},
): Promise<ChallengeDetail | undefined> {
  return toChallengeDetail(await getChallenge(challengeId, { signal }));
}
