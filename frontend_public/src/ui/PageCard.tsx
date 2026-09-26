import type { ReactNode } from 'react';

import styles from './PageCard.module.css';
import { Wordmark } from './Wordmark';

/**
 * **Every page's frame**: paper, and one white card with the wordmark at its head, as the club
 * website's signed-out pages are drawn (club mock 1). Laid out for a phone first: the card fills
 * the width less a gutter, and stops growing at a narrow column on anything wider.
 */
export function PageCard({ brand, children }: { brand: string; children: ReactNode }) {
  return (
    <main className={styles.page}>
      <div className={styles.card}>
        <Wordmark name={brand} />
        {children}
      </div>
    </main>
  );
}

/** A page's title and the line under it, for a page that is only words. */
export function PageTitle({ title, lead }: { title: string; lead: string }) {
  return (
    <header className={styles.header}>
      <h1 className={styles.title}>{title}</h1>
      <p className={styles.lead}>{lead}</p>
    </header>
  );
}

/** A part of the card below its head, set off by a rule. */
export function CardSection({ children }: { children: ReactNode }) {
  return <section className={styles.section}>{children}</section>;
}
