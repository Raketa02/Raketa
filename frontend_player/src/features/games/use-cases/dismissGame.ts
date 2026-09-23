/**
 * *Remove this card.* **The reader's own act, and it removes a card rather than a fact**
 * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §5).
 *
 * A called-off game's card carries nothing the challenge row does not, and it is the one ending
 * a player wants gone; the dismissal is recorded on the game so the card is gone on their other
 * phone and after a reinstall, and the rail is derived on every read. The game, its record, the
 * row and the screen behind it are untouched, and nobody else's rail moves — which is why there
 * is no sheet in front of it.
 *
 * The route answers nothing, and nothing is folded here: what should be gone is the card, and
 * the rail's own read is what says so.
 */

import { postDismissal } from '../api/gamesApi';

export async function dismissGame(gameId: string): Promise<void> {
  await postDismissal(gameId);
}
