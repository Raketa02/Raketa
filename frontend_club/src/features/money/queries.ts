import 'server-only';

import { clubDay } from '@/features/courts/mappers';
import { readAsClub } from '@/server/club';

import { toMoneyMonth, toPayouts, type MoneyMonth, type Payout } from './mappers';
import type { MonthQuery } from './schemas';

/** **A month of the club's money**: this month when the query names none. */
export async function getMoneyMonth(query: MonthQuery): Promise<MoneyMonth> {
  const outcome = await readAsClub((api, auth) =>
    api.GET('/api/v1/club/money', {
      ...auth,
      params: { query: query.month === null ? {} : { month: query.month } },
    }),
  );
  if (!outcome.ok) throw new Error(`The club's money could not be read: ${outcome.error.code}`);
  // Asked for no month, the backend read this one: its month, not this server's clock, says which.
  const thisMonth = query.month === null ? outcome.data.month : clubDay(Date.now()).slice(0, 7);
  return toMoneyMonth(outcome.data, thisMonth);
}

/**
 * **The club's payouts, as Stripe has them**, newest first; `null` when they could not be read.
 * They are read from Stripe as the page is drawn, and Stripe may not answer: the month's money
 * is the backend's own, and is shown all the same.
 */
export async function getPayouts(): Promise<readonly Payout[] | null> {
  const outcome = await readAsClub((api, auth) => api.GET('/api/v1/club/payouts', auth));
  return outcome.ok ? toPayouts(outcome.data) : null;
}
