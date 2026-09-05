/**
 * Your games, as the app talks about them.
 *
 * A pass-through with a mapping, which is what ADR-0009's uniform-strict escape hatch is for:
 * there is no rule the client is entitled to apply to this list. **It is not re-sorted** — the
 * order is *newest arrangement first* and it is the server's, and a client that re-ordered it
 * would be inventing an opinion about which of the three moments of a game's life matters.
 */

import type { Cancellable } from '../api/gamesApi';
import { getGames } from '../api/gamesApi';
import type { Game } from '../domain/game';
import { toGames } from '../mappers/gameMappers';

export function readGames(options: Cancellable = {}): Promise<readonly Game[]> {
  return getGames(options).then(toGames);
}
