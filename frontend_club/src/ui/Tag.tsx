import type { ReactNode } from 'react';

import styles from './Tag.module.css';

/**
 * **A word set on a tinted pill** (club mock 4's *active* and *invited*): green for what is in
 * order, amber for what is waiting, red for what has lapsed.
 */
export function Tag({ tone, children }: { tone: 'green' | 'amber' | 'red'; children: ReactNode }) {
  return <span className={`${styles.tag} ${styles[tone]}`}>{children}</span>;
}
