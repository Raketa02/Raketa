import { formatZloty } from '@/ui/format';
import tableStyles from '@/ui/Table.module.css';

import { MONEY_COPY, playedAt, sportAndStatus } from '../copy';
import type { MoneyBooking } from '../mappers';

import styles from './Money.module.css';

const COPY = MONEY_COPY;

/** A figure's cell, which says on a phone what it is, since the column heads are gone there. */
function Figure({ label, grosze }: { label: string; grosze: number }) {
  return (
    <td
      className={`${styles.figure} ${tableStyles.labelled}`}
      data-label={label}
      data-below-nought={grosze < 0}
    >
      {formatZloty(grosze)}
    </td>
  );
}

/**
 * **A month's bookings, booking by booking** (the screens B7): when each game is played, its
 * court, sport and status, what the players paid, what was given back, Stripe's card fees and
 * what is the club's, and whether a payout has carried it to the bank yet.
 */
export function MoneyTable({ bookings }: { bookings: readonly MoneyBooking[] }) {
  const { columns } = COPY;
  return (
    <table className={tableStyles.table}>
      <thead className={tableStyles.head}>
        <tr>
          <th scope="col">{columns.when}</th>
          <th scope="col">{columns.court}</th>
          <th scope="col" className={styles.figureHead}>
            {columns.collected}
          </th>
          <th scope="col" className={styles.figureHead}>
            {columns.refunded}
          </th>
          <th scope="col" className={styles.figureHead}>
            {columns.cardFees}
          </th>
          <th scope="col" className={styles.figureHead}>
            {columns.net}
          </th>
          <th scope="col">{columns.paidOut}</th>
        </tr>
      </thead>
      <tbody>
        {bookings.map((booking) => (
          <tr key={booking.id}>
            <th scope="row" className={styles.when}>
              {playedAt(booking.day, booking.from)}
            </th>
            <td>
              <span className={styles.court}>{booking.court}</span>{' '}
              <span className={styles.what}>{sportAndStatus(booking.sport, booking.status)}</span>
            </td>
            <Figure label={columns.collected} grosze={booking.takings.collectedGrosze} />
            <Figure label={columns.refunded} grosze={booking.takings.refundedGrosze} />
            <Figure label={columns.cardFees} grosze={booking.takings.cardFeesGrosze} />
            <Figure label={columns.net} grosze={booking.takings.netGrosze} />
            <td>
              {booking.paidOut ? (
                <span className={styles.paidOut}>{COPY.paidOut}</span>
              ) : (
                <span className={styles.notPaidOut}>{COPY.notPaidOut}</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
