/**
 * **A group's Fill in tab** — `GET /pools/{id}/fill-in?sport` (#545), *Seats to fill* and the tab's
 * badge ([#557](https://github.com/Raketa02/Raketa/issues/557)). *You're In* is the live yeses
 * (`useLiveYeses`), each row's game read in detail (`useProposal`).
 *
 * Filed under the group's root (`proposalKeys.fillIn`), so every answer in the group re-reads it
 * with the decks — a seat taken from a card leaves its row — and a changed Games & money with every
 * deck. The app's defaults otherwise, the deck's reasoning: read again on focus, never polled while
 * the tab is open.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import type { FillIn } from '../domain/fillIn';
import { readFillIn } from '../use-cases/fillIn';

import { proposalKeys } from './proposalKeys';

export function useFillIn(groupId: string, sport: Sport) {
  return useQuery<FillIn, AppError>({
    queryKey: proposalKeys.fillIn(groupId, sport),
    queryFn: ({ signal }) => readFillIn(groupId, sport, { signal }),
  });
}

/** **The Fill in tab's badge** — the *Seats to fill* rows (the screens A1, mock 11). */
export function useFillInBadge(groupId: string, sport: Sport): number {
  return useFillIn(groupId, sport).data?.badge ?? 0;
}
