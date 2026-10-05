import type { ReactNode } from 'react';

import styles from './Card.module.css';

/**
 * A white panel on paper (club mock 2's table, club mock 3's form). Named by a heading inside
 * it (`labelledBy`), it is a region a screen reader can jump to, as each section of Courts &
 * prices is.
 */
export function Card({
  labelledBy,
  id,
  children,
}: {
  labelledBy?: string;
  /** So a link can lead to it: `/courts#hours`. */
  id?: string;
  children: ReactNode;
}) {
  return (
    <section id={id} aria-labelledby={labelledBy} className={styles.card}>
      {children}
    </section>
  );
}
