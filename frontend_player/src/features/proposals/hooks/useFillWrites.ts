/**
 * **The fill's two writes, and what a booking re-reads** — the yes sent when its ten seconds are up,
 * and the yes again on a payment confirmed in the app
 * ([#555](https://github.com/Raketa02/Raketa/issues/555); #541).
 *
 * | | |
 * | --- | --- |
 * | `useBookingYes` | `POST /proposals/{id}/yes` — a yes that waited behind *Undo* |
 * | `useConfirmPaymentYes` | `POST /seat-charges/{id}/confirmation` — *I confirmed my payment* |
 * | `rereadAfterFill` | what a game booked changes: every deck, the live yeses and the payments to confirm, Home's games, the receipts |
 *
 * ## Now or not at all
 *
 * The deck's answers are held while offline and sent on reconnect; **these two are not**
 * (`networkMode: 'always'`), the setup's own rule. Each can book a game and charge everybody on it,
 * and a booking that lands minutes after the player stopped waiting for it — on a reconnect they
 * never saw — is worse than a sentence saying it did not go. A failure is said, and the card is
 * dealt again for another yes.
 *
 * ## The handlers sit on the mutation
 *
 * Every call carries the card it was said on and the deck it was dealt in, and the mutation's own
 * callbacks read them back off the variables — a call's own callbacks are dropped when the mutation
 * is called again before it settles, and the fill's host outlives every screen that asked it.
 */

import { useMutation, useQueryClient, type QueryClient } from '@tanstack/react-query';

import { gameKeys } from '@/features/games/types';
import { paymentKeys } from '@/features/payments/types';
import type { AppError } from '@/shared/errors';

import { isRescue, type YesAnswer } from '../domain/fill';
import { answerCard, confirmPayment } from '../use-cases/answers';

import { proposalKeys } from './proposalKeys';
import type { BookAsk, ConfirmAsk } from './useFill';
import { reread } from './useGroupDeck';
import { useLatest } from './useLatest';

export interface FillHandlers<Ask> {
  readonly onAnswered: (answer: YesAnswer, ask: Ask) => void;
  readonly onRefused: (error: AppError, ask: Ask) => void;
}

/** A write the player waits on: made now, or not at all — never queued for later. */
export const NOW_OR_NOT = { networkMode: 'always' } as const;

export function useBookingYes(handlers: FillHandlers<BookAsk>) {
  const client = useQueryClient();
  const latest = useLatest(handlers);

  return useMutation<YesAnswer | null, AppError, BookAsk>({
    ...NOW_OR_NOT,
    mutationKey: proposalKeys.answers(),
    mutationFn: ({ card }) =>
      answerCard({ proposalId: card.proposalId, said: 'yes', rescue: isRescue(card) }),
    onSuccess: (answer, ask) => {
      if (answer !== null) latest.current.onAnswered(answer, ask);
    },
    onError: (error, ask) => latest.current.onRefused(error, ask),
    onSettled: (_answer, _error, { dealtIn }) => reread(client, dealtIn.groupId, { yeses: true }),
  });
}

export function useConfirmPaymentYes(handlers: FillHandlers<ConfirmAsk>) {
  const client = useQueryClient();
  const latest = useLatest(handlers);

  return useMutation<YesAnswer, AppError, ConfirmAsk>({
    ...NOW_OR_NOT,
    mutationFn: ({ seatChargeId }) => confirmPayment(seatChargeId),
    onSuccess: (answer, ask) => latest.current.onAnswered(answer, ask),
    onError: (error, ask) => latest.current.onRefused(error, ask),
    onSettled: (_answer, _error, { dealtIn }) =>
      Promise.all([
        reread(client, dealtIn.groupId, { yeses: true }),
        client.invalidateQueries({ queryKey: proposalKeys.paymentsToConfirm() }),
        // Home's badge counts every payment to confirm (#556).
        client.invalidateQueries({ queryKey: proposalKeys.home() }),
      ]),
  });
}

/**
 * **What a booked game changes, re-read** (the mechanics §11.5): every version and card of it leaves
 * every deck, the players' other yeses at that hour are withdrawn and a capped week's paused — so
 * every deck, every Fill in and the live yeses — and the game is in Home (its booking, #556, and its
 * Game), its details read again, and a receipt in Payments. A game waiting for one payment (#625)
 * re-reads the same: it is on Home, waiting.
 */
export function rereadAfterFill(client: QueryClient) {
  return Promise.all([
    client.invalidateQueries({ queryKey: proposalKeys.home() }),
    // A rescue joined was read from outside a moment ago (#545), and its row leaves Fill in.
    client.invalidateQueries({ queryKey: proposalKeys.bookings() }),
    client.invalidateQueries({ queryKey: proposalKeys.proposals() }),
    client.invalidateQueries({ queryKey: proposalKeys.decks() }),
    client.invalidateQueries({ queryKey: proposalKeys.liveYeses() }),
    client.invalidateQueries({ queryKey: proposalKeys.paymentsToConfirm() }),
    client.invalidateQueries({ queryKey: gameKeys.all }),
    client.invalidateQueries({ queryKey: paymentKeys.receipts() }),
  ]);
}
