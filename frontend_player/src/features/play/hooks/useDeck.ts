/**
 * The deck's three acts and its one read: deal, yes, no, and the outstanding count.
 *
 * ## The deal is a query, because a second deal is not a second copy of the first
 *
 * `POST /deck` mints a record like every other ranked list, and unlike every other ranked list
 * **nothing reads a deal back by id**. So it was written as a mutation, whose response is held
 * by the component that fired it and by nothing else — and that is exactly the hole, because
 * the deck is also the one surface where asking twice *costs* something. A deal excludes
 * everybody dealt to this player within the server's `DEALT_MEMORY`, so the second ask returns
 * a **different ten people**: the mechanism that makes *a spent deal deals again* work is the
 * same mechanism that makes an accidental deal spend the pool.
 *
 * Held by the screen, every remount was an accidental deal. Leaving Match me for Find a game
 * and coming back dealt again; so did returning to a sport chip already dealt for, because the
 * only memory of *I have asked this* was a ref that died with the route. A player toggling
 * between two chips emptied their own deck without answering a card, and the deck then told
 * them, truthfully, that they had seen everybody.
 *
 * So the deal is held in Query under `searchKeys.deck(sport, week)` — **the ask, not the
 * answer** — which is the one key that can be built *before* the request and therefore the one
 * key under which *already asked* is a fact rather than a ref. What that buys is the whole
 * fix: coming back to a chip and coming back to the screen both find the deal already there.
 *
 * The mutation's posture is kept and now has to be configured rather than inherited:
 * `RANKED_LIST_QUERY_OPTIONS` is `staleTime: Infinity`, `refetchOnWindowFocus: false` and
 * `retry: false`, and `refetchOnReconnect` is turned off beside them — every one of those is
 * the same sentence, that **nothing mints a deal except the player asking for one**.
 *
 * ## How far through a deal the player is, is part of the deal
 *
 * The ids answered are held *inside* the cache entry rather than beside it, and that is the
 * half without which the rest is a regression: a deal that outlives the screen with its
 * progress left behind on the screen comes back with every answered card on it again. Keeping
 * the two together also states by construction what the screen used to state by pairing an id
 * list with a `search_id` — an answer cannot outlive the deal it was given on, because it is
 * held in it.
 *
 * ## Nothing here retries, and dealing again is the player's own act
 *
 * Mutations ship `retry: false` and all three keep it. A deal is a recording write on a route
 * that is deliberately not idempotent — *"post again for a new deal with a new `search_id`"* —
 * so an automatic retry is a second recorded deal nobody asked for, exactly as it is on a
 * search. Re-dealing when a deal is spent is a consequence of the player answering the last
 * card, which is a press, not a timer.
 *
 * ## The pause is kept, and the asymmetry is written down at both sites
 *
 * `networkMode: 'online'` is the app's default and these three inherit it, so an answer made
 * offline is **held until the connection returns** rather than failed. `features/challenges/`
 * alone overrides it, because a challenge's answer window is derived *at send* and the pause
 * would split the tap from the send
 * (`features/challenges/hooks/challengeMutationOptions.ts`). Neither a yes nor a pass derives
 * anything from the moment it lands: a yes carries its own `expires_at`
 * dated server-side, and a pass's window is *"not yours to name"* and has no field on the
 * request at all. So the deck keeps the pause, and a deferred answer really is the answer.
 */

