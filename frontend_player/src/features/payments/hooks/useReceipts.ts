/**
 * **You › Payments' *RECEIPTS*** — `GET /players/me/receipts` (#555). The app's defaults: a booking
 * anywhere re-reads it (`paymentKeys.receipts()`, crossed for the fill), and a return to the screen
 * after thirty seconds reads it again.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { Receipt } from '../domain/receipts';
import { readReceipts } from '../use-cases/seatCharges';

import { paymentKeys } from './paymentKeys';

export function useReceipts() {
  return useQuery<readonly Receipt[], AppError>({
    queryKey: paymentKeys.receipts(),
    queryFn: ({ signal }) => readReceipts({ signal }),
  });
}
