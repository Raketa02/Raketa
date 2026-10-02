/**
 * **The club's money, as the backend would answer it** (#548): a month of its bookings' money,
 * by the day each game is played, with the month's totals; and its payouts, as Stripe has them,
 * newest first. A test seats the rows (`moneyRow(…)`, `payout(…)`); the fake keeps the backend's
 * rules for which month a row is in, their order and the totals. A test that is about one reply
 * overrides that handler with `stub.on`.
 */

import { randomUUID } from 'node:crypto';

import type { components } from '../../src/generated/schema';

import { refusal, type StubBackend } from './backend';
import { atClubHour, clubTime, dayFromToday } from './clock';
import type { Court } from './courts';

type MoneyBooking = components['schemas']['MoneyBookingSchema'];
type Totals = components['schemas']['MoneyTotalsSchema'];
export type Payout = components['schemas']['PayoutSchema'];
type ErrorBody = components['schemas']['ErrorResponse'];

const MONTH = /^\d{4}-(0[1-9]|1[0-2])$/;

/**
 * **One booking's money**, on `court` at `hour` of the local `day`: a full game played and paid,
 * 140 zł collected, nothing refunded and 6 zł of card fees, unless the test says otherwise. What
 * is the club's is derived, as the backend derives it.
 */
export function moneyRow(
  fields: { court: Court; day: string; hour: number } & Partial<
    Omit<MoneyBooking, 'court_name' | 'sport' | 'starts_at' | 'net_grosze'>
  >,
): MoneyBooking {
  const { court, day, hour, ...rest } = fields;
  const row = {
    booking_id: randomUUID(),
    starts_at: atClubHour(day, hour),
    court_name: court.name,
    sport: court.sport,
    status: 'PLAYED' as const,
    collected_grosze: 140_00,
    refunded_grosze: 0,
    card_fees_grosze: 6_00,
    paid_out: false,
    ...rest,
  };
  return {
    ...row,
    net_grosze: row.collected_grosze - row.refunded_grosze - row.card_fees_grosze,
  };
}

/** **A payout to the club's bank**, in it already unless the test says otherwise. */
export function payout(fields: Pick<Payout, 'amount_grosze' | 'arrives_at'> & Partial<Payout>) {
  return { payout_id: `po_${randomUUID().slice(0, 12)}`, status: 'PAID' as const, ...fields };
}

export class FakeClubMoney {
  /** Every booking that took money, any month; a month lists its own, soonest first. */
  bookings: MoneyBooking[] = [];
  /** The payouts Stripe has made to the club's bank, in any order; the list is newest first. */
  payouts: Payout[] = [];

  constructor(
    private readonly stub: StubBackend,
    /** `null` when the request carries a live access token; the 401 to send otherwise. */
    private readonly guard: (authorization: string | undefined) => {
      status: 401;
      body: ErrorBody;
    } | null,
  ) {}

  /** Seat a booking's money, and answer it, so a test can name it. */
  add(row: MoneyBooking): MoneyBooking {
    this.bookings.push(row);
    return row;
  }

  install(): this {
    this.stub.on('get', '/api/v1/club/money', ({ headers, query }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      const month = query.month ?? dayFromToday(0).slice(0, 7);
      if (!MONTH.test(month)) return { status: 422, body: refusal('validation_error') };
      const rows = this.bookings
        .filter((row) => clubTime(row.starts_at).day.startsWith(`${month}-`))
        .sort((a, b) => Date.parse(a.starts_at) - Date.parse(b.starts_at));
      const sum = (pick: (row: MoneyBooking) => number) =>
        rows.reduce((total, row) => total + pick(row), 0);
      const totals: Totals = {
        collected_grosze: sum((row) => row.collected_grosze),
        refunded_grosze: sum((row) => row.refunded_grosze),
        card_fees_grosze: sum((row) => row.card_fees_grosze),
        net_grosze: sum((row) => row.net_grosze),
      };
      return {
        status: 200,
        body: { month, read_at: new Date().toISOString(), totals, bookings: rows },
      };
    });

    this.stub.on('get', '/api/v1/club/payouts', ({ headers, query }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      const limit = Number(query.limit ?? 30);
      const newest = [...this.payouts].sort(
        (a, b) => Date.parse(b.arrives_at) - Date.parse(a.arrives_at),
      );
      return { status: 200, body: { payouts: newest.slice(0, limit) } };
    });

    return this;
  }
}
