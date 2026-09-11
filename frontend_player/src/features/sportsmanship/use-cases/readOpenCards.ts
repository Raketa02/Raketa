/**
 * The courts still waiting for this player's stars.
 *
 * A pass-through with a mapping, which is what ADR-0009's uniform-strict escape hatch is for:
 * **there is no rule the client is entitled to apply to this list.** The window — the day
 * after, and seven days — is the server's, and a card not yet a day old, one whose week has
 * run out and one already answered are all equally absent. A client that re-derived any of
 * that would be a second spelling of the window the `POST` is judged against, and the two
 * would disagree silently.
 */

import type { Cancellable } from '../api/sportsmanshipApi';
import { getOpenCards } from '../api/sportsmanshipApi';
import type { OpenCard } from '../domain/card';
import { toOpenCards } from '../mappers/sportsmanshipMappers';

export function readOpenCards(options: Cancellable = {}): Promise<readonly OpenCard[]> {
  return getOpenCards(options).then(toOpenCards);
}
