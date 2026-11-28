/**
 * **What a receipt row says** — composed from a value, beside the fixed words in `paymentsCopy.ts`
 * ([#555](https://github.com/Rakieta02/Rakieta/issues/555); the screens A7.3; mock 49). Kept out of
 * the copy module, which the shell reads at module load and which therefore imports nothing that
 * reaches back into a feature.
 */

import { sportLabel } from '@/features/onboarding/types';
import { dayDate } from '@/shared/date/calendarDay';
import { platformClock, platformDay } from '@/shared/date/platformZone';
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
 * *−40 zł · paid* for a share taken, *+38,24 zł · refunded* for a refund — the true minus sign,
 * never a hyphen, which a screen reader reads as a dash — and *40 zł held · released*, unsigned, for
 * a hold let go: nothing moved (#644).
 */
export function receiptAmount(receipt: Pick<Receipt, 'kind' | 'amountGrosze'>): string {
  const amount = formatZloty(receipt.amountGrosze);
  switch (receipt.kind) {
    case 'CHARGE':
      return `−${amount} · ${WORDS.paid}`;
    case 'REFUND':
      return `+${amount} · ${WORDS.refunded}`;
    case 'RELEASED':
      return `${amount} ${WORDS.held} · ${WORDS.released}`;
  }
}

/** The day a hold was let go, as a bank app dates it — *28 Sep*. */
function releasedDay(receipt: Pick<Receipt, 'movedAt'>): string | undefined {
  const day = platformDay(receipt.movedAt);
  return day === undefined ? undefined : dayDate(day);
}

/** Exactly what was kept on a refund's payment — nothing to say on a refund in full. */
function keptWords(receipt: Pick<Receipt, 'keptGrosze'>): string | undefined {
  const kept = receipt.keptGrosze;
  return kept === undefined || kept === 0
    ? undefined
    : `${formatZloty(kept)} ${WORDS.keptOnYourPayment}`;
}

/**
 * **What the movement leaves to explain, under the row** (the screens A7.3, #644): *1,76 zł kept on
 * your payment* under a refund, *Released 28 Sep* under a hold let go; nothing under a share taken.
 */
export function receiptNote(
  receipt: Pick<Receipt, 'kind' | 'keptGrosze' | 'movedAt'>,
): string | undefined {
  switch (receipt.kind) {
    case 'CHARGE':
      return undefined;
    case 'REFUND':
      return keptWords(receipt);
    case 'RELEASED': {
      const day = releasedDay(receipt);
      return day === undefined ? undefined : `${WORDS.releasedOn} ${day}`;
    }
  }
}

/** Which way the money went, aloud — *28 zł paid*, *40 zł held, released 28 Sep*. */
function movementSpoken(receipt: Receipt): readonly string[] {
  const amount = formatZloty(receipt.amountGrosze);
  switch (receipt.kind) {
    case 'CHARGE':
      return [`${amount} ${WORDS.paid}`];
    case 'REFUND': {
      const kept = keptWords(receipt);
      return [`${amount} ${WORDS.refunded}`, ...(kept === undefined ? [] : [kept])];
    }
    case 'RELEASED': {
      const day = releasedDay(receipt);
      return [
        `${amount} ${WORDS.held}`,
        day === undefined ? WORDS.released : `${WORDS.released} ${day}`,
      ];
    }
  }
}

/**
 * One receipt, spoken whole: *Bonarka Arena, Padel · Today · 16:00, 28 zł paid* — and what is left
 * to explain, *…, 38,24 zł refunded, 1,76 zł kept on your payment*.
 */
export function receiptLabel(receipt: Receipt, day: ReceiptDay | undefined): string {
  return [receiptClub(receipt), receiptLine(receipt, day), ...movementSpoken(receipt)].join(', ');
}
