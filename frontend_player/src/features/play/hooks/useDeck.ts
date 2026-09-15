/**
 * The deck's four acts and its one read: deal, yes, no, *Show them again* — and where each
 * sport stands against its cap.
 *
 * ## The deal is a query, because a second deal is not a second copy of the first
 *
 * `POST /deck` mints a record like every other ranked list, and unlike every other ranked list
 * **nothing reads a deal back by id**. So it was written as a mutation, whose response is held
 * by the component that fired it and by nothing else — and that is exactly the hole, because
 * the deck is also the one surface where asking twice *costs* something. A deal excludes
 * everybody dealt to this player within the server's `DEALT_MEMORY`, so the second ask returns
 * a **different ten people**: the mechanism that makes *the next hand* work is the same
 * mechanism that makes an accidental deal spend the pool.
 *
 * Held by the screen, every remount was an accidental deal. Leaving the deck for another tab
 * and coming back dealt again; so did returning to a sport chip already dealt for, because the
 * only memory of *I have asked this* was a ref that died with the route. A player toggling
 * between two chips emptied their own deck without answering a card, and the deck then told
 * them, truthfully, that they had seen everybody.
 *
 * So the deal is held in Query under `searchKeys.deck(sport, under)` — **the ask, not the
 * answer** — which is the one key that can be built *before* the request and therefore the one
 * key under which *already asked* is a fact rather than a ref. What that buys is the whole
 * fix: coming back to a chip and coming back to the tab both find the deal already there.
 *
 * The mutation's posture is kept and now has to be configured rather than inherited:
 * `RANKED_LIST_QUERY_OPTIONS` is `staleTime: Infinity`, `refetchOnWindowFocus: false` and
 * `retry: false`, and `refetchOnReconnect` is turned off beside them — every one of those is
 * the same sentence, that **nothing mints a deal except the player asking for one**.
 *
 * ## A deal is hands, and asking again appends one
 *
 * The deal stays ten cards under one `search_id`, and the client asks for the next hand when
 * two remain, so the cards behind are real people and the join is invisible
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §5). `refetch()` is therefore **not a replacement**: the query function folds the hand it is
 * handed onto whatever the entry holds **when the hand lands** (`withHand`, over
 * `domain/deckHand`'s `appendHand`) — read after the `await`, never before it, because the
 * player keeps answering while the next hand is on its way and a fold over the pre-flight entry
 * would put every card answered during the round trip back on top. Every card keeps the
 * `search_id` it came off, because that is the origin key its answer has to cite and a card
 * from the first hand may be answered after the second has arrived. The envelope, the pool
 * and the prompts are the latest hand's — `remaining` and `want_to_play_you` are as fresh as
 * the hand — and `latestHand` is what tells a hand of nought apart from a hand answered out.
 *
 * **A reset replaces, and it is the one act that does.** *Show them again* re-deals people the
 * held deal has already recorded as answered, so appending the fresh hand would hide exactly
 * the cards the player asked to see again. `useResetDeck` resets the entry — Query's own
 * *back to the initial state, then refetch* — so the next hand starts a deal with nothing
 * answered on it.
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
 * Mutations ship `retry: false` and all four keep it. A deal is a recording write on a route
 * that is deliberately not idempotent — *"post again for a new deal with a new `search_id`"* —
 * so an automatic retry is a second recorded deal nobody asked for, exactly as it is on a
 * search. Asking for the next hand is a consequence of the player answering down to two, which
 * is a press, not a timer.
 *
 * ## The pause is kept, and the asymmetry is written down at both sites
 *
 * `networkMode: 'online'` is the app's default and these inherit it, so an answer made
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

import type { RaisedPrompt } from '../domain/raisedPrompt';
import type { SearchEnvelope } from '../domain/candidate';
import {
  appendHand,
  oneFewerWaiting,
  sameCard,
  type AnsweredCard,
  type DeckDeal,
} from '../domain/deckHand';
import { outgoingAfterYes } from '../domain/outgoingInterest';
import { dealDeck, type DeckAsk, type DeckOutcome } from '../use-cases/dealDeck';
import { resetDeck } from '../use-cases/resetDeck';
import { sayNo, sayYes, type CardAnswer, type InterestExpressed } from '../use-cases/answerCard';
import type { MyInterest } from '../mappers/interestMappers';

import { RANKED_LIST_QUERY_OPTIONS, searchKeys, type DealtUnder } from './searchKeys';

/**
 * The deal, **and how far through it the player is** — the whole of what the deck holds.
 *
 * `answered` is not a second fact beside the deal; it is a fact *about* this deal, and living
 * in the same entry is what makes it impossible for an id to outlive the deal it was answered
 * under. `domain/deckHand` takes the two apart again to say which of the four things the
 * screen is showing. The envelope and the prompts are the **latest** hand's; the cards are
 * every hand's.
 */
