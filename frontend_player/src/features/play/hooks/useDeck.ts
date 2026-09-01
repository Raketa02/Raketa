/**
 * The deck's three acts and its one read: deal, yes, no, and the count above them.
 *
 * ## The deal is a mutation, and it writes no cache entry
 *
 * `POST /deck` mints a record like every other ranked list, and unlike every other ranked list
 * **nothing reads a deal back by id**. `searchKeys.detail(id)` exists for the surfaces that
 * read a record — the builder reads the origin a line-up is judged against, the pool re-reads
 * its rows — and a deal seats nobody: cards are answered as they are dealt, and *a spent deal
 * deals again* rather than being re-read.
 *
 * The posture that entry buys is kept anyway, and by construction rather than by configuration:
 * a mutation's response is never refetched, never stale and never reordered by foregrounding,
 * which is the whole of what `RANKED_LIST_QUERY_OPTIONS` is for. Writing an entry nothing reads
 * would put a **second shape** under a key whose one reader types it as an origin search — and
 * a deal has no mode and no line-up, so it is not one.
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
 * would split the tap from the send (`features/challenges/hooks/sendOptions.ts`). Neither a
 * yes nor a pass derives anything from the moment it lands: a yes carries its own `expires_at`
 * dated server-side, and a pass's window is *"not yours to name"* and has no field on the
 * request at all. So the deck keeps the pause, and a deferred answer really is the answer.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import { dealDeck, type DeckAsk, type DeckOutcome } from '../use-cases/dealDeck';
import { readOutstandingInterest } from '../use-cases/readOutstandingInterest';
import { sayNo, sayYes, type CardAnswer, type InterestExpressed } from '../use-cases/answerCard';
import type { OutstandingInterest } from '../mappers/interestMappers';

import { searchKeys } from './searchKeys';

export function useDealDeck() {
  return useMutation<DeckOutcome, AppError, DeckAsk>({ mutationFn: dealDeck });
}

/**
 * *Let's play* — and the count above the deck, updated from the tap's own answer.
 *
 * `ExpressedInterestResponse` carries where the sport stands **after** this tap, so the
 * segment's number moves without a second round trip: Part 7's *"prefer response-driven
 * updates; don't immediately refetch what you were just handed"*. It is a patch of one sport
 * rather than a whole entry, because the read answers for all four and the tap knows about one.
 *
 * **Nothing is invalidated.** A yes changes exactly one number and the response is that
 * number; asking the server again for what it has just said would be the refetch this rule
 * exists to refuse, on the one read in the tab that is already allowed to move on its own.
 *
 * **And nothing is seeded.** Where the read has not landed, the updater returns `undefined`
 * and Query leaves the entry alone: writing `{padel: 3}` as the whole answer would mark a
 * one-sport map fresh for the stale time, and every other sport would read as nought until it
 * expired. A patch is a patch of something.
 */
export function useSayYes() {
  const client = useQueryClient();

  return useMutation<InterestExpressed, AppError, CardAnswer>({
    mutationFn: sayYes,
    onSuccess: ({ outstanding }) => {
      client.setQueryData<OutstandingInterest>(searchKeys.interest(), (held) =>
        held === undefined ? undefined : { ...held, ...outstanding },
      );
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
 * The **Match me count**: your outstanding yeses, per sport.
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
