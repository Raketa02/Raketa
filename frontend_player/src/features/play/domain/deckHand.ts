/**
 * What the deck is showing, what stands behind it, how many are left — and, when it is showing
 * nobody, **which of the two empty states is the true one**.
 *
 * ## The card in front of you is derived, never held
 *
 * `playSession` refuses the deck's current card by name: *"which card is showing is derived
 * from the dealt list minus the one leaving — never held here"*
 * ([#264](https://github.com/Raketa02/Raketa/issues/264)). So this takes the deal and the ids
 * already answered and returns the top of what is left. A stored index is a second answer to
 * *where am I in this deal*, free to disagree with the list the moment a deal is replaced.
 *
 * ## A deal is hands, and every card remembers its own
 *
 * The deal stays ten cards under one `search_id`, and the client asks for the next hand when
 * two remain and **appends** it, so the cards behind are real people and the join is invisible
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §5). A yes or a pass cites the deal the card came off — *"a yes with no origin is refused
 * rather than recorded with a null link"* — so a card from the first hand answered after the
 * second was appended has to cite the first. Hence `DealtCard`: the person and their origin key,
 * held together, rather than one `searchId` on the deal that would be wrong for every card but
 * the latest hand's.
 *
 * ## A spent deal is not an empty pool, and conflating them is the bug this type prevents
 *
 * *"The screen runs out of cards long before the pool does, and only a fresh deal that comes
 * back empty is the empty state"*
 * ([`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §7). A
 * hand answered out with nothing appended is `spent`, which is a **request** — deal again, new
 * `search_id` — and the player never sees it. Only a hand that arrived with nothing is an
 * ending, and with appending that reads off the **latest** hand: an empty hand under cards
 * still unanswered is the ending waiting its turn, not a reason to deal a third time.
 *
 * ## And the ending has two readings, split on one number
 *
 * `players_in_range` is post-gate and is the whole of the difference:
 *
 * - **more than nobody** — you have seen everybody the deck can deal you, and *Show them
 *   again* is what there is to do about it;
 * - **nobody at all** — there is no one inside your radius this week, and the deck is the one
 *   Play surface where *widen in You* survives as advice, because the relaxation ladder is the
 *   pool's and a deal is offered no rungs. A reset there would deal nobody.
 *
 * Split any other way — on the deal being empty alone — the advice is *widen your radius* to a
 * player who has simply answered everybody, which is the product telling them to look further
 * away from people it has already found for them.
 *
 * **The advice itself is still gated**, and that gate is `radius_clamp`'s rather than this
 * rule's: a player already at the ceiling of their own slider must never be told to widen, and
 * whether they are is a fact about the answer (`domain/candidate`) rather than about the hand.
 *
 * ## *N left* is true, because it counts the pool and not the hand
 *
 * The count of cards left was deliberately never shown while a hand was all the client knew:
 * a hand is ten from a bigger pool, and a counter that says *2 left* and then produces ten
 * more lies. The envelope now carries `pool.remaining` — the people eligible beyond this hand —
 * so the counter prints **remaining plus unanswered in hand**, counting down as the player
 * answers (ADR-0169 §5).
 */

import type { Candidate, PoolDescription } from './candidate';
import { isLiker } from './yesBudget';

/**
 * One card as the deck holds it: **the person, and the deal they came off.**
 *
 * The `searchId` is the origin key every answer about this person cites, and it belongs to the
 * card rather than to the deal because the deal is more than one hand — see the module note.
 */
export interface DealtCard {
  readonly candidate: Candidate;
  readonly searchId: string;
}

/**
 * One card answered — **the person and the deal they were dealt on**, because an answer belongs
 * to a card and not to a person: the same player dealt again on a later hand (after a reset, or
 * once the dealt memory has lapsed) is a new card, dealt and not hidden.
 */
export interface AnsweredCard {
  readonly searchId: string;
  readonly playerId: string;
}

/** The deal, as the deck holds it: every hand so far, the pool as the latest hand described it. */
export interface DeckDeal {
  /** Every card dealt on this deck so far — hand after hand, in dealt order. */
  readonly cards: readonly DealtCard[];
  /** The pool as the **latest** hand described it: `remaining` and `wantToPlayYou` are fresh. */
  readonly pool: PoolDescription;
  /**
   * How many cards the latest hand brought.
   *
   * Nought is the ending — once the cards above it are answered — and the one fact the
   * flattened list cannot say for itself: a hand of ten appended to a hand of ten and a hand
   * of nought appended to a hand of twenty are the same twenty cards.
   */
  readonly latestHand: number;
}

/** How many real cards stand behind the top one — the mock's two, and never a placeholder. */
export const CARDS_BEHIND = 2;

/**
 * How few unanswered cards is few enough to ask for the next hand.
 *
 * Two, so that the cards behind are always real people: at two the card behind the top one is
 * the hand's last, and the one behind *that* has to come from the next deal (ADR-0169 §5).
 */
export const PREFETCH_AT = 2;

/**
 * What the deck draws right now.
 *
 * Four arms and not `DealtCard | undefined`, because the three ways of having no card are
 * three different screens: one is a request to the server, and the other two give opposite
 * advice.
 */