export interface HeldDeal extends DeckDeal {
  readonly envelope: SearchEnvelope;
  readonly prompts: readonly RaisedPrompt[];
  /**
   * The cards answered on this deal — **by card, not by person**. Empty on arrival, and empty
   * again after a reset; a person dealt again on a later hand is a new card and is not hidden by
   * an answer given on an earlier one (`domain/deckHand`).
   */
  readonly answered: readonly AnsweredCard[];
}

/**
 * **One hand folded onto what is held** — or the start of a deal, where nothing is.
 *
 * The cards and the pool are `appendHand`'s (`domain/deckHand`, where the rule about the same
 * card twice lives); what this adds is the entry's own — the envelope and the prompts become
 * the latest hand's, and the answers already given are kept.
 */
export function withHand(held: HeldDeal | undefined, hand: DeckOutcome): HeldDeal {
  return {
    ...appendHand(held, {
      searchId: hand.envelope.searchId,
      candidates: hand.candidates,
      pool: hand.pool,
    }),
    envelope: hand.envelope,
    prompts: hand.prompts,
    answered: held?.answered ?? [],
  };
}

/**
 * **The whole question a deal answers** — the request, and the one fact the request does not
 * carry because the server resolves it from the player's own profile.
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
 * carry: the screen has two standings in which no deal may run — no rated sport, and a
 * profile that has not landed — and it hands `undefined` for both rather than a question with
 * holes in it. An undeclared sport was a third until the deck stopped reading declarations
 * (ADR-0169 §2).
 *
 * `refetch()` is a **new `POST`** — a new `search_id` and a new hand — **appended** to what is
 * held (see the module note). That is the player's own act on every path that reaches it:
 * *Deal again* under a refusal, and answering down to two cards.
 */
export function useDeal(question: DeckQuestion | undefined) {
  const client = useQueryClient();
  const queryKey = searchKeys.deck(question?.ask.sport, question?.under);

  return useQuery<HeldDeal, AppError>({
    queryKey,
    queryFn:
      question === undefined
        ? skipToken
        : async () => {
            const hand = await dealDeck(question.ask);
            // Read **after** the round trip: the entry moves while the hand is in flight — see
            // the module note — and a fold over what it held before would undo those answers.
            return withHand(client.getQueryData<HeldDeal>(queryKey), hand);
          },
    ...RANKED_LIST_QUERY_OPTIONS,
    // The last two spellings of the one rule, and the two `staleTime: Infinity` does not give
    // for free. A connection coming back must not mint a deal, and — the one that is easy to
    // miss — **a failed deal must not be re-attempted by the next mount**: `retryOnMount`
    // defaults to true, so leaving Players after a refusal and coming back would deal again
    // with nothing pressed. The retry is *Deal again* under the sentence.
    refetchOnReconnect: false,
    retryOnMount: false,
  });
}

/**
 * Answering, as it happens to the **held deal** — the card is gone, or the card is back.
 *
 * The deal is found by the `search_id` the card was dealt under rather than by rebuilding its
 * key, which is the same discipline the screen used to keep by hand: an answer belongs to one
 * deal, and a deal that has since been replaced must not take it. Written as a cache update
 * rather than as a refetch because the answer *is* the change — Part 7's *"don't immediately
 * refetch what you were just handed"* — and because a refetch here would mint a deal.
 */
export interface DeckProgress {
  /** The card has left. It is answered, and the deck advances past it. */
  readonly cardLeft: (card: AnsweredCard) => void;
  /** The write was refused. The card comes back, so the retry is the button already pressed. */
  readonly cardReturned: (card: AnsweredCard) => void;
}

export function useDeckProgress(): DeckProgress {
  const client = useQueryClient();

  const move = (
    card: AnsweredCard,
    next: (answered: readonly AnsweredCard[]) => readonly AnsweredCard[],
  ) => {
    client.setQueriesData<HeldDeal>({ queryKey: searchKeys.decks() }, (held) =>
      held === undefined || !holdsHand(held, card.searchId)
        ? held
        : { ...held, answered: next(held.answered) },
    );
  };

  return {
    cardLeft: (card) =>
      move(card, (answered) =>
        answered.some((done) => sameCard(done, card)) ? answered : [...answered, card],
      ),
    cardReturned: (card) =>
      move(card, (answered) => answered.filter((done) => !sameCard(done, card))),
  };
}

