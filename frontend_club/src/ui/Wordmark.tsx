import Link from 'next/link';

import styles from './Wordmark.module.css';

/** The coral square and **Rakieta for Clubs** (club mock 1). The brand is Rakieta (ADR-0211). */
export function Wordmark({ href }: { href?: string }) {
  const mark = (
    <>
      <span className={styles.mark} aria-hidden="true" />
      <span className={styles.name}>Rakieta for Clubs</span>
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
