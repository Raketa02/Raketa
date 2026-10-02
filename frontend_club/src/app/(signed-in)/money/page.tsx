import type { Metadata } from 'next';

import { Money } from '@/features/money/components/Money';
import { MONEY_COPY } from '@/features/money/copy';
import { getMoneyMonth, getPayouts } from '@/features/money/queries';
import { readMonthQuery } from '@/features/money/schemas';
import { getSetup } from '@/features/overview/queries';

export const metadata: Metadata = { title: MONEY_COPY.title };

/**
 * **Money** (the screens B7): the month the address names, or this one; the payouts; and where
 * the club's Stripe account stands, which says whether it has a dashboard to open.
 */
export default async function MoneyPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = readMonthQuery(await searchParams);
  const [month, payouts, setup] = await Promise.all([
    getMoneyMonth(query),
    getPayouts(),
    getSetup(),
  ]);
  return <Money month={month} payouts={payouts} payments={setup.payments} />;
}
