/**
 * **The club's money, wire to view.** The only file in this feature that imports a generated
 * type (ADR-0187 §6); everything else reads the view models it makes.
 */

import type { components } from '@/generated/schema';
import { clubClock, type BookingStatus } from '@/features/bookings/mappers';
import type { Sport } from '@/features/club-details/mappers';
import { clubDay } from '@/features/courts/mappers';

type WireMonth = components['schemas']['ClubMoneyResponse'];
type WireTotals = components['schemas']['MoneyTotalsSchema'];
type WireBooking = components['schemas']['MoneyBookingSchema'];
type WirePayouts = components['schemas']['PayoutsResponse'];

/** Where a payout stands, as Stripe says: on its way, in the bank, refused by it, or cancelled. */
export type PayoutStatus = components['schemas']['PayoutStatus'];

/**
 * **What a booking, or a month, came to**, in grosze, on the club's own Stripe account: what the
 * players paid, what was given back, Stripe's card fees, and what is the club's.
 */
export interface Takings {
  readonly collectedGrosze: number;
  readonly refundedGrosze: number;
  readonly cardFeesGrosze: number;
  /** Below nought when a game given back whole cost the club its card fees. */
  readonly netGrosze: number;
}

/** **One booking's money**, as a row of the month draws it. */
export interface MoneyBooking {
  readonly id: string;
  /** The local day it is played on, `2026-03-02`. */
  readonly day: string;
  /** The club's clock at its start, `19:00`. */
  readonly from: string;
  readonly court: string;
  readonly sport: Sport;
  readonly status: BookingStatus;
  readonly takings: Takings;
  /** A payout carried its money to the club's bank; until then it waits on the account. */
  readonly paidOut: boolean;
}

/** **A month of the club's money**: its totals, and its bookings soonest first. */
export interface MoneyMonth {
  /** The month read, `2026-03`. */
  readonly month: string;
  /** The month at the club now: the page offers the way back to it. */
  readonly thisMonth: string;
  readonly totals: Takings;
  readonly bookings: readonly MoneyBooking[];
}

function toTakings(wire: WireTotals): Takings {
  return {
    collectedGrosze: wire.collected_grosze,
    refundedGrosze: wire.refunded_grosze,
    cardFeesGrosze: wire.card_fees_grosze,
    netGrosze: wire.net_grosze,
  };
}

function toBooking(wire: WireBooking): MoneyBooking {
  return {
    id: wire.booking_id,
    day: clubDay(Date.parse(wire.starts_at)),
    from: clubClock(wire.starts_at),
    court: wire.court_name,
    sport: wire.sport,
    status: wire.status,
    takings: toTakings(wire),
    paidOut: wire.paid_out,
  };
}

export function toMoneyMonth(wire: WireMonth, thisMonth: string): MoneyMonth {
  return {
    month: wire.month,
    thisMonth,
    totals: toTakings(wire.totals),
    bookings: wire.bookings.map(toBooking),
  };
}

/** **A payout to the club's bank**, from its Stripe account: a day's games over, in one sum. */
export interface Payout {
  readonly id: string;
  /** The local day it reaches, or reached, the bank, `2026-03-17`. */
  readonly day: string;
  readonly amountGrosze: number;
  readonly status: PayoutStatus;
}

/** Newest first, as Stripe lists them. */
export function toPayouts(wire: WirePayouts): readonly Payout[] {
  return wire.payouts.map((each) => ({
    id: each.payout_id,
    day: clubDay(Date.parse(each.arrives_at)),
    amountGrosze: each.amount_grosze,
    status: each.status,
  }));
}
