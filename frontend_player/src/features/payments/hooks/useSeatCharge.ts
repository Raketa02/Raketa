/**
 * **A refused share, read and confirmed on the phone** — the payments half of *Confirm your payment
 * to keep your seat* ([#555](https://github.com/Raketa02/Raketa/issues/555); #541; the mechanics
 * §12.2). The yes again — `POST /seat-charges/{id}/confirmation` — is the proposals feature's, as
 * the backend's is, and its caller sends it once this says `confirmed`.
 *
 * | | |
 * | --- | --- |
 * | `useSeatCharge` | `GET /seat-charges/{id}` — what the confirmation draws: the club, the share, the game, why it was refused |
 * | `useConfirmOnPhone` | the same read again **for the press** — the secret, straight to the port, never cached — then the provider's confirmation on the club's account |
 *
 * **Read once per sheet.** `staleTime: 0` and no refetch on focus: the payment's state is what the
 * press is about to change, and a re-read landing mid-confirmation would redraw the sheet under the
 * player's thumb with a status the press has not finished moving.
 */

import { useQuery } from '@tanstack/react-query';
import { useCallback } from 'react';

import type { AppError } from '@/shared/errors';
import { usePayments, type PaymentAnswer } from '@/shared/lib/platform';

import type { ConfirmWithCard, SeatCharge } from '../domain/seatCharge';
import { readPaymentToConfirm, readSeatCharge } from '../use-cases/seatCharges';

import { paymentKeys } from './paymentKeys';

export function useSeatCharge(seatChargeId: string) {
  return useQuery<SeatCharge | undefined, AppError>({
    queryKey: paymentKeys.seatCharge(seatChargeId),
    queryFn: ({ signal }) => readSeatCharge(seatChargeId, { signal }),
    staleTime: 0,
    refetchOnWindowFocus: false,
  });
}

/**
 * What confirming on the phone came to: the provider's four words, or `notWaiting` — the payment no
 * longer waits for the player (confirmed elsewhere, or let go), which only the server's yes again can
 * settle.
 */
export type PhoneConfirmation = PaymentAnswer | 'notWaiting';

/**
 * **Confirm one refused share on the phone.** Rejects only when the server could not be read for
 * the secret — the caller says why, as for any read; the provider's half never rejects.
 */
export function useConfirmOnPhone() {
  const payments = usePayments();
  return useCallback(
    async (seatChargeId: string, withCard: ConfirmWithCard): Promise<PhoneConfirmation> => {
      const ask = await readPaymentToConfirm(seatChargeId);
      if (ask === null) return 'notWaiting';
      return payments.confirmPayment({ ...ask, with: withCard });
    },
    [payments],
  );
}
