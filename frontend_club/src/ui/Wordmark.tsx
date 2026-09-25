import Link from 'next/link';

import styles from './Wordmark.module.css';

/** The coral square and **Raketa for Clubs** (club mock 1). The brand is Raketa (ADR-0187 §8). */
export function Wordmark({ href }: { href?: string }) {
  const mark = (
    <>
      <span className={styles.mark} aria-hidden="true" />
      <span className={styles.name}>Raketa for Clubs</span>
    </>
  );
  return href === undefined ? (
    <span className={styles.wordmark}>{mark}</span>
  ) : (
    <Link href={href} className={styles.wordmark}>
      {mark}
    </Link>
  );
}
