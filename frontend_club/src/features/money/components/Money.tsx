import type { PaymentsStatus } from '@/features/overview/mappers';
import { Card } from '@/ui/Card';
import { PageHeader } from '@/ui/PageHeader';
import { PeriodBar } from '@/ui/PeriodBar';

import { MONEY_COPY, monthTitle } from '../copy';
import type { MoneyMonth, Payout } from '../mappers';
import { monthAfter, monthHref } from '../schemas';

import styles from './Money.module.css';
import { MoneyTable } from './MoneyTable';
import { MonthPicker } from './MonthPicker';
import { Payouts } from './Payouts';
import { Totals } from './Totals';

const COPY = MONEY_COPY;

/**
 * **Money** (the screens B7, the mechanics §16.11): one month at a time, *‹ March 2026 ›* and a
 * month box, the month's totals at the top and its bookings under them, by the day each game is
 * played on; then the payouts, and the club's own Stripe dashboard.
 */
export function Money({
  month,
  payouts,
  payments,
}: {
  month: MoneyMonth;
  /** `null` when Stripe could not be reached for them. */
  payouts: readonly Payout[] | null;
  /** Where the club's Stripe account stands. */
  payments: PaymentsStatus;
}) {
  const at = (other: string) => monthHref(other === month.thisMonth ? null : other);
  const title = monthTitle(month.month);
  return (
    <>
      <PageHeader caption={COPY.caption} title={COPY.title} />
      <Card labelledBy="month-title">
        <PeriodBar
          label={COPY.month.label}
          titleId="month-title"
          title={title}
          previous={{ href: at(monthAfter(month.month, -1)), label: COPY.month.previous }}
          next={{ href: at(monthAfter(month.month, 1)), label: COPY.month.next }}
          back={
            month.month === month.thisMonth
              ? null
              : { href: monthHref(null), label: COPY.month.thisMonth }
          }
          picker={<MonthPicker month={month.month} />}
        />
        <Totals totals={month.totals} />
        {month.bookings.length === 0 ? (
          <p className={styles.none}>{COPY.empty(title)}</p>
        ) : (
          <MoneyTable bookings={month.bookings} />
        )}
      </Card>
      <Payouts payouts={payouts} payments={payments} />
    </>
  );
}
