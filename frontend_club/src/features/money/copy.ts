/**
 * **Every sentence Money says** (the screens B7; the mechanics §16.11), and how a month is named.
 */

import { BOOKINGS_COPY, shortDay } from '@/features/bookings/copy';
import type { BookingStatus } from '@/features/bookings/mappers';
import { sportName, type Sport } from '@/features/club-details/mappers';

import type { PayoutStatus } from './mappers';
import { monthParts } from './schemas';

const MONTH_NAMES = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

/** *March 2026*, from `2026-03`. */
export function monthTitle(month: string): string {
  const { year, number } = monthParts(month);
  return `${MONTH_NAMES[number - 1]} ${year}`;
}

/** *Mon 2 Mar · 19:00*: the day a game is played on, and its hour. */
export function playedAt(day: string, from: string): string {
  return `${shortDay(day)} · ${from}`;
}

/** *Padel · Played*: the game's sport, and what it is now, as on the Bookings page. */
export function sportAndStatus(sport: Sport, status: BookingStatus): string {
  return `${sportName(sport)} · ${BOOKINGS_COPY.statuses[status]}`;
}

/** The four figures, as the totals and the columns both name them. */
const FIGURES = {
  collected: 'Collected',
  refunded: 'Refunded',
  cardFees: 'Card fees',
  net: 'Net',
} as const;

export const MONEY_COPY = {
  caption: 'Paid on your own Stripe account',
  title: 'Money',
  month: {
    /** The month's controls, as a screen reader names them. */
    label: 'Month',
    previous: 'Previous month',
    next: 'Next month',
    thisMonth: 'This month',
    pick: 'Go to a month',
    show: 'Show',
  },
  /** A month in which no booking took money. */
  empty: (month: string) => `No Raketa booking took money in ${month}.`,
  totals: FIGURES,
  columns: { when: 'When', court: 'Court', ...FIGURES, paidOut: 'Paid out' },
  paidOut: 'Paid out ✓',
  notPaidOut: 'Not yet',
  payouts: {
    title: 'Payouts',
    lead:
      'From your Stripe account to your bank, newest first. You are paid after the game is ' +
      "played: at the close of each day, that day's games go to your bank in one payout. Your " +
      'bank details, disputes and tax documents are in your Stripe dashboard.',
    dashboard: 'Open your Stripe dashboard',
    columns: { date: 'Date', amount: 'Amount', status: 'Status' },
    statuses: {
      PENDING: 'On its way',
      IN_TRANSIT: 'On its way',
      PAID: 'In your bank',
      FAILED: 'Your bank refused it',
      CANCELLED: 'Cancelled',
    } satisfies Record<PayoutStatus, string>,
    /** Under a payout the bank refused: Stripe asks the club for its details. */
    failed: 'Check your bank details in your Stripe dashboard.',
    none: 'No payouts yet.',
    unreachable: "We couldn't reach Stripe for your payouts. Try again in a moment.",
    notConnected:
      'Players pay your own Stripe account, so nothing reaches your bank until payments are ' +
      'connected.',
    connect: 'Connect payments on Overview',
  },
} as const;
