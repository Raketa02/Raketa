/**
 * **Leave the game** — `POST /bookings/{id}/departure` (#544), from a booked game's details
 * ([#557](https://github.com/Raketa02/Raketa/issues/557); the mechanics §13).
 *
 * **Pending, never optimistic, and not retried**: leaving moves money — a refund before the club's
 * cut-off, none after it until somebody takes the seat — and the sheet in front of it quoted what it
 * costs. A refusal is said on that sheet; the game has started, been called off, or is no longer the
 * reader's, so the booking is read again and the details draw what it is now.
 *
 * **What leaving changes, re-read**: Home (the game leaves the leaver's), the receipts (a refund),
 * the live yeses (leaving while the club decides withdraws the yes), every deck and Fill in (the seat
 * is offered — and a game waiting is filling again), the details of any game still filling and the
 * games list (the leaver is off the Game). **Not the booking itself**: it answers `booking_not_found`
 * to the leaver at once, and the details screen is on its way back to Home as the reply lands.
 */

import { useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query';

import { gameKeys } from '@/features/games/types';
import { paymentKeys } from '@/features/payments/types';
import type { AppError } from '@/shared/errors';

import type { LeavingKind } from '../domain/vocabulary';
import { leaveGame } from '../use-cases/home';

import { proposalKeys } from './proposalKeys';

export function useLeaveBooking(bookingId: string) {
  const client = useQueryClient();

  return useMutation<LeavingKind, AppError, void>({
    mutationFn: () => leaveGame(bookingId),
    onSuccess: () => rereadAfterLeaving(client),
    onError: () => client.invalidateQueries({ queryKey: proposalKeys.booking(bookingId) }),
  });
}

function rereadAfterLeaving(client: QueryClient) {
  return Promise.all([
    client.invalidateQueries({ queryKey: proposalKeys.home() }),
    client.invalidateQueries({ queryKey: proposalKeys.decks() }),
    client.invalidateQueries({ queryKey: proposalKeys.liveYeses() }),
    client.invalidateQueries({ queryKey: proposalKeys.proposals() }),
    client.invalidateQueries({ queryKey: gameKeys.all }),
    client.invalidateQueries({ queryKey: paymentKeys.receipts() }),
  ]);
}