export type DeckStanding =
  /** One person, yes or no, with the next people behind them — real cards, or nothing. */
  | {
      readonly kind: 'card';
      readonly card: DealtCard;
      /** The next {@link CARDS_BEHIND} unanswered, in order — fewer where fewer remain. */
      readonly behind: readonly DealtCard[];
      /** How many are still unanswered in the hand, the top card included. */
      readonly unanswered: number;
    }
  /** Every card dealt has been answered and nothing was appended. Deal again — the player sees nothing. */
  | { readonly kind: 'spent' }
  /** The latest hand came back with nothing, and there are people in range. */
  | { readonly kind: 'seen-everybody' }
  /** The latest hand came back with nothing, and nobody is in range at all. */
  | { readonly kind: 'nobody-in-range' };

export function deckStanding(deal: DeckDeal, answered: readonly AnsweredCard[]): DeckStanding {
  const left = unanswered(deal, answered);
  const [showing, ...rest] = left;

  if (showing !== undefined) {
    return {
      kind: 'card',
      card: showing,
      behind: rest.slice(0, CARDS_BEHIND),
      unanswered: left.length,
    };
  }

  // Answered out, rather than dealt nothing. The two are the same empty list and completely
  // different facts, and only the latest hand's own size can tell them apart.
  if (deal.latestHand > 0) return { kind: 'spent' };

  return deal.pool.playersInRange > 0 ? { kind: 'seen-everybody' } : { kind: 'nobody-in-range' };
}

/** How many cards in the hand nobody has answered yet. */
export function unansweredIn(deal: DeckDeal, answered: readonly AnsweredCard[]): number {
  return unanswered(deal, answered).length;
}

/**
 * *N left* — the pool beyond the hand, plus the hand still unanswered.
 *
 * A deal that carried no `remaining` — every other ranked list, and a build behind the
 * contract — reads it as nought, so the counter states the hand and never invents a pool.
 */
export function cardsLeft(deal: DeckDeal, answered: readonly AnsweredCard[]): number {
  return (deal.pool.remaining ?? 0) + unansweredIn(deal, answered);
}

/**
 * Whether the next hand should be asked for **now** — at {@link PREFETCH_AT} unanswered, while
 * the pool says there are people beyond this hand, and never after a hand that brought nobody.
 *
 * The last clause is the one that stops a loop: a pool that still claims people over a hand
 * that came back empty would otherwise be asked again on every render, and the server has
 * already answered.
 */
export function wantsTheNextHand(deal: DeckDeal, answered: readonly AnsweredCard[]): boolean {
  return (
    deal.latestHand > 0 &&
    (deal.pool.remaining ?? 0) > 0 &&
    unansweredIn(deal, answered) <= PREFETCH_AT
  );
}

function unanswered(deal: DeckDeal, answered: readonly AnsweredCard[]): readonly DealtCard[] {
  return deal.cards.filter((card) => !answered.some((done) => isTheCard(done, card)));
}

/** Whether two answers name one card — the same person, on the same deal. */
export function sameCard(a: AnsweredCard, b: AnsweredCard): boolean {
  return a.playerId === b.playerId && a.searchId === b.searchId;
}

/** Whether an answer is about this dealt card. */
export function isTheCard(answer: AnsweredCard, card: DealtCard): boolean {
  return sameCard(answer, { searchId: card.searchId, playerId: card.candidate.playerId });
}

/** The one spelling of a card's identity as a string — for a React key, and nothing else. */
export function cardKey(card: DealtCard): string {
  return `${card.searchId}:${card.candidate.playerId}`;
}

/** One hand as `POST /deck` answered it — the shape `appendHand` folds onto the deal. */
export interface DealtHand {
  readonly searchId: string;
  readonly candidates: readonly Candidate[];
  readonly pool: PoolDescription;
}

/**
 * **One hand folded onto the deal** — or the start of one, where nothing is held.
 *
 * The cards keep their own `search_id`; the pool becomes the latest hand's. Nothing here sorts,
 * and whom to deal — a person again, or not — is the server's decision: a person dealt again on
 * a **new** `search_id` is a new card. The one thing dropped is the same card twice — the same
 * person on the same `search_id`, which the route promises never to answer — because appending
 * it would hold a hand that can never be answered out, and the effect that asks for the next
 * hand would ask for ever. A hand of nothing new is a hand of nought, and nought is the ending.
 */
export function appendHand(deal: DeckDeal | undefined, hand: DealtHand): DeckDeal {
  const held = deal?.cards ?? [];
  const already = new Set(held.map(cardKey));
  const dealt = hand.candidates
    .map((candidate) => ({ candidate, searchId: hand.searchId }))
    .filter((card) => !already.has(cardKey(card)));

  return { cards: [...held, ...dealt], pool: hand.pool, latestHand: dealt.length };
}

/**
 * The deal with one fewer person waiting — **only where the card answered was a liker's**
 * (ADR-0169 §4).
 *
 * A mutual on a stranger's card is somebody who said yes *after* the deal counted, and the
 * count never included them; a liker carried `INTEREST_LIFT` because their yes was there to be
 * counted. Untouched where the deal holds no such card, or no count at all. The count is the
 * latest hand's and is as fresh as the hand: a hand dealt after the mutual closed has already
 * left them out, and the decrement then overshoots by one until the next deal — accepted, as the
 * record accepts the count's other rounding.
 */
export function oneFewerWaiting(deal: DeckDeal, answer: AnsweredCard): DeckDeal {
  const card = deal.cards.find((dealt) => isTheCard(answer, dealt));
  const waiting = deal.pool.wantToPlayYou;
  if (card === undefined || !isLiker(card.candidate) || waiting === undefined || waiting === 0) {
    return deal;
  }
  return { ...deal, pool: { ...deal.pool, wantToPlayYou: waiting - 1 } };
}
