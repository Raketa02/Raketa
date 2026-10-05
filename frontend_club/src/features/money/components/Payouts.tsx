import { shortDay } from '@/features/bookings/copy';
import type { PaymentsStatus } from '@/features/overview/mappers';
import { ButtonLink } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { formatZloty } from '@/ui/format';
import { Notice } from '@/ui/Notice';
import { SectionHeader } from '@/ui/SectionHeader';
import tableStyles from '@/ui/Table.module.css';
import { Tag } from '@/ui/Tag';
import { TextLink } from '@/ui/TextLink';

import { MONEY_COPY } from '../copy';
import type { Payout, PayoutStatus } from '../mappers';

import styles from './Money.module.css';

const COPY = MONEY_COPY.payouts;

/**
 * **Stripe's own dashboard**, where the club signs in to its account. Each club's account is its
 * own, with Stripe's full dashboard, so one address serves every club.
 */
const STRIPE_DASHBOARD = 'https://dashboard.stripe.com';

const TONES = {
  PENDING: 'amber',
  IN_TRANSIT: 'amber',
  PAID: 'green',
  FAILED: 'red',
  CANCELLED: 'neutral',
} as const satisfies Record<PayoutStatus, string>;

function PayoutsTable({ payouts }: { payouts: readonly Payout[] }) {
  const { columns } = COPY;
  return (
    <table className={tableStyles.table}>
      <thead className={tableStyles.head}>
        <tr>
          <th scope="col">{columns.date}</th>
          <th scope="col" className={styles.figureHead}>
            {columns.amount}
          </th>
          <th scope="col">{columns.status}</th>
        </tr>
      </thead>
      <tbody>
        {payouts.map((payout) => (
          <tr key={payout.id}>
            <th scope="row" className={styles.when}>
              {shortDay(payout.day)}
            </th>
            <td className={styles.figure}>{formatZloty(payout.amountGrosze)}</td>
            <td>
              <div className={styles.status}>
                <Tag tone={TONES[payout.status]}>{COPY.statuses[payout.status]}</Tag>
                {payout.status === 'FAILED' ? (
                  <>
                    {' '}
                    <span className={styles.why}>{COPY.failed}</span>
                  </>
                ) : null}
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/**
 * **Payouts** (the screens B7): what Stripe has sent to the club's bank, newest first, each with
 * the day it reaches the bank, its amount and where it stands; and the club's own Stripe
 * dashboard, for its bank details, disputes and tax documents. A club that has not started
 * connecting payments has no account to open, so it is sent to connect them instead.
 */
export function Payouts({
  payouts,
  payments,
}: {
  /** `null` when Stripe could not be reached for them. */
  payouts: readonly Payout[] | null;
  payments: PaymentsStatus;
}) {
  const connected = payments !== 'NOT_STARTED';
  return (
    <Card labelledBy="payouts-title">
      <SectionHeader
        id="payouts-title"
        title={COPY.title}
        lead={COPY.lead}
        aside={
          connected ? (
            <ButtonLink href={STRIPE_DASHBOARD} newTab>
              {COPY.dashboard}
            </ButtonLink>
          ) : undefined
        }
      />
      {payouts === null ? (
        <Notice tone="error">{COPY.unreachable}</Notice>
      ) : payouts.length > 0 ? (
        <PayoutsTable payouts={payouts} />
      ) : connected ? (
        <p className={styles.none}>{COPY.none}</p>
      ) : (
        <p className={styles.none}>
          {COPY.notConnected} <TextLink href="/overview">{COPY.connect}</TextLink>
        </p>
      )}
    </Card>
  );
}
