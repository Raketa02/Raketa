/**
 * The radar's one read: the reading for the sport the pane is on.
 *
 * ## Five minutes, and refetched on the three moments the spec names
 *
 * A reading is refetched *when the Radar pane is opened and the held one is older than five
 * minutes, on a sport switch, and on a cold start*; Deck → Radar → Deck inside the window
 * refetches nothing, and nothing polls
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §1, [`the-radar.md`](../../../../../docs/specs/matchmaking/the-radar.md) §2). Query's own
 * vocabulary says exactly that: `staleTime` of five minutes with `refetchOnMount` at its
 * default, so a pane mounting over a fresh entry reads it and one mounting over a stale entry
 * asks again; a sport switch is a different key and its own first ask; a cold start is an empty
 * cache. The two things that would refetch without the pane opening are turned off —
 * **foregrounding** and a **connection returning** — for the reason every ranked list in Play
 * turns them off (`hooks/searchKeys`): the field must not move under a finger for a reason the
 * player did not give.
 *
 * ## Not `RANKED_LIST_QUERY_OPTIONS`, deliberately
 *
 * The deal is held for ever because a second deal *spends the pool*; a reading is not a deal
 * and spends nothing (ADR-0174 §4), so the stale time is the spec's five minutes and the
 * garbage-collection time is the app's default rather than infinity. `retry: false` is kept:
 * a reading records a search server-side, and *nothing in Play retries without the player
 * asking* — the retry is *Try again* in the footer.
 *
 * ## The reading is not appended to and not patched here
 *
 * `refetch()` replaces: a reading is the whole population inside the reach and not a hand.
 * What #464 will write onto a row after an answer — the card's last line — is a patch of the
 * held entry by the answer's own mutation, as the deck's chip is, and not this hook's.
 */

import { skipToken, useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Reading } from '../domain/reading';
import { readReading } from '../use-cases/readReading';

import { searchKeys } from './searchKeys';

/** How long a held reading answers for before the pane opening asks again — the spec's five minutes. */
export const READING_STALE_MS = 5 * 60 * 1000;

export function useReading(sport: Sport | undefined) {
  return useQuery<Reading, AppError>({
    queryKey: searchKeys.reading(sport),
    queryFn: sport === undefined ? skipToken : () => readReading(sport),
    staleTime: READING_STALE_MS,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    retry: false,
  });
}
