/**
 * *That is what happened.* **Only from across the net, and one opponent suffices.**
 *
 * The person across the net is the whole of the evidence that a score was real, which is why a
 * teammate cannot do this and why one opponent is enough.
 *
 * **It settles the result at once and closes the game** (#654; ADR-0195 §5): the six-hour grace in
 * which a disagreement could still win is retired, so in doubles the first agreement from the other
 * side is the one that counts, and no different score is taken after it.
 *
 * The answer is dropped for the reason `stateResult`'s is: a standing folded against the
 * server's clock does not belong in a list folded against an older `read_at`.
 */

import { postResultAcceptance } from '../api/gamesApi';

export async function acceptResult(gameId: string): Promise<void> {
  await postResultAcceptance(gameId);
}
