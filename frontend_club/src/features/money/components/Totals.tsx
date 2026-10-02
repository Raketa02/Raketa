import { formatZloty } from '@/ui/format';

import { MONEY_COPY } from '../copy';
import type { Takings } from '../mappers';

import styles from './Money.module.css';

const COPY = MONEY_COPY.totals;

/** **The month's totals, at the top** (the screens B7): collected, refunded, card fees and net. */
export function Totals({ totals }: { totals: Takings }) {
  const figures = [
    [COPY.collected, totals.collectedGrosze],
    [COPY.refunded, totals.refundedGrosze],
    [COPY.cardFees, totals.cardFeesGrosze],
    [COPY.net, totals.netGrosze],
  ] as const;
  return (
    <dl className={styles.totals}>
      {figures.map(([label, grosze]) => (
        <div key={label} className={styles.total}>
          <dt>{label}</dt>
          <dd>{formatZloty(grosze)}</dd>
        </div>
      ))}
    </dl>
  );
}
