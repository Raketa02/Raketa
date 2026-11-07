/**
 * **A friends game's four writes** ([#759](https://github.com/Raketa02/Raketa/issues/759)) — each
 * a mutation the player waits on, made now or not at all (`networkMode: 'always'`): a send that
 * books a court, or an answer that holds money, landing minutes later would be the wrong game.
 * **None is retried** — the app's rule for a write that moves money.
 *
 * | | |
 * | --- | --- |
 * | `useSendFriendsGame` | *Send game and pay* — booked: every read a booking changes, as a fill's (`rereadAfterFill`) |
 * | `useAcceptFriendsGame` | *Accept* — the card moves to Your games, and the reader's other yeses at the hour go |
 * | `useDeclineFriendsGame` | *Not this time* — the card leaves Home |
 * | `useCallOffFriendsGame` | *Call it off* — the game off, the court the club's again |
 * | `useConfirmFriendsPayment` | a refused payment confirmed in the app — a send's, held for the send again; an accept's, the accept |
 */

import { useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { YesAnswer } from '../domain/fill';
import {
  answerRefusalOf,
  type FriendsGameAccepted,
  type FriendsGameSend,
  type FriendsGameSent,
} from '../domain/friendsGame';
import { confirmPayment } from '../use-cases/answers';
import {
  acceptFriendsGame,
  callOffFriendsGame,
  declineFriendsGame,
  sendFriendsGame,
} from '../use-cases/friendsGames';

import { proposalKeys } from './proposalKeys';
import { NOW_OR_NOT, rereadAfterFill } from './useFillWrites';

export function useSendFriendsGame(groupId: string) {
  const client = useQueryClient();
  return useMutation<FriendsGameSent, AppError, FriendsGameSend>({
    ...NOW_OR_NOT,
    mutationFn: (send) => sendFriendsGame(groupId, send),
    onSuccess: (sent) => {
      if (sent.booked) void rereadAfterFill(client);
    },
  });
}

export function useAcceptFriendsGame() {
  const client = useQueryClient();
  return useMutation<FriendsGameAccepted, AppError, string>({
    ...NOW_OR_NOT,
    mutationFn: (bookingId) => acceptFriendsGame(bookingId),
    onSuccess: (accepted) => {
      if (accepted.accepted) void rereadAfterFill(client);
    },
    onError: (error) => invitationGone(client, error),
  });
}

export function useDeclineFriendsGame() {
  const client = useQueryClient();
  return useMutation<void, AppError, string>({
    ...NOW_OR_NOT,
    mutationFn: (bookingId) => declineFriendsGame(bookingId),
    onSuccess: () => client.invalidateQueries({ queryKey: proposalKeys.home() }),
    onError: (error) => invitationGone(client, error),
  });
}

/**
 * **An answer refused because the invitation is gone** — ended, the game off or under way, or never
 * the reader's: Home is read again, and its card leaves.
 */
function invitationGone(client: QueryClient, error: AppError) {
  if (answerRefusalOf(error.code) === 'gone') {
    void client.invalidateQueries({ queryKey: proposalKeys.home() });
  }
}

export function useCallOffFriendsGame(bookingId: string) {
  const client = useQueryClient();
  return useMutation<void, AppError, void>({
    ...NOW_OR_NOT,
    mutationFn: () => callOffFriendsGame(bookingId),
    // The court is the club's again: every deck may deal it, and the game reads *Called off*.
    onSuccess: () => rereadAfterFill(client),
  });
}

/**
 * **A friends game's refused payment, confirmed in the app** — `POST /seat-charges/{id}/confirmation`
 * (#751): a send's payment is held for the send again under the same booking; an invited friend's
 * share is their *Accept* again. Asked of the provider, never taken on the phone's word.
 */
export function useConfirmFriendsPayment() {
  const client = useQueryClient();
  return useMutation<YesAnswer, AppError, string>({
    ...NOW_OR_NOT,
    mutationFn: (seatChargeId) => confirmPayment(seatChargeId),
    onSettled: () =>
      Promise.all([
        client.invalidateQueries({ queryKey: proposalKeys.paymentsToConfirm() }),
        client.invalidateQueries({ queryKey: proposalKeys.home() }),
      ]),
  });
}
