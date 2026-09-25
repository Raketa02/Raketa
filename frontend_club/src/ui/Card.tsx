import type { ReactNode } from 'react';

import styles from './Card.module.css';

/** A white panel on paper (club mock 2's table, club mock 3's form). */
export function Card({ children }: { children: ReactNode }) {
  return <section className={styles.card}>{children}</section>;
}
