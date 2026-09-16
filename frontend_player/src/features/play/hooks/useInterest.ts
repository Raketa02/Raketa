/**
 * **Your own yeses, held once and read twice** — the count the deck's counter subtracts, and
 * the list the builder's cards and the challenge screen look a person up in.
 *
 * One `GET /interest`, one cache entry, and three hooks over it with `select`: the deck wants
 * *where does each sport stand*, the pool and the challenge screen want *whom have I said yes
 * to*, the radar's sheet wants *whose yes came back*, and a key per reader would be three
 * requests for one response
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §8, [ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §4). `settleYes` patches the one entry on a tap's own answer, and every reader sees the patch.
 *
 * On the app's ordinary defaults — 30 s stale, refetching on focus — which is the deliberate
 * exception to *nothing in Play background-refetches*. That rule is about **orderings**: a
 * pool that reorders under a finger is the harm, and a count has no order to lose, and a
 * lookup that gains a name adds a tag to a card without moving it. These are the two facts in
 * the tab that should move while somebody is looking at them.
 *
 * `useDeck.ts` is where the deck's *own* hooks live; this file is beside it because its second
 * and third readers are not the deck.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { MutualInterest, OutgoingInterest } from '../domain/outgoingInterest';
import type { MyInterest, OutstandingInterest } from '../mappers/interestMappers';
import { readMyInterest } from '../use-cases/readMyInterest';

import { searchKeys } from './searchKeys';

/** The one read, as every reader asks for it — so the two hooks below share a cache entry. */
const interestQuery = {
  queryKey: searchKeys.interest(),
  queryFn: ({ signal }: { readonly signal: AbortSignal }) => readMyInterest({ signal }),
} as const;

/**
 * **Where every sport stands against its cap** — the count, the cap and the life of a yes,
 * which the counter subtracts and the ending prints.
 */
export function useOutstandingInterest() {
  return useQuery<MyInterest, AppError, OutstandingInterest>({
    ...interestQuery,
    select: (interest) => interest.standing,
  });
}

/**
 * **Whom the reader has said yes to, per sport** — the fact *You said yes* is drawn from, on a
 * pool row and under the organiser's card on a challenge (ADR-0169 §8).
 *
 * The rule that reads it is `domain/outgoingInterest`'s `saidYesTo`; a surface holds the map
 * and asks it one person at a time, and nothing draws the map as a list.
 */
export function useOutgoingInterest() {
  return useQuery<MyInterest, AppError, OutgoingInterest>({
    ...interestQuery,
    select: (interest) => interest.outgoing,
  });
}

/**
 * **Whose yes came back, per sport** — the fact *You're matched* is drawn from, on the radar's
 * record sheet and nowhere else (ADR-0174 §4).
 *
 * The rule that reads it is `domain/outgoingInterest`'s `matchedWith`, one person at a time;
 * nothing draws the map as a list, which is what keeps ADR-0169 §8's *no list of your yeses*
 * true of the ones that came back too.
 */
export function useMutualInterest() {
  return useQuery<MyInterest, AppError, MutualInterest>({
    ...interestQuery,
    select: (interest) => interest.mutual,
  });
}
