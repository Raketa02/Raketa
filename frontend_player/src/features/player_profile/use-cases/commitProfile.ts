/**
 * End the part: send every answer it collected, under the key it was collected against.
 *
 * **One call, one profile.** Nothing here batches, splits or retries — the request is one
 * body by design, and whether to send it again is the step's decision and the player's.
 *
 * ## What comes back stops here, and that is deliberate
 *
 * The commit answers with the whole profile — the tags, the photo ids, the week and the area.
 * **None of it is carried out of this function.** Nothing in the app reads a Player profile
 * yet: the last step needs to know the commit landed, and the entry gate needs to know a
 * profile exists, and neither of those is a field of the response. Mapping it into a domain
 * object nobody renders would be inventing a second, stale copy of a profile the server owns
 * — the same answer `toUploadedPhotoId` gives the signed URL it drops.
 *
 * The profile screen is what will want this body, and it will want it read back through its
 * own read rather than remembered from the moment onboarding ended.
 */

import { commitPlayerProfile } from '../api/playerProfileApi';
import type { ProfileCommit } from '../domain/profileCommit';
import { toCommitRequest } from '../mappers/playerProfileMappers';

export interface CommitProfileInput {
  /** Every answer, proved complete by `readyToCommit` before it could be built. */
  readonly commit: ProfileCommit;
  /**
   * The part's own key. **The same one on a retry** — that is the whole defence, and the
   * reason it is passed in rather than made here: a use case that minted one would mint a
   * second on the second attempt.
   */
  readonly idempotencyKey: string;
}

/**
 * **No `AbortSignal`, and the absence is the decision.** Every read in this app threads
 * Query's signal so leaving a screen stops the work; this is a write, and a write cancelled
 * in flight leaves the client unable to say whether it landed — which is the one thing the
 * player must not be guessed at about. The commit outlives whatever is on screen, and the
 * idempotency key is what makes that safe.
 */
export async function commitProfile({ commit, idempotencyKey }: CommitProfileInput): Promise<void> {
  await commitPlayerProfile({ body: toCommitRequest(commit), idempotencyKey });
}
