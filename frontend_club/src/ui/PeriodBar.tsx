import Link from 'next/link';
import type { ReactNode } from 'react';

import styles from './PeriodBar.module.css';
import { TextLink } from './TextLink';

/** A way to another period: where it goes, and what a screen reader calls it. */
interface Way {
  readonly href: string;
  readonly label: string;
}

/**
 * **One period at a time** (Bookings' day, Money's month): *‹ its name ›*, a way back to the
 * present while another is shown, and at the right a box to go to any (`PeriodPicker`).
 * The title's `id` names the card it heads.
 */
export function PeriodBar({
  label,
  titleId,
  title,
  previous,
  next,
  back,
  picker,
}: {
  /** The controls, as a screen reader names them. */
  label: string;
  titleId: string;
  title: string;
  previous: Way;
  next: Way;
  /** Back to today, or this month, while another is shown; `null` while it is. */
  back: Way | null;
  picker: ReactNode;
}) {
  return (
    <div className={styles.bar}>
      <nav aria-label={label} className={styles.nav}>
        <Link href={previous.href} className={styles.arrow} aria-label={previous.label}>
          ‹
        </Link>
        <h2 id={titleId} className={styles.title}>
          {title}
        </h2>
        <Link href={next.href} className={styles.arrow} aria-label={next.label}>
          ›
        </Link>
        {back === null ? null : <TextLink href={back.href}>{back.label}</TextLink>}
      </nav>
      {picker}
    </div>
  );
}
