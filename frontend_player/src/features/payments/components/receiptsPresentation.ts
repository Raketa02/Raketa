/**
 * **What a receipt row says** — composed from a value, beside the fixed words in `paymentsCopy.ts`
 * ([#555](https://github.com/Raketa02/Raketa/issues/555); the screens A7.3; mock 49). Kept out of
 * the copy module, which the shell reads at module load and which therefore imports nothing that
 * reaches back into a feature.
 */

import { sportLabel } from '@/features/onboarding/types';
import { dayDate } from '@/shared/date/calendarDay';
import { platformClock } from '@/shared/date/platformZone';
import { formatZloty } from '@/shared/formatting/ratingFormat';
import { dayName } from '@/shared/vocabulary/availabilityPresentation';

import type { Receipt, ReceiptDay } from '../domain/receipts';

import { PAYMENTS_COPY } from './paymentsCopy';

const WORDS = PAYMENTS_COPY.receipts;

/** The club a receipt names — the seller — or the words for one that no longer exists. */
export function receiptClub(receipt: Pick<Receipt, 'club'>): string {
  return receipt.club.name ?? WORDS.unknownClub;
}

function dayWords(day: ReceiptDay): string {
  switch (day.kind) {
    case 'today':
      return WORDS.today;
    case 'tomorrow':
      return WORDS.tomorrow;
    case 'yesterday':
      return WORDS.yesterday;
    case 'weekday':
      return dayName(day.weekday);
    case 'dated':
      return dayDate(day.day);
  }
}

/** *Padel · Today · 16:00* — the game the share was for, under the club. */
export function receiptLine(
  receipt: Pick<Receipt, 'sport' | 'startsAt'>,
  day: ReceiptDay | undefined,
): string {
  return [
    sportLabel(receipt.sport),
    day === undefined ? undefined : dayWords(day),
    platformClock(receipt.startsAt),
  ]
    .filter((part): part is string => part !== undefined)
    .join(' · ');
}

/**
 * *−28 zł* for a charge, *+26,58 zł* for a refund — the true minus sign, never a hyphen, which a
 * screen reader reads as a dash.
 */
export function receiptAmount(receipt: Pick<Receipt, 'kind' | 'amountGrosze'>): string {
  const sign = receipt.kind === 'CHARGE' ? '−' : '+';
  return `${sign}${formatZloty(receipt.amountGrosze)}`;
}

/** One receipt, spoken whole: *Bonarka Arena, Padel · Today · 16:00, 28 zł paid*. */
export function receiptLabel(receipt: Receipt, day: ReceiptDay | undefined): string {
  const how = receipt.kind === 'CHARGE' ? WORDS.paid : WORDS.refunded;
  return `${receiptClub(receipt)}, ${receiptLine(receipt, day)}, ${formatZloty(receipt.amountGrosze)} ${how}`;
}
