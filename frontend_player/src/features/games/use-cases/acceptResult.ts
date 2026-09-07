/**
 * *That is what happened.* **Only from across the net, and one opponent suffices.**
 *
 * The person across the net is the whole of the evidence that a score was real, which is why a
 * teammate cannot do this and why one opponent is enough.
 *
 * **It settles nothing on its own.** The grace runs from the score rather than from this tap,
 * so inside it a disagreement still wins — a partner who is quick to their phone cannot close
 * the door on an opponent who has not read the score yet. The screen therefore goes on offering
 * the disagreement underneath, and says when the agreement becomes final.
 *
 * The answer is dropped for the reason `stateResult`'s is: a standing folded against the
 * server's clock does not belong in a list folded against an older `read_at`.
 */

import { postResultAcceptance } from '../api/gamesApi';

export async function acceptResult(gameId: string): Promise<void> {
  await postResultAcceptance(gameId);
}
