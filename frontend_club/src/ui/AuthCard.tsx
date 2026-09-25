import type { ReactNode } from 'react';

import styles from './AuthCard.module.css';
import { Wordmark } from './Wordmark';

/**
 * **The signed-out frame** (club mock 1): paper, and one white card with the wordmark at its
 * head. `wide` is for the sign-up form, whose map wants the room.
 */
export function AuthCard({
  title,
  lead,
  wide = false,
  children,
}: {
  title?: string;
  lead?: ReactNode;
  wide?: boolean;
  children: ReactNode;
}) {
  return (
    <main className={styles.page}>
      <section className={wide ? `${styles.card} ${styles.wide}` : styles.card}>
        <Wordmark />
        {title === undefined ? null : <h1 className={styles.title}>{title}</h1>}
        {lead === undefined ? null : <p className={styles.lead}>{lead}</p>}
        {children}
      </section>
    </main>
  );
}
