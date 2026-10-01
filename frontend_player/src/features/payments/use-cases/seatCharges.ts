/**
 * **A refused share and the receipts** — pass-throughs over the two reads (#555). The secret is
 * read on its own, for the one press that uses it: see `domain/seatCharge`.
 */

import { getReceipts, getSeatCharge, type Cancellable } from '../api/paymentsApi';
import type { Receipt } from '../domain/receipts';
import type { PaymentToConfirm, SeatCharge } from '../domain/seatCharge';
import { toPaymentToConfirm, toReceipts, toSeatCharge } from '../mappers/seatChargeMappers';

export async function readSeatCharge(
  seatChargeId: string,
  options: Cancellable = {},
): Promise<SeatCharge | undefined> {
  return toSeatCharge(await getSeatCharge(seatChargeId, options));
}

/** What the phone confirms with, asked of the server now — `null` once nothing waits for the player. */
export async function readPaymentToConfirm(seatChargeId: string): Promise<PaymentToConfirm | null> {
  return toPaymentToConfirm(await getSeatCharge(seatChargeId));
}

export async function readReceipts(options: Cancellable = {}): Promise<readonly Receipt[]> {
  return toReceipts(await getReceipts(options));
}
