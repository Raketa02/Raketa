/**
 * The wire boundary: `OpenCardsResponse` in, {@link OpenCard}s out, and an answer back.
 *
 * **There is nothing here to degrade.** Every other mapper in this app has a rule for a code
 * an old build cannot read — a standing, a side, a `Term` — because those files carry closed
 * vocabularies. A card carries two ids and a list of ids and no vocabulary at all, so there is
 * no unreadable value it can arrive with, no clause to drop and nothing to refuse whole. The
 * one thing that can make a card undrawable is the **game** behind it going missing, and that
 * is `domain/card.ts`'s join rather than this file's.
 *
 * **The order is the server's and nothing re-sorts it** — soonest to expire first, which is
 * the one thing about the list a client could not compute: expiry runs from the game, and the
 * game's own list is ordered newest arrangement first.
 */

import type { components } from '@/generated/schema';

import type { OpenCard } from '../domain/card';
import type { StarsGiven } from '../domain/stars';

type AnswerTheCardRequest = components['schemas']['AnswerTheCardRequest'];
type OpenCardsResponse = components['schemas']['OpenCardsResponse'];

/** The cards waiting for this player's stars, in the order they were served. */
export function toOpenCards(response: OpenCardsResponse): readonly OpenCard[] {
  return response.cards.map((card) => ({ gameId: card.game_id, players: [...card.players] }));
}

/**
 * One card, answered.
 *
 * **`ratings` is always present, empty included.** The field is optional on the wire and an
 * empty list is an *answer* — it closes the card without rating anybody — so omitting it would
 * spell the same act two ways and leave the server to decide they were one.
 */
export function toAnswerTheCardRequest(given: readonly StarsGiven[]): AnswerTheCardRequest {
  return { ratings: given.map((one) => ({ player_id: one.playerId, stars: one.stars })) };
}