import { skipToken, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';

import { yesRoute } from '@/features/challenges/types';
import type { AppError } from '@/shared/errors';

import { dealDeck, type DeckAsk, type DeckOutcome } from '../use-cases/dealDeck';
import { readOutstandingInterest } from '../use-cases/readOutstandingInterest';
import { sayNo, sayYes, type CardAnswer, type InterestExpressed } from '../use-cases/answerCard';
import type { OutstandingInterest } from '../mappers/interestMappers';

import { RANKED_LIST_QUERY_OPTIONS, searchKeys, type DealtUnder } from './searchKeys';

/**
 * One deal, **and how far through it the player is** — the whole of what the deck holds.
 *
 * `answered` is not a second fact beside the deal; it is a fact *about* this deal, and living
 * in the same entry is what makes it impossible for an id to outlive the `search_id` it was
 * answered under. `domain/deckHand` takes the two apart again to say which of the four things
 * the screen is showing.
 */
export interface HeldDeal extends DeckOutcome {
  /** The ids answered on this deal. Empty on arrival, and empty again on the next one. */
  readonly answered: readonly string[];
}

/**
 * **The whole question a deal answers** — the request, and the two facts the request does not
 * carry because the server resolves them from the player's own profile.
 *
 * One value rather than two arguments, so the pair cannot drift: they are true together or
 * absent together — the screen has one branch in which a deal may run at all — and a key built
 * from half of a question is the bug `DealtUnder` exists to close.
 */
export interface DeckQuestion {
  readonly ask: DeckAsk;
  readonly under: DealtUnder;
}

/**
 * The deal for this question, dealt once and then **found** rather than dealt again.
 *
 * `skipToken` rather than `enabled`, so that *there is nothing to ask* is a fact the types
 * carry: the screen has three standings in which no deal may run — no rated sport, an
 * undeclared sport, and a profile that has not landed — and it hands `undefined` for all
 * three rather than a question with holes in it.
 *
 * Re-dealing is `refetch()`, which is a **new `POST`** and therefore a new `search_id` and a
 * new ten people. That is the player's own act on both paths that reach it: *Deal again* under
 * a refusal, and answering the last card of a hand.
 */
export function useDeal(question: DeckQuestion | undefined) {
  return useQuery<HeldDeal, AppError>({
    queryKey: searchKeys.deck(question?.ask.sport, question?.ask.sentWeek, question?.under),
    queryFn:
      question === undefined
        ? skipToken
        : async () => ({ ...(await dealDeck(question.ask)), answered: [] }),
    ...RANKED_LIST_QUERY_OPTIONS,
    // The last two spellings of the one rule, and the two `staleTime: Infinity` does not give
    // for free. A connection coming back must not mint a deal, and — the one that is easy to
    // miss — **a failed deal must not be re-attempted by the next mount**: `retryOnMount`
    // defaults to true, so leaving Match me after a refusal and coming back would deal again
    // with nothing pressed. The retry is *Deal again* under the sentence, on both screens the
    // player can reach it from.
    refetchOnReconnect: false,
    retryOnMount: false,
  });
}

/** One card, and the deal it was answered on. */
export interface AnsweredCard {
  readonly searchId: string;
  readonly playerId: string;
}

/**
 * Answering, as it happens to the **held deal** — the card is gone, or the card is back.
 *
 * The deal is found by the `search_id` it was minted under rather than by rebuilding its key,
 * which is the same discipline the screen used to keep by hand: an answer belongs to one deal,
 * and a deal that has since been replaced must not take it. Written as a cache update rather
 * than as a refetch because the answer *is* the change — Part 7's *"don't immediately refetch
 * what you were just handed"* — and because a refetch here would mint a deal.
 */
export interface DeckProgress {
  /** The card has left. It is answered, and the deck advances past it. */
  readonly cardLeft: (card: AnsweredCard) => void;
  /** The write was refused. The card comes back, so the retry is the button already pressed. */
  readonly cardReturned: (card: AnsweredCard) => void;
}

export function useDeckProgress(): DeckProgress {
  const client = useQueryClient();

  const move = (searchId: string, next: (answered: readonly string[]) => readonly string[]) => {
    client.setQueriesData<HeldDeal>({ queryKey: searchKeys.decks() }, (held) =>
      held === undefined || held.envelope.searchId !== searchId
        ? held
        : { ...held, answered: next(held.answered) },
    );
  };

  return {
    cardLeft: ({ searchId, playerId }) =>
      move(searchId, (answered) =>
        answered.includes(playerId) ? answered : [...answered, playerId],
      ),
    cardReturned: ({ searchId, playerId }) =>
      move(searchId, (answered) => answered.filter((gone) => gone !== playerId)),
  };
}

/**
 * *Let's play* — the outstanding-yes count, updated from the tap's own answer, and **the yes
 * screen, when the answer is a mutual naming a chat.**
 *
 * `ExpressedInterestResponse` carries where the sport stands **after** this tap, so the number
 * the deck's ending sentence prints moves without a second round trip: Part 7's *"prefer
 * response-driven updates; don't immediately refetch what you were just handed"*. It is a patch
 * of one sport rather than a whole entry, because the read answers for all four and the tap
 * knows about one.

 * The patch outlived the segment it was written for: `Match me · 3` was struck for reading as a
 * count of waiting cards, and what is left is one reader — `outgoingYeses`, on the ending — for
 * which being right without a round trip matters exactly as much.
 *
 * **Nothing is invalidated.** A yes changes exactly one number and the response is that
 * number; asking the server again for what it has just said would be the refetch this rule
 * exists to refuse, on the one read in the tab that is already allowed to move on its own.
 *
 * **And nothing is seeded.** Where the read has not landed, the updater returns `undefined`
 * and Query leaves the entry alone: writing `{padel: 3}` as the whole answer would mark a
 * one-sport map fresh for the stale time, and every other sport would read as nought until it
 * expired. A patch is a patch of something.
 *
 * ## A mutual naming a challenge is a screen, pushed from here and not from the press
 *
 * When the reply says `mutual` **and** names a challenge, the yes screen is pushed for it as a
 * mutual's — *Matched!* — over wherever the player is by then
 * ([ADR-0167](../../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §1, [#434](https://github.com/Raketa02/Raketa/issues/434)). It is pushed from **this**
 * `onSuccess` and deliberately not from the screen's per-press callback: the callbacks handed to
 * `mutate()` are dropped the moment the component that called it unmounts, and the yes is
 * optimistic — the card flies on the press and the reply may land after the player has moved to
 * the next card, or to another tab. A slow reply must not swallow the moment, so the push lives
 * with the mutation, which outlives the screen. The card's flight is not waited for: a screen
 * over a card still leaving is the screen the record asks for, and *Later* pops back to a deck
 * that has finished advancing.
 *
 * **The other two answers stay sentences, and stay with the press.** A one-sided yes and a
 * mutual naming no chat are toasts the screen raises from its own callback, exactly as before —
 * a full-screen celebration must never overstate what happened, and a toast about a card the
 * player has already left behind is not owed to them the way the screen is.
 *
 * The route is the challenges feature's, read through its surface: both entries to the yes
 * screen end in a challenge, and the mutual reply names the one it opened (ADR-0154).
 */
export function useSayYes() {
  const client = useQueryClient();

  return useMutation<InterestExpressed, AppError, CardAnswer>({
    mutationFn: sayYes,
    onSuccess: ({ outstanding, mutual, challengeId }) => {
      client.setQueryData<OutstandingInterest>(searchKeys.interest(), (held) =>
        held === undefined ? undefined : { ...held, ...outstanding },
      );

      if (mutual && challengeId !== null) router.push(yesRoute(challengeId, 'mutual'));
    },
  });
}

/**
 * *Not today* — recorded, and answered by nothing.
 *
 * There is no cache to update and no number to move: **no route anywhere returns a pass**, and
 * a client that kept its own count of them would be publishing the one figure §21 refuses to
 * publish, to the only person it could reach.
 */
export function useSayNo() {
  return useMutation<void, AppError, CardAnswer>({ mutationFn: sayNo });
}

/**
 * **Your outstanding yeses, per sport** — the figure the deck's ending sentence counts.
 *
 * On the app's ordinary defaults — 30 s stale, refetching on focus — which is the deliberate
 * exception to *nothing in Play background-refetches*. That rule is about **orderings**: a
 * pool that reorders under a finger is the harm, and a count has no order to lose. This is the
 * one number in the tab that should move while somebody is looking at it.
 */
export function useOutstandingInterest() {
  return useQuery<OutstandingInterest, AppError>({
    queryKey: searchKeys.interest(),
    queryFn: ({ signal }) => readOutstandingInterest({ signal }),
  });
}
