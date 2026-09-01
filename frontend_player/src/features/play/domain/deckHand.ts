/**
 * What the deck is showing, and — when it is showing nobody — **which of the two empty states
 * is the true one**.
 *
 * ## The card in front of you is derived, never held
 *
 * `playSession` refuses the deck's current card by name: *"which card is showing is derived
 * from the dealt list minus the one leaving — never held here"*
 * ([#264](https://github.com/Raketa02/Raketa/issues/264)). So this takes the deal and the ids
 * already answered and returns the top of what is left. A stored index is a second answer to
 * *where am I in this deal*, free to disagree with the list the moment a deal is replaced.
 *
 * ## A spent deal is not an empty pool, and conflating them is the bug this type prevents
 *
 * *"The screen runs out of cards long before the pool does, and only a fresh deal that comes
 * back empty is the empty state"*
 * ([`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §7). Ten
 * cards answered is `spent`, which is a **request** — deal again, new `search_id` — and the
 * player never sees it. Only a deal that arrived with nothing is an ending.
 *
 * ## And the ending has two readings, split on one number
 *
 * `players_in_range` is post-gate and is the whole of the difference:
 *
 * - **more than nobody** — you have seen everybody the deck can deal you, and what you have to
 *   show for it is your own outgoing yeses;
 * - **nobody at all** — there is no one inside your radius this week, and the deck is the one
 *   Play surface where *widen in You* survives as advice, because the relaxation ladder is the
 *   pool's and a deal is offered no rungs.
 *
 * Split any other way — on the deal being empty alone — the advice is *widen your radius* to a
 * player who has simply answered everybody, which is the product telling them to look further
 * away from people it has already found for them.
 *
 * **The advice itself is still gated**, and that gate is `radius_clamp`'s rather than this
 * rule's: a player already at the ceiling of their own slider must never be told to widen, and
 * whether they are is a fact about the answer (`domain/candidate`) rather than about the hand.
 *
 * ## And a card carries no *how many left*
 *
 * The prototype's head drew `{n} left`, and a deal is at most ten cards out of a pool the
 * player never sees the size of — so a count there is a progress bar over an arbitrary batch.
 * *A spent deal deals again*, which makes the number wrong the moment it would matter.
 */

import type { Candidate, PoolDescription } from './candidate';

/** One deal, as the deck holds it: the rows, and the pool they were drawn from. */
export interface DeckDeal {
  readonly candidates: readonly Candidate[];
  readonly pool: PoolDescription;
}

/**
 * What the deck draws right now.
 *
 * Four arms and not `Candidate | undefined`, because the three ways of having no card are
 * three different screens: one is a request to the server, and the other two give opposite
 * advice.
 */
export type DeckStanding =
  /** One person, yes or no — and the deck deliberately says nothing about how many follow. */
  | { readonly kind: 'card'; readonly candidate: Candidate }
  /** Every card in this deal has been answered. Deal again — the player sees nothing. */
  | { readonly kind: 'spent' }
  /** A fresh deal came back with nothing, and there are people in range. */
  | { readonly kind: 'seen-everybody' }
  /** A fresh deal came back with nothing, and nobody is in range at all. */
  | { readonly kind: 'nobody-in-range' };

export function deckStanding(deal: DeckDeal, answered: readonly string[]): DeckStanding {
  const left = deal.candidates.filter((candidate) => !answered.includes(candidate.playerId));
  const [showing] = left;

  if (showing !== undefined) return { kind: 'card', candidate: showing };

  // Answered out, rather than dealt nothing. The two are the same empty list and completely
  // different facts, and only the deal's own length can tell them apart.
  if (deal.candidates.length > 0) return { kind: 'spent' };

  return deal.pool.playersInRange > 0 ? { kind: 'seen-everybody' } : { kind: 'nobody-in-range' };
}
