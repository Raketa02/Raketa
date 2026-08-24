/**
 * Put a changed card back where it was.
 *
 * `ADR-0074` has every action off Now return Now's update in its own response,
 * so returning from the route is a **cache write and not a fetch**. That is not a
 * saving here, it is the whole mechanism: popping back off a route is
 * deliberately none of `ADR-0054`'s four occasions and `useNow` is
 * `staleTime: Infinity` with `refetchOnMount: false`, so without this the player
 * would come back from leaving a match to a card still offering her the way out.
 *
 * **In place, and nothing else.** The card is replaced where it already sits; no
 * card is added, none is removed, and no region is reordered. That is `ADR-0032`
 * — *order is a property of the composed screen* — applied to the one moment a
 * client is holding a card the server has just recomposed: the alternative is a
 * match sliding under the player's thumb while she is looking at it.
 *
 * **The shelves are not touched at all**, and that is stated rather than left to
 * the type. An update carries one card and the update shape holds no shelf, so
 * there is nothing to apply there — but a later session reaching for *the same
 * match, wherever it appears* would be reordering a ranked list from a write,
 * which is the edit this file exists to have already refused.
 *
 * **A card the screen does not hold is not inserted.** A departure from a match
 * that is not on this sport's screen changes nothing on it, and inventing a
 * region for the card would be the client deciding a card's *place* — the one
 * judgement `ADR-0070` keeps on the server.
 *
 * **The second form removes rather than replaces**, and it is the one thing here
 * that shortens a region. `ADR-0070` requires the one-card answer to be able to
 * say *this card is no longer on your screen*, and `ADR-0087`'s write is the
 * first that can: a queue place is the whole of what put that match on the
 * strip. It is still not the client deciding a card's place — the server said
 * the card is gone, and this removes exactly the match it named, from wherever
 * it was, in the order the rest were already in.
 */

import type { ComposedScreen, MatchCard, NowUpdate } from '../domain/ComposedScreen';

export function applyNowUpdate(screen: ComposedScreen, update: NowUpdate): ComposedScreen {
  const apply =
    update.kind === 'card'
      ? (cards: readonly MatchCard[]) => replaced(cards, update.card)
      : (cards: readonly MatchCard[]) => removed(cards, update.matchId);

  return {
    ...screen,
    offers: { cards: apply(screen.offers.cards) },
    yourMatches: { cards: apply(screen.yourMatches.cards) },
  };
}

/**
 * The same list with one card swapped, or the same list.
 *
 * Identity is preserved when nothing matched, so a screen holding the match in
 * neither region is handed back unchanged and React has nothing to re-render.
 */
function replaced(cards: readonly MatchCard[], card: MatchCard): readonly MatchCard[] {
  if (!cards.some((held) => held.matchId === card.matchId)) return cards;
  return cards.map((held) => (held.matchId === card.matchId ? card : held));
}

/**
 * The same list without one match, or the same list.
 *
 * Identity is preserved on a miss for the reason above, and the surviving cards
 * keep the order they arrived in: removing one is not a licence to re-order the
 * rest, which is `ADR-0032` on the one operation that could.
 */
function removed(cards: readonly MatchCard[], matchId: string): readonly MatchCard[] {
  if (!cards.some((held) => held.matchId === matchId)) return cards;
  return cards.filter((held) => held.matchId !== matchId);
}
