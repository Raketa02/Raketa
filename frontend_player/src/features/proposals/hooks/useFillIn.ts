/**
 * **A group's Fill in tab** — `GET /pools/{id}/fill-in?sport` (#545), its rescues and the tab's
 * badge ([#557](https://github.com/Raketa02/Raketa/issues/557); the rows not seen yet since #849).
 * You’re in, the tab beside it since
 * #847, is the live yeses (`useLiveYeses`), each row's game read in detail (`useProposal`) — and asks
 * this read only whether Fill in is empty, for its starting card.
 *
 * Filed under the group's root (`proposalKeys.fillIn`), so every answer in the group re-reads it
 * with the decks — a seat taken from a card leaves its row — and a changed Games & money with every
 * deck. The app's defaults otherwise, the deck's reasoning: read again on focus, never polled while
 * the tab is open.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import { rescueIds, standingSeats, type FillIn, type SeatToFill } from '../domain/fillIn';
import { readFillIn } from '../use-cases/fillIn';

import { proposalKeys } from './proposalKeys';
import { useReadClock } from './useHome';
import { useUnseenCount } from './useSeenRows';

/** How one observer asks: `retryOnMount: false` for a tab that reads it without drawing its refusal. */
export interface FillInObserver {
  readonly retryOnMount?: boolean;
}

export function useFillIn(groupId: string, sport: Sport, observer: FillInObserver = {}) {
  return useQuery<FillIn, AppError>({
    queryKey: proposalKeys.fillIn(groupId, sport),
    queryFn: ({ signal }) => readFillIn(groupId, sport, { signal }),
    ...observer,
  });
}

/**
 * **The rescues still offered, on the read's clock** — the read, the clock, running while a row is
 * offered so a row leaves at its deadline by itself, and the rows standing at it: `undefined` until
 * the read has answered.
 */
export function useSeatsToFill(groupId: string, sport: Sport, observer: FillInObserver = {}) {
  const read = useFillIn(groupId, sport, observer);
  const board = read.data;
  const now = useReadClock(board?.readAt, read.dataUpdatedAt, (board?.seatsToFill.length ?? 0) > 0);
  const seats: readonly SeatToFill[] | undefined =
    board === undefined ? undefined : standingSeats(board.seatsToFill, now);
  return { read, now, seats };
}

/**
 * **The Fill in tab's badge** — the rescues still standing that the reader hasn't seen (ADR-0208,
 * #849; the screens A1), each known by its booking and counted against what the phone kept for
 * this group and sport. The read's own `badge` is no longer read: the rows are, on the read's
 * clock, so a rescue past its deadline leaves the count as it leaves the tab.
 */
export function useFillInBadge(groupId: string, sport: Sport): number {
  const { seats } = useSeatsToFill(groupId, sport);
  return useUnseenCount(
    groupId,
    sport,
    ['fillIn'],
    seats === undefined ? undefined : rescueIds(seats),
  );
}