/** Whether this deal holds a card dealt under `searchId` — any of its hands, not only the latest. */
function holdsHand(held: HeldDeal, searchId: string): boolean {
  return held.cards.some((card) => card.searchId === searchId);
}

/**
 * *Let's play* — the outstanding-yes count and the reader's own list, updated from the tap's
 * own answer, **the chip's count when a liker's yes comes back mutual**, and **the yes screen,
 * when the answer is a mutual naming a chat.**
 *
 * `ExpressedInterestResponse` carries where the sport stands **after** this tap, so the number
 * the counter's *N yeses to give* subtracts moves without a second round trip: Part 7's *"prefer
 * response-driven updates; don't immediately refetch what you were just handed"*. It is a patch
 * of one sport rather than a whole entry, because the read answers for all four and the tap
 * knows about one. **The reply says how the outgoing list moved too** — one-sided, and the
 * person is on it; mutual, and they are not — so the builder's *You said yes* is true the moment
 * the player crosses to Play, and the rule is `outgoingAfterYes`'s rather than this hook's
 * (ADR-0169 §8).
 *
 * **Nothing is invalidated.** A yes changes exactly one number and one list, and the response
 * says both; asking the server again for what it has just said would be the refetch this rule
 * exists to refuse, on the one read in the tab that is already allowed to move on its own.
 *
 * **And nothing is seeded.** Where the read has not landed, the updater returns `undefined`
 * and Query leaves the entry alone: writing `{padel: …}` as the whole answer would mark a
 * one-sport map fresh for the stale time, and every other sport would read as nought until it
 * expired. A patch is a patch of something.
 *
 * ## The chip counts down on a liker's mutual, from the reply and not from the press
 *
 * `pool.want_to_play_you` rides on the deal, so it is as fresh as the hand — and a yes on
 * somebody who carried `inclusion_reason` that comes back `mutual` is one of those people
 * answered, so the held deal's count drops by one (ADR-0169 §4). The card is looked up in the
 * held deal by the answer's own two keys rather than carried on the mutation's variables,
 * because the fact is the deal's and the write is here for the same reason the push below is:
 * the reply may land after the screen that fired it has gone.
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
 * **A mutual naming no chat stays a sentence, and stays with the press.** It is the one toast
 * an answer still raises, exactly as before — a full-screen celebration must never overstate
 * what happened. The one-sided yes and the pass have no sentence any more: the stamp and the
 * card leaving are the feedback, and what a listener gets is the spoken result (ADR-0169 §3).
 *
 * The route is the challenges feature's, read through its surface: both entries to the yes
 * screen end in a challenge, and the mutual reply names the one it opened (ADR-0154).
 */
export function useSayYes() {
  const client = useQueryClient();

  return useMutation<InterestExpressed, AppError, CardAnswer>({
    mutationFn: sayYes,
    onSuccess: ({ outstanding, mutual, challengeId }, answer) => {
      client.setQueryData<MyInterest>(searchKeys.interest(), (held) =>
        held === undefined
          ? undefined
          : {
              standing: { ...held.standing, ...outstanding },
              outgoing: outgoingAfterYes(held.outgoing, answer, mutual),
            },
      );

      if (mutual) {
        client.setQueriesData<HeldDeal>({ queryKey: searchKeys.decks() }, (held) =>
          held === undefined ? held : { ...held, ...oneFewerWaiting(held, answer) },
        );
      }

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
 * *Show them again* — the reset, and then a deal with **nothing answered on it**.
 *
 * The write answers nothing, so the deal is where the difference shows: on success the held
 * deal under this question is reset — Query's own *back to the initial state, then refetch the
 * active query* — rather than refetched, because a refetch appends and a reset re-deals people
 * the held deal has already recorded as answered (see the module note). A refused reset leaves
 * the ending on screen with its sentence above the button, and the button is the retry.
 */
export function useResetDeck(question: DeckQuestion | undefined) {
  const client = useQueryClient();

  return useMutation<void, AppError, void>({
    mutationFn: async () => {
      if (question === undefined) return;
      await resetDeck(question.ask.sport);
    },
    onSuccess: () => {
      if (question === undefined) return;
      void client.resetQueries({
        queryKey: searchKeys.deck(question.ask.sport, question.under),
        exact: true,
      });
    },
  });
}
